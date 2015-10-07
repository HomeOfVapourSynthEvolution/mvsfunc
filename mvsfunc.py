################################################################################################################################
## mvsfunc - mawen1250's VapourSynth functions
## 2015.09
################################################################################################################################
## Requirments:
##     fmtconv
##     zimg
##     BM3D
################################################################################################################################
## Main functions:
##     Depth
##     ToRGB
##     ToYUV
##     BM3D
################################################################################################################################
## Utility functions:
##     Min
##     Max
##     Avg
##     MinFilter
##     MaxFilter
##     LimitFilter
##     ShowAverage
##     FilterCombed
################################################################################################################################
## Frame property functions:
##     SetColorSpace
##     AssumeFrame
##     AssumeTFF
##     AssumeBFF
##     AssumeField
##     AssumeCombed
################################################################################################################################
## Helper functions:
##     GetMatrix
################################################################################################################################


import vapoursynth as vs


################################################################################################################################


VSMaxPlaneNum = 3


################################################################################################################################





################################################################################################################################
################################################################################################################################
################################################################################################################################
## Main functions below
################################################################################################################################
################################################################################################################################
################################################################################################################################


################################################################################################################################
## Main function: Depth()
################################################################################################################################
## Bit depth conversion with dithering
################################################################################################################################
## Basic parameters
##     input {clip}: clip to be converted
##         can be of YUV/RGB/Gray/YCoCg color family, can be of 8-16 bit integer or 16/32 bit float
##     depth {int}: output bit depth, can be 8-16 bit integer or 16/32 bit float
##         default is the same as that of the input clip
##     sample {int}: output sample type, can be 0(vs.INTEGER) or 1(vs.FLOAT)
##         default is the same as that of the input clip
##     fulls {bool}: define if input clip is of full range
##         the frame property '_ColorRange' will be overwritten if this argument is not None
##         default: None, assume True for RGB/YCgCo input, assume False for Gray/YUV input
##     fulld {bool}: define if output clip is of full range
##         the frame property '_ColorRange' will be overwritten by it
##         default is the same as "fulls"
################################################################################################################################
## Advanced parameters
##     dither {int|str}: dithering algorithm applied for depth conversion
##         - {int}: same as "dmode" in fmtc.bitdepth, will be automatically converted if using z.Depth
##         - {str}: same as "dither" in z.Depth, will be automatically converted if using fmtc.bitdepth
##         - default:
##             - output depth is 32, and conversions without quantization error: 1 | "none"
##             - otherwise: 3 | "error_diffusion"
##     useZ {bool}: force using of z.Depth or fmtc.bitdepth for depth conversion
##         By default, z.Depth is used when full range integer is involved.
##             Full range definition is [0, (1 << depth) - 1] for z.Depth and [0, 1 << depth] for fmtc.bitdepth.
##             The standard definition is [0, (1 << depth) - 1] thus z.Depth is preferred in this case.
##             Though it can be weird for full range chroma, which is [0.5, 1 << (depth - 1), (1 << depth) - 0.5].
##         When 13-,15-bit integer or 16-bit float is involved, z.Depth is always used.
##         - None: automatically determined
##         - False: force fmtc.bitdepth
##         - True: force z.Depth
##         default: None
################################################################################################################################
## Parameters of fmtc.bitdepth
##     ampo, ampn, dyn, staticnoise: same as those in fmtc.bitdepth, ignored when using z.Depth
################################################################################################################################
def Depth(input, depth=None, sample=None, fulls=None, fulld=None, \
dither=None, useZ=None, ampo=None, ampn=None, dyn=None, staticnoise=None):
    # Set VS core and function name
    core = vs.get_core()
    funcName = 'Depth'
    clip = input
    
    if not isinstance(input, vs.VideoNode):
        raise TypeError(funcName + ': \"input\" must be a clip!')
    
    # Get properties of input clip
    sFormat = input.format
    
    sColorFamily = sFormat.color_family
    sIsRGB = sColorFamily == vs.RGB
    sIsYUV = sColorFamily == vs.YUV
    sIsGRAY = sColorFamily == vs.GRAY
    sIsYCOCG = sColorFamily == vs.YCOCG
    if sColorFamily == vs.COMPAT:
        raise ValueError(funcName + ': Color family *COMPAT* is not supported!')
    
    sbitPS = sFormat.bits_per_sample
    sSType = sFormat.sample_type
    
    if fulls is None:
        # If not set, assume limited range for YUV and Gray input
        fulls = False if sIsYUV or sIsGRAY else True
    elif not isinstance(fulls, int):
        raise TypeError(funcName + ': \"fulls\" must be a bool!')
    else:
        clip = SetColorSpace(clip, ColorRange=0 if fulls else 1)
    
    # Get properties of output clip
    if depth is None:
        dbitPS = sbitPS
    elif not isinstance(depth, int):
        raise TypeError(funcName + ': \"depth\" must be a int!')
    else:
        dbitPS = depth
    if sample is None:
        if depth is None:
            dSType = sSType
        else:
            dSType = vs.FLOAT if dbitPS >= 32 else 0
    elif not isinstance(sample, int):
        raise TypeError(funcName + ': \"sample\" must be a int!')
    elif sample != vs.INTEGER and sample != vs.FLOAT:
        raise ValueError(funcName + ': \"sample\" must be either 0(vs.INTEGER) or 1(vs.FLOAT)!')
    else:
        dSType = sample
    if dSType == vs.INTEGER and (dbitPS < 8 or dbitPS > 16):
        raise ValueError(funcName + ': {0}-bit integer output is not supported!'.format(dbitPS))
    if dSType == vs.FLOAT and (dbitPS != 16 and dbitPS != 32):
        raise ValueError(funcName + ': {0}-bit float output is not supported!'.format(dbitPS))
    
    if fulld is None:
        fulld = fulls
    elif not isinstance(fulld, int):
        raise TypeError(funcName + ': \"fulld\" must be a bool!')
    
    # Whether to use z.Depth or fmtc.bitdepth for conversion
    # If not set, when full range is involved for integer format, use z.Depth
    # When 11-,13-,14-,15-bit integer or 16-bit float format is involved, always use z.Depth
    if useZ is None:
        useZ = (sSType == vs.INTEGER and fulls) or (dSType == vs.INTEGER and fulld)
    elif not isinstance(useZ, int):
        raise TypeError(funcName + ': \"useZ\" must be a bool!')
    if sSType == vs.INTEGER and (sbitPS == 13 or sbitPS == 15):
        useZ = True
    if dSType == vs.INTEGER and (dbitPS == 13 or dbitPS == 15):
        useZ = True
    if (sSType == vs.FLOAT and sbitPS < 32) or (dSType == vs.FLOAT and dbitPS < 32):
        useZ = True
    
    # Dithering type
    if ampn is not None and not isinstance(ampn, float) and not isinstance(ampn, int):
            raise TypeError(funcName + ': \"ampn\" must be a float or int!')
    
    if dither is None:
        if dbitPS == 32 or (dbitPS >= sbitPS and fulld == fulls and fulld == False):
            dither = "none" if useZ else 1
        else:
            dither = "error_diffusion" if useZ else 3
    elif not isinstance(dither, int) and not isinstance(dither, str):
        raise TypeError(funcName + ': \"dither\" must be a int or str!')
    else:
        if isinstance(dither, str):
            dither = dither.lower()
            if dither != "none" and dither != "ordered" and dither != "random" and dither != "error_diffusion":
                raise ValueError(funcName + ': Unsupported \"dither\" specified!')
        else:
            if dither < 0 or dither > 7:
                raise ValueError(funcName + ': Unsupported \"dither\" specified!')
        if useZ and isinstance(dither, int):
            if dither == 0:
                dither = "ordered"
            elif dither == 1 or dither == 2:
                if ampn is not None and ampn > 0:
                    dither = "random"
                else:
                    dither = "none"
            else:
                dither = "error_diffusion"
        elif not useZ and isinstance(dither, str):
            if dither == "none":
                dither = 1
            elif dither == "ordered":
                dither = 0
            elif dither == "random":
                if ampn is None:
                    dither = 1
                    ampn = 1
                elif ampn > 0:
                    dither = 1
                else:
                    dither = 3
            else:
                dither = 3
    
    if not useZ:
        if ampo is None:
            ampo = 1.5 if dither == 0 else 1
        elif not isinstance(ampo, float) and not isinstance(ampo, int):
            raise TypeError(funcName + ': \"ampo\" must be a float or int!')
    
    # Skip processing if not needed
    if dSType == sSType and dbitPS == sbitPS and (sSType == vs.FLOAT or fulld == fulls):
        return clip
    
    # Apply conversion
    if useZ:
        clip = core.z.Depth(clip, dither=dither, sample=dSType, depth=dbitPS, fullrange_in=fulls, fullrange_out=fulld)
    else:
        clip = core.fmtc.bitdepth(clip, bits=dbitPS, flt=dSType, fulls=fulls, fulld=fulld, dmode=dither, ampo=ampo, ampn=ampn, dyn=dyn, staticnoise=staticnoise)
    
    # Output
    clip = SetColorSpace(clip, ColorRange=0 if fulld else 1)
    return clip
################################################################################################################################


