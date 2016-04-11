import sys

from os.path import join
from setuptools import setup
from version import __version__


if sys.version_info[0] < 3:
    dependencies = open(join('requirements', 'python2.txt')).read().split()
else:
    dependencies = open(join('requirements', 'python3.txt')).read().split()


setup(
    name='twarc',
    version=__version__,
    url='http://github.com/edsu/twarc',
    author='Ed Summers',
    author_email='ehs@pobox.com',
    py_modules=['twarc', ],
    scripts=['twarc.py', 'utils/twarc-archive.py'],
    description='command line utility to archive Twitter search results '
                'as line-oriented-json',
    install_requires=dependencies,
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
