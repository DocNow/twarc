import sys

from os.path import join
from setuptools import setup

__version__ = '2.0.0'

with open("README.md") as f:
    long_description = f.read()

dependencies = open('requirements.txt')

setup(
    name='twarc',
    version=__version__,
    url='https://github.com/docnow/twarc',
    packages=['twarc', ],
    description='Archive tweets from the command line',
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.7',
    install_requires=dependencies,
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'python-dotenv'],
    entry_points={'console_scripts': ['twarc = twarc:main']}
)
