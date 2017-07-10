import sys
import os

from os.path import join
from setuptools import setup

# Also in twarc.py
__version__ = '1.1.3'

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
        url='http://github.com/docnow/twarc',
        author='Ed Summers',
        author_email='ehs@pobox.com',
        py_modules=['twarc', ],
        scripts=scripts,
        description='Archive tweets from the command line',
        install_requires=dependencies,
        setup_requires=['pytest-runner'],
        tests_require=['pytest'],
    )