################################################################################################################################
## Main function: ToRGB()
################################################################################################################################
## Convert any color space to full range RGB.
## Thus, if input is limited range RGB, it will be converted to full range.
## If matrix is 10, "2020cl" or "bt2020c", the output is linear RGB
################################################################################################################################
## Basic parameters
##     input {clip}: clip to be converted
##         can be of YUV/RGB/Gray/YCoCg color family, can be of 8-16 bit integer or 16/32 bit float
##     matrix {int|str}: color matrix of input clip, only makes sense for YUV/YCoCg input
##         decides the conversion coefficients from YUV to RGB
##         check GetMatrix() for available values
##         the frame property '_Matrix' will be overwritten if this argument is not None
##         default: None, guessed according to the color family and size of input clip
##     depth {int}: output bit depth, can be 8-16 bit integer or 16/32 bit float
##         default is the same as that of the input clip
##     sample {int}: output sample type, can be 0(vs.INTEGER) or 1(vs.FLOAT)
##         default is the same as that of the input clip
##     full {bool}: define if input clip is of full range
##         default: guessed according to the color family of input clip and "matrix"
################################################################################################################################
## Parameters of depth conversion
##     dither, useZ, ampo, ampn, dyn, staticnoise:
##         same as those in Depth()
################################################################################################################################
## Parameters of resampling
##     kernel, taps, a1, a2, cplace:
##         used for chroma re-sampling, same as those in fmtc.resample
##         default: kernel="bicubic", a1=0, a2=0.5, also known as "Catmull-Rom".
################################################################################################################################
def ToRGB(input, matrix=None, depth=None, sample=None, full=None, \
dither=None, useZ=None, ampo=None, ampn=None, dyn=None, staticnoise=None, \
kernel=None, taps=None, a1=None, a2=None, cplace=None):
    # Set VS core and function name
    core = vs.get_core()
    funcName = 'ToRGB'
    clip = input
    
    if not isinstance(input, vs.VideoNode):
        raise TypeError(funcName + ': \"input\" must be a clip!')
    
    # Get string format parameter "matrix"
    if matrix is not None:
        matrix_id = GetMatrix(input, matrix, True, True)
        clip = SetColorSpace(clip, Matrix=False if matrix_id > 10 else matrix_id)
    matrix = GetMatrix(input, matrix, True)
    
    # Get properties of input clip
    sFormat = input.format
    
    sColorFamily = sFormat.color_family
    sIsRGB = sColorFamily == vs.RGB
    sIsYUV = sColorFamily == vs.YUV
    sIsGRAY = sColorFamily == vs.GRAY
    sIsYCOCG = sColorFamily == vs.YCOCG
    if sColorFamily == vs.COMPAT:
        raise ValueError(funcName + ': Color family *COMPAT* is not supported!')
    
    sbitPS = sFormat.bits_per_sample
    sSType = sFormat.sample_type
    
    sHSubS = 1 << sFormat.subsampling_w
    sVSubS = 1 << sFormat.subsampling_h
    
    if full is None:
        # If not set, assume limited range for YUV and Gray input
        # Assume full range for YCgCo and OPP input
        if (sIsGRAY or sIsYUV or sIsYCOCG) and (matrix == "RGB" or matrix == "YCgCo" or matrix == "OPP"):
            fulls = True
        else:
            fulls = False if sIsYUV or sIsGRAY else True
    elif not isinstance(full, int):
        raise TypeError(funcName + ': \"full\" must be a bool!')
    else:
        fulls = full
    
    # Get properties of output clip
    if depth is None:
        dbitPS = sbitPS
    elif not isinstance(depth, int):
        raise TypeError(funcName + ': \"depth\" must be a int!')
    else:
        dbitPS = depth
    if sample is None:
        if depth is None:
            dSType = sSType
        else:
            dSType = vs.FLOAT if dbitPS >= 32 else 0
    elif not isinstance(sample, int):
        raise TypeError(funcName + ': \"sample\" must be a int!')
    elif sample != vs.INTEGER and sample != vs.FLOAT:
        raise ValueError(funcName + ': \"sample\" must be either 0(vs.INTEGER) or 1(vs.FLOAT)!')
    else:
        dSType = sample
    if dSType == vs.INTEGER and (dbitPS < 8 or dbitPS > 16):
        raise ValueError(funcName + ': {0}-bit integer output is not supported!'.format(dbitPS))
    if dSType == vs.FLOAT and (dbitPS != 16 and dbitPS != 32):
        raise ValueError(funcName + ': {0}-bit float output is not supported!'.format(dbitPS))
    
    fulld = True
    
    # Get properties of internal processed clip
    pSType = max(sSType, dSType) # If float sample type is involved, then use float for conversion
    if pSType == vs.FLOAT:
        # For float sample type, only 32-bit is supported by fmtconv
        pbitPS = 32
    else:
        # Apply conversion in the higher one of input and output bit depth
        pbitPS = max(sbitPS, dbitPS)
        # For integer sample type, only 8-, 9-, 10-, 12-, 16-bit is supported by fmtc.matrix
        if pbitPS == 11:
            pbitPS = 12
        elif pbitPS > 12 and pbitPS < 16:
            pbitPS = 16
        if sHSubS != 1 or sVSubS != 1:
            # When chroma re-sampling is needed, always process in 16-bit for integer sample type
            pbitPS = 16
    
    # fmtc.resample parameters
    if kernel is None:
        kernel = "bicubic"
        if a1 is None and a2 is None:
            a1 = 0
            a2 = 0.5
    elif not isinstance(kernel, str):
        raise TypeError(funcName + ': \"kernel\" must be a str!')
    
    # Conversion
    if sIsRGB:
        # Skip matrix conversion for RGB input
        # Apply depth conversion for output clip
        clip = Depth(clip, dbitPS, dSType, fulls, fulld, dither, useZ, ampo, ampn, dyn, staticnoise)
    elif sIsGRAY:
        # Apply depth conversion for output clip
        clip = Depth(clip, dbitPS, dSType, fulls, fulld, dither, useZ, ampo, ampn, dyn, staticnoise)
        # Shuffle planes for Gray input
        clip = core.std.ShufflePlanes([clip,clip,clip], [0,0,0], vs.RGB)
    else:
        # Apply depth conversion for processed clip
        clip = Depth(clip, pbitPS, pSType, fulls, fulls, dither, useZ, ampo, ampn, dyn, staticnoise)
        # Apply chroma up-sampling if needed
        if sHSubS != 1 or sVSubS != 1:
            clip = core.fmtc.resample(clip, kernel=kernel, taps=taps, a1=a1, a2=a2, css="444", planes=[2,3,3], fulls=fulls, fulld=fulls, cplace=cplace)
        # Apply matrix conversion for YUV or YCoCg input
        if matrix == "OPP":
            clip = core.fmtc.matrix(clip, fulls=fulls, fulld=fulld, coef=[1,1,2/3,0, 1,0,-4/3,0, 1,-1,2/3,0], col_fam=vs.RGB)
        elif matrix == "2020cl":
            clip = core.fmtc.matrix2020cl(clip, full=fulls)
        else:
            clip = core.fmtc.matrix(clip, mat=matrix, fulls=fulls, fulld=fulld, col_fam=vs.RGB)
        # Apply depth conversion for output clip
        clip = Depth(clip, dbitPS, dSType, fulld, fulld, dither, useZ, ampo, ampn, dyn, staticnoise)
    
    # Output
    return clip
################################################################################################################################


################################################################################################################################
## Main function: ToYUV()
################################################################################################################################
## Convert any color space to YUV/YCoCg with/without sub-sampling.
## If input is RGB, it's assumed to be of full range.
##     Thus, limited range RGB clip should first be manually converted to full range before call this function.
## If matrix is 10, "2020cl" or "bt2020c", the input should be linear RGB
################################################################################################################################
## Basic parameters
##     input {clip}: clip to be converted
##         can be of YUV/RGB/Gray/YCoCg color family, can be of 8-16 bit integer or 16/32 bit float
##     matrix {int|str}: color matrix of output clip
##         decides the conversion coefficients from RGB to YUV
##         check GetMatrix() for available values
##         the frame property '_Matrix' will be overwritten if this argument is not None
##         default: None, guessed according to the color family and size of input clip
##     css {str}: chroma sub-sampling of output clip, similar to the one in fmtc.resample
##         If two number is defined, then the first is horizontal sub-sampling and the second is vertical sub-sampling.
##         For example, "11" is 4:4:4, "21" is 4:2:2, "22" is 4:2:0.
##         preset values:
##         - "444" | "4:4:4" | "11"
##         - "440" | "4:4:0" | "12"
##         - "422" | "4:2:2" | "21"
##         - "420" | "4:2:0" | "22"
##         - "411" | "4:1:1" | "41"
##         - "410" | "4:1:0" | "42"
##         default: 4:4:4 for RGB/Gray input, same as input is for YUV/YCoCg input
##     depth {int}: output bit depth, can be 8-16 bit integer or 16/32 bit float
##         default is the same as that of the input clip
##     sample {int}: output sample type, can be 0(vs.INTEGER) or 1(vs.FLOAT)
##         default is the same as that of the input clip
##     full {bool}: define if input/output Gray/YUV/YCoCg clip is of full range
##         default: guessed according to the color family of input clip and "matrix"
################################################################################################################################
## Parameters of depth conversion
##     dither, useZ, ampo, ampn, dyn, staticnoise:
##         same as those in Depth()
################################################################################################################################
## Parameters of resampling
##     kernel, taps, a1, a2, cplace:
##         used for chroma re-sampling, same as those in fmtc.resample
##         default: kernel="bicubic", a1=0, a2=0.5, also known as "Catmull-Rom"
################################################################################################################################
def ToYUV(input, matrix=None, css=None, depth=None, sample=None, full=None, \
dither=None, useZ=None, ampo=None, ampn=None, dyn=None, staticnoise=None, \
kernel=None, taps=None, a1=None, a2=None, cplace=None):
    # Set VS core and function name
    core = vs.get_core()
    funcName = 'ToYUV'
    clip = input
    
    if not isinstance(input, vs.VideoNode):
        raise TypeError(funcName + ': \"input\" must be a clip!')
    
    # Get string format parameter "matrix"
    if matrix is not None:
        matrix_id = GetMatrix(input, matrix, False, True)
        clip = SetColorSpace(clip, Matrix=False if matrix_id > 10 else matrix_id)
    matrix = GetMatrix(input, matrix, False)
    
    # Get properties of input clip
    sFormat = input.format
    
    sColorFamily = sFormat.color_family
    sIsRGB = sColorFamily == vs.RGB
    sIsYUV = sColorFamily == vs.YUV
    sIsGRAY = sColorFamily == vs.GRAY
    sIsYCOCG = sColorFamily == vs.YCOCG
    if sColorFamily == vs.COMPAT:
        raise ValueError(funcName + ': Color family *COMPAT* is not supported!')
    
    sbitPS = sFormat.bits_per_sample
    sSType = sFormat.sample_type
    
    sHSubS = 1 << sFormat.subsampling_w
    sVSubS = 1 << sFormat.subsampling_h
    
    if sIsRGB:
        # Always assume full range for RGB input
        fulls = True
    elif full is None:
        # If not set, assume limited range for YUV and Gray input
        # Assume full range for YCgCo and OPP input
        if (sIsGRAY or sIsYUV or sIsYCOCG) and (matrix == "RGB" or matrix == "YCgCo" or matrix == "OPP"):
            fulls = True
        else:
            fulls = False if sIsYUV or sIsGRAY else True
    elif not isinstance(full, int):
        raise TypeError(funcName + ': \"full\" must be a bool!')
    else:
        fulls = full
    
    # Get properties of output clip
    if depth is None:
        dbitPS = sbitPS
    elif not isinstance(depth, int):
        raise TypeError(funcName + ': \"depth\" must be a int!')
    else:
        dbitPS = depth
    if sample is None:
        if depth is None:
            dSType = sSType
        else:
            dSType = vs.FLOAT if dbitPS >= 32 else 0
    elif not isinstance(sample, int):
        raise TypeError(funcName + ': \"sample\" must be a int!')
    elif sample != vs.INTEGER and sample != vs.FLOAT:
        raise ValueError(funcName + ': \"sample\" must be either 0(vs.INTEGER) or 1(vs.FLOAT)!')
    else:
        dSType = sample
    if dSType == vs.INTEGER and (dbitPS < 8 or dbitPS > 16):
        raise ValueError(funcName + ': {0}-bit integer output is not supported!'.format(dbitPS))
    if dSType == vs.FLOAT and (dbitPS != 16 and dbitPS != 32):
        raise ValueError(funcName + ': {0}-bit float output is not supported!'.format(dbitPS))
    
    if full is None:
        # If not set, assume limited range for YUV and Gray output
        # Assume full range for YCgCo and OPP output
        if matrix == "RGB" or matrix == "YCgCo" or matrix == "OPP":
            fulld = True
        else:
            fulld = True if sIsYCOCG else False
    elif not isinstance(full, int):
        raise TypeError(funcName + ': \"full\" must be a bool!')
    else:
        fulld = full
    
    # Chroma sub-sampling parameters
    if css is None:
        dHSubS = sHSubS
        dVSubS = sVSubS
        css = '{ssw}{ssh}'.format(ssw=dHSubS, ssh=dVSubS)
    elif not isinstance(css, str):
        raise TypeError(funcName + ': \"css\" must be a str!')
    else:
        if css == "444" or css == "4:4:4":
            css = "11"
        elif css == "440" or css == "4:4:0":
            css = "12"
        elif css == "422" or css == "4:2:2":
            css = "21"
        elif css == "420" or css == "4:2:0":
            css = "22"
        elif css == "411" or css == "4:1:1":
            css = "41"
        elif css == "410" or css == "4:1:0":
            css = "42"
        dHSubS = int(css[0])
        dVSubS = int(css[1])
    
    # Get properties of internal processed clip
    pSType = max(sSType, dSType) # If float sample type is involved, then use float for conversion
    if pSType == vs.FLOAT:
        # For float sample type, only 32-bit is supported by fmtconv
        pbitPS = 32
    else:
        # Apply conversion in the higher one of input and output bit depth
        pbitPS = max(sbitPS, dbitPS)
        # For integer sample type, only 8-, 9-, 10-, 12-, 16-bit is supported by fmtc.matrix
        if pbitPS == 11:
            pbitPS = 12
        elif pbitPS > 12 and pbitPS < 16:
            pbitPS = 16
        if dHSubS != sHSubS or dVSubS != sVSubS:
            # When chroma re-sampling is needed, always process in 16-bit for integer sample type
            pbitPS = 16
    
    # fmtc.resample parameters
    if kernel is None:
        kernel = "bicubic"
        if a1 is None and a2 is None:
            a1 = 0
            a2 = 0.5
    elif not isinstance(kernel, str):
        raise TypeError(funcName + ': \"kernel\" must be a str!')
    
    # Conversion
    if sIsYUV or sIsYCOCG:
        # Skip matrix conversion for YUV/YCoCg input
        # Change chroma sub-sampling if needed
        if dHSubS != sHSubS or dVSubS != sVSubS:
            # Apply depth conversion for processed clip
            clip = Depth(clip, pbitPS, pSType, fulls, fulls, dither, useZ, ampo, ampn, dyn, staticnoise)
            clip = core.fmtc.resample(clip, kernel=kernel, taps=taps, a1=a1, a2=a2, css=css, planes=[2,3,3], fulls=fulls, fulld=fulls, cplace=cplace)
        # Apply depth conversion for output clip
        clip = Depth(clip, dbitPS, dSType, fulls, fulld, dither, useZ, ampo, ampn, dyn, staticnoise)
    elif sIsGRAY:
        # Apply depth conversion for output clip
        clip = Depth(clip, dbitPS, dSType, fulls, fulld, dither, useZ, ampo, ampn, dyn, staticnoise)
        # Shuffle planes for Gray input
        widthc = input.width // dHSubS
        heightc = input.width // dVSubS
        UV = core.std.BlankClip(clip, width=widthc, height=heightc, \
        color=0 if dSType == vs.FLOAT else 1 << (dbitPS - 1))
        clip = core.std.ShufflePlanes([clip,UV,UV], [0,0,0], vs.YUV)
    else:
        # Apply depth conversion for processed clip
        clip = Depth(clip, pbitPS, pSType, fulls, fulls, dither, useZ, ampo, ampn, dyn, staticnoise)
        # Apply matrix conversion for RGB input
        if matrix == "OPP":
            clip = core.fmtc.matrix(clip, fulls=fulls, fulld=fulld, coef=[1/3,1/3,1/3,0, 1/2,0,-1/2,0, 1/4,-1/2,1/4,0], col_fam=vs.YUV)
        elif matrix == "2020cl":
            clip = core.fmtc.matrix2020cl(clip, full=fulld)
        else:
            clip = core.fmtc.matrix(clip, mat=matrix, fulls=fulls, fulld=fulld, col_fam=vs.YCOCG if matrix == "YCgCo" else vs.YUV)
        # Change chroma sub-sampling if needed
        if dHSubS != sHSubS or dVSubS != sVSubS:
            clip = core.fmtc.resample(clip, kernel=kernel, taps=taps, a1=a1, a2=a2, css=css, planes=[2,3,3], fulls=fulld, fulld=fulld, cplace=cplace)
        # Apply depth conversion for output clip
        clip = Depth(clip, dbitPS, dSType, fulld, fulld, dither, useZ, ampo, ampn, dyn, staticnoise)
    
    # Output
    return clip
