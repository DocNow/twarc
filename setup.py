import sys

from os.path import join
from setuptools import setup, Command


class PyTest(Command):
    """
    A command to convince setuptools to run pytests.
    """
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import pytest
        pytest.main("test.py")

if sys.version_info[0] < 3:
    dependencies = open(join('requirements', 'python2.txt')).read().split()
else:
    dependencies = open(join('requirements', 'python3.txt')).read().split()


setup(
    name='twarc',
    version='0.2.7',
    url='http://github.com/edsu/twarc',
    author='Ed Summers',
    author_email='ehs@pobox.com',
    py_modules=['twarc', ],
    scripts=['twarc.py'],
    description='command line utility to archive Twitter search results as line-oriented-json',
    cmdclass={'test': PyTest},
    install_requires=dependencies,
    tests_require=['pytest']
)


