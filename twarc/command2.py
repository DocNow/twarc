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
@click.option('--v2', is_flag=True, default=False)
@click.pass_context
def cli(ctx, consumer_key, consumer_secret, access_token, access_token_secret, bearer_token, v2):
    if v2:
        ctx.obj = twarc.Twarc2(bearer_token)
    else:
        ctx.obj = twarc.Twarc()

@cli.command()
@click.option('--flatten', is_flag=True, default=False)
@click.pass_obj
def sample(T, flatten):
    """
    Fetch tweets from the sample stream.
    """
    if T.api_version == "1.1":
        sample = T.sample()
    else:
        sample = T.sample(flatten=flatten)
    for obj in sample:
        click.echo(json.dumps(obj))
