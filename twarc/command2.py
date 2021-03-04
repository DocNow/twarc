import os
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
@click.pass_obj
def recent_search(T, query, since_id, until_id, start_time, end_time, flatten):
    """
    Search for recent tweets .
    """
    for obj in T.recent_search(query, since_id, until_id, start_time, end_time):
        if flatten:
            obj = flat(obj)
        click.echo(json.dumps(obj))

@cli.command()
@click.option('--flatten', is_flag=True, default=False,
    help='Include expansions inline with tweets.') 
@click.pass_obj
def sample(T, flatten):
    """
    Fetch tweets from the sample stream.
    """
    if T.api_version == "1.1":
        sample = T.sample()
    else:
        sample = T.sample()
    for obj in sample:
        if flatten:
            obj = flat(obj)
        click.echo(json.dumps(obj))

@cli.command()
@click.argument('infile', type=click.File('r'), default='-')
@click.argument('outfile', type=click.File('w'), default='-')
def flatten(infile, outfile):
    """
    "Flatten" tweets, or move expansions inline with tweet objects.
    """
    for line in infile:
        data = json.loads(line)
        data = twarc.expansions.flatten(data)
        outfile.write(json.dumps(data))
