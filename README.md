# twarc

[![Build Status](https://github.com/docnow/twarc/workflows/tests/badge.svg)](https://github.com/DocNow/twarc/actions/workflows/main.yml)

Collect data at the command line from the Twitter API (v1.1 and v2).

* Read the [documentation](https://twarc-project.readthedocs.io)
* Ask questions in [Slack](https://bit.ly/docnow-slack) or [Matrix](https://matrix.to/#/#docnow:matrix.org?via=matrix.org&via=petrichor.me&via=converser.eu)

## Contributing 

## Documentation

The documentation is managed at ReadTheDocs. If you would like to improve the documentation you can edit the Markdown files in `docs` or add new ones. Then send a pull request and we can add it.

If you prefer you can create a page on the [wiki](https://github.com/docnow/twarc/wiki/) to workshop the documentation, and then when/if you think it's ready to merged with the documentation create an [issue](https://github.com/docnow/twarc/issues). Please feel free to create whatever documentation is useful in the wiki area.

## Code

If you are interested in adding functionality to twarc or fixing something that's broken here are the steps to setting up your development environment:

    git clone https://github.io/docnow/twarc
    cd twarc

Create a .env file that included Twitter App keys to use during testing:

    BEARER_TOKEN=CHANGEME
    CONSUMER_KEY=CHANGEME
    CONSUMER_SECRET=CHANGEME
    ACCESS_TOKEN=CHANGEME
    ACCESS_TOKEN_SECRET=CHANGEME

Now run the tests:

    python setup.py test

Add your code and some new tests, and send a pull request!
