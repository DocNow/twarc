"""
The command line interfact to the Twitter v2 API.
"""

import os
import re
import json
import twarc
import click

from click_plugins import with_plugins
from pkg_resources import iter_entry_points
from twarc.expansions import flatten as flat


@with_plugins(iter_entry_points('twarc.plugins'))
@click.group()
@click.option('--consumer-key', type=str)
@click.option('--consumer-secret', type=str)
@click.option('--access-token', type=str)
@click.option('--access-token-secret', type=str)
@click.option('--bearer-token', type=str)
@click.pass_context
def cli(ctx, consumer_key, consumer_secret, access_token, access_token_secret, bearer_token):
    """
    Collect raw data from the Twitter V2 API.
    """
    ctx.obj = twarc.Twarc2(bearer_token)


@cli.command()
@click.option('--since-id', type=int,
    help='Match tweets sent after tweet id')
@click.option('--until-id', type=int,
    help='Match tweets sent prior to tweet id')
@click.option('--start-time',
    type=click.DateTime(formats=('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S')),
    help='Match tweets created after time (ISO 8601/RFC 3339), e.g.  2021-01-01T12:31:04')
@click.option('--end-time',
    type=click.DateTime(formats=('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S')),
    help='Match tweets sent before time (ISO 8601/RFC 3339)')
@click.option('--flatten', is_flag=True, default=False,
    help='Include expansions inline with tweets.') 
@click.argument('query', type=str)
@click.argument('outfile', type=click.File('w'), default='-')
@click.pass_obj
def recent_search(T, query, since_id, until_id, start_time, end_time, flatten):
    """
    Search for recent tweets.
    """
    for result in T.recent_search(query, since_id, until_id, start_time, end_time):
        if flatten:
            result = flat(result)
        click.echo(json.dumps(result), file=outfile)


@cli.command()
@click.option('--flatten', is_flag=True, default=False,
    help='Include expansions inline with tweets.') 
@click.argument('outfile', type=click.File('w'), default='-')
@click.pass_obj
def sample(T, flatten, outfile):
    """
    Fetch tweets from the sample stream.
    """
    for result in T.sample():
        if flatten:
            result = flat(result)
        click.echo(json.dumps(result), file=outfile)


@cli.command()
@click.argument('infile', type=click.File('r'), default='-')
@click.argument('outfile', type=click.File('w'), default='-')
@click.option('--flatten', is_flag=True, default=False,
    help='Include expansions inline with tweets.') 
@click.pass_obj
def hydrate(T, infile, outfile, flatten):
    """
    Hydrate tweet ids from a file or stdin to a file or stdout.
    """
    for result in T.tweet_lookup(infile):
        if flatten:
            result = flat(result)
        click.echo(json.dumps(result), file=outfile)


@cli.command()
@click.option('--usernames', is_flag=True, default=False)
@click.option('--flatten', is_flag=True, default=False,
    help='Include expansions inline with tweets.') 
@click.argument('infile', type=click.File('r'), default='-')
@click.argument('outfile', type=click.File('w'), default='-')
@click.pass_obj
def users(T, infile, outfile, usernames, flatten):
    for result in T.user_lookup(infile, usernames):
        click.echo(json.dumps(result), file=outfile)


@cli.command()
@click.argument('infile', type=click.File('r'), default='-')
@click.argument('outfile', type=click.File('w'), default='-')
def flatten(infile, outfile):
    """
    "Flatten" tweets, or move expansions inline with tweet objects.
    """
    for line in infile:
        result = json.loads(line)
        result = twarc.expansions.flatten(result)
        click.echo(json.dumps(result), file=outfile)


