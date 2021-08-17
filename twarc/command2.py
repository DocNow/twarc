"""
The command line interfact to the Twitter v2 API.
"""

import re
import json
import twarc
import click
import logging
import pathlib
import datetime
import configobj
import threading

from tqdm.auto import tqdm
from datetime import timezone
from click_plugins import with_plugins
from pkg_resources import iter_entry_points

from twarc.version import version
from twarc.handshake import handshake
from twarc.config import ConfigProvider
from twarc.expansions import ensure_flattened
from click_config_file import configuration_option
from twarc.decorators2 import (
    cli_api_error,
    TimestampProgressBar,
    FileSizeProgressBar,
    _millis2snowflake,
    _date2millis,
)


config_provider = ConfigProvider()
log = logging.getLogger("twarc")


@with_plugins(iter_entry_points("twarc.plugins"))
@click.group()
@click.option(
    "--consumer-key",
    type=str,
    envvar="CONSUMER_KEY",
    help='Twitter app consumer key (aka "App Key")',
)
@click.option(
    "--consumer-secret",
    type=str,
    envvar="CONSUMER_SECRET",
    help='Twitter app consumer secret (aka "App Secret")',
)
@click.option(
    "--access-token",
    type=str,
    envvar="ACCESS_TOKEN",
    help="Twitter app access token for user authentication.",
)
@click.option(
    "--access-token-secret",
    type=str,
    envvar="ACCESS_TOKEN_SECRET",
    help="Twitter app access token secret for user authentication.",
)
@click.option(
    "--bearer-token",
    type=str,
    envvar="BEARER_TOKEN",
    help="Twitter app access bearer token.",
)
@click.option(
    "--app-auth/--user-auth",
    default=True,
    help="Use application authentication or user authentication. Some rate limits are "
    "higher with user authentication, but not all endpoints are supported.",
    show_default=True,
)
@click.option("--log", "-l", "log_file", default="twarc.log")
@click.option("--verbose", is_flag=True, default=False)
@click.option(
    "--metadata/--no-metadata",
    default=True,
    show_default=True,
    help="Include/don't include metadata about when and how data was collected.",
)
@configuration_option(
    cmd_name="twarc", config_file_name="config", provider=config_provider
)
@click.pass_context
def twarc2(
    ctx,
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret,
    bearer_token,
    log_file,
    metadata,
    app_auth,
    verbose,
):
    """
    Collect data from the Twitter V2 API.
    """
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    log.info("using config %s", config_provider.file_path)

    if bearer_token or (consumer_key and consumer_secret):
        if app_auth and (bearer_token or (consumer_key and consumer_secret)):
            ctx.obj = twarc.Twarc2(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                bearer_token=bearer_token,
                metadata=metadata,
            )
        # Check everything is present for user auth.
        elif consumer_key and consumer_secret and access_token and access_token_secret:
            ctx.obj = twarc.Twarc2(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                metadata=metadata,
            )
        else:
            click.echo(
                click.style(
                    "🙃  To use user authentication, you need all of the following:\n"
                    "- consumer_key\n",
                    "- consumer_secret\n",
                    "- access_token\n",
                    "- access_token_secret\n",
                    fg="red",
                ),
                err=True,
            )
            click.echo("You can configure twarc2 using the `twarc2 configure` command.")
    else:
        click.echo()
        click.echo("👋  Hi I don't see a configuration file yet, so lets make one.")
        click.echo()
        click.echo("Please follow these steps:")
        click.echo()
        click.echo("1. visit https://developer.twitter.com/en/portal/")
        click.echo("2. create a project and an app")
        click.echo("3. go to your Keys and Tokens and generate your keys")
        click.echo()
        ctx.invoke(configure)


@twarc2.command("configure")
@click.pass_context
def configure(ctx):
    """
    Set up your Twitter app keys.
    """

    config_file = config_provider.file_path
    log.info("creating config file: %s", config_file)

    config_dir = pathlib.Path(config_file).parent
    if not config_dir.is_dir():
        log.info("creating config directory: %s", config_dir)
        config_dir.mkdir(parents=True)

    keys = handshake()
    if keys is None:
        raise click.ClickException("Unable to authenticate")

    config = configobj.ConfigObj(unrepr=True)
    config.filename = config_file

    # Only write non empty keys.
    for key in [
        "consumer_key",
        "consumer_secret",
        "access_token",
        "access_token_secret",
        "bearer_token",
    ]:
        if keys.get(key, None):
            config[key] = keys[key]

    config.write()

    click.echo(
        click.style(f"\nYour keys have been written to {config_file}", fg="green")
    )
    click.echo()
    click.echo("\n✨ ✨ ✨  Happy twarcing! ✨ ✨ ✨\n")

    ctx.exit()


