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
from twarc.decorators import cli_api_error
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


@cli.command('search')
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
@click.option('--archive', is_flag=True, default=False,
    help='Search the full archive (requires Academic Research track)')
@click.option('--limit', default=0, help='Limit search to n tweets')
@click.option('--flatten', is_flag=True, default=False,
    help='Include expansions inline with tweets, and one line per tweet.') 
@click.argument('query', type=str)
@click.argument('outfile', type=click.File('w'), default='-')
@click.pass_obj
@cli_api_error
def search(T, query, outfile, since_id, until_id, start_time, end_time, limit, archive, flatten):
    """
    Search for recent tweets.
    """
    for result in T.search(query, since_id, until_id, start_time, end_time, limit, archive):
        _write(result, outfile, flatten)


@cli.command('sample')
@click.option('--max-tweets', default=0, help='Maximum number of tweets to return.')
@click.option('--flatten', is_flag=True, default=False,
    help='Include expansions inline with tweets, and one line per tweet.') 
@click.argument('outfile', type=click.File('w'), default='-')
@click.pass_obj
@cli_api_error
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
        _write(result, outfile, flatten)


@cli.command('hydrate')
@click.argument('infile', type=click.File('r'), default='-')
@click.argument('outfile', type=click.File('w'), default='-')
@click.option('--flatten', is_flag=True, default=False,
    help='Include expansions inline with tweets, and one line per tweet.') 
@click.pass_obj
@cli_api_error
def hydrate(T, infile, outfile, flatten):
    """
    Hydrate tweet ids from a file or stdin to a file or stdout.
    """
    for result in T.tweet_lookup(infile):
        _write(result, outfile, flatten)


@cli.command('users')
@click.option('--usernames', is_flag=True, default=False)
@click.option('--flatten', is_flag=True, default=False,
    help='Include expansions inline with tweets, and one line per tweet.') 
@click.argument('infile', type=click.File('r'), default='-')
@click.argument('outfile', type=click.File('w'), default='-')
@click.pass_obj
@cli_api_error
def users(T, infile, outfile, usernames, flatten):
    """
    Get data for user ids or usernames.
    """
    for result in T.user_lookup(infile, usernames):
        _write(result, outfile, flatten)


@cli.command('flatten')
@click.argument('infile', type=click.File('r'), default='-')
@click.argument('outfile', type=click.File('w'), default='-')
@cli_api_error
def flatten(infile, outfile):
    """
    "Flatten" tweets, or move expansions inline with tweet objects.
    """
    for line in infile:
        result = json.loads(line)
        _flatten(result, outfile, True)


@cli.command('stream')
@click.option('--max-tweets', default=0, help='Maximum number of tweets to return.')
@click.option('--flatten', is_flag=True, default=False,
    help='Include expansions inline with tweets, and one line per tweet.') 
@click.argument('outfile', type=click.File('w'), default='-')
@click.pass_obj
@cli_api_error
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
        _write(result, outfile, flatten)


@cli.group()
@click.pass_obj
def stream_rules(T):
    """
    List, add and delete rules for your stream.
    """
    pass


@stream_rules.command('list')
@click.pass_obj
@cli_api_error
def list_stream_rules(T):
    result = T.get_stream_rules()
    if 'data' not in result or len(result['data']) == 0:
        click.echo('No rules yet. Add them with ' + click.style('twarc2 stream-rules add', bold=True))
    else:
        count = 0
        for rule in result['data']:
            if count > 5:
                count = 0
            s = rule['value']
            if 'tag' in rule:
                s += f" (tag: {rule['tag']})"
            click.echo(click.style(f'☑ {s}'))
            count += 1


@stream_rules.command('add')
@click.pass_obj
@click.option('--tag', type=str, help='a tag to help identify the rule')
@click.argument('value', type=str)
@cli_api_error
def add_stream_rule(T, value, tag):
    if tag:
        rules = [{"value": value, "tag": tag}]
    else:
        rules = [{"value": value}] 

    results = T.add_stream_rules(rules)
    if 'errors' in results:
        click.echo(_error_str(results['errors']), err=True)
    else:
        click.echo(click.style(f'🚀 Added rule for "{value}"', fg='green'))


@stream_rules.command('delete')
@click.argument('value')
@click.pass_obj
@cli_api_error
def delete_stream_rule(T, value):
    # find the rule id
    result = T.get_stream_rules()
    if 'data' not in result:
        click.echo(click.style('💔 There are no rules to delete!', fg='red'), err=True)
    else:
        rule_id = None
        for rule in result['data']:
            if rule['value'] == value:
                rule_id = rule['id']
                break
        if not rule_id:
            click.echo(click.style(f'🙃 No rule could be found for "{value}"',
                fg='red'), err=True)
        else:
            results = T.delete_stream_rule_ids([rule_id])
            if 'errors' in results:
                click.echo(_error_str(results['errors']), err=True)
            else:
                click.echo(f"🗑  Deleted stream rule for {value}", color='green') 


@stream_rules.command('delete-all')
@click.pass_obj
@cli_api_error
def delete_all(T):
    result = T.get_stream_rules()
    if 'data' not in result:
        click.echo(click.style('💔 There are no rules to delete!', fg='red'), err=True)
    else:
        rule_ids = [r['id'] for r in result['data']]
        results = T.delete_stream_rule_ids(rule_ids)
        click.echo(f"🗑 Deleted {len(rule_ids)} rules.")


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
            s = "💣 "
            if 'message' in part:
                s += part['message']
            elif 'title' in part:
                s += part['title']
            else:
                s = 'Unknown error'
            if 'type' in part:
                s += f" see: {part['type']}"
            parts.append(s)

    return click.style("\n".join(parts), fg="red")

def _write(results, outfile, flatten):
    if 'data' in results:
        if flatten:
            if isinstance(results['data'], list):
                for r in flat(results)['data']:
                    click.echo(json.dumps(r), file=outfile)
            else:
                r = flat(results)['data'][0]
                click.echo(json.dumps(r) + "\n", file=outfile)
        else:
            click.echo(json.dumps(results) + "\n", file=outfile)
