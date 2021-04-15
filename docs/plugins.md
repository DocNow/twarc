# Plugins

twarc v1 collected a set of utilities for working with tweet json in the
[utils] directory of the git repository. This was a handy way to develop and
share snippets of code. But some utilities had different dependencies which
weren't managed in a uniform way. Some of the utilities had slightly different
interfaces. They needed to be downloaded from GitHub manually and weren't
easily accessible at the command line if you remembered where you put them.

With *twarc2* these utilities are now installable as plugins, which are made
available as subcommands using the same twarc2 command line. Plugins are
published separately from twarc on [PyPI] and are installed with [pip]. Here is
a list of some known plugins (if you write one please [let us know] so we can
add it to this list):

* [twarc-ids](https://pypi.org/project/twarc-ids/): extract tweet ids from tweets
* [twarc-videos](https://pypi.org/project/twarc-videos): extract videos from tweets
* [twarc-csv](https://pypi.org/project/twarc-csv/): export tweets to CSV
* [twarc-timelines](https://pypi.org/project/twarc-timelines): download tweet timelines for a list of users

## Writing a Plugin

The [twarc-ids] plugin provides an example of how to write plugins. This
reference plugin simply reads collected tweet JSON data and writes out the tweet
identifiers. First you install the plugin:

    pip install twarc-ids

and then you use it:

    twarc2 ids tweets.json > ids.txt

Internally twarc's command line is implemented using the [click] library. The
[click-plugins] module is what manages twarc2 plugins. Basically you import
`click` and implement your plugin as you would any other click utility, for
example:

```python
import json
import click

@click.command()
@click.argument('infile', type=click.File('r'), default='-')
@click.argument('outfile', type=click.File('w'), default='-')
def ids(infile, outfile):
    """
    Extract tweet ids from tweet JSON.
    """
    for line in infile:
        tweet = json.loads(line)
        click.echo(t['data']['id'], file=outfile)
```

Note that the plugin takes input file *infile* and writes to an output file
*outfile* which default to stdin and stdout respectively. This allows plugin
utilities to be used as part of pipelines. You can add options using the
standard facilities that click provides if your plugin needs them.

If your plugin needs to talk to the Twitter API then just add the
`@click.pass_obj` decorator which will ensure that the first parameter in
your function will be a Twarc2 client that is configured to use the
client's keys.

```python
@click.command()
@click.argument('infile', type=click.File('r'), default='-')
@click.argument('outfile', type=click.File('w'), default='-')
@click.pass_obj
def ids(twarc_client, infile, outfile):
    # do something with the twarc client here
```

Finally you just need to create a `setup.py` file for your project that
looks something like this:

```python

import setuptools

setuptools.setup(
    name='twarc-ids',
    version='0.0.1',
    url='https://github.com/docnow/twarc-ids',
    author='Ed Summers',
    author_email='ehs@pobox.com',
    py_modules=['twarc_ids'],
    description='A twarc plugin to read Twitter data and output the tweet ids',
    install_requires=['twarc'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    entry_points='''
        [twarc.plugins]
        ids=twarc_ids:ids
    '''
)
```

The key part here is the `entry_points` section which is what allows twarc2 to
discover twarc.plugins dynamically at runtime, and also defines how the
subcommand maps to the plugin's function.

It's good practice to include a test or two for your plugin to ensure it works
over time. Check out the example [here] for how to test command line utilities
easily with click.

[twarc-ids]: https://github.com/docnow/twarc-ids/
[PyPI]: https://python.org/pypi/
[pip]: https://pip.pypa.io/en/stable/
[click]: https://click.palletsprojects.com/
[click-plugins]: https://github.com/click-contrib/click-plugins
[here]: https://github.com/DocNow/twarc-ids/blob/main/test_twarc_ids.py
[let us know]: https://github.com/docnow/twarc/issues/
[utils]: https://github.com/DocNow/twarc/tree/main/utils
