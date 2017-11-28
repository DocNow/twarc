import sys
import os

from os.path import join
from setuptools import setup

# Also in twarc.py
__version__ = '1.3.1'

if sys.version_info[0] < 3:
    dependencies = open(join('requirements', 'python2.txt')).read().split()
else:
    dependencies = open(join('requirements', 'python3.txt')).read().split()

if os.name == "nt":
    scripts = ['twarc.py']
else:
    scripts = ['bin/twarc']

if __name__ == "__main__":
    setup(
        name='twarc',
        version=__version__,
        url='https://github.com/docnow/twarc',
        author='Ed Summers',
        author_email='ehs@pobox.com',
        packages=['twarc'],
        scripts=scripts,
        description='Archive tweets from the command line',
        install_requires=dependencies,
        setup_requires=['pytest-runner'],
        tests_require=['pytest'],
    )
