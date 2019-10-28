import sys

from os.path import join
from setuptools import setup

# Also in twarc/__init__.py
__version__ = '1.7.5'

with open("README.md") as f:
    long_description = f.read()

if sys.version_info[0] < 3:
    dependencies = open(join('requirements', 'python2.txt')).read().split()
else:
    dependencies = open(join('requirements', 'python3.txt')).read().split()

if __name__ == "__main__":
    setup(
        name='twarc',
        version=__version__,
        url='https://github.com/docnow/twarc',
        author='Ed Summers',
        author_email='ehs@pobox.com',
        packages=['twarc', ],
        description='Archive tweets from the command line',
        long_description=long_description,
        long_description_content_type="text/markdown",
        python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
        install_requires=dependencies,
        setup_requires=['pytest-runner'],
        tests_require=['pytest'],
        entry_points={'console_scripts': ['twarc = twarc:main']}
    )
