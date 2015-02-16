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

setup(
    name='twarc',
    version='0.2.1',
    url='http://github.com/edsu/twarc',
    author='Ed Summers',
    author_email='ehs@pobox.com',
    py_modules=['twarc', ],
    scripts=['twarc.py'],
    description='command line utility to archive Twitter search results as line-oriented-json',
    cmdclass={'test': PyTest},
    install_requires=['python-dateutil', 'requests_oauthlib'],
    tests_require=['pytest']
)