@twarc2.command("version")
def get_version():
    """
    Return the version of twarc that is installed.
    """
    click.echo(f"twarc v{version}")


def _search(
    T,
    query,
    outfile,
    since_id,
    until_id,
    start_time,
    end_time,
    limit,
    max_results,
    archive,
    hide_progress,
):
    """
    Search for tweets.
    """
    count = 0

    # Make sure times are always in UTC, click sometimes doesn't add timezone:
    if start_time is not None and start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time is not None and end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    if archive:
        search_method = T.search_all

        # default number of tweets per response 500 when not set otherwise
        if max_results == 0:
            max_results = 100  # temp fix for #504

        # start time defaults to the beginning of Twitter to override the
        # default of the last month. Only do this if start_time is not already
        # specified and since_id and until_id aren't being used
        if start_time is None and since_id is None and until_id is None:
            start_time = datetime.datetime(2006, 3, 21, tzinfo=datetime.timezone.utc)
    else:
        if max_results == 0:
            max_results = 100
        search_method = T.search_recent

    hide_progress = True if (outfile.name == "<stdout>") else hide_progress

    with TimestampProgressBar(
        since_id, until_id, start_time, end_time, disable=hide_progress
    ) as progress:
        for result in search_method(
            query, since_id, until_id, start_time, end_time, max_results
        ):
            _write(result, outfile)
            tweet_ids = [t["id"] for t in result.get("data", [])]
            log.info("archived %s", ",".join(tweet_ids))
            progress.update_with_result(result)
            count += len(result["data"])
            if limit != 0 and count >= limit:
                # Display message when stopped early
                progress.desc = f"Set --limit of {limit} reached"
                break
        else:
            progress.early_stop = False


