# twarc

[![DOI](https://zenodo.org/badge/7605723.svg)](https://zenodo.org/badge/latestdoi/7605723) [![Build Status](https://github.com/docnow/twarc/workflows/tests/badge.svg)](https://github.com/DocNow/twarc/actions/workflows/main.yml) [![Standard](https://img.shields.io/endpoint?url=https%3A%2F%2Ftwbadges.glitch.me%2Fbadges%2Fstandard)](https://developer.twitter.com/en/docs/twitter-api) [![Premium](https://img.shields.io/endpoint?url=https%3A%2F%2Ftwbadges.glitch.me%2Fbadges%2Fpremium)](https://developer.twitter.com/) [![v2](https://img.shields.io/endpoint?url=https%3A%2F%2Ftwbadges.glitch.me%2Fbadges%2Fv2)](https://developer.twitter.com/en/docs/twitter-api)

twarc is a command line tool and Python library for collecting and archiving Twitter JSON
data via the Twitter API. It has separate commands (twarc and twarc2) for working with the older
v1.1 API and the newer v2 API and Academic Access (respectively).

* Read the [documentation](https://twarc-project.readthedocs.io)
* Ask questions here in [GitHub](https://github.com/DocNow/twarc/discussions), in [Slack](https://bit.ly/docnow-slack) or [Matrix](https://matrix.to/#/#docnow:matrix.org?via=matrix.org&via=petrichor.me&via=converser.eu)

twarc has been developed with generous support from the [Mellon Foundation](https://mellon.org/).

## Contributing 

New features are welcome and encouraged for twarc. However, to keep the core twarc library and command line tool sustainable we will look at new functionality with the following principles in mind:

1. Purpose: twarc is for *collection* and *archiving* of Twitter data via the Twitter API.
2. Sustainability: keeping the surface area of twarc and it's dependencies small enough to ensure high quality.
3. Utility: what is exposed by twarc should be applicable to different people, projects and domains, and not specific use cases.
4. API consistency: as much as sensible we aim to make twarc consistent with the Twitter API, and also aim to make twarc consistent with itself - so commands in core twarc should work similarly to each other, and twarc functionality should align towards the Twitter API.

For features and approaches that fall outside of this, twarc enables external packages to hook into the twarc2 command line tool via [click-plugins](https://github.com/click-contrib/click-plugins). This means that if you want to propose new functionality, you can create your own package without coordinating with core twarc.

### Documentation

The documentation is managed at ReadTheDocs. If you would like to improve the documentation you can edit the Markdown files in `docs` or add new ones. Then send a pull request and we can add it.

To view your documentation locally you should be able to:

    pip install -r requirements-mkdocs.txt
    mkdocs serve
    open http://127.0.0.1:8000/

If you prefer you can create a page on the [wiki](https://github.com/docnow/twarc/wiki/) to workshop the documentation, and then when/if you think it's ready to be merged with the documentation create an [issue](https://github.com/docnow/twarc/issues). Please feel free to create whatever documentation is useful in the wiki area.

### Code

If you are interested in adding functionality to twarc or fixing something that's broken here are the steps to setting up your development environment:

    git clone https://github.com/docnow/twarc
    cd twarc
    pip install -r requirements.txt

Create a .env file that included Twitter App keys to use during testing:

    BEARER_TOKEN=CHANGEME
    CONSUMER_KEY=CHANGEME
    CONSUMER_SECRET=CHANGEME
    ACCESS_TOKEN=CHANGEME
    ACCESS_TOKEN_SECRET=CHANGEME

Now run the tests:

    python setup.py test

Add your code and some new tests, and send a pull request!

