#!/usr/bin/env python3

import setuptools
from pathlib import Path

long_description = Path("README.md").read_text()
install_requires = Path("requirements.txt").read_text()

package_name = "mvsfunc"

exec(Path(f'{package_name}/_metadata.py').read_text(), meta := {})

setuptools.setup(
    name=package_name,
    version=meta['__version__'],
    author=meta['__author_name__'],
    author_email=meta['__author_email__'],
    maintainer=meta['__maintainer_name__'],
    maintainer_email=meta['__maintainer_email__'],
    description=meta['__doc__'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=[
        package_name
    ],
    package_data={
        package_name: ['py.typed'],
    },
    install_requires=install_requires,
    project_urls={
        "Source Code": 'https://github.com/HomeOfVapourSynthEvolution/mvsfunc',
    },
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
        "Typing :: Typed",

        "Topic :: Multimedia :: Video",
    ],
    python_requires='>=3.6',
)