@twarc2.command("search")
@click.option("--since-id", type=int, help="Match tweets sent after tweet id")
@click.option("--until-id", type=int, help="Match tweets sent prior to tweet id")
@click.option(
    "--start-time",
    type=click.DateTime(formats=("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")),
    help="Match tweets created after UTC time (ISO 8601/RFC 3339), e.g.  2021-01-01T12:31:04",
)
@click.option(
    "--end-time",
    type=click.DateTime(formats=("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")),
    help="Match tweets sent before UTC time (ISO 8601/RFC 3339)",
)
@click.option(
    "--archive",
    is_flag=True,
    default=False,
    help="Search the full archive (requires Academic Research track). Defaults to searching the entire twitter archive if --start-time is not specified.",
)
@click.option("--limit", default=0, help="Maximum number of tweets to save")
@click.option(
    "--max-results", default=0, help="Maximum number of tweets per API response"
)
@click.option(
    "--hide-progress",
    is_flag=True,
    default=False,
    help="Hide the Progress bar. Default: show progress, unless using pipes.",
)
@click.argument("query", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def search(
    T,
    query,
    outfile,
    since_id,
    until_id,
    start_time,
    end_time,
    limit,
    max_results,
    archive,
    hide_progress,
):
    """
    Search for tweets.
    """
    return _search(
        T,
        query,
        outfile,
        since_id,
        until_id,
        start_time,
        end_time,
        limit,
        max_results,
        archive,
        hide_progress,
    )


@twarc2.command("counts")
@click.option("--since-id", type=int, help="Count tweets sent after tweet id")
@click.option("--until-id", type=int, help="Count tweets sent prior to tweet id")
@click.option(
    "--start-time",
    type=click.DateTime(formats=("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")),
    help="Count tweets created after UTC time (ISO 8601/RFC 3339), e.g.  2021-01-01T12:31:04",
)
@click.option(
    "--end-time",
    type=click.DateTime(formats=("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")),
    help="Count tweets sent before UTC time (ISO 8601/RFC 3339)",
)
@click.option(
    "--archive",
    is_flag=True,
    default=False,
    help="Count using the full archive (requires Academic Research track)",
)
@click.option(
    "--granularity",
    default="hour",
    type=click.Choice(["day", "hour", "minute"], case_sensitive=False),
    help="Aggregation level for counts. Can be one of: day, hour, minute. Default is hour.",
)
@click.option(
    "--limit",
    default=0,
    help="Maximum number of days of results to save (minimum is 30 days)",
)
@click.option(
    "--text",
    is_flag=True,
    default=False,
    help="Output the counts as human readable text",
)
@click.option("--csv", is_flag=True, default=False, help="Output counts as CSV")
@click.option(
    "--hide-progress",
    is_flag=True,
    default=False,
    help="Hide the Progress bar. Default: show progress, unless using pipes.",
)
@click.argument("query", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def counts(
    T,
    query,
    outfile,
    since_id,
    until_id,
    start_time,
    end_time,
    archive,
    granularity,
    limit,
    text,
    csv,
    hide_progress,
):
    """
    Return counts of tweets matching a query.
    """
    count = 0

    # Make sure times are always in UTC, click sometimes doesn't add timezone:
    if start_time is not None and start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time is not None and end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    if archive:
        count_method = T.counts_all
        # start time defaults to the beginning of Twitter to override the
        # default of the last month. Only do this if start_time is not already
        # specified and since_id isn't being used
        if start_time is None and since_id is None:
            start_time = datetime.datetime(2006, 3, 21, tzinfo=datetime.timezone.utc)
    else:
        count_method = T.counts_recent

    if csv:
        click.echo(f"start,end,{granularity}_count", file=outfile)

    hide_progress = True if (outfile.name == "<stdout>") else hide_progress
    total_tweets = 0

    with TimestampProgressBar(
        since_id, until_id, start_time, end_time, disable=hide_progress
    ) as progress:
        for result in count_method(
            query,
            since_id,
            until_id,
            start_time,
            end_time,
            granularity,
        ):
            # Count outputs:
            if text:
                for r in result["data"]:
                    total_tweets += r["tweet_count"]
                    click.echo(
                        "{start} - {end}: {tweet_count:,}".format(**r), file=outfile
                    )
            elif csv:
                for r in result["data"]:
                    click.echo(
                        f'{r["start"]},{r["end"]},{r["tweet_count"]}', file=outfile
                    )
            else:
                _write(result, outfile)

            # Progress and limits:
            if len(result["data"]) > 0:
                progress.update_with_dates(
                    result["data"][0]["start"], result["data"][-1]["end"]
                )
                progress.tweet_count += result["meta"]["total_tweet_count"]
            count += len(result["data"])

            if limit != 0 and count >= limit:
                break
            if text:
                click.echo(
                    click.style(
                        "\nTotal Tweets: {:,}\n".format(total_tweets), fg="green"
                    ),
                    file=outfile,
                )
        else:
            progress.early_stop = False


@twarc2.command("tweet")
@click.option("--pretty", is_flag=True, default=False, help="Pretty print the JSON")
@click.argument("tweet_id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def tweet(T, tweet_id, outfile, pretty):
    """
    Look up a tweet using its tweet id or URL.
    """
    if "https" in tweet_id:
        tweet_id = url_or_id.split("/")[-1]
    if not re.match("^\d+$", tweet_id):
        click.echo(click.style("Please enter a tweet URL or ID", fg="red"), err=True)
    result = next(T.tweet_lookup([tweet_id]))
    _write(result, outfile, pretty=pretty)


@twarc2.command("followers")
@click.option(
    "--limit",
    default=0,
    help="Maximum number of followers to save. Increments of 1000.",
)
@click.option(
    "--hide-progress",
    is_flag=True,
    default=False,
    help="Hide the Progress bar. Default: show progress",
)
@click.argument("user", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def followers(T, user, outfile, limit, hide_progress):
    """
    Get the followers for a given user.
    """
    count = 0
    user_id = None
    lookup_total = 0

    if outfile is not None and (outfile.name == "<stdout>"):
        hide_progress = True

    if not hide_progress:
        target_user = T._ensure_user(user)
        user_id = target_user["id"]
        lookup_total = target_user["public_metrics"]["followers_count"]

    with tqdm(disable=hide_progress, total=lookup_total) as progress:
        for result in T.followers(user, user_id=user_id):
            _write(result, outfile)
            count += len(result["data"])
            progress.update(len(result["data"]))
            if limit != 0 and count >= limit:
                progress.desc = f"Set --limit of {limit} reached"
                break


@twarc2.command("following")
@click.option(
    "--limit", default=0, help="Maximum number of friends to save. Increments of 1000."
)
@click.option(
    "--hide-progress",
    is_flag=True,
    default=False,
    help="Hide the Progress bar. Default: show progress",
)
@click.argument("user", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def following(T, user, outfile, limit, hide_progress):
    """
    Get the users who are following a given user.
    """
    count = 0
    user_id = None
    lookup_total = 0

    if outfile is not None and (outfile.name == "<stdout>"):
        hide_progress = True

    if not hide_progress:
        target_user = T._ensure_user(user)
        user_id = target_user["id"]
        lookup_total = target_user["public_metrics"]["following_count"]

    with tqdm(disable=hide_progress, total=lookup_total) as progress:
        for result in T.following(user, user_id=user_id):
            _write(result, outfile)
            count += len(result["data"])
            progress.update(len(result["data"]))
            if limit != 0 and count >= limit:
                progress.desc = f"Set --limit of {limit} reached"
                break


@twarc2.command("sample")
@click.option("--limit", default=0, help="Maximum number of tweets to save")
@click.argument("outfile", type=click.File("a+"), default="-")
@click.pass_obj
@cli_api_error
def sample(T, outfile, limit):
    """
    Fetch tweets from the sample stream.
    """
    count = 0
    event = threading.Event()
    click.echo(
        click.style(
            f"Started a random sample stream, writing to {outfile.name}\nCTRL+C to stop...",
            fg="green",
        )
    )
    for result in T.sample(event=event):
        count += 1
        if limit != 0 and count >= limit:
            event.set()
        _write(result, outfile)
        if result:
            log.info("archived %s", result["data"]["id"])


@twarc2.command("hydrate")
@click.argument("infile", type=click.File("r"), default="-")
@click.argument("outfile", type=click.File("w"), default="-")
@click.option(
    "--hide-progress",
    is_flag=True,
    default=False,
    help="Hide the Progress bar. Default: show progress, unless using pipes.",
)
@click.pass_obj
@cli_api_error
def hydrate(T, infile, outfile, hide_progress):
    """
    Hydrate tweet ids.
    """
    with FileSizeProgressBar(infile, outfile, disable=hide_progress) as progress:
        for result in T.tweet_lookup(infile):
            _write(result, outfile)
            tweet_ids = [t["id"] for t in result.get("data", [])]
            log.info("archived %s", ",".join(tweet_ids))
            progress.update_with_result(result, error_resource_type="tweet")


@twarc2.command("dehydrate")
@click.argument("infile", type=click.File("r"), default="-")
@click.argument("outfile", type=click.File("w"), default="-")
@click.option(
    "--hide-progress",
    is_flag=True,
    default=False,
    help="Hide the Progress bar. Default: show progress, unless using pipes.",
)
@cli_api_error
def dehydrate(infile, outfile, hide_progress):
    """
    Extract IDs from a dataset.
    """
    if infile.name == outfile.name:
        click.echo(
            click.style(
                f"💔 Cannot extract files in-place, specify a different output file!",
                fg="red",
            ),
            err=True,
        )
        return

    with FileSizeProgressBar(infile, outfile, disable=hide_progress) as progress:
        count = 0
        for line in infile:
            count += 1
            progress.update(len(line))

            # ignore empty lines
            line = line.strip()
            if not line:
                continue

            try:
                for tweet in ensure_flattened(json.loads(line)):
                    click.echo(tweet["id"], file=outfile)
            except ValueError as e:
                click.echo(f"Unexpected JSON data on line {count}", err=True)
                break
            except json.decoder.JSONDecodeError as e:
                click.echo(f"Invalid JSON on line {count}", err=True)
                break


@twarc2.command("users")
@click.argument("infile", type=click.File("r"), default="-")
@click.argument("outfile", type=click.File("w"), default="-")
@click.option("--usernames", is_flag=True, default=False)
@click.option(
    "--hide-progress",
    is_flag=True,
    default=False,
    help="Hide the Progress bar. Default: show progress, unless using pipes.",
)
@click.pass_obj
@cli_api_error
def users(T, infile, outfile, usernames, hide_progress):
    """
    Get data for user ids or usernames.
    """
    with FileSizeProgressBar(infile, outfile, disable=hide_progress) as progress:
        for result in T.user_lookup(infile, usernames):
            _write(result, outfile)
            if usernames:
                progress.update_with_result(
                    result,
                    field="username",
                    error_resource_type="user",
                    error_parameter="usernames",
                )
            else:
                progress.update_with_result(result, error_resource_type="user")


@twarc2.command("mentions")
@click.option("--since-id", type=int, help="Match tweets sent after tweet id")
@click.option("--until-id", type=int, help="Match tweets sent prior to tweet id")
@click.option(
    "--start-time",
    type=click.DateTime(formats=("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")),
    help="Match tweets created after time (ISO 8601/RFC 3339), e.g.  2021-01-01T12:31:04",
)
@click.option(
    "--end-time",
    type=click.DateTime(formats=("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")),
    help="Match tweets sent before time (ISO 8601/RFC 3339)",
)
@click.option(
    "--hide-progress",
    is_flag=True,
    default=False,
    help="Hide the Progress bar. Default: show progress",
)
@click.argument("user_id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def mentions(
    T, user_id, outfile, since_id, until_id, start_time, end_time, hide_progress
):
    """
    Retrieve max of 800 of the most recent tweets mentioning the given user.
    """

    with tqdm(disable=hide_progress, total=800) as progress:
        for result in T.mentions(user_id, since_id, until_id, start_time, end_time):
            _write(result, outfile)
            progress.update(len(result["data"]))
        else:
            if progress.n > 800:
                progress.desc = f"API limit reached with {progress.n} tweets"
                progress.n = 800
            else:
                progress.desc = f"Set limit reached with {progress.n} tweets"


@twarc2.command("timeline")
@click.option("--limit", default=0, help="Maximum number of tweets to return")
@click.option("--since-id", type=int, help="Match tweets sent after tweet id")
@click.option("--until-id", type=int, help="Match tweets sent prior to tweet id")
@click.option(
    "--exclude-retweets",
    is_flag=True,
    default=False,
    help="Exclude retweets from timeline",
)
@click.option(
    "--exclude-replies",
    is_flag=True,
    default=False,
    help="Exclude replies from timeline",
)
@click.option(
    "--start-time",
    type=click.DateTime(formats=("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")),
    help="Match tweets created after time (ISO 8601/RFC 3339), e.g.  2021-01-01T12:31:04",
)
@click.option(
    "--end-time",
    type=click.DateTime(formats=("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")),
    help="Match tweets sent before time (ISO 8601/RFC 3339)",
)
@click.option(
    "--use-search",
    is_flag=True,
    default=False,
    help="Use the search/all API endpoint which is not limited to the last 3200 tweets, but requires Academic Product Track access.",
)
@click.option(
    "--hide-progress",
    is_flag=True,
    default=False,
    help="Hide the Progress bar. Default: show progress, unless using pipes.",
)
@click.argument("user_id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def timeline(
    T,
    user_id,
    outfile,
    since_id,
    until_id,
    start_time,
    end_time,
    use_search,
    limit,
    exclude_retweets,
    exclude_replies,
    hide_progress,
):
    """
    Retrieve recent tweets for the given user.
    """

    count = 0
    user = T._ensure_user(user_id)  # It's possible to skip this to optimize more

    if use_search or (start_time or end_time) or (since_id or until_id):
        pbar = TimestampProgressBar

        # Infer start time as the user created time if not using ids
        if start_time is None and (since_id is None and until_id is None):
            start_time = datetime.datetime.strptime(
                user["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
        # Infer since_id as user created time if using ids
        if start_time is None and since_id is None:
            infer_id = _millis2snowflake(
                _date2millis(
                    datetime.datetime.strptime(
                        user["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                )
            )
            # Snowflake epoch is 1288834974657 so if older, just set it to "1"
            since_id = infer_id if infer_id > 0 else 1

        pbar_params = {
            "since_id": since_id,
            "until_id": until_id,
            "start_time": start_time,
            "end_time": end_time,
            "disable": hide_progress,
        }

    else:
        pbar = tqdm
        pbar_params = {
            "disable": hide_progress,
            "total": user["public_metrics"]["tweet_count"],
        }

    tweets = _timeline_tweets(
        T,
        use_search,
        user_id,
        since_id,
        until_id,
        start_time,
        end_time,
        exclude_retweets,
        exclude_replies,
    )

    with pbar(**pbar_params) as progress:
        for result in tweets:
            _write(result, outfile)

            count += len(result["data"])
            if isinstance(progress, TimestampProgressBar):
                progress.update_with_result(result)
            else:
                progress.update(len(result["data"]))

            if limit != 0 and count >= limit:
                # Display message when stopped early
                progress.desc = f"Set --limit of {limit} reached"
                break
        else:
            if isinstance(progress, TimestampProgressBar):
                progress.early_stop = False
            if not use_search and user["public_metrics"]["tweet_count"] > 3200:
                progress.desc = f"API limit of 3200 reached"


@twarc2.command("timelines")
@click.option("--limit", default=0, help="Maximum number of tweets to return")
@click.option(
    "--timeline-limit",
    default=0,
    help="Maximum number of tweets to return per-timeline",
)
@click.option(
    "--use-search",
    is_flag=True,
    default=False,
    help="Use the search/all API endpoint which is not limited to the last 3200 tweets, but requires Academic Product Track access.",
)
@click.option(
    "--exclude-retweets",
    is_flag=True,
    default=False,
    help="Exclude retweets from timeline",
)
@click.option(
    "--exclude-replies",
    is_flag=True,
    default=False,
    help="Exclude replies from timeline",
)
@click.option(
    "--hide-progress",
    is_flag=True,
    default=False,
    help="Hide the Progress bar. Default: show progress, unless using pipes.",
)
@click.argument("infile", type=click.File("r"), default="-")
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
def timelines(
    T,
    infile,
    outfile,
    limit,
    timeline_limit,
    use_search,
    exclude_retweets,
    exclude_replies,
    hide_progress,
):
    """
    Fetch the timelines of every user in an input source of tweets. If
    the input is a line oriented text file of user ids or usernames that will
    be used instead.

    The infile can be:

        - A file containing one user id per line (either quoted or unquoted)
        - A JSONL file containing tweets collected in the Twitter API V2 format

    """
    total_count = 0
    line_count = 0
    seen = set()

    with FileSizeProgressBar(infile, outfile, disable=hide_progress) as progress:
        for line in infile:
            progress.update(len(line))
            line_count += 1
            line = line.strip()
            if line == "":
                log.warn("skipping blank line on line %s", line_count)
                continue

            users = None
            try:
                # assume this the line contains some tweet json
                data = json.loads(line)

                # if it parsed as a string or int assume it's a username
                if isinstance(data, str) or isinstance(data, int):
                    users = set([line])

                # otherwise try to flatten the data and get the user ids
                else:
                    try:
                        users = set([t["author"]["id"] for t in ensure_flattened(data)])
                    except (KeyError, ValueError):
                        log.warn(
                            "ignored line %s which didn't contain users", line_count
                        )
                        continue

            except json.JSONDecodeError:
                # maybe it's a single user?
                users = set([line])

            if users is None:
                click.echo(
                    click.style(
                        f"unable to find user or users on line {line_count}",
                        fg="red",
                    ),
                    err=True,
                )
                break

            for user in users:

                # only process a given user once
                if user in seen:
                    log.info("already processed %s, skipping", user)
                    continue

                # ignore what don't appear to be a username or user id since
                # they can cause the Twitter API to throw a 400 error
                if not re.match(r"^((\w{1,15})|(\d+))$", user):
                    log.warn(
                        'invalid username or user id "%s" on line %s', line, line_count
                    )
                    continue

                seen.add(user)

                tweets = _timeline_tweets(
                    T,
                    use_search,
                    user,
                    None,
                    None,
                    None,
                    None,
                    exclude_retweets,
                    exclude_replies,
                )

                timeline_count = 0
                for response in tweets:
                    _write(response, outfile)

                    timeline_count += len(response["data"])
                    if timeline_limit != 0 and timeline_count >= timeline_limit:
                        break

                    total_count += len(response["data"])
                    if limit != 0 and total_count >= limit:
                        return


def _timeline_tweets(
    T,
    use_search,
    user_id,
    since_id,
    until_id,
    start_time,
    end_time,
    exclude_retweets,
    exclude_replies,
):
    if use_search:
        q = f"from:{user_id}"
        if exclude_retweets and "-is:retweet" not in q:
            q += " -is:retweet"
        if exclude_replies and "-is:reply" not in q:
            q += " -is:reply"
        tweets = T.search_all(q, since_id, until_id, start_time, end_time, 100)
    else:
        tweets = T.timeline(
            user_id,
            since_id,
            until_id,
            start_time,
            end_time,
            exclude_retweets,
            exclude_replies,
        )
    return tweets


@twarc2.command("conversation")
@click.option("--since-id", type=int, help="Match tweets sent after tweet id")
@click.option("--until-id", type=int, help="Match tweets sent prior to tweet id")
@click.option(
    "--start-time",
    type=click.DateTime(formats=("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")),
    help="Match tweets created after UTC time (ISO 8601/RFC 3339), e.g.  2021-01-01T12:31:04",
)
@click.option(
    "--end-time",
    type=click.DateTime(formats=("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")),
    help="Match tweets sent before UTC time (ISO 8601/RFC 3339)",
)
@click.option(
    "--archive",
    is_flag=True,
    default=False,
    help="Search the full archive (requires Academic Research track)",
)
@click.option("--limit", default=0, help="Maximum number of tweets to save")
@click.option(
    "--max-results", default=0, help="Maximum number of tweets per API response"
)
@click.option(
    "--hide-progress",
    is_flag=True,
    default=False,
    help="Hide the Progress bar. Default: show progress, unless using pipes.",
)
@click.argument("tweet_id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def conversation(
    T,
    tweet_id,
    outfile,
    since_id,
    until_id,
    start_time,
    end_time,
    limit,
    max_results,
    archive,
    hide_progress,
):
    """
    Retrieve a conversation thread using the tweet id.
    """
    q = f"conversation_id:{tweet_id}"
    return _search(
        T,
        q,
        outfile,
        since_id,
        until_id,
        start_time,
        end_time,
        limit,
        max_results,
        archive,
        hide_progress,
    )


@twarc2.command("conversations")
@click.option("--limit", default=0, help="Maximum number of tweets to return")
@click.option(
    "--conversation-limit",
    default=0,
    help="Maximum number of tweets to return per-conversation",
)
@click.option(
    "--archive",
    is_flag=True,
    default=False,
    help="Use the Academic Research project track access to the full archive",
)
@click.option(
    "--hide-progress",
    is_flag=True,
    default=False,
    help="Hide the Progress bar. Default: show progress, unless using pipes.",
)
@click.argument("infile", type=click.File("r"), default="-")
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def conversations(
    T, infile, outfile, archive, limit, conversation_limit, hide_progress
):
    """
    Fetch the full conversation threads that the input tweets are a part of.
    Alternatively the input can be a line oriented file of conversation ids.
    """

    # keep track of converstation ids that have been fetched so that they
    # aren't fetched twice
    seen = set()

    # use the archive or recent search?
    search = T.search_all if archive else T.search_recent

    count = 0
    stop = False

    with FileSizeProgressBar(infile, outfile, disable=hide_progress) as progress:
        for line in infile:
            progress.update(len(line))
            conv_ids = []

            # stop will get set when the total tweet limit has been met
            if stop:
                break

            # get a specific conversation id
            line = line.strip()
            if re.match(r"^\d+$", line):
                if line in seen:
                    continue
                conv_ids = [line]

            # generate all conversation_ids that are referenced in tweets input
            else:

                def f():
                    for tweet in ensure_flattened(json.loads(line)):
                        yield tweet.get("conversation_id")

                conv_ids = f()

            # output results while paying attention to the set limits
            conv_count = 0

            for conv_id in conv_ids:

                if conv_id in seen:
                    log.info(f"already fetched conversation_id {conv_id}")
                seen.add(conv_id)

                conv_count = 0

                log.info(f"fetching conversation {conv_id}")
                for result in search(f"conversation_id:{conv_id}"):
                    _write(result, outfile, False)

                    count += len(result["data"])
                    if limit != 0 and count >= limit:
                        log.info(f"reached tweet limit of {limit}")
                        stop = True
                        break

                    conv_count += len(result["data"])
                    if conversation_limit != 0 and conv_count >= conversation_limit:
                        log.info(f"reached conversation limit {conversation_limit}")
                        break


@twarc2.command("flatten")
@click.argument("infile", type=click.File("r"), default="-")
@click.argument("outfile", type=click.File("w"), default="-")
@click.option(
    "--hide-progress",
    is_flag=True,
    default=False,
    help="Hide the Progress bar. Default: show progress, unless using pipes.",
)
@cli_api_error
def flatten(infile, outfile, hide_progress):
    """
    "Flatten" tweets, or move expansions inline with tweet objects and ensure
    that each line of output is a single tweet.
    """
    if infile.name == outfile.name:
        click.echo(
            click.style(
                f"💔 Cannot flatten files in-place, specify a different output file!",
                fg="red",
            ),
            err=True,
        )
        return

    with FileSizeProgressBar(infile, outfile, disable=hide_progress) as progress:
        for line in infile:
            for tweet in ensure_flattened(json.loads(line)):
                _write(tweet, outfile, False)
            progress.update(len(line))


@twarc2.command("stream")
@click.option("--limit", default=0, help="Maximum number of tweets to return")
@click.argument("outfile", type=click.File("a+"), default="-")
@click.pass_obj
@cli_api_error
def stream(T, outfile, limit):
    """
    Fetch tweets from the live stream.
    """
    event = threading.Event()
    count = 0
    click.echo(click.style(f"Started a stream with rules:", fg="green"), err=True)
    _print_stream_rules(T)
    click.echo(
        click.style(f"Writing to {outfile.name}\nCTRL+C to stop...", fg="green"),
        err=True,
    )
    for result in T.stream(event=event):
        count += 1
        if limit != 0 and count == limit:
            log.info(f"reached limit {limit}")
            event.set()
        _write(result, outfile)
        if "data" in result:
            log.info("archived %s", result["data"]["id"])


@twarc2.group()
@click.pass_obj
def stream_rules(T):
    """
    List, add and delete rules for your stream.
    """
    pass


@stream_rules.command("list")
@click.pass_obj
@cli_api_error
def list_stream_rules(T):
    """
    List all the active stream rules.
    """
    _print_stream_rules(T)


def _print_stream_rules(T):
    """
    Output all the active stream rules
    """
    result = T.get_stream_rules()
    if "data" not in result or len(result["data"]) == 0:
        click.echo(
            "No rules yet. Add them with "
            + click.style("twarc2 stream-rules add", bold=True),
            err=True,
        )
    else:
        count = 0
        for rule in result["data"]:
            if count > 5:
                count = 0
            s = rule["value"]
            if "tag" in rule:
                s += f" (tag: {rule['tag']})"
            click.echo(click.style(f"☑  {s}"), err=True)
            count += 1


@stream_rules.command("add")
@click.pass_obj
@click.option("--tag", type=str, help="a tag to help identify the rule")
@click.argument("value", type=str)
@cli_api_error
def add_stream_rule(T, value, tag):
    """
    Create a new stream rule to match a value. Rules can be grouped with
    optional tags.
    """
    if tag:
        rules = [{"value": value, "tag": tag}]
    else:
        rules = [{"value": value}]

    results = T.add_stream_rules(rules)
    if "errors" in results:
        click.echo(_error_str(results["errors"]), err=True)
    else:
        click.echo(click.style(f"🚀  Added rule for ", fg="green") + f'"{value}"')


@stream_rules.command("delete")
@click.argument("value")
@click.pass_obj
@cli_api_error
def delete_stream_rule(T, value):
    """
    Delete the stream rule that matches a given value.
    """
    # find the rule id
    result = T.get_stream_rules()
    if "data" not in result:
        click.echo(click.style("💔  There are no rules to delete!", fg="red"), err=True)
    else:
        rule_id = None
        for rule in result["data"]:
            if rule["value"] == value:
                rule_id = rule["id"]
                break
        if not rule_id:
            click.echo(
                click.style(f'🙃  No rule could be found for "{value}"', fg="red"),
                err=True,
            )
        else:
            results = T.delete_stream_rule_ids([rule_id])
            if "errors" in results:
                click.echo(_error_str(results["errors"]), err=True)
            else:
                click.echo(f"🗑  Deleted stream rule for {value}", color="green")


@stream_rules.command("delete-all")
@click.pass_obj
@cli_api_error
def delete_all(T):
    """
    Delete all stream rules!
    """
    result = T.get_stream_rules()
    if "data" not in result:
        click.echo(click.style("💔  There are no rules to delete!", fg="red"), err=True)
    else:
        rule_ids = [r["id"] for r in result["data"]]
        results = T.delete_stream_rule_ids(rule_ids)
        click.echo(f"🗑  Deleted {len(rule_ids)} rules.")


def _rule_str(rule):
    s = f"id={rule['id']} value={rule['value']}"
    if "tag" in rule:
        s += f" tag={rule['tag']}"
    return s


def _error_str(errors):
    # collapse all the error messages into a newline delimited red colored list
    # the passed in errors can be single error object or a list of objects, each
    # of which has an errors key that points to a list of error objects

    if type(errors) != list or "errors" not in errors:
        errors = [{"errors": errors}]

    parts = []
    for error in errors:
        for part in error["errors"]:
            s = "💣  "
            if "message" in part:
                s += click.style(part["message"], fg="red")
            elif "title" in part:
                s += click.style(part["title"], fg="red")
            else:
                s = click.style("Unknown error", fg="red")
            if "type" in part:
                s += f" see: {part['type']}"
            parts.append(s)

    return click.style("\n".join(parts), fg="red")


def _write(results, outfile, pretty=False):
    indent = 2 if pretty else None
    click.echo(json.dumps(results, indent=indent), file=outfile)