################################################################################################################################


################################################################################################################################
## Main function: BM3D()
################################################################################################################################
## A wrap function for BM3D/V-BM3D denoising filter
## The BM3D filtering is always done in 16-bit int or 32-bit float opponent(OPP) color space internally.
## It can automatically convert any input color space to OPP and convert it back after filtering.
## Alternatively, you can specify "output" to force outputting RGB or OPP, and "css" to change chroma subsampling.
## For Gray input, no color space conversion is involved, thus "output" and "css" won't take effect.
## You can specify "refine" for any number of final estimate refinements.
################################################################################################################################
## Basic parameters
##     input {clip}: clip to be filtered
##         can be of YUV/RGB/Gray/YCoCg color family, can be of 8-16 bit integer or 16/32 bit float
##     sigma {float[]}: same as "sigma" in BM3D, used for both basic estimate and final estimate
##         the strength of filtering, should be carefully adjusted according to the noise
##         set 0 to disable the filtering of corresponding plane
##         default: [5.0,5.0,5.0]
##     radius1 {int}: temporal radius of basic estimate
##         - 0: BM3D (spatial denoising)
##         - 1~16: temporal radius of V-BM3D (spatial-temporal denoising)
##         default: 0
##     radius2 {int}: temporal radius of final estimate
##         default is the same as "radius1"
##     profile1 {str}: same as "profile" in BM3D basic estimate
##         default: "fast"
##     profile2 {str}: same as "profile" in BM3D final estimate
##         default is the same as "profile1"
################################################################################################################################
## Advanced parameters
##     refine {int}: refinement times
##         - 0: basic estimate only
##         - 1: basic estimate + refined with final estimate, the original behavior of BM3D
##         - n: basic estimate + refined with final estimate for n times
##             each final estimate takes the filtered clip in previous estimate as reference clip to filter the input clip
##         default: 1
##     pre {clip} (optional): pre-filtered clip for basic estimate
##         must be of the same format and dimension as the input clip
##         should be a clip better suited for block-matching than the input clip
##     ref {clip} (optional): basic estimate clip
##         must be of the same format and dimension as the input clip
##         replace the basic estimate of BM3D and serve as the reference clip for final estimate
##     psample {int}: internal processed precision
##         - 0: 16-bit integer, less accuracy, less memory consumption
##         - 1: 32-bit float, more accuracy, more memory consumption
##         default: 0
################################################################################################################################
## Parameters of input properties
##     matrix {int|str}: color matrix of input clip, only makes sense for YUV/YCoCg input
##         check GetMatrix() for available values
##         default: guessed according to the color family and size of input clip
##     full {bool}: define if input clip is of full range
##         default: guessed according to the color family of input clip and "matrix"
################################################################################################################################
## Parameters of output properties
##     output {int}: type of output clip, doesn't make sense for Gray input
##         - 0: same format as input clip
##         - 1: full range RGB (converted from input clip)
##         - 2: full range OPP (converted from full range RGB, the color space where the filtering takes place)
##         default: 0
##     css {str}: chroma subsampling of output clip, only valid when output=0 and input clip is YUV/YCoCg
##         check ToYUV() for available values
##         default is the same as that of the input clip
##     depth {int}: bit depth of output clip, can be 8-16 for integer or 16/32 for float
##         default is the same as that of the input clip
##     sample {int}: sample type of output clip, can be 0(vs.INTEGER) or 1(vs.FLOAT)
##         default is the same as that of the input clip
################################################################################################################################
## Parameters of depth conversion
##     dither, useZ, ampo, ampn, dyn, staticnoise:
##         same as those in Depth()
################################################################################################################################
## Parameters of resampling
##     cu_kernel, cu_taps, cu_a1, cu_a2, cu_cplace:
##         used for chroma up-sampling, same as those in fmtc.resample
##         default: kernel="bicubic", a1=0, a2=0.5, also known as "Catmull-Rom"
##     cd_kernel, cd_taps, cd_a1, cd_a2, cd_cplace:
##         used for chroma down-sampling, same as those in fmtc.resample
##         default: kernel="bicubic", a1=0, a2=0.5, also known as "Catmull-Rom"
################################################################################################################################
## Parameters of BM3D basic estimate
##     block_size1, block_step1, group_size1, bm_range1, bm_step1, ps_num1, ps_range1, ps_step1, th_mse1, hard_thr:
##         same as those in bm3d.Basic/bm3d.VBasic
################################################################################################################################
## Parameters of BM3D final estimate
##     block_size2, block_step2, group_size2, bm_range2, bm_step2, ps_num2, ps_range2, ps_step2, th_mse2:
##         same as those in bm3d.Final/bm3d.VFinal
################################################################################################################################
def BM3D(input, sigma=None, radius1=None, radius2=None, profile1=None, profile2=None, \
refine=None, pre=None, ref=None, psample=None, \
matrix=None, full=None, \
output=None, css=None, depth=None, sample=None, \
dither=None, useZ=None, ampo=None, ampn=None, dyn=None, staticnoise=None, \
cu_kernel=None, cu_taps=None, cu_a1=None, cu_a2=None, cu_cplace=None, \
cd_kernel=None, cd_taps=None, cd_a1=None, cd_a2=None, cd_cplace=None, \
block_size1=None, block_step1=None, group_size1=None, bm_range1=None, bm_step1=None, ps_num1=None, ps_range1=None, ps_step1=None, th_mse1=None, hard_thr=None, \
block_size2=None, block_step2=None, group_size2=None, bm_range2=None, bm_step2=None, ps_num2=None, ps_range2=None, ps_step2=None, th_mse2=None):
    # Set VS core and function name
    core = vs.get_core()
    funcName = 'BM3D'
    clip = input
    
    if not isinstance(input, vs.VideoNode):
        raise TypeError(funcName + ': \"input\" must be a clip!')
    
    # Get string format parameter "matrix"
    matrix = GetMatrix(input, matrix, True)
    
    # Get properties of input clip
    sFormat = input.format
    
    sColorFamily = sFormat.color_family
    sIsRGB = sColorFamily == vs.RGB
    sIsYUV = sColorFamily == vs.YUV
    sIsGRAY = sColorFamily == vs.GRAY
    sIsYCOCG = sColorFamily == vs.YCOCG
    if sColorFamily == vs.COMPAT:
        raise ValueError(funcName + ': Color family *COMPAT* is not supported!')
    
    sbitPS = sFormat.bits_per_sample
    sSType = sFormat.sample_type
    
    sHSubS = 1 << sFormat.subsampling_w
    sVSubS = 1 << sFormat.subsampling_h
    
    if full is None:
        # If not set, assume limited range for YUV and Gray input
        # Assume full range for YCgCo and OPP input
        if (sIsGRAY or sIsYUV or sIsYCOCG) and (matrix == "RGB" or matrix == "YCgCo" or matrix == "OPP"):
            fulls = True
        else:
            fulls = False if sIsYUV or sIsGRAY else True
    elif not isinstance(full, int):
        raise TypeError(funcName + ': \"full\" must be a bool!')
    else:
        fulls = full
    
    # Get properties of internal processed clip
    if psample is None:
        psample = vs.INTEGER
    elif not isinstance(psample, int):
        raise TypeError(funcName + ': \"psample\" must be a int!')
    elif psample != vs.INTEGER and psample != vs.FLOAT:
        raise ValueError(funcName + ': \"psample\" must be either 0(vs.INTEGER) or 1(vs.FLOAT)!')
    pbitPS = 16 if psample == vs.INTEGER else 32
    pSType = psample
    
    # Chroma sub-sampling parameters
    if css is None:
        dHSubS = sHSubS
        dVSubS = sVSubS
        css = '{ssw}{ssh}'.format(ssw=dHSubS, ssh=dVSubS)
    elif not isinstance(css, str):
        raise TypeError(funcName + ': \"css\" must be a str!')
    else:
        if css == "444" or css == "4:4:4":
            css = "11"
        elif css == "440" or css == "4:4:0":
            css = "12"
        elif css == "422" or css == "4:2:2":
            css = "21"
        elif css == "420" or css == "4:2:0":
            css = "22"
        elif css == "411" or css == "4:1:1":
            css = "41"
        elif css == "410" or css == "4:1:0":
            css = "42"
        dHSubS = int(css[0])
        dVSubS = int(css[1])
    
    if cu_cplace is not None and cd_cplace is None:
        cd_cplace = cu_cplace
    
    # Parameters processing
    if sigma is None:
        sigma = [5.0,5.0,5.0]
    else:
        if isinstance(sigma, int):
            sigma = float(sigma)
            sigma = [sigma,sigma,sigma]
        elif isinstance(sigma, float):
            sigma = [sigma,sigma,sigma]
        elif isinstance(sigma, list):
            while len(sigma) < 3:
                sigma.append(sigma[len(sigma) - 1])
        else:
            raise TypeError(funcName + ': sigma must be a float[] or int[]!')
    if sIsGRAY:
        sigma = [sigma[0],0,0]
    
    if radius1 is None:
        radius1 = 0
    elif not isinstance(radius1, int):
        raise TypeError(funcName + ': \"radius1\" must be a int!')
    elif radius1 < 0:
        raise ValueError(funcName + ': valid range of \"radius1\" is [0, +inf)!')
    if radius2 is None:
        radius2 = radius1
    elif not isinstance(radius2, int):
        raise TypeError(funcName + ': \"radius2\" must be a int!')
    elif radius2 < 0:
        raise ValueError(funcName + ': valid range of \"radius2\" is [0, +inf)!')
    
    if profile1 is None:
        profile1 = "fast"
    elif not isinstance(profile1, str):
        raise TypeError(funcName + ': \"profile1\" must be a str!')
    if profile2 is None:
        profile2 = profile1
    elif not isinstance(profile2, str):
        raise TypeError(funcName + ': \"profile2\" must be a str!')
    
    if refine is None:
        refine = 1
    elif not isinstance(refine, int):
        raise TypeError(funcName + ': \"refine\" must be a int!')
    elif refine < 0:
        raise ValueError(funcName + ': valid range of \"refine\" is [0, +inf)!')
    
    if output is None:
        output = 0
    elif not isinstance(output, int):
        raise TypeError(funcName + ': \"output\" must be a int!')
    elif output < 0 or output > 2:
        raise ValueError(funcName + ': valid values of \"output\" are 0, 1 and 2!')
    
    if pre is not None:
        if not isinstance(pre, vs.VideoNode):
            raise TypeError(funcName + ': \"pre\" must be a clip!')
        if pre.format != sFormat:
            raise ValueError(funcName + ': clip \"pre\" must be of the same format as the input clip!')
        if pre.width != input.width or pre.height != input.height:
            raise ValueError(funcName + ': clip \"pre\" must be of the same size as the input clip!')
    
    if ref is not None:
        if not isinstance(ref, vs.VideoNode):
            raise TypeError(funcName + ': \"ref\" must be a clip!')
        if ref.format != sFormat:
            raise ValueError(funcName + ': clip \"ref\" must be of the same format as the input clip!')
        if ref.width != input.width or ref.height != input.height:
            raise ValueError(funcName + ': clip \"ref\" must be of the same size as the input clip!')
    
    # Get properties of output clip
    if depth is None:
        if output == 0:
            dbitPS = sbitPS
        else:
            dbitPS = pbitPS
    elif not isinstance(depth, int):
        raise TypeError(funcName + ': \"depth\" must be a int!')
    else:
        dbitPS = depth
    if sample is None:
        if depth is None:
            if output == 0:
                dSType = sSType
            else:
                dSType = pSType
        else:
            dSType = vs.FLOAT if dbitPS >= 32 else 0
    elif not isinstance(sample, int):
        raise TypeError(funcName + ': \"sample\" must be a int!')
    elif sample != vs.INTEGER and sample != vs.FLOAT:
        raise ValueError(funcName + ': \"sample\" must be either 0(vs.INTEGER) or 1(vs.FLOAT)!')
    else:
        dSType = sample
    if dSType == vs.INTEGER and (dbitPS < 8 or dbitPS > 16):
        raise ValueError(funcName + ': {0}-bit integer output is not supported!'.format(dbitPS))
    if dSType == vs.FLOAT and (dbitPS != 16 and dbitPS != 32):
        raise ValueError(funcName + ': {0}-bit float output is not supported!'.format(dbitPS))
    
    if output == 0:
        fulld = fulls
    else:
        # Always full range output when output=1|output=2 (full range RGB or full range OPP)
        fulld = True
    
    # Convert to processed format
    # YUV/YCoCg/RGB input is converted to opponent color space as full range YUV
    # Gray input is converted to full range Gray
    onlyY = False
    if sIsGRAY:
        onlyY = True
        # Convert Gray input to full range Gray in processed format
        clip = Depth(clip, pbitPS, pSType, fulls, True, dither, useZ, ampo, ampn, dyn, staticnoise)
        if pre is not None:
            pre = Depth(pre, pbitPS, pSType, fulls, True, dither, useZ, ampo, ampn, dyn, staticnoise)
        if ref is not None:
            ref = Depth(ref, pbitPS, pSType, fulls, True, dither, useZ, ampo, ampn, dyn, staticnoise)
    else:
        # Convert input to full range RGB
        clip = ToRGB(clip, matrix, pbitPS, pSType, fulls, \
        dither, useZ, ampo, ampn, dyn, staticnoise, cu_kernel, cu_taps, cu_a1, cu_a2, cu_cplace)
        if pre is not None:
            pre = ToRGB(pre, matrix, pbitPS, pSType, fulls, \
            dither, useZ, ampo, ampn, dyn, staticnoise, cu_kernel, cu_taps, cu_a1, cu_a2, cu_cplace)
        if ref is not None:
            ref = ToRGB(ref, matrix, pbitPS, pSType, fulls, \
            dither, useZ, ampo, ampn, dyn, staticnoise, cu_kernel, cu_taps, cu_a1, cu_a2, cu_cplace)
        # Convert full range RGB to full range OPP
        clip = ToYUV(clip, "OPP", "444", pbitPS, pSType, True, \
        dither, useZ, ampo, ampn, dyn, staticnoise, cu_kernel, cu_taps, cu_a1, cu_a2, cu_cplace)
        if pre is not None:
            pre = ToYUV(pre, "OPP", "444", pbitPS, pSType, True, \
            dither, useZ, ampo, ampn, dyn, staticnoise, cu_kernel, cu_taps, cu_a1, cu_a2, cu_cplace)
        if ref is not None:
            ref = ToYUV(ref, "OPP", "444", pbitPS, pSType, True, \
            dither, useZ, ampo, ampn, dyn, staticnoise, cu_kernel, cu_taps, cu_a1, cu_a2, cu_cplace)
        # Convert OPP to Gray if only Y is processed
        srcOPP = clip
        if sigma[1] <= 0 and sigma[2] <= 0:
            onlyY = True
            clip = core.std.ShufflePlanes([clip], [0], vs.GRAY)
            if pre is not None:
                pre = core.std.ShufflePlanes([pre], [0], vs.GRAY)
            if ref is not None:
                ref = core.std.ShufflePlanes([ref], [0], vs.GRAY)
    
    # Basic estimate
    if ref is not None:
        # Use custom basic estimate specified by clip "ref"
        flt = ref
    elif radius1 < 1:
        # Apply BM3D basic estimate
        # Optional pre-filtered clip for block-matching can be specified by "pre"
        flt = core.bm3d.Basic(clip, ref=pre, profile=profile1, sigma=sigma, \
        block_size=block_size1, block_step=block_step1, group_size=group_size1, \
        bm_range=bm_range1, bm_step=bm_step1, th_mse=th_mse1, hard_thr=hard_thr, matrix=100)
    else:
        # Apply V-BM3D basic estimate
        # Optional pre-filtered clip for block-matching can be specified by "pre"
        flt = core.bm3d.VBasic(clip, ref=pre, profile=profile1, sigma=sigma, radius=radius1, \
        block_size=block_size1, block_step=block_step1, group_size=group_size1, \
        bm_range=bm_range1, bm_step=bm_step1, ps_num=ps_num1, ps_range=ps_range1, ps_step=ps_step1, \
        th_mse=th_mse1, hard_thr=hard_thr, matrix=100).bm3d.VAggregate(radius=radius1, sample=pSType)
        # Shuffle Y plane back if not processed
        if not onlyY and sigma[0] <= 0:
            flt = core.std.ShufflePlanes([clip,flt,flt], [0,1,2], vs.YUV)
    
    # Final estimate
    for i in range(0, refine):
        if radius1 < 1:
            # Apply BM3D final estimate
            flt = core.bm3d.Basic(clip, ref=flt, profile=profile2, sigma=sigma, \
            block_size=block_size2, block_step=block_step2, group_size=group_size2, \
            bm_range=bm_range2, bm_step=bm_step2, th_mse=th_mse2, matrix=100)
        else:
            # Apply V-BM3D final estimate
            flt = core.bm3d.VBasic(clip, ref=flt, profile=profile2, sigma=sigma, radius=radius2, \
            block_size=block_size2, block_step=block_step2, group_size=group_size2, \
            bm_range=bm_range2, bm_step=bm_step2, ps_num=ps_num2, ps_range=ps_range2, ps_step=ps_step2, \
            th_mse=th_mse2, matrix=100).bm3d.VAggregate(radius=radius1, sample=pSType)
            # Shuffle Y plane back if not processed
            if not onlyY and sigma[0] <= 0:
                flt = core.std.ShufflePlanes([clip,flt,flt], [0,1,2], vs.YUV)
    
    # Convert to output format
    if sIsGRAY:
        clip = Depth(flt, dbitPS, dSType, True, fulld, dither, useZ, ampo, ampn, dyn, staticnoise)
    else:
        # Shuffle back to YUV if not all planes are processed
        if onlyY:
            clip = core.std.ShufflePlanes([flt,srcOPP,srcOPP], [0,1,2], vs.YUV)
        elif sigma[1] <= 0 or sigma[2] <= 0:
            clip = core.std.ShufflePlanes([flt, clip if sigma[1] <= 0 else flt, \
            clip if sigma[2] <= 0 else flt], [0,1,2], vs.YUV)
        else:
            clip = flt
        # Convert to final output format
        if output <= 1:
            # Convert full range OPP to full range RGB
            clip = ToRGB(clip, "OPP", pbitPS, pSType, True, \
            dither, useZ, ampo, ampn, dyn, staticnoise, cu_kernel, cu_taps, cu_a1, cu_a2, cu_cplace)
        if output <= 0 and not sIsRGB:
            # Convert full range RGB to YUV/YCoCg
            clip = ToYUV(clip, matrix, css, dbitPS, dSType, fulld, \
            dither, useZ, ampo, ampn, dyn, staticnoise, cd_kernel, cd_taps, cd_a1, cd_a2, cd_cplace)
        else:
            # Depth conversion for RGB or OPP output
            clip = Depth(clip, dbitPS, dSType, True, fulld, dither, useZ, ampo, ampn, dyn, staticnoise)
    
    # Output
    return clip
