from setuptools import setup

setup(
    name = 'twarc',
    version = '0.0.3',
    url = 'http://github.com/edsu/twarc',
    author = 'Ed Summers',
    author_email = 'ehs@pobox.com',
    py_modules = ['twarc',],
    scripts = ['twarc.py'],
    description = 'command line utility to archive Twitter search results as line-oriented-json', 
    install_requires = ['oauth2', 'python-dateutil']
)
