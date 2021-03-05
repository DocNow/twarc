"""
The command line interfact to the Twitter v2 API.
"""

import os
import re
import json
import twarc
import click
import threading

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
@click.option('--max-tweets', default=0, help='Maximum number of tweets to return.')
@click.option('--flatten', is_flag=True, default=False,
    help='Include expansions inline with tweets.') 
@click.argument('outfile', type=click.File('w'), default='-')
@click.pass_obj
def sample(T, flatten, outfile, max_tweets):
    """
    Fetch tweets from the sample stream.
    """
    count = 0
    event = threading.Event()
    for result in T.sample(event=event):
        count += 1
        if max_tweets != 0 and count >= max_tweets:
            event.set()
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
    """
    Get data for user ids or usernames.
    """
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


@cli.command()
@click.option('--max-tweets', default=0, help='Maximum number of tweets to return.')
@click.option('--flatten', is_flag=True, default=False,
    help='Include expansions inline with tweets.') 
@click.argument('outfile', type=click.File('w'), default='-')
@click.pass_obj
def stream(T, flatten, outfile, max_tweets):
    """
    Fetch tweets from the live stream.
    """
    event = threading.Event()
    count = 0
    for result in T.stream(event=event):
        count += 1
        if max_tweets != 0 and count == max_tweets:
            event.set()
        if flatten:
            result = flat(result)
        click.echo(json.dumps(result), file=outfile)


@cli.group()
@click.pass_obj
def stream_rules(T):
    """
    List, add and delete rules for your stream.
    """
    pass

@stream_rules.command()
@click.pass_obj
def list(T):
    result = T.get_stream_rules()
    if 'data' not in result or len(result['data']) == 0:
        click.echo('No rules yet, add them with twarc rules-add')
    else:
        for rule in result['data']:
            click.echo(f"- {_rule_str(rule)}")

@stream_rules.command()
@click.pass_obj
@click.option('--tag', type=str, help='a tag to help identify the rule')
@click.argument('value', type=str)
def add(T, value, tag):
    if tag:
        rules = [{"value": value, "tag": tag}]
    else:
        rules = [{"value": value}] 

    results = T.add_stream_rules(rules)

    if 'errors' in results:
        click.echo(_error_str(results['errors']), err=True)
    else:
        rule = results['data'][0]
        click.echo(click.style(f"Added rule: {_rule_str(rule)}", fg='green'))

@stream_rules.command()
@click.argument('rule_id')
@click.pass_obj
def delete(T, rule_id):
    results = T.delete_stream_rule_ids([rule_id])
    if 'errors' in results:
        click.echo(_error_str(results['errors']), err=True)
    else:
        click.echo(f"Deleted stream rule {rule_id}") 

def _rule_str(rule):
    s = f"id={rule['id']} value={rule['value']}"
    if 'tag' in rule:
        s += f" tag={rule['tag']}"
    return s

def _error_str(errors):
    # collapse all the error messages into a newline delimited red colored list
    # the passed in errors can be single error object or a list of objects, each 
    # of which has an errors key that points to a list of error objects

    if type(errors) != list:
        errors = [{"errors": errors}]

    parts = []
    for error in errors:
        for part in error['errors']:
            if 'message' in part:
                s = part['message']
            elif 'title' in part:
                s = part['title']
            else:
                s = 'Unknown error'
            if 'type' in part:
                s += f" see: {part['type']}"
            parts.append(s)

    return click.style("\n".join(parts), fg="red")