################################################################################################################################





################################################################################################################################
################################################################################################################################
################################################################################################################################
## Utility functions below
################################################################################################################################
################################################################################################################################
################################################################################################################################


################################################################################################################################
## Utility function: Min()
################################################################################################################################
## Take 2 clips and return pixel-wise minimum of them.
## With a special mode=2 for difference clip.
################################################################################################################################
## Basic parameters
##     clip1 {clip}: the first clip
##         can be of YUV/RGB/Gray/YCoCg color family, can be of 8-16 bit integer or 16/32 bit float
##     clip2 {clip}: the second clip
##         must be of the same format and dimension as "clip1"
##     mode {int[]}: specify processing mode for each plane
##         - 0: don't process, copy "clip1" to output
##         - 1: normal minimum, output = min(clip1, clip2)
##         - 2: difference minimum, output = abs(clip2 - neutral) < abs(clip1 - neutral) ? clip2 : clip1
##         default: [1,1,1] for YUV/RGB/YCoCg input, [1] for Gray input
################################################################################################################################
## Advanced parameters
##     neutral {int|float}: specfy the neutral value used for mode=2
##         default: 1 << (bits_per_sample - 1) for integer input, 0 for float input
################################################################################################################################
def Min(clip1, clip2, mode=None, neutral=None):
    return _Operator2(clip1, clip2, mode, neutral, 'Min')
