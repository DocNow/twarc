import os
import json
import twarc
import click

from click_plugins import with_plugins
from pkg_resources import iter_entry_points

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
@click.pass_obj
def sample(T):
    """
    Fetch tweets from the sample stream.
    """
    if T.api_version == "1.1":
        sample = T.sample()
    else:
        sample = T.sample()
    for obj in sample:
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