################################################################################################################################


################################################################################################################################
## Utility function: Max()
################################################################################################################################
## Take 2 clips and return pixel-wise maximum of them.
## With a special mode=2 for difference clip.
################################################################################################################################
## Basic parameters
##     clip1 {clip}: the first clip
##         can be of YUV/RGB/Gray/YCoCg color family, can be of 8-16 bit integer or 16/32 bit float
##     clip2 {clip}: the second clip
##         must be of the same format and dimension as "clip1"
##     mode {int[]}: specify processing mode for each plane
##         - 0: don't process, copy "clip1" to output
##         - 1: normal maximum, output = max(clip1, clip2)
##         - 2: difference maximum, output = abs(clip2 - neutral) > abs(clip1 - neutral) ? clip2 : clip1
##         default: [1,1,1] for YUV/RGB/YCoCg input, [1] for Gray input
################################################################################################################################
## Advanced parameters
##     neutral {int|float}: specfy the neutral value used for mode=2
##         default: 1 << (bits_per_sample - 1) for integer input, 0 for float input
################################################################################################################################
def Max(clip1, clip2, mode=None, neutral=None):
    return _Operator2(clip1, clip2, mode, neutral, 'Max')
################################################################################################################################


################################################################################################################################
## Utility function: Avg()
################################################################################################################################
## Take 2 clips and return pixel-wise average of them.
################################################################################################################################
## Basic parameters
##     clip1 {clip}: the first clip
##         can be of YUV/RGB/Gray/YCoCg color family, can be of 8-16 bit integer or 16/32 bit float
##     clip2 {clip}: the second clip
##         must be of the same format and dimension as "clip1"
##     mode {int[]}: specify processing mode for each plane
##         - 0: don't process, copy "clip1" to output
##         - 1: average, output = (clip1 + clip2) / 2
##         default: [1,1,1] for YUV/RGB/YCoCg input, [1] for Gray input
################################################################################################################################
def Avg(clip1, clip2, mode=None):
    return _Operator2(clip1, clip2, mode, None, 'Avg')
################################################################################################################################


################################################################################################################################
## Utility function: MinFilter()
################################################################################################################################
## Apply filtering with minimum difference of the 2 filtered clips.
################################################################################################################################
## Basic parameters
##     src {clip}: source clip
##         can be of YUV/RGB/Gray/YCoCg color family, can be of 8-16 bit integer or 16/32 bit float
##     flt1 {clip}: filtered clip 1
##         must be of the same format and dimension as "src"
##     flt2 {clip}: filtered clip 2
##         must be of the same format and dimension as "src"
##     planes {int[]}: specify which planes to process
##         unprocessed planes will be copied from "src"
##         default: all planes will be processed, [0,1,2] for YUV/RGB/YCoCg input, [0] for Gray input
################################################################################################################################
def MinFilter(src, flt1, flt2, planes=None):
    return _Min_Max_Filter(src, flt1, flt2, planes, 'MinFilter')
################################################################################################################################


################################################################################################################################
## Utility function: MaxFilter()
################################################################################################################################
## Apply filtering with maximum difference of the 2 filtered clips.
################################################################################################################################
## Basic parameters
##     src {clip}: source clip
##         can be of YUV/RGB/Gray/YCoCg color family, can be of 8-16 bit integer or 16/32 bit float
##     flt1 {clip}: filtered clip 1
##         must be of the same format and dimension as "src"
##     flt2 {clip}: filtered clip 2
##         must be of the same format and dimension as "src"
##     planes {int[]}: specify which planes to process
##         unprocessed planes will be copied from "src"
##         default: all planes will be processed, [0,1,2] for YUV/RGB/YCoCg input, [0] for Gray input
################################################################################################################################
def MaxFilter(src, flt1, flt2, planes=None):
    return _Min_Max_Filter(src, flt1, flt2, planes, 'MaxFilter')
################################################################################################################################


################################################################################################################################
## Utility function: LimitFilter()
################################################################################################################################
## Similar to the AviSynth function Dither_limit_dif16() and HQDeringmod_limit_dif16().
## It acts as a post-processor, and is very useful to limit the difference of filtering while avoiding artifacts.
## Common used cases: de-banding, de-ringing, de-noising, sharpening, combing high precision source with low precision filtering, etc.
################################################################################################################################
## There are 2 implementations, default one with std.Expr, the other with std.Lut.
## The Expr version supports all mode, while the Lut version doesn't support float input and ref clip.
## Also the Lut version will truncate the filtering diff if it exceeds half the value range(128 for 8-bit, 32768 for 16-bit).
## The Lut version might be faster than Expr version in some cases, for example 8-bit input and brighten_thr != thr.
################################################################################################################################
## Algorithm for Y/R/G/B plane (for chroma, replace "thr" and "brighten_thr" with "thrc")
##     dif = flt - src
##     dif_ref = flt - ref
##     dif_abs = abs(dif_ref)
##     thr_1 = brighten_thr if (dif > 0) else thr
##     thr_2 = thr_1 * elast
##
##     if dif_abs <= thr_1:
##         final = flt
##     elif dif_abs >= thr_2:
##         final = src
##     else:
##         final = src + dif * (thr_2 - dif_abs) / (thr_2 - thr_1)
################################################################################################################################
## Basic parameters
##     flt {clip}: filtered clip, to compute the filtering diff
##         can be of YUV/RGB/Gray/YCoCg color family, can be of 8-16 bit integer or 16/32 bit float
##     src {clip}: source clip, to apply the filtering diff
##         must be of the same format and dimension as "flt"
##     ref {clip} (optional): reference clip, to compute the weight to be applied on filtering diff
##         must be of the same format and dimension as "flt"
##         default: None (use "src")
##     thr {float}: threshold (8-bit scale) to limit filtering diff
##         default: 1.0
##     elast {float}: elasticity of the soft threshold
##         default: 2.0
##     planes {int[]}: specify which planes to process
##         unprocessed planes will be copied from "flt"
##         default: all planes will be processed, [0,1,2] for YUV/RGB/YCoCg input, [0] for Gray input
################################################################################################################################
## Advanced parameters
##     brighten_thr {float}: threshold (8-bit scale) for filtering diff that brightening the image (Y/R/G/B plane)
##         set a value different from "thr" is useful to limit the overshoot/undershoot/blurring introduced in sharpening/de-ringing
##         default is the same as "thr"
##     thrc {float}: threshold (8-bit scale) for chroma (U/V/Co/Cg plane)
##         default is the same as "thr"
##     force_expr {bool}
##         - True: force to use the std.Expr implementation
##         - False: use the std.Lut implementation if possible
##         default: True
################################################################################################################################
def LimitFilter(flt, src, ref=None, thr=None, elast=None, brighten_thr=None, thrc=None, force_expr=None, planes=None):
    # Set VS core and function name
    core = vs.get_core()
    funcName = 'LimitFilter'
    
    if not isinstance(flt, vs.VideoNode):
        raise TypeError(funcName + ': \"flt\" must be a clip!')
    if not isinstance(src, vs.VideoNode):
        raise TypeError(funcName + ': \"src\" must be a clip!')
    if ref is not None and not isinstance(ref, vs.VideoNode):
        raise TypeError(funcName + ': \"ref\" must be a clip!')
    
    # Get properties of input clip
    sFormat = flt.format
    if sFormat.id != src.format.id:
        raise ValueError(funcName + ': \"flt\" and \"src\" must be of the same format!')
    if flt.width != src.width or flt.height != src.height:
        raise ValueError(funcName + ': \"flt\" and \"src\" must be of the same width and height!')
    
    if ref is not None:
        if sFormat.id != ref.format.id:
            raise ValueError(funcName + ': \"flt\" and \"ref\" must be of the same format!')
        if flt.width != ref.width or flt.height != ref.height:
            raise ValueError(funcName + ': \"flt\" and \"ref\" must be of the same width and height!')
    
    sColorFamily = sFormat.color_family
    sIsYUV = sColorFamily == vs.YUV
    sIsYCOCG = sColorFamily == vs.YCOCG
    
    sSType = sFormat.sample_type
    sbitPS = sFormat.bits_per_sample
    sNumPlanes = sFormat.num_planes
    
    # Parameters
    if thr is None:
        thr = 1.0
    elif isinstance(thr, int) or isinstance(thr, float):
        if thr < 0:
            raise ValueError(funcName + ':valid range of \"thr\" is [0, +inf)')
    else:
        raise TypeError(funcName + ': \"thr\" must be a int or a float!')
    
    if elast is None:
        elast = 2.0
    elif isinstance(elast, int) or isinstance(elast, float):
        if elast < 1:
            raise ValueError(funcName + ':valid range of \"elast\" is [1, +inf)')
    else:
        raise TypeError(funcName + ': \"elast\" must be a int or a float!')
    
    if brighten_thr is None:
        brighten_thr = thr
    elif isinstance(brighten_thr, int) or isinstance(brighten_thr, float):
        if brighten_thr < 0:
            raise ValueError(funcName + ':valid range of \"brighten_thr\" is [0, +inf)')
    else:
        raise TypeError(funcName + ': \"brighten_thr\" must be a int or a float!')
    
    if thrc is None:
        thrc = thr
    elif isinstance(thrc, int) or isinstance(thrc, float):
        if thrc < 0:
            raise ValueError(funcName + ':valid range of \"thrc\" is [0, +inf)')
    else:
        raise TypeError(funcName + ': \"thrc\" must be a int or a float!')
    
    if force_expr is None:
        force_expr = True
    elif not isinstance(force_expr, int):
        raise TypeError(funcName + ': \"force_expr\" must be a bool!')
    if ref is not None or sSType != vs.INTEGER:
        force_expr = True
    
    # planes
    process = [0 for i in range(VSMaxPlaneNum)]
    
    if planes is None:
        process = [1 for i in range(VSMaxPlaneNum)]
    elif isinstance(planes, int):
        if planes < 0 or planes >= VSMaxPlaneNum:
            raise ValueError(funcName + ': valid range of \"planes\" is [0, {VSMaxPlaneNum})!'.format(VSMaxPlaneNum=VSMaxPlaneNum))
        process[planes] = 1
    elif isinstance(planes, list):
        for p in planes:
            if not isinstance(p, int):
                raise TypeError(funcName + ': \"planes\" must be a (list of) int!')
            elif p < 0 or p >= VSMaxPlaneNum:
                raise ValueError(funcName + ': valid range of \"planes\" is [0, {VSMaxPlaneNum})!'.format(VSMaxPlaneNum=VSMaxPlaneNum))
            process[p] = 1
    else:
        raise TypeError(funcName + ': \"planes\" must be a (list of) int!')
    
    # Process
    if thr <= 0 and brighten_thr <= 0:
        if sIsYUV or sIsYCOCG:
            if thrc <= 0:
                return src
        else:
            return src
    if thr >= 255 and brighten_thr >= 255:
        if sIsYUV or sIsYCOCG:
            if thrc >= 255:
                return flt
        else:
            return flt
    if thr >= 128 or brighten_thr >= 128:
        force_expr = True
    
    if force_expr: # implementation with std.Expr
        valueRange = (1 << sbitPS) - 1 if sSType == vs.INTEGER else 1
        limitExprY = _LimitFilterExpr(ref is not None, thr, elast, brighten_thr, valueRange)
        limitExprC = _LimitFilterExpr(ref is not None, thrc, elast, thrc, valueRange)
        expr = []
        for i in range(sNumPlanes):
            if process[i]:
                if i > 0 and (sIsYUV or sIsYCOCG):
                    expr.append(limitExprC)
                else:
                    expr.append(limitExprY)
            else:
                expr.append("")
        
        if ref is None:
            clip = core.std.Expr([flt, src], expr)
        else:
            clip = core.std.Expr([flt, src, ref], expr)
    else: # implementation with std.MakeDiff, std.Lut and std.MergeDiff
        diff = core.std.MakeDiff(flt, src, planes=planes)
        if sIsYUV or sIsYCOCG:
            if process[0]:
                diff = _LimitDiffLut(diff, thr, elast, brighten_thr, [0])
            if process[1] or process[2]:
                _planes = []
                if process[1]:
                    _planes.append(1)
                if process[2]:
                    _planes.append(2)
                diff = _LimitDiffLut(diff, thrc, elast, thrc, [1, 2])
        else:
            diff = _LimitDiffLut(diff, thr, elast, brighten_thr, planes)
        clip = core.std.MakeDiff(flt, diff, planes=planes)
    
    # Output
    return clip
################################################################################################################################


################################################################################################################################
## Utility function: ShowAverage()
################################################################################################################################
## Display unnormalized average of each plane
################################################################################################################################
## Basic parameters
##     clip {clip}: clip to be evaluated
##         can be of YUV/RGB/Gray/YCoCg color family, can be of 8-16 bit integer
################################################################################################################################
## Advanced parameters
##     alignment {int}: same as the one in text.Text()
##         default: 7
################################################################################################################################
def ShowAverage(clip, alignment=None):
    # Set VS core and function name
    core = vs.get_core()
    funcName = 'ShowAverage'
    
    if not isinstance(clip, vs.VideoNode):
        raise TypeError(funcName + ': \"clip\" must be a clip!')
    
    # Get properties of input clip
    sFormat = clip.format
    
    sColorFamily = sFormat.color_family
    sIsYUV = sColorFamily == vs.YUV
    sIsYCOCG = sColorFamily == vs.YCOCG
    
    sSType = sFormat.sample_type
    sbitPS = sFormat.bits_per_sample
    sNumPlanes = sFormat.num_planes
    
    valueRange = (1 << sbitPS) - 1 if sSType == vs.INTEGER else 1
    offset = [0, -0.5, -0.5] if sSType == vs.FLOAT and (sIsYUV or sIsYCOCG) else [0, 0, 0]
    
    # Process and output
    def _ShowAverageFrame(n, f):
        text = ""
        if sNumPlanes == 1:
            average = f.props.PlaneAverage * valueRange + offset[0]
            text += "PlaneAverage[{plane}]={average}".format(plane=0, average=average)
        else:
            for p in range(sNumPlanes):
                average = f[p].props.PlaneAverage * valueRange + offset[p]
                text += "PlaneAverage[{plane}]={average}\n".format(plane=p, average=average)
        return core.text.Text(clip, text, alignment)
    
    avg = []
    for p in range(sNumPlanes):
        avg.append(core.std.PlaneAverage(clip, p))
    
    return core.std.FrameEval(clip, _ShowAverageFrame, prop_src=avg)
################################################################################################################################


################################################################################################################################
## Utility function: FilterCombed()
################################################################################################################################
## Take the frames from clip "flt" that is marked as combed and the ones from clip "src" that is not.
## The frame property '_Combed' from clip "props" is evaluated to determine whether it's combed.
################################################################################################################################
## Basic parameters
##     src {clip}: the source clip
##         can be of any constant format
##     flt {clip}: the filtered clip (de-interlaced)
##         must be of the same format and dimension as "src"
##     props {clip} (optional): the clip from which the frame property is evaluated
##         can be of any format, should have the same number of frames as "src"
##         default: None (use "src")
################################################################################################################################
def FilterCombed(src, flt, props=None):
    # Set VS core and function name
    core = vs.get_core()
    funcName = 'FilterCombed'
    
    if not isinstance(src, vs.VideoNode):
        raise TypeError(funcName + ': \"src\" must be a clip!')
    if not isinstance(flt, vs.VideoNode):
        raise TypeError(funcName + ': \"flt\" must be a clip!')
    if props is not None and not isinstance(props, vs.VideoNode):
        raise TypeError(funcName + ': \"props\" must be a clip!')
    
    # Get properties of input clip
    sFormat = src.format
    if sFormat.id != flt.format.id:
        raise ValueError(funcName + ': \"src\" and \"flt\" must be of the same format!')
    if src.width != flt.width or src.height != flt.height:
        raise ValueError(funcName + ': \"src\" and \"flt\" must be of the same width and height!')
    
    if props is None:
        props = src
    else:
        if sFormat.id != props.format.id:
            raise ValueError(funcName + ': \"src\" and \"props\" must be of the same format!')
        if src.width != props.width or src.height != props.height:
            raise ValueError(funcName + ': \"src\" and \"props\" must be of the same width and height!')
    
    # FrameEval function
    def _FilterCombedFrame(n, f):
        try:
            if f.props._Combed:
                return flt
        except:
            pass
        return src
    
    # Process
    return core.std.FrameEval(src, _FilterCombedFrame, props)
################################################################################################################################





################################################################################################################################
################################################################################################################################
################################################################################################################################
## Frame property functions below
################################################################################################################################
################################################################################################################################
################################################################################################################################


################################################################################################################################
## Frame property function: SetColorSpace()
################################################################################################################################
## Modify the color space related frame properties in the given clip.
## Detailed descriptions of these properties: http://www.vapoursynth.com/doc/apireference.html
################################################################################################################################
## Parameters
##     %Any%: for the property named "_%Any%"
##         - None: do nothing
##         - True: do nothing
##         - False: delete corresponding frame properties if exist
##         - {int}: set to this value
################################################################################################################################
def SetColorSpace(clip, ChromaLocation=None, ColorRange=None, Primaries=None, Matrix=None, Transfer=None):
    # Set VS core and function name
    core = vs.get_core()
    funcName = 'SetColorSpace'
    
    if not isinstance(clip, vs.VideoNode):
        raise TypeError(funcName + ': \"clip\" must be a clip!')
    
    # Modify frame properties
    if ChromaLocation is None:
        pass
    elif isinstance(ChromaLocation, bool):
        if ChromaLocation is False:
            clip = core.std.SetFrameProp(clip, prop='_ChromaLocation', delete=True)
    elif isinstance(ChromaLocation, int):
        if ChromaLocation >= 0 and ChromaLocation <=5:
            clip = core.std.SetFrameProp(clip, prop='_ChromaLocation', intval=ChromaLocation)
        else:
            raise ValueError(funcName + ': valid range of \"ChromaLocation\" is [0, 5]!')
    else:
        raise TypeError(funcName + ': \"ChromaLocation\" must be a int or a bool!')
    
    if ColorRange is None:
        pass
    elif isinstance(ColorRange, bool):
        if ColorRange is False:
            clip = core.std.SetFrameProp(clip, prop='_ColorRange', delete=True)
    elif isinstance(ColorRange, int):
        if ColorRange >= 0 and ColorRange <=1:
            clip = core.std.SetFrameProp(clip, prop='_ColorRange', intval=ColorRange)
        else:
            raise ValueError(funcName + ': valid range of \"ColorRange\" is [0, 1]!')
    else:
        raise TypeError(funcName + ': \"ColorRange\" must be a int or a bool!')
    
    if Primaries is None:
        pass
    elif isinstance(Primaries, bool):
        if Primaries is False:
            clip = core.std.SetFrameProp(clip, prop='_Primaries', delete=True)
    elif isinstance(Primaries, int):
        clip = core.std.SetFrameProp(clip, prop='_Primaries', intval=Primaries)
    else:
        raise TypeError(funcName + ': \"Primaries\" must be a int or a bool!')
    
    if Matrix is None:
        pass
    elif isinstance(Matrix, bool):
        if Matrix is False:
            clip = core.std.SetFrameProp(clip, prop='_Matrix', delete=True)
    elif isinstance(Matrix, int):
        clip = core.std.SetFrameProp(clip, prop='_Matrix', intval=Matrix)
    else:
        raise TypeError(funcName + ': \"Matrix\" must be a int or a bool!')
    
    if Transfer is None:
        pass
    elif isinstance(Transfer, bool):
        if Transfer is False:
            clip = core.std.SetFrameProp(clip, prop='_Transfer', delete=True)
    elif isinstance(Transfer, int):
        clip = core.std.SetFrameProp(clip, prop='_Transfer', intval=Transfer)
    else:
        raise TypeError(funcName + ': \"Transfer\" must be a int or a bool!')
    
    # Output
    return clip
################################################################################################################################


################################################################################################################################
## Frame property function: AssumeFrame()
################################################################################################################################
## Set all the frames in the given clip to be frame-based(progressive).
## It can be used to prevent the field order set in de-interlace filters from being overridden by the frame property '_FieldBased'.
## Also it may be useful to be applied before upscaling or anti-aliasing scripts using EEDI3/nnedi3, etc.(whose field order should be specified explicitly)
################################################################################################################################
def AssumeFrame(clip):
    # Set VS core and function name
    core = vs.get_core()
    funcName = 'AssumeFrame'
    
    if not isinstance(clip, vs.VideoNode):
        raise TypeError(funcName + ': \"clip\" must be a clip!')
    
    # Modify frame properties
    clip = core.std.SetFrameProp(clip, prop='_FieldBased', intval=0)
    clip = core.std.SetFrameProp(clip, prop='_Field', delete=True)
    
    # Output
    return clip
################################################################################################################################


################################################################################################################################
## Frame property function: AssumeTFF()
################################################################################################################################
## Set all the frames in the given clip to be top-field-first(interlaced).
## This frame property will override the field order set in those de-interlace filters.
################################################################################################################################
def AssumeTFF(clip):
    # Set VS core and function name
    core = vs.get_core()
    funcName = 'AssumeTFF'
    
    if not isinstance(clip, vs.VideoNode):
        raise TypeError(funcName + ': \"clip\" must be a clip!')
    
    # Modify frame properties
    clip = core.std.SetFrameProp(clip, prop='_FieldBased', intval=2)
    clip = core.std.SetFrameProp(clip, prop='_Field', delete=True)
    
    # Output
    return clip
################################################################################################################################


################################################################################################################################
## Frame property function: AssumeBFF()
################################################################################################################################
## Set all the frames in the given clip to be bottom-field-first(interlaced).
## This frame property will override the field order set in those de-interlace filters.
################################################################################################################################
def AssumeBFF(clip):
    # Set VS core and function name
    core = vs.get_core()
    funcName = 'AssumeBFF'
    
    if not isinstance(clip, vs.VideoNode):
        raise TypeError(funcName + ': \"clip\" must be a clip!')
    
    # Modify frame properties
    clip = core.std.SetFrameProp(clip, prop='_FieldBased', intval=1)
    clip = core.std.SetFrameProp(clip, prop='_Field', delete=True)
    
    # Output
    return clip
################################################################################################################################


################################################################################################################################
## Frame property function: AssumeField()
################################################################################################################################
## Set all the frames in the given clip to be field-based(derived from interlaced frame).
################################################################################################################################
## Parameters
##     top {bool}:
##         - True: top-field-based
##         - False: bottom-field-based
################################################################################################################################
def AssumeField(clip, top):
    # Set VS core and function name
    core = vs.get_core()
    funcName = 'AssumeField'
    
    if not isinstance(clip, vs.VideoNode):
        raise TypeError(funcName + ': \"clip\" must be a clip!')
    
    if not isinstance(top, int):
        raise TypeError(funcName + ': \"top\" must be a bool!')
    
    # Modify frame properties
    clip = core.std.SetFrameProp(clip, prop='_FieldBased', delete=True)
    clip = core.std.SetFrameProp(clip, prop='_Field', intval=1 if top else 0)
    
    # Output
    return clip
################################################################################################################################


################################################################################################################################
## Frame property function: AssumeCombed()
################################################################################################################################
## Set all the frames in the given clip to be combed or not.
################################################################################################################################
## Parameters
##     combed {bool}:
##         - None: delete property '_Combed' if exist
##         - True: set property '_Combed' to 1
##         - False: set property '_Combed' to 0
##         default: True
################################################################################################################################
def AssumeCombed(clip, combed=True):
    # Set VS core and function name
    core = vs.get_core()
    funcName = 'AssumeCombed'
    
    if not isinstance(clip, vs.VideoNode):
        raise TypeError(funcName + ': \"clip\" must be a clip!')
    
    # Modify frame properties
    if combed is None:
        clip = core.std.SetFrameProp(clip, prop='_Combed', delete=True)
    elif not isinstance(combed, int):
        raise TypeError(funcName + ': \"combed\" must be a bool!')
    else:
        clip = core.std.SetFrameProp(clip, prop='_Combed', intval=combed)
    
    # Output
    return clip
################################################################################################################################





################################################################################################################################
################################################################################################################################
################################################################################################################################
## Helper functions below
################################################################################################################################
################################################################################################################################
################################################################################################################################


################################################################################################################################
## Helper function: GetMatrix()
################################################################################################################################
## Return str or int format parameter "matrix"
################################################################################################################################
## Parameters
##     clip: the source clip
##     matrix: explicitly specify matrix in int or str format, not case-sensitive
##         - 0 | "RGB"
##         - 1 | "709" | "bt709"
##         - 2 | "Unspecified": same as not specified (None)
##         - 4 | "FCC"
##         - 5 | "bt470bg": same as "601"
##         - 6 | "601" | "smpte170m"
##         - 7 | "240" | "smpte240m"
##         - 8 | "YCgCo" | "YCoCg"
##         - 9 | "2020" | "bt2020nc"
##         - 10 | "2020cl" | "bt2020c"
##         - 100 | "OPP" | "opponent": same as the opponent color space used in BM3D denoising filter
##         default: guessed according to the color family and size of input clip
##     dIsRGB {bool}: specify if the target is RGB
##         If source and target are both RGB and "matrix" is not specified, then assume matrix="RGB".
##         default: False for RGB input, otherwise True
##     id {bool}:
##         - False: output matrix name{str}
##         - True: output matrix id{int}
##         default: False
################################################################################################################################
def GetMatrix(clip, matrix=None, dIsRGB=None, id=False):
    # Set VS core and function name
    core = vs.get_core()
    funcName = 'GetMatrix'
    
    if not isinstance(clip, vs.VideoNode):
        raise TypeError(funcName + ': \"clip\" must be a clip!')
    
    # Get properties of input clip
    sFormat = clip.format
    
    sColorFamily = sFormat.color_family
    sIsRGB = sColorFamily == vs.RGB
    sIsYUV = sColorFamily == vs.YUV
    sIsGRAY = sColorFamily == vs.GRAY
    sIsYCOCG = sColorFamily == vs.YCOCG
    if sColorFamily == vs.COMPAT:
        raise ValueError(funcName + ': Color family *COMPAT* is not supported!')
    
    # Get properties of output clip
    if dIsRGB is None:
        dIsRGB = not sIsRGB
    elif not isinstance(dIsRGB, int):
        raise TypeError(funcName + ': \"dIsRGB\" must be a bool!')
    
    # id
    if not isinstance(id, int):
        raise TypeError(funcName + ': \"id\" must be a bool!')
    
    # Resolution level
    noneD = False
    SD = False
    HD = False
    UHD = False
    
    if clip.width <= 0 or clip.height <= 0:
        noneD = True
    elif clip.width <= 1024 and clip.height <= 576:
        SD = True
    elif clip.width <= 2048 and clip.height <= 1536:
        HD = True
    else:
        UHD = True
    
    # Convert to string format
    if matrix is None:
        matrix = "Unspecified"
    elif not isinstance(matrix, int) and not isinstance(matrix, str):
        raise TypeError(funcName + ': \"matrix\" must be a int or str!')
    else:
        if isinstance(matrix, str):
            matrix = matrix.lower()
        if matrix == 0 or matrix == "rgb": # GBR
            matrix = 0 if id else "RGB"
        elif matrix == 1 or matrix == "709" or matrix == "bt709": # bt709
            matrix = 1 if id else "709"
        elif matrix == 2 or matrix == "unspecified": # Unspecified
            matrix = 2 if id else "Unspecified"
        elif matrix == 4 or matrix == "fcc": # fcc
            matrix = 4 if id else "FCC"
        elif matrix == 5 or matrix == "bt470bg": # bt470bg
            matrix = 5 if id else "601"
        elif matrix == 6 or matrix == "601" or matrix == "smpte170m": # smpte170m
            matrix = 6 if id else "601"
        elif matrix == 7 or matrix == "240" or matrix == "smpte240m": # smpte240m
            matrix = 7 if id else "240"
        elif matrix == 8 or matrix == "ycgco" or matrix == "ycocg": # YCgCo
            matrix = 8 if id else "YCgCo"
        elif matrix == 9 or matrix == "2020" or matrix == "bt2020nc": # bt2020nc
            matrix = 9 if id else "2020"
        elif matrix == 10 or matrix == "2020cl" or matrix == "bt2020c": # bt2020c
            matrix = 10 if id else "2020cl"
        elif matrix == 100 or matrix == "opp" or matrix == "opponent": # opponent color space
            matrix = 100 if id else "OPP"
        else:
            raise ValueError(funcName + ': Unsupported matrix specified!')
    
    # If unspecified, automatically determine it based on color family and resolution level
    if matrix == 2 or matrix == "Unspecified":
        if dIsRGB and sIsRGB:
            matrix = 0 if id else "RGB"
        elif sIsYCOCG:
            matrix = 8 if id else "YCgCo"
        else:
            matrix = (6 if id else "601") if SD else (9 if id else "2020") if UHD else (1 if id else "709")
    
    # Output
    return matrix
################################################################################################################################





################################################################################################################################
################################################################################################################################
################################################################################################################################
## Internal used functions below
################################################################################################################################
################################################################################################################################
################################################################################################################################


################################################################################################################################
## Internal used function for Min(), Max() and Avg()
################################################################################################################################
def _Operator2(clip1, clip2, mode, neutral, funcName):
    # Set VS core
    core = vs.get_core()
    
    if not isinstance(clip1, vs.VideoNode):
        raise TypeError(funcName + ': \"clip1\" must be a clip!')
    if not isinstance(clip2, vs.VideoNode):
        raise TypeError(funcName + ': \"clip2\" must be a clip!')
    
    # Get properties of input clip
    sFormat = clip1.format
    if sFormat.id != clip2.format.id:
        raise ValueError(funcName + ': \"clip1\" and \"clip2\" must be of the same format!')
    if clip1.width != clip2.width or clip1.height != clip2.height:
        raise ValueError(funcName + ': \"clip1\" and \"clip2\" must be of the same width and height!')
    
    sSType = sFormat.sample_type
    sbitPS = sFormat.bits_per_sample
    sNumPlanes = sFormat.num_planes
    
    # mode
    if mode is None:
        mode = [1 for i in range(VSMaxPlaneNum)]
    elif isinstance(mode, int):
        mode = [mode for i in range(VSMaxPlaneNum)]
    elif isinstance(mode, list):
        for m in mode:
            if not isinstance(m, int):
                raise TypeError(funcName + ': \"mode\" must be a (list of) int!')
        while len(mode) < VSMaxPlaneNum:
            mode.append(mode[len(mode) - 1])
    else:
        raise TypeError(funcName + ': \"mode\" must be a (list of) int!')
    
    # neutral
    if neutral is None:
        neutral = 1 << (sbitPS - 1) if sSType == vs.INTEGER else 0
    elif not (isinstance(neutral, int) or isinstance(neutral, float)):
        raise TypeError(funcName + ': \"neutral\" must be a int or a float!')
    
    # Process and output
    expr = []
    for i in range(sNumPlanes):
        if funcName == 'Min':
            if mode[i] >= 2:
                expr.append("y {neutral} - abs x {neutral} - abs < y x ?".format(neutral=neutral))
            elif mode[i] == 1:
                expr.append("x y min")
            else:
                expr.append("")
        elif funcName == 'Max':
            if mode[i] >= 2:
                expr.append("y {neutral} - abs x {neutral} - abs > y x ?".format(neutral=neutral))
            elif mode[i] == 1:
                expr.append("x y max")
            else:
                expr.append("")
        elif funcName == 'Avg':
            if mode[i] >= 1:
                expr.append("x y + 2 /")
            else:
                expr.append("")
        else:
            raise ValueError('_Operator2: Unknown \"funcName\" specified!')
    
    return core.std.Expr([clip1, clip2], expr)
################################################################################################################################


################################################################################################################################
## Internal used function for MinFilter() and MaxFilter()
################################################################################################################################
def _Min_Max_Filter(src, flt1, flt2, planes, funcName):
    # Set VS core and function name
    core = vs.get_core()
    
    if not isinstance(src, vs.VideoNode):
        raise TypeError(funcName + ': \"src\" must be a clip!')
    if not isinstance(flt1, vs.VideoNode):
        raise TypeError(funcName + ': \"flt1\" must be a clip!')
    if not isinstance(flt2, vs.VideoNode):
        raise TypeError(funcName + ': \"flt2\" must be a clip!')
    
    # Get properties of input clip
    sFormat = src.format
    if sFormat.id != flt1.format.id or sFormat.id != flt2.format.id:
        raise ValueError(funcName + ': \"src\", \"flt1\" and \"flt2\" must be of the same format!')
    if src.width != flt1.width or src.height != flt1.height or src.width != flt2.width or src.height != flt2.height:
        raise ValueError(funcName + ': \"src\", \"flt1\" and \"flt2\" must be of the same width and height!')
    
    sNumPlanes = sFormat.num_planes
    
    # planes
    process = [0 for i in range(VSMaxPlaneNum)]
    
    if planes is None:
        process = [1 for i in range(VSMaxPlaneNum)]
    elif isinstance(planes, int):
        if planes < 0 or planes >= VSMaxPlaneNum:
            raise ValueError(funcName + ': valid range of \"planes\" is [0, {VSMaxPlaneNum})!'.format(VSMaxPlaneNum=VSMaxPlaneNum))
        process[planes] = 1
    elif isinstance(planes, list):
        for p in planes:
            if not isinstance(p, int):
                raise TypeError(funcName + ': \"planes\" must be a (list of) int!')
            elif p < 0 or p >= VSMaxPlaneNum:
                raise ValueError(funcName + ': valid range of \"planes\" is [0, {VSMaxPlaneNum})!'.format(VSMaxPlaneNum=VSMaxPlaneNum))
            process[p] = 1
    else:
        raise TypeError(funcName + ': \"planes\" must be a (list of) int!')
    
    # Process and output
    expr = []
    for i in range(sNumPlanes):
        if process[i]:
            if funcName == 'MinFilter':
                expr.append("x z - abs x y - abs < z y ?")
            elif funcName == 'MaxFilter':
                expr.append("x z - abs x y - abs > z y ?")
            else:
                raise ValueError('_Min_Max_Filter: Unknown \"funcName\" specified!')
        else:
            expr.append("")
    
    return core.std.Expr([src, flt1, flt2], expr)
################################################################################################################################


################################################################################################################################
## Internal used functions for LimitFilter()
################################################################################################################################
def _LimitFilterExpr(defref, thr, elast, largen_thr, value_range):
    flt = " x "
    src = " y "
    ref = " z " if defref else src
    
    dif = " {flt} {src} - ".format(flt=flt, src=src)
    dif_ref = " {flt} {ref} - ".format(flt=flt, ref=ref)
    dif_abs = dif_ref + " abs "
    
    thr = thr * value_range / 255
    largen_thr = largen_thr * value_range / 255
    
    if thr <= 0 and largen_thr <= 0:
        limitExpr = " {src} ".format(src=src)
    elif thr >= value_range and largen_thr >= value_range:
        limitExpr = ""
    elif elast <= 1:
        limitExpr = " {dif_abs} {thr} <= {flt} {src} ? "
    else:
        thr_1 = thr
        thr_2 = thr * elast
        thr_slope = 1 / (thr_2 - thr_1)
        # final = src + dif * (thr_2 - dif_abs) / (thr_2 - thr_1)
        limitExpr = " {src} {dif} {thr_2} {dif_abs} - * {thr_slope} * + "
        limitExpr = " {dif_abs} {thr_1} <= {flt} {dif_abs} {thr_2} >= {src} " + limitExpr + " ? ? "
        limitExpr = limitExpr.format(dif=dif, dif_abs=dif_abs, thr_1=thr_1, thr_2=thr_2, thr_slope=thr_slope, flt=flt, src=src)
        
        if largen_thr != thr:
            thr_1 = largen_thr
            thr_2 = largen_thr * elast
            thr_slope = 1 / (thr_2 - thr_1)
            # final = src + dif * (thr_2 - dif_abs) / (thr_2 - thr_1)
            limitExprLargen = " {src} {dif} {thr_2} {dif_abs} - * {thr_slope} * + "
            limitExprLargen = " {dif_abs} {thr_1} <= {flt} {dif_abs} {thr_2} >= {src} " + limitExprLargen + " ? ? "
            limitExpr = " {flt} {ref} > " + limitExprLargen + " " + limitExpr + " ? "
            limitExpr = limitExpr.format(dif=dif, dif_abs=dif_abs, thr_1=thr_1, thr_2=thr_2, thr_slope=thr_slope, flt=flt, src=src, ref=ref)
    
    return limitExpr
################################################################################################################################
def _LimitDiffLut(diff, thr, elast, largen_thr, planes):
    # Set VS core and function name
    core = vs.get_core()
    funcName = '_LimitDiffLut'
    
    if not isinstance(diff, vs.VideoNode):
        raise TypeError(funcName + ': \"diff\" must be a clip!')
    
    # Get properties of input clip
    sFormat = diff.format
    
    sSType = sFormat.sample_type
    sbitPS = sFormat.bits_per_sample
    
    if sSType == vs.INTEGER:
        neutral = 1 << (sbitPS - 1)
        value_range = (1 << sbitPS) - 1
    else:
        neutral = 0
        value_range = 1
        raise ValueError(funcName + ': \"diff\" must be of integer format!')
    
    # Process
    thr = thr * value_range / 255
    largen_thr = largen_thr * value_range / 255
    '''
    # for std.MergeDiff(src, limitedDiff)
    if thr <= 0 and largen_thr <= 0:
        def limitLut(x):
            return neutral
        return core.std.Lut(diff, planes=planes, function=limitLut)
    elif thr >= value_range / 2 and largen_thr >= value_range / 2:
        return diff
    elif elast <= 1:
        def limitLut(x):
            dif = x - neutral
            dif_abs = abs(dif)
            thr_1 = largen_thr if dif > 0 else thr
            return x if dif_abs <= thr_1 else neutral
        return core.std.Lut(diff, planes=planes, function=limitLut)
    else:
        def limitLut(x):
            dif = x - neutral
            dif_abs = abs(dif)
            thr_1 = largen_thr if dif > 0 else thr
            thr_2 = thr_1 * elast
            thr_slope = 1 / (thr_2 - thr_1)
            
            if dif_abs <= thr_1:
                return x
            elif dif_abs >= thr_2:
                return neutral
            else:
                # final = src - dif * ((dif_abs - thr_1) / (thr_2 - thr_1) - 1)
                return round(dif * (thr_2 - dif_abs) * thr_slope + neutral)
    '''
    # for std.MakeDiff(flt, limitedDiff)
    if thr <= 0 and largen_thr <= 0:
        return diff
    elif thr >= value_range / 2 and largen_thr >= value_range / 2:
        def limitLut(x):
            return neutral
        return core.std.Lut(diff, planes=planes, function=limitLut)
    elif elast <= 1:
        def limitLut(x):
            dif = x - neutral
            dif_abs = abs(dif)
            thr_1 = largen_thr if dif > 0 else thr
            return neutral if dif_abs <= thr_1 else x
        return core.std.Lut(diff, planes=planes, function=limitLut)
    else:
        def limitLut(x):
            dif = x - neutral
            dif_abs = abs(dif)
            thr_1 = largen_thr if dif > 0 else thr
            thr_2 = thr_1 * elast
            thr_slope = 1 / (thr_2 - thr_1)
            
            if dif_abs <= thr_1:
                return neutral
            elif dif_abs >= thr_2:
                return x
            else:
                # final = flt - dif * (dif_abs - thr_1) / (thr_2 - thr_1)
                return round(dif * (dif_abs - thr_1) * thr_slope + neutral)
        return core.std.Lut(diff, planes=planes, function=limitLut)
################################################################################################################################
