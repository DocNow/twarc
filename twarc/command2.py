"""
The command line interfact to the Twitter v2 API.
"""

from itertools import filterfalse
import os
import re
import json
import time
import twarc
import click
import logging
import pathlib
import datetime
import humanize
import requests
import configobj
import threading

from tqdm.auto import tqdm
from tqdm.utils import CallbackIOWrapper

from datetime import timezone
from click_plugins import with_plugins
from pkg_resources import iter_entry_points

from twarc.version import version
from twarc.handshake import handshake
from twarc.config import ConfigProvider
from twarc.expansions import (
    ensure_flattened,
    EXPANSIONS,
    TWEET_FIELDS,
    USER_FIELDS,
    MEDIA_FIELDS,
    POLL_FIELDS,
    PLACE_FIELDS,
    LIST_FIELDS,
)
from click import command, option, Option, UsageError
from click_config_file import configuration_option
from twarc.decorators2 import (
    cli_api_error,
    TimestampProgressBar,
    FileSizeProgressBar,
    FileLineProgressBar,
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
        click.echo("👋  Hi I don't see a configuration file yet, so let's make one.")
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
    expansions,
    tweet_fields,
    user_fields,
    media_fields,
    poll_fields,
    place_fields,
):
    """
    Common function to Search for tweets.
    """
    count = 0

    # Make sure times are always in UTC, click sometimes doesn't add timezone:
    if start_time is not None and start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time is not None and end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    if archive:
        search_method = T.search_all

        # start time defaults to the beginning of Twitter to override the
        # default of the last month. Only do this if start_time is not already
        # specified and since_id and until_id aren't being used
        if start_time is None and since_id is None and until_id is None:
            start_time = datetime.datetime(2006, 3, 21, tzinfo=datetime.timezone.utc)
    else:
        search_method = T.search_recent

    hide_progress = True if (outfile.name == "<stdout>") else hide_progress

    with TimestampProgressBar(
        since_id, until_id, start_time, end_time, disable=hide_progress
    ) as progress:
        for result in search_method(
            query=query,
            since_id=since_id,
            until_id=until_id,
            start_time=start_time,
            end_time=end_time,
            max_results=max_results,
            expansions=expansions,
            tweet_fields=tweet_fields,
            user_fields=user_fields,
            media_fields=media_fields,
            poll_fields=poll_fields,
            place_fields=place_fields,
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


class MutuallyExclusiveOption(Option):
    """
    Custom click class to make some options mutually exclusive
    via https://gist.github.com/jacobtolar/fb80d5552a9a9dfc32b12a829fa21c0c
    """

    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop("mutually_exclusive", []))
        help = kwargs.get("help", "")
        if self.mutually_exclusive:
            ex_str = ", ".join(
                self.parse_name(name) for name in self.mutually_exclusive
            )
            kwargs["help"] = help + (
                " NOTE: This argument is mutually exclusive with "
                " arguments: [" + ex_str + "]."
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def parse_name(self, name):
        return f'--{name.replace("_","-")}'

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise UsageError(
                f"Incorrect usage: {self.parse_name(self.name)} is mutually exclusive with "
                f"arguments `{', '.join(self.parse_name(name) for name in self.mutually_exclusive)} use either one or the other."
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(ctx, opts, args)


def command_line_input_output_file_arguments(f):
    """
    Decorator for specifying input and output file arguments in a command
    """
    f = click.argument("outfile", type=click.File("w"), default="-")(f)
    f = click.argument("infile", type=click.File("r"), default="-")(f)
    return f


def command_line_progressbar_option(f):
    """
    Decorator for specifying a progress bar option.
    """
    f = click.option(
        "--hide-progress",
        is_flag=True,
        default=False,
        help="Hide the Progress bar. Default: show progress, unless using pipes.",
    )(f)
    return f


def command_line_search_options(f):
    """
    Decorator for specifying time range search API parameters.
    """
    f = click.option(
        "--until-id", type=int, help="Match tweets sent prior to tweet id"
    )(f)
    f = click.option("--since-id", type=int, help="Match tweets sent after tweet id")(f)
    f = click.option(
        "--end-time",
        type=click.DateTime(formats=("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")),
        help='Match tweets sent before UTC time (ISO 8601/RFC 3339), \n e.g.  --end-time "2021-01-01T12:31:04"',
    )(f)
    f = click.option(
        "--start-time",
        type=click.DateTime(formats=("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")),
        help='Match tweets created after UTC time (ISO 8601/RFC 3339), \n e.g.  --start-time "2021-01-01T12:31:04"',
    )(f)
    return f


def command_line_timelines_options(f):
    """
    Decorator for common timelines command line options
    """
    f = click.option(
        "--exclude-replies",
        is_flag=True,
        default=False,
        help="Exclude replies from timeline",
    )(f)
    f = click.option(
        "--exclude-retweets",
        is_flag=True,
        default=False,
        help="Exclude retweets from timeline",
    )(f)
    f = click.option(
        "--use-search",
        is_flag=True,
        default=False,
        help="Use the search/all API endpoint which is not limited to the last 3200 tweets, but requires Academic Product Track access.",
    )(f)
    return f


def _validate_max_results(context, parameter, value):
    """
    Validate and set appropriate max_results parameter.
    """

    archive_set = "archive" in context.params and context.params["archive"]
    no_context_annotations_set = (
        "no_context_annotations" in context.params
        and context.params["no_context_annotations"]
    )
    minimal_fields_set = (
        "minimal_fields" in context.params and context.params["minimal_fields"]
    )
    has_context_annotations = (
        "tweet_fields" in context.params
        and "context_annotations" in context.params["tweet_fields"].split(",")
    )

    if value:

        if not archive_set and value > 100:
            raise click.BadParameter(
                "--max-results cannot be greater than 100 when using Standard Access. Specify --archive if you have Academic Access."
            )
        if value < 10 or value > 500:
            raise click.BadParameter("--max-results must be between 10 and 500")
        if value > 100 and has_context_annotations:
            raise click.BadParameter(
                "--max-results cannot be greater than 100 when using context annotations. Set --no-context-annotations to remove them, or don't specify them in --tweet-fields."
            )

        return value

    else:

        if archive_set and (
            no_context_annotations_set
            or minimal_fields_set
            or not has_context_annotations
        ):
            return 500

        return 100


def command_line_search_archive_options(f):
    """
    Decorator for specifying additional search API parameters.
    """
    f = click.option(
        "--limit", default=0, help="Maximum number of tweets to save", type=int
    )(f)
    f = click.option(
        "--max-results",
        default=None,
        help="Maximum number of tweets per API response",
        callback=_validate_max_results,
        type=int,
    )(f)
    f = click.option(
        "--archive",
        is_flag=True,
        default=False,
        is_eager=True,
        help="Use the full archive (requires Academic Research track)",
    )(f)
    return f


def _validate_expansions(context, parameter, value):
    """
    Validate passed comma separated values for expansions.
    """
    if value:
        values = value.split(",")
        valid = parameter.default.split(",")
        for v in values:
            if v not in valid:
                raise click.BadOptionUsage(
                    parameter.name,
                    f'"{v}" is not a valid entry for --{parameter.name}. Must be a comma separated string, without spaces, like this:\n--{parameter.name} "{parameter.default}"',
                )
        return ",".join(values)


def command_line_expansions_options(f):
    """
    Decorator for specifying custom fields and expansions
    """
    f = click.option(
        "--poll-fields",
        default=",".join(POLL_FIELDS),
        type=click.STRING,
        help="Comma separated list of poll fields to retrieve. Default is all available.",
        callback=_validate_expansions,
    )(f)
    f = click.option(
        "--place-fields",
        default=",".join(PLACE_FIELDS),
        type=click.STRING,
        help="Comma separated list of place fields to retrieve. Default is all available.",
        callback=_validate_expansions,
    )(f)
    f = click.option(
        "--media-fields",
        default=",".join(MEDIA_FIELDS),
        type=click.STRING,
        help="Comma separated list of media fields to retrieve. Default is all available.",
        callback=_validate_expansions,
    )(f)
    f = click.option(
        "--user-fields",
        default=",".join(USER_FIELDS),
        type=click.STRING,
        help="Comma separated list of user fields to retrieve. Default is all available.",
        callback=_validate_expansions,
    )(f)
    f = click.option(
        "--tweet-fields",
        default=",".join(TWEET_FIELDS),
        type=click.STRING,
        is_eager=True,
        help="Comma separated list of tweet fields to retrieve. Default is all available.",
        callback=_validate_expansions,
    )(f)
    f = click.option(
        "--expansions",
        default=",".join(EXPANSIONS),
        type=click.STRING,
        help="Comma separated list of expansions to retrieve. Default is all available.",
        callback=_validate_expansions,
    )(f)
    return f


def command_line_expansions_shortcuts(f):
    """
    Decorator for specifying common fields and expansions presets
    """
    f = click.option(
        "--minimal-fields",
        cls=MutuallyExclusiveOption,
        mutually_exclusive=[
            "no_context_annotations",
            "expansions",
            "tweet_fields",
            "user_fields",
            "media_fields",
            "poll_fields",
            "place_fields",
            "counts_only",
        ],
        is_flag=True,
        default=False,
        is_eager=True,
        help="By default twarc gets all available data. This option requests the minimal retrievable amount of data - only IDs and object references are retrieved. Setting this makes --max-results 500 the default.",
    )(f)
    f = click.option(
        "--no-context-annotations",
        cls=MutuallyExclusiveOption,
        mutually_exclusive=[
            "minimal_fields",
            "expansions",
            "tweet_fields",
            "user_fields",
            "media_fields",
            "poll_fields",
            "place_fields",
            "counts_only",
        ],
        is_flag=True,
        default=False,
        is_eager=True,
        help="By default twarc gets all available data. This leaves out context annotations (Twitter API limits --max-results to 100 if these are requested). Setting this makes --max-results 500 the default.",
    )(f)
    return f


def _process_expansions_shortcuts(kwargs):
    # Override fields and expansions
    if kwargs.pop("minimal_fields", None):
        kwargs[
            "expansions"
        ] = "author_id,in_reply_to_user_id,referenced_tweets.id,referenced_tweets.id.author_id,attachments.poll_ids,attachments.media_keys,geo.place_id"
        kwargs[
            "tweet_fields"
        ] = "id,conversation_id,author_id,in_reply_to_user_id,referenced_tweets,geo"
        kwargs[
            "user_fields"
        ] = "id,username,name,pinned_tweet_id"  # pinned_tweet_id is the only extra one, id,username,name are always returned.
        kwargs["media_fields"] = "media_key"
        kwargs["poll_fields"] = "id"
        kwargs["place_fields"] = "id"

    if kwargs.pop("no_context_annotations", None):
        kwargs[
            "tweet_fields"
        ] = "attachments,author_id,conversation_id,created_at,entities,geo,id,in_reply_to_user_id,lang,public_metrics,text,possibly_sensitive,referenced_tweets,reply_settings,source,withheld"

    return kwargs


def command_line_verbose_options(f):
    """
    Decorator for specifying verbose and json output
    """
    f = click.option(
        "--verbose",
        is_flag=True,
        default=False,
        help="Show all URLs and metadata.",
    )(f)
    f = click.option(
        "--json-output",
        is_flag=True,
        default=False,
        help="Return the raw json content from the API.",
    )(f)
    return f


@twarc2.command("search")
@command_line_search_options
@command_line_search_archive_options
@command_line_expansions_shortcuts
@command_line_expansions_options
@command_line_progressbar_option
@click.argument("query", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def search(
    T,
    query,
    outfile,
    **kwargs,
):
    """
    Search for tweets. For help on how to write a query see https://developer.twitter.com/en/docs/twitter-api/tweets/search/integrate/build-a-query
    """

    kwargs = _process_expansions_shortcuts(kwargs)

    return _search(
        T,
        query,
        outfile,
        **kwargs,
    )


@twarc2.command("counts")
@command_line_search_options
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
@command_line_progressbar_option
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
        # specified and since_id/until_id aren't being used
        if start_time is None and since_id is None and until_id is None:
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
@command_line_expansions_shortcuts
@command_line_expansions_options
@click.option("--pretty", is_flag=True, default=False, help="Pretty print the JSON")
@click.argument("tweet_id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def tweet(T, tweet_id, outfile, pretty, **kwargs):
    """
    Look up a tweet using its tweet id or URL.
    """

    kwargs = _process_expansions_shortcuts(kwargs)

    if "https" in tweet_id:
        tweet_id = tweet_id.split("/")[-1]
    if not re.match("^\d+$", tweet_id):
        click.echo(click.style("Please enter a tweet URL or ID", fg="red"), err=True)
    result = next(T.tweet_lookup([tweet_id], **kwargs))
    _write(result, outfile, pretty=pretty)


@twarc2.command("followers")
@click.option(
    "--limit",
    default=0,
    help="Maximum number of followers to save. Increments of 1000 or --max-results if set.",
    type=int,
)
@click.option(
    "--max-results",
    default=1000,
    help="Maximum number of users per page. Default is 1000.",
    type=int,
)
@command_line_progressbar_option
@click.argument("user", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def followers(T, user, outfile, limit, max_results, hide_progress):
    """
    Get the followers for a given user.
    """
    user_id = None
    lookup_total = 1

    hide_progress = True if (outfile.name == "<stdout>") else hide_progress

    if not hide_progress:
        target_user = T._ensure_user(user)
        user_id = target_user["id"]
        lookup_total = target_user["public_metrics"]["followers_count"]

    _write_with_progress(
        func=T.followers,
        user=user,
        user_id=user_id,
        outfile=outfile,
        limit=limit,
        hide_progress=hide_progress,
        progress_total=lookup_total,
        max_results=max_results,
    )


@twarc2.command("following")
@click.option(
    "--limit",
    default=0,
    help="Maximum number of friends to save. Increments of 1000 or --max-results if set.",
    type=int,
)
@click.option(
    "--max-results",
    default=1000,
    help="Maximum number of users per page. Default is 1000.",
    type=int,
)
@command_line_progressbar_option
@click.argument("user", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def following(T, user, outfile, limit, max_results, hide_progress):
    """
    Get the users that a given user is following.
    """
    user_id = None
    lookup_total = 1

    hide_progress = True if (outfile.name == "<stdout>") else hide_progress

    if not hide_progress:
        target_user = T._ensure_user(user)
        user_id = target_user["id"]
        lookup_total = target_user["public_metrics"]["following_count"]

    _write_with_progress(
        func=T.following,
        user=user,
        user_id=user_id,
        outfile=outfile,
        limit=limit,
        hide_progress=hide_progress,
        progress_total=lookup_total,
        max_results=max_results,
    )


@twarc2.command("liking-users")
@click.option(
    "--limit",
    default=0,
    help="Maximum number of liking users to retrieve. Increments of 100 or --max-results if set.",
    type=int,
)
@click.option(
    "--max-results",
    default=100,
    help="Maximum number of users (likes) per page. Default is and maximum is 100.",
    type=int,
)
@command_line_progressbar_option
@click.argument("tweet_id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def liking_users(T, tweet_id, outfile, limit, max_results, hide_progress):
    """
    Get the users that liked a specific tweet.

    Note that the progress bar is approximate.

    """
    lookup_total = 1

    if not re.match("^\d+$", str(tweet_id)):
        click.echo(click.style("Please enter a tweet ID", fg="red"), err=True)

    hide_progress = True if (outfile.name == "<stdout>") else hide_progress

    if not hide_progress:
        # TODO: we could probably do this everytime, and avoid doing any lookups
        # for tweets that don't exist anymore.
        target_tweet = list(T.tweet_lookup([tweet_id]))[0]
        if "data" in target_tweet:
            lookup_total = target_tweet["data"][0]["public_metrics"]["like_count"]

    _write_with_progress(
        func=T.liking_users,
        tweet_id=tweet_id,
        outfile=outfile,
        limit=limit,
        hide_progress=hide_progress,
        progress_total=lookup_total,
        max_results=max_results,
    )


@twarc2.command("retweeted-by")
@click.option(
    "--limit",
    default=0,
    help="Maximum number of retweeting users to retrieve. Increments of 100 or --max-results if set.",
    type=int,
)
@click.option(
    "--max-results",
    default=100,
    help="Maximum number of users (retweets) per page of results. Default and maximum is 100.",
    type=int,
)
@command_line_progressbar_option
@click.argument("tweet_id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def retweeted_by(T, tweet_id, outfile, limit, max_results, hide_progress):
    """
    Get the users that retweeted a specific tweet.

    Note that the progress bar is approximate.

    """
    lookup_total = 0

    if not re.match("^\d+$", str(tweet_id)):
        click.echo(click.style("Please enter a tweet ID", fg="red"), err=True)

    hide_progress = True if (outfile.name == "<stdout>") else hide_progress

    if not hide_progress:
        # TODO: we could probably do this everytime, and avoid doing any lookups
        # for tweets that don't exist anymore.
        target_tweet = list(T.tweet_lookup([tweet_id]))[0]
        if "data" in target_tweet:
            lookup_total = target_tweet["data"][0]["public_metrics"]["retweet_count"]

    _write_with_progress(
        func=T.retweeed_by,
        tweet_id=tweet_id,
        outfile=outfile,
        limit=limit,
        hide_progress=hide_progress,
        progress_total=lookup_total,
        max_results=max_results,
    )


@twarc2.command("quotes")
@click.option(
    "--limit",
    default=0,
    help="Maximum number of retweeting users to retrieve. Increments of 100 or --max-results if set.",
    type=int,
)
@click.option(
    "--max-results",
    default=100,
    help="Maximum number of users (retweets) per page of results. Default and maximum is 100.",
    type=int,
)
@command_line_expansions_shortcuts
@command_line_expansions_options
@command_line_progressbar_option
@click.argument("tweet_id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def quotes(T, tweet_id, outfile, limit, max_results, hide_progress, **kwargs):
    """
    Get the tweets that quote tweet the given tweet.

    Note that the progress bar is approximate.
    """
    count = 0
    lookup_total = 0
    kwargs = _process_expansions_shortcuts(kwargs)
    # Also remove media poll and place from kwargs, these are not valid for this endpoint:
    kwargs.pop("media_fields", None)
    kwargs.pop("poll_fields", None)
    kwargs.pop("place_fields", None)

    if not re.match("^\d+$", str(tweet_id)):
        click.echo(click.style("Please enter a tweet ID", fg="red"), err=True)

    hide_progress = True if (outfile.name == "<stdout>") else hide_progress

    if not hide_progress:
        target_tweet = list(T.tweet_lookup([tweet_id]))[0]
        if "data" in target_tweet:
            lookup_total = target_tweet["data"][0]["public_metrics"]["quote_count"]

    _write_with_progress(
        func=T.quotes,
        tweet_id=tweet_id,
        outfile=outfile,
        limit=limit,
        hide_progress=hide_progress,
        progress_total=lookup_total,
        max_results=max_results,
        **kwargs,
    )


@twarc2.command("liked-tweets")
@click.option(
    "--limit",
    default=0,
    help="Maximum number of liked tweets to retrieve. Increments of 100 or --max-results if set.",
    type=int,
)
@click.option(
    "--max-results",
    default=100,
    help="Maximum number of liked tweets per page of results. Default and maximum is 100.",
    type=int,
)
@command_line_progressbar_option
@click.argument("user_id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def liked_tweets(T, user_id, outfile, limit, max_results, hide_progress):
    """
    Get the tweets liked by a specific user_id.

    Note that the progress bar is approximate.

    """

    # NB: there doesn't appear to be anyway to get the total count of likes
    # a user has made, so the progress bar isn't very useful in this case...
    _write_with_progress(
        func=T.liked_tweets,
        user_id=user_id,
        outfile=outfile,
        limit=limit,
        hide_progress=hide_progress,
        progress_total=1,
        max_results=max_results,
    )


@twarc2.command("sample")
@command_line_expansions_shortcuts
@command_line_expansions_options
@click.option("--limit", default=0, help="Maximum number of tweets to save")
@click.argument("outfile", type=click.File("a+"), default="-")
@click.pass_obj
@cli_api_error
def sample(T, outfile, limit, **kwargs):
    """
    Fetch tweets from the sample stream.
    """

    kwargs = _process_expansions_shortcuts(kwargs)

    count = 0
    event = threading.Event()
    click.echo(
        click.style(
            f"Started a random sample stream, writing to {outfile.name}\nCTRL+C to stop...",
            fg="green",
        ),
        err=True,
    )
    for result in T.sample(event=event, **kwargs):
        count += 1
        if limit != 0 and count >= limit:
            event.set()
        _write(result, outfile)

        if result and "data" in result:
            log.info("archived %s", result["data"]["id"])


@twarc2.command("hydrate")
@command_line_expansions_shortcuts
@command_line_expansions_options
@command_line_input_output_file_arguments
@command_line_progressbar_option
@click.pass_obj
@cli_api_error
def hydrate(T, infile, outfile, hide_progress, **kwargs):
    """
    Hydrate tweet ids.
    """

    kwargs = _process_expansions_shortcuts(kwargs)

    with FileLineProgressBar(infile, outfile, disable=hide_progress) as progress:
        for result in T.tweet_lookup(infile, **kwargs):
            _write(result, outfile)
            tweet_ids = [t["id"] for t in result.get("data", [])]
            log.info("archived %s", ",".join(tweet_ids))
            progress.update_with_result(result, error_resource_type="tweet")


@twarc2.command("dehydrate")
@click.option(
    "--id-type",
    default="tweets",
    type=click.Choice(["tweets", "users"], case_sensitive=False),
    help="IDs to extract - either 'tweets' or 'users'.",
)
@command_line_progressbar_option
@command_line_input_output_file_arguments
@cli_api_error
def dehydrate(infile, outfile, id_type, hide_progress):
    """
    Extract tweet or user IDs from a dataset.
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
        unique_ids = set()
        for line in infile:
            count += 1
            progress.update(len(line))

            # ignore empty lines
            line = line.strip()
            if not line:
                continue

            try:
                for tweet in ensure_flattened(json.loads(line)):
                    if id_type == "tweets":
                        click.echo(tweet["id"], file=outfile)
                        unique_ids.add(tweet["id"])
                    elif id_type == "users":
                        click.echo(tweet["author_id"], file=outfile)
                        unique_ids.add(tweet["author_id"])
            except KeyError as e:
                click.echo(
                    f"No {id_type} ID found in JSON data on line {count}", err=True
                )
                break
            except ValueError as e:
                click.echo(f"Unexpected JSON data on line {count}", err=True)
                break
            except json.decoder.JSONDecodeError as e:
                click.echo(f"Invalid JSON on line {count}", err=True)
                break
    click.echo(
        f"ℹ️  Parsed {len(unique_ids)} {id_type} IDs from {count} lines in {infile.name} file.",
        err=True,
    )


@twarc2.command("users")
@command_line_expansions_shortcuts
@command_line_expansions_options
@click.option("--usernames", is_flag=True, default=False)
@command_line_progressbar_option
@command_line_input_output_file_arguments
@click.pass_obj
@cli_api_error
def users(T, infile, outfile, usernames, hide_progress, **kwargs):
    """
    Get data for user ids or usernames.
    """

    kwargs = _process_expansions_shortcuts(kwargs)
    # Also remove media poll and place from kwargs, these are not valid for this endpoint:
    kwargs.pop("media_fields", None)
    kwargs.pop("poll_fields", None)
    kwargs.pop("place_fields", None)

    with FileLineProgressBar(infile, outfile, disable=hide_progress) as progress:
        for result in T.user_lookup(infile, usernames, **kwargs):
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


@twarc2.command("user")
@command_line_expansions_shortcuts
@command_line_expansions_options
@click.argument("name-or-id", type=click.Choice(["name", "id"]))
@click.argument("user", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def user(T, name_or_id, user, outfile, **kwargs):
    """
    Get the profile data for a single user by either username or ID.

    To look up a user by ID:

        twarc2 user id 12

    To look up a user by username:

        twarc2 user name jack

    """

    kwargs = _process_expansions_shortcuts(kwargs)
    # Also remove media poll and place from kwargs, these are not valid for this endpoint:
    kwargs.pop("media_fields", None)
    kwargs.pop("poll_fields", None)
    kwargs.pop("place_fields", None)

    username = name_or_id == "name"

    user_data = list(T.user_lookup([user], username, **kwargs))
    _write(user_data, outfile)


@twarc2.command("mentions")
@command_line_search_options
@command_line_expansions_shortcuts
@command_line_expansions_options
@command_line_progressbar_option
@click.argument("user_id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def mentions(T, user_id, outfile, hide_progress, **kwargs):
    """
    Retrieve max of 800 of the most recent tweets mentioning the given user.
    """

    kwargs = _process_expansions_shortcuts(kwargs)

    with tqdm(disable=hide_progress, total=800) as progress:
        for result in T.mentions(user_id, **kwargs):
            _write(result, outfile)
            progress.update(len(result.get("data", [])))
        else:
            if progress.n > 800:
                progress.desc = f"API limit reached with {progress.n} tweets"
                progress.n = 800
            else:
                progress.desc = f"Set limit reached with {progress.n} tweets"


@twarc2.command("timeline")
@command_line_search_options
@command_line_timelines_options
@command_line_expansions_shortcuts
@command_line_expansions_options
@command_line_progressbar_option
@click.option("--limit", default=0, help="Maximum number of tweets to return")
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
    **kwargs,
):
    """
    Retrieve recent tweets for the given user.
    """

    kwargs = _process_expansions_shortcuts(kwargs)

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
        use_search=use_search,
        user_id=user_id,
        since_id=since_id,
        until_id=until_id,
        start_time=start_time,
        end_time=end_time,
        exclude_retweets=exclude_retweets,
        exclude_replies=exclude_replies,
        **kwargs,
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
@command_line_search_options
@command_line_timelines_options
@command_line_expansions_shortcuts
@command_line_expansions_options
@command_line_progressbar_option
@command_line_input_output_file_arguments
@click.pass_obj
def timelines(
    T,
    infile,
    outfile,
    limit,
    timeline_limit,
    use_search,
    hide_progress,
    **kwargs,
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
    kwargs = _process_expansions_shortcuts(kwargs)

    with FileLineProgressBar(infile, outfile, disable=hide_progress) as progress:
        for line in infile:
            progress.update()
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
                    use_search=use_search,
                    user_id=user,
                    **kwargs,
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
    **kwargs,
):
    if use_search:
        q = f"from:{user_id}"
        if exclude_retweets and "-is:retweet" not in q:
            q += " -is:retweet"
        if exclude_replies and "-is:reply" not in q:
            q += " -is:reply"
        tweets = T.search_all(
            query=q,
            since_id=since_id,
            until_id=until_id,
            start_time=start_time,
            end_time=end_time,
            **kwargs,
        )
    else:
        tweets = T.timeline(
            user=user_id,
            since_id=since_id,
            until_id=until_id,
            start_time=start_time,
            end_time=end_time,
            exclude_retweets=exclude_retweets,
            exclude_replies=exclude_replies,
            **kwargs,
        )
    return tweets


@twarc2.command("searches")
@command_line_search_options
@command_line_search_archive_options
@click.option(
    "--counts-only",
    is_flag=True,
    default=False,
    help="Only retrieve counts of tweets matching the search, not the tweets themselves. "
    "outfile will be a CSV containing the counts for all of the queries in the input file.",
)
@click.option(
    "--combine-queries",
    is_flag=True,
    default=False,
    help="""Merge consecutive queries into a single OR query.
    For example, if the three rows in your file are: banana, apple, pear
    then a single query ((banana) OR (apple) OR (pear)) will be issued.
    """,
)
@click.option(
    "--granularity",
    default="day",
    type=click.Choice(["day", "hour", "minute"], case_sensitive=False),
    help="Aggregation level for counts (only used when --count-only is used). Can be one of: day, hour, minute. Default is day.",
)
@command_line_expansions_shortcuts
@command_line_expansions_options
@command_line_progressbar_option
@command_line_input_output_file_arguments
@click.pass_obj
def searches(
    T,
    infile,
    outfile,
    limit,
    max_results,
    since_id,
    until_id,
    start_time,
    end_time,
    archive,
    counts_only,
    granularity,
    combine_queries,
    hide_progress,
    **kwargs,
):
    """
    Execute each search in the input file, one at a time.

    The infile must be a file containing one query per line. Each line will be
    passed through directly to the Twitter API - unlike the timelines command
    quotes will not be removed.

    Input queries will be deduplicated - if the same literal query is present
    in the file, it will still only be run once.

    It is recommended that this command first be run with --counts-only, to
    check that each of the queries is retrieving the volume of tweets
    expected, and to avoid consuming quota unnecessarily.

    """
    line_count = 0
    seen = set()
    kwargs = _process_expansions_shortcuts(kwargs)

    # Make sure times are always in UTC, click sometimes doesn't add timezone:
    if start_time is not None and start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time is not None and end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    # Standard API max query length
    max_query_length = 512

    # TODO: this duplicates existing logic in _search, but _search is too
    # specific to be reused here.
    if archive:
        # start time defaults to the beginning of Twitter to override the
        # default of the last month. Only do this if start_time is not already
        # specified and since_id and until_id aren't being used
        if start_time is None and since_id is None and until_id is None:
            start_time = datetime.datetime(2006, 3, 21, tzinfo=datetime.timezone.utc)

        # Academic track let's you use longer queries
        max_query_length = 1024

    if counts_only:
        api_method = T.counts_all if archive else T.counts_recent
        kwargs.pop("expansions", None)
        kwargs.pop("tweet_fields", None)
        kwargs.pop("user_fields", None)
        kwargs.pop("media_fields", None)
        kwargs.pop("poll_fields", None)
        kwargs.pop("place_fields", None)
        kwargs = {
            **kwargs,
            **{
                "since_id": since_id,
                "until_id": until_id,
                "start_time": start_time,
                "end_time": end_time,
                "granularity": granularity,
            },
        }

        # Write the header for the CSV output
        click.echo(f"query,start,end,{granularity}_count", file=outfile)

    else:
        api_method = T.search_all if archive else T.search_recent
        kwargs = {
            **kwargs,
            **{
                "since_id": since_id,
                "until_id": until_id,
                "start_time": start_time,
                "end_time": end_time,
                "max_results": max_results,
            },
        }

    # TODO: Validate the queries are all valid length before beginning and report errors

    # TODO: Needs an inputlines progress bar instead, as the queries are variable
    # size.
    with FileLineProgressBar(infile, outfile, disable=hide_progress) as progress:

        merged_query = ""

        for query in infile:
            query = query.strip()

            progress.update(1)
            line_count += 1

            if query == "":
                log.warn("skipping blank line on line %s", line_count)
                continue

            if len(query) >= max_query_length:
                log.warn(f"skipping too long query {query} on line {line_count}")
                continue

            if query in seen:
                log.info("already processed %s, skipping", query)
                continue

            seen.add(query)
            retrieved = 0

            if combine_queries and merged_query:
                extended_query = f"{merged_query} OR ({query})"
                # We've exceeded the limit, so now we can issue
                # the merged query.
                if len(extended_query) >= max_query_length:
                    issue_query = merged_query
                    merged_query = f"({query})"
                else:
                    # We haven't exceed the length yet, so accept the addon
                    merged_query = extended_query
                    continue

            elif combine_queries:
                merged_query = f"({query})"
                continue

            else:
                # This is the normal case - we are not doing any combination.
                issue_query = query

            log.info(f'Beginning search for "{issue_query}"')

            response = api_method(issue_query, **kwargs)

            for result in response:

                if counts_only:
                    for r in result["data"]:
                        click.echo(
                            f'{issue_query},{r["start"]},{r["end"]},{r["tweet_count"]}',
                            file=outfile,
                        )

                else:
                    # Apply the limit if not counting
                    _write(result, outfile)

                    retrieved += len(result["data"])

                    if limit and (retrieved >= limit):
                        break

        # Make sure to process the final batch of queries if using the combined strategy
        if combine_queries and (
            merged_query == extended_query or merged_query == f"({query})"
        ):
            log.info(f'Beginning search for "{merged_query}"')
            response = api_method(merged_query, **kwargs)

            for result in response:

                if counts_only:
                    for r in result["data"]:
                        click.echo(
                            f'{merged_query},{r["start"]},{r["end"]},{r["tweet_count"]}',
                            file=outfile,
                        )

                else:
                    # Apply the limit if not counting
                    _write(result, outfile)

                    retrieved += len(result["data"])

                    if limit and (retrieved >= limit):
                        break


@twarc2.command("conversation")
@command_line_search_options
@command_line_search_archive_options
@command_line_expansions_shortcuts
@command_line_expansions_options
@command_line_progressbar_option
@click.argument("tweet_id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def conversation(
    T,
    tweet_id,
    outfile,
    **kwargs,
):
    """
    Retrieve a conversation thread using the tweet id.
    """

    kwargs = _process_expansions_shortcuts(kwargs)

    q = f"conversation_id:{tweet_id}"
    return _search(
        T,
        q,
        outfile,
        **kwargs,
    )


@twarc2.command("conversations")
@click.option(
    "--conversation-limit",
    default=0,
    help="Maximum number of tweets to return per-conversation",
)
@command_line_search_options
@command_line_search_archive_options
@command_line_expansions_shortcuts
@command_line_expansions_options
@command_line_progressbar_option
@command_line_input_output_file_arguments
@click.pass_obj
@cli_api_error
def conversations(
    T, infile, outfile, archive, limit, conversation_limit, hide_progress, **kwargs
):
    """
    Fetch the full conversation threads that the input tweets are a part of.
    Alternatively the input can be a line oriented file of conversation ids.
    """

    kwargs = _process_expansions_shortcuts(kwargs)

    # keep track of converstation ids that have been fetched so that they
    # aren't fetched twice
    seen = set()

    # use the archive or recent search?
    search = T.search_all if archive else T.search_recent

    count = 0
    stop = False

    with FileLineProgressBar(infile, outfile, disable=hide_progress) as progress:
        for line in infile:
            progress.update()
            conv_ids = []

            # stop will get set when the total tweet limit has been met
            if stop:
                break

            # get a specific conversation id
            line = line.strip()
            if line and re.match(r"^\d+$", line):
                if line in seen:
                    continue
                conv_ids = [line]

            # generate all conversation_ids that are referenced in tweets input
            elif line:

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
                for result in search(f"conversation_id:{conv_id}", **kwargs):
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
@command_line_progressbar_option
@command_line_input_output_file_arguments
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


@twarc2.command("places")
@click.option(
    "--type",
    "search_type",
    type=click.Choice(["name", "geo", "ip"]),
    default="name",
    help="How to search for places (defaults to name)",
)
@click.option(
    "--granularity",
    type=click.Choice(["neighborhood", "city", "admin", "country"]),
    default="neighborhood",
    help="What type of places to search for (defaults to neighborhood)",
)
@click.option("--max-results", type=int, help="Maximum results to return")
@click.option("--json", is_flag=True, help="Output raw JSON response")
@click.argument("value")
@click.argument("outfile", type=click.File("w"), default="-")
@click.pass_obj
@cli_api_error
def places(T, value, outfile, search_type, granularity, max_results, json):
    """
    Search for places by place name, geo coordinates or ip address.
    """
    params = {"granularity": granularity}

    if search_type == "name":
        params["query"] = value
    elif search_type == "ip":
        params["ip"] = value
    elif search_type == "geo":
        try:
            lat, lon = list(map(float, value.split(",")))
            params = {"lat": lat, "lon": lon}
        except:
            click.echo("--geo must be lat,lon", err=True)

    if max_results:
        params["max_results"] = max_results

    result = T.geo(**params)

    if "errors" in result:
        click.echo(_error_str(result["errors"]), err=True)
    elif json:
        _write(result, outfile)
    else:
        for place in result["result"]["places"]:
            if granularity == "country":
                line = "{0} [id={1}]".format(place["country"], place["id"])
            else:
                line = "{0}, {1} [id={2}]".format(
                    place["full_name"], place["country"], place["id"]
                )
            click.echo(line)


@twarc2.command("stream")
@click.option("--limit", default=0, help="Maximum number of tweets to return")
@command_line_expansions_shortcuts
@command_line_expansions_options
@click.argument("outfile", type=click.File("a+"), default="-")
@click.pass_obj
@cli_api_error
def stream(T, outfile, limit, **kwargs):
    """
    Fetch tweets from the live stream.
    """

    kwargs = _process_expansions_shortcuts(kwargs)
    event = threading.Event()
    count = 0
    click.echo(click.style(f"Started a stream with rules:", fg="green"), err=True)
    _print_stream_rules(T)
    click.echo(
        click.style(f"Writing to {outfile.name}\nCTRL+C to stop...", fg="green"),
        err=True,
    )
    for result in T.stream(event=event, **kwargs):
        count += 1
        if limit != 0 and count == limit:
            log.info(f"reached limit {limit}")
            event.set()
        _write(result, outfile)

        if result and "data" in result:
            log.info("archived %s", result["data"]["id"])


@twarc2.group()
@click.pass_obj
def lists(T):
    """
    Lists API support.
    """
    pass


@lists.command("lookup")
@click.argument("list_id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.option("--pretty", is_flag=True, default=False, help="Pretty print the JSON")
@click.option(
    "--list-fields",
    default=",".join(LIST_FIELDS),
    type=click.STRING,
    is_eager=True,
    help="Comma separated list of tweet fields to retrieve. Default is all available.",
    callback=_validate_expansions,
)
@click.pass_obj
@cli_api_error
def lists_lookup(T, list_id, outfile, pretty, **kwargs):
    """
    Look up a single list using its list id or URL.
    """

    kwargs = _process_expansions_shortcuts(kwargs)

    if "https" in list_id:
        list_id = list_id.split("/")[-1]
    if not re.match("^\d+$", list_id):
        click.echo(click.style("Please enter a List URL or ID", fg="red"), err=True)
    result = T.list_lookup(list_id, **kwargs)
    _write(result, outfile, pretty=pretty)


@lists.command("bulk-lookup")
@command_line_input_output_file_arguments
@command_line_progressbar_option
@click.option(
    "--list-fields",
    default=",".join(LIST_FIELDS),
    type=click.STRING,
    is_eager=True,
    help="Comma separated list of fields about a list to retrieve. Default is all available.",
    callback=_validate_expansions,
)
@click.pass_obj
@cli_api_error
def lists_bulk_lookup(T, infile, outfile, hide_progress, **kwargs):
    """
    Look up the details of many lists given a file of IDs or URLs.
    """

    kwargs = _process_expansions_shortcuts(kwargs)

    with FileLineProgressBar(infile, outfile, disable=hide_progress) as progress:
        for list_id in infile:
            progress.update()

            if "https" in list_id:
                list_id = list_id.split("/")[-1]
            if not re.match("^\d+$", list_id):
                click.echo(
                    click.style("Skipping invalid List URL or ID: {line}", fg="red"),
                    err=True,
                )
                continue
            result = T.list_lookup(list_id.strip(), **kwargs)
            _write(result, outfile)


@lists.command("all")
@click.argument("user", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.option(
    "--list-fields",
    default=",".join(LIST_FIELDS),
    type=click.STRING,
    is_eager=True,
    help="Comma separated list of tweet fields to retrieve. Default is all available.",
    callback=_validate_expansions,
)
@click.option(
    "--limit",
    default=0,
    help="Maximum number of lists to save. Default is all.",
    type=int,
)
@command_line_progressbar_option
@click.pass_obj
@cli_api_error
def lists_all(T, user, outfile, limit, hide_progress, **kwargs):
    """
    Get all Lists that a user created or is subscribed to.

    You can use the `owned` or `followed` command to get just the lists
    created by the user, or just the lists followed by the user
    respectively.

    """
    kwargs = _process_expansions_shortcuts(kwargs)
    _write_with_progress(
        func=T.owned_lists,
        user=user,
        outfile=outfile,
        limit=limit,
        hide_progress=hide_progress,
        progress_total=1,
        **kwargs,
    )
    _write_with_progress(
        func=T.followed_lists,
        user=user,
        outfile=outfile,
        limit=limit,
        hide_progress=hide_progress,
        progress_total=1,
        **kwargs,
    )


@lists.command("owned")
@click.argument("user", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.option(
    "--list-fields",
    default=",".join(LIST_FIELDS),
    type=click.STRING,
    is_eager=True,
    help="Comma separated list of tweet fields to retrieve. Default is all available.",
    callback=_validate_expansions,
)
@click.option(
    "--limit",
    default=0,
    help="Maximum number of lists to save. Default is all.",
    type=int,
)
@command_line_progressbar_option
@click.pass_obj
@cli_api_error
def lists_owned(T, user, outfile, limit, hide_progress, **kwargs):
    """
    Get all Lists that a user created.
    """
    kwargs = _process_expansions_shortcuts(kwargs)
    _write_with_progress(
        func=T.owned_lists,
        user=user,
        outfile=outfile,
        limit=limit,
        hide_progress=hide_progress,
        progress_total=1,
        **kwargs,
    )


@lists.command("followed")
@click.argument("user", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.option(
    "--list-fields",
    default=",".join(LIST_FIELDS),
    type=click.STRING,
    is_eager=True,
    help="Comma separated list of tweet fields to retrieve. Default is all available.",
    callback=_validate_expansions,
)
@click.option(
    "--limit",
    default=0,
    help="Maximum number of lists to save. Default is all.",
    type=int,
)
@command_line_progressbar_option
@click.pass_obj
@cli_api_error
def lists_followed(T, user, outfile, limit, hide_progress, **kwargs):
    """
    Get all Lists that a user is following.
    """
    kwargs = _process_expansions_shortcuts(kwargs)
    _write_with_progress(
        func=T.followed_lists,
        user=user,
        outfile=outfile,
        limit=limit,
        hide_progress=hide_progress,
        progress_total=1,
        **kwargs,
    )


@lists.command("memberships")
@click.argument("user", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.option(
    "--list-fields",
    default=",".join(LIST_FIELDS),
    type=click.STRING,
    is_eager=True,
    help="Comma separated list of tweet fields to retrieve. Default is all available.",
    callback=_validate_expansions,
)
@click.option(
    "--limit",
    default=0,
    help="Maximum number of lists to save. Default is all.",
    type=int,
)
@command_line_progressbar_option
@click.pass_obj
@cli_api_error
def lists_memberships(T, user, outfile, limit, hide_progress, **kwargs):
    """
    Get all Lists that a user is a member of.
    """
    kwargs = _process_expansions_shortcuts(kwargs)
    lookup_total = 1

    hide_progress = True if (outfile.name == "<stdout>") else hide_progress

    if not hide_progress:
        target_user = T._ensure_user(user)
        lookup_total = target_user["public_metrics"]["listed_count"]

    _write_with_progress(
        func=T.list_memberships,
        user=user,
        outfile=outfile,
        limit=limit,
        hide_progress=hide_progress,
        progress_total=lookup_total,
        **kwargs,
    )


@lists.command("followers")
@click.argument("list-id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.option(
    "--limit",
    default=0,
    help="Maximum number of lists to save. Default is all.",
    type=int,
)
@command_line_expansions_options
@command_line_progressbar_option
@click.pass_obj
@cli_api_error
def lists_followers(T, list_id, outfile, limit, hide_progress, **kwargs):
    """
    Get all Users that are following (subscribed) to a list.
    """
    kwargs = _process_expansions_shortcuts(kwargs)
    # Also remove media poll and place from kwargs, these are not valid for this endpoint:
    kwargs.pop("media_fields", None)
    kwargs.pop("poll_fields", None)
    kwargs.pop("place_fields", None)

    _list = ensure_flattened(T.list_lookup(list_id))[-1]
    list_id = _list["id"]
    lookup_total = int(_list["follower_count"])

    _write_with_progress(
        func=T.list_followers,
        list_id=list_id,
        outfile=outfile,
        limit=limit,
        hide_progress=hide_progress,
        progress_total=lookup_total,
        **kwargs,
    )


@lists.command("members")
@click.argument("list-id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.option(
    "--limit",
    default=0,
    help="Maximum number of lists to save. Default is all.",
    type=int,
)
@command_line_expansions_options
@command_line_progressbar_option
@click.pass_obj
@cli_api_error
def lists_members(T, list_id, outfile, limit, hide_progress, **kwargs):
    """
    Get all Users that are members of a list.
    """
    kwargs = _process_expansions_shortcuts(kwargs)
    # Also remove media poll and place from kwargs, these are not valid for this endpoint:
    kwargs.pop("media_fields", None)
    kwargs.pop("poll_fields", None)
    kwargs.pop("place_fields", None)

    _list = ensure_flattened(T.list_lookup(list_id))[-1]
    list_id = _list["id"]
    lookup_total = int(_list["member_count"])

    _write_with_progress(
        func=T.list_members,
        list_id=list_id,
        outfile=outfile,
        limit=limit,
        hide_progress=hide_progress,
        progress_total=lookup_total,
        **kwargs,
    )


@lists.command("tweets")
@click.argument("list-id", type=str)
@click.argument("outfile", type=click.File("w"), default="-")
@click.option(
    "--limit",
    default=0,
    help="Maximum number of tweets to save. Default and max is last 800.",
    type=int,
)
@command_line_expansions_options
@command_line_progressbar_option
@click.pass_obj
@cli_api_error
def lists_tweets(T, list_id, outfile, limit, hide_progress, **kwargs):
    """
    Get up to the most recent 800 tweets posted by members of a list.
    """
    kwargs = _process_expansions_shortcuts(kwargs)
    # Also remove media poll and place from kwargs, these are not valid for this endpoint:
    kwargs.pop("media_fields", None)
    kwargs.pop("poll_fields", None)
    kwargs.pop("place_fields", None)

    _write_with_progress(
        func=T.list_tweets,
        list_id=list_id,
        outfile=outfile,
        limit=limit,
        hide_progress=hide_progress,
        progress_total=800,
        **kwargs,
    )


@twarc2.group()
@click.pass_obj
def stream_rules(T):
    """
    List, add and delete rules for your stream.
    """
    pass


@stream_rules.command("list")
@click.option("--display-ids", is_flag=True, help="display the rule ids")
@click.pass_obj
@cli_api_error
def list_stream_rules(T, display_ids):
    """
    List all the active stream rules.
    """
    _print_stream_rules(T, display_ids)


def _print_stream_rules(T, display_ids=False):
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
            if display_ids:
                s += f" (id: {rule['id']})"

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


@twarc2.group()
@click.pass_obj
def compliance_job(T):
    """
    Create, retrieve and list batch compliance jobs for Tweets and Users.
    """
    pass


@compliance_job.command("list")
@click.argument(
    "job_type",
    required=False,
    default=None,
    type=click.Choice(["tweets", "users"], case_sensitive=False),
)
@click.option(
    "--status",
    default=None,
    type=click.Choice(
        ["created", "in_progress", "complete", "failed"], case_sensitive=False
    ),
    help="Filter by job status. Only one of 'created', 'in_progress', 'complete', 'failed' can be specified. If not set, returns all.",
)
@command_line_verbose_options
@click.pass_obj
@cli_api_error
def compliance_job_list(T, job_type, status, verbose, json_output):
    """
    Returns a list of compliance jobs by job type and status.
    """

    if job_type:
        job_result = T.compliance_job_list(job_type.lower(), status)
        results = job_result["data"] if "data" in job_result else []
    else:
        tweets_result = T.compliance_job_list("tweets", status)
        users_result = T.compliance_job_list("users", status)
        tweets_jobs = tweets_result["data"] if "data" in tweets_result else []
        users_jobs = users_result["data"] if "data" in users_result else []
        results = tweets_jobs + users_jobs

    if json_output:
        click.echo(json.dumps(results))
        return

    if len(results) == 0:
        job_type_message = "tweet or user" if job_type is None else job_type
        status_message = f' with Status "{status}"' if status else ""
        click.echo(
            click.style(
                f"🙃 There are no {job_type_message} compliance jobs{status_message}. To create a new job, see:\n twarc2 compliance-job create --help",
                fg="red",
            ),
            err=True,
        )
    else:
        for job in results:
            _print_compliance_job(job, verbose)


@compliance_job.command("get")
@click.argument("job")
@command_line_verbose_options
@click.pass_obj
@cli_api_error
def compliance_job_get(T, job, verbose, json_output):
    """
    Returns status and download information about the job ID.
    """
    if json_output:
        result = T.compliance_job_get(job)
        click.echo(json.dumps(result))
        return

    job = _get_job(T, job)
    if job is None:
        return

    _print_compliance_job(job, verbose)

    # Ask to download if complete
    if job["status"] == "complete":
        continue_download = input(
            f"This job is complete, download it now into the current folder? [y or n]? "
        )
        if continue_download.lower()[0] == "y":
            _download_job(job)


@compliance_job.command("create")
@click.argument(
    "job_type",
    required=True,
    type=click.Choice(["tweets", "users"], case_sensitive=False),
)
@click.argument("infile", type=click.Path(), required=True)
@click.argument("outfile", type=click.Path(), required=False, default=None)
@click.option("--job-name", type=str, help="A name or tag to help identify the job.")
@click.option(
    "--wait/--no-wait",
    default=True,
    help="Wait for the job to finish and download the results. Wait by default.",
)
@command_line_progressbar_option
@click.pass_obj
@cli_api_error
def compliance_job_create(T, job_type, infile, outfile, job_name, wait, hide_progress):
    """
    Create a new compliance job and upload tweet IDs.
    """

    # Check for file contents:
    with open(infile) as f:
        try:
            int(f.readline())
        except:
            click.echo(
                click.style(
                    f"🙃 The file {infile} does not contain a list of IDs. Use:",
                    fg="red",
                ),
                err=True,
            )
            click.echo(
                click.style(
                    f" twarc2 dehydrate --id-type {job_type} {infile} output_ids.txt",
                ),
                err=True,
            )
            click.echo(
                click.style(
                    f"to create a file with {job_type} IDs.",
                    fg="red",
                ),
                err=True,
            )
            return

    # Create a job (not resumable right now):
    _job = T.compliance_job_create(job_type, job_name)["data"]

    click.echo(
        click.style(
            f"Created a new {job_type} job {_job['id']}. Uploading {infile}.",
            fg="yellow",
            bold=True,
        ),
        err=True,
    )

    # Upload the file
    with open(infile, "rb") as f:
        with tqdm(
            total=os.stat(infile).st_size, unit="B", unit_scale=True, unit_divisor=1024
        ) as pbar:
            wrapped_file = CallbackIOWrapper(pbar.update, f, "read")
            requests.put(
                _job["upload_url"],
                data=wrapped_file,
                headers={"Content-Type": "text/plain"},
            )

    if wait:
        if _wait_for_job(T, _job):
            _download_job(_job, outfile, hide_progress)


@compliance_job.command("download")
@click.argument("job")
@click.argument("outfile", type=click.Path(), required=False, default=None)
@click.option(
    "--wait/--no-wait",
    default=True,
    help="Wait for the job to finish and download the results. Wait by default.",
)
@command_line_progressbar_option
@click.pass_obj
@cli_api_error
def compliance_job_download(T, job, outfile, wait, hide_progress):
    """
    Download the compliance job with the specified ID.
    """

    _job = _get_job(T, job)
    if _job is None:
        click.echo(
            click.style(
                f"Job {job} not found. List valid job IDs with 'twarc2 compliance-job list' or Retry submitting the job with 'twarc2 compliance-job create'",
                fg="red",
                bold=True,
            ),
            err=True,
        )
        return

    if _job["status"] == "complete":
        _download_job(_job, outfile, hide_progress)
    elif _job["status"] == "expired" or _job["status"] == "failed":
        click.echo(
            click.style(
                f"Job {_job['id']} is '{_job['status']}'. Retry submitting the job with 'twarc2 compliance-job create'",
                fg="red",
                bold=True,
            ),
            err=True,
        )
        return
    else:
        if not wait:
            click.echo(
                click.style(
                    f"Job {_job['id']} is '{_job['status']}'. Use:\n twarc2 compliance-job get {_job['id']}\nto get the status. Or run:\n twarc2 compliance-job download {_job['id']}\nto wait for the job to complete.",
                    fg="yellow",
                    bold=True,
                ),
                err=True,
            )
        else:
            if _wait_for_job(T, _job):
                _download_job(_job, outfile, hide_progress)


def _get_job(T, job):
    """
    Retrieve a job from the API by ID
    """
    result = T.compliance_job_get(job)
    if "data" not in result:
        click.echo(
            click.style(
                f"Job {job} could not be found. List valid job IDs with 'twarc2 compliance-job list'",
                fg="red",
                bold=True,
            ),
            err=True,
        )
        return None
    return result["data"]


def _wait_for_job(T, job, hide_progress=False):
    """
    Wait for the compliance job to complete
    """

    if (
        job is not None
        and "status" in job
        and (job["status"] == "failed" or job["status"] == "expired")
    ):
        click.echo(
            click.style(
                f"Stopped waiting for job... Job status is {job['status']}",
                fg="red",
                bold=True,
            )
        )
        return False

    click.echo(
        click.style(
            f"Waiting for job {job['id']} to complete. Press Ctrl+C to cancel.",
            fg="yellow",
            bold=True,
        ),
        err=True,
    )

    start_time = datetime.datetime.now(datetime.timezone.utc)
    est_completion = (
        datetime.datetime.strptime(
            job["estimated_completion"], "%Y-%m-%dT%H:%M:%S.%fZ"
        ).replace(tzinfo=datetime.timezone.utc)
        if "estimated_completion" in job
        else start_time
    )
    seconds_wait = int((est_completion - start_time).total_seconds())
    if seconds_wait <= 0:
        click.echo(
            click.style(
                f"Estimated completion time unknown, waiting 1 minute instead.",
                fg="yellow",
                bold=True,
            ),
            err=True,
        )
        seconds_wait = 60
        est_completion = datetime.datetime.now(
            datetime.timezone.utc
        ) + datetime.timedelta(seconds=60)

    with TimestampProgressBar(
        since_id=None,
        until_id=None,
        start_time=start_time,
        end_time=est_completion,
        disable=hide_progress,
        bar_format="{l_bar}{bar}| Waiting {n_time}/{total_time}{postfix}",
    ) as pbar:

        while True:
            try:
                pbar.refresh()
                pbar.reset()
                for i in range(seconds_wait * 10):
                    pbar.update(100)
                    time.sleep(0.1)

                job = _get_job(T, job["id"])

                if job is not None and "status" in job:
                    total_wait = humanize.naturaldelta(
                        datetime.datetime.now(datetime.timezone.utc) - start_time
                    )
                    pbar.set_postfix_str(
                        f"Job Status: {job['status']}. Waited for: {total_wait}"
                    )

                    if job["status"] == "complete":
                        return True
                    elif job["status"] == "in_progress" or job["status"] == "created":
                        continue
                    else:
                        click.echo(
                            click.style(
                                f"Stopped waiting for job... Job status is {job['status']}",
                                fg="red",
                                bold=True,
                            )
                        )
                        return False
                else:
                    click.echo(
                        click.style(
                            f"Stopped waiting for job... Failed to retrieve job from API.",
                            fg="red",
                            bold=True,
                        ),
                        err=True,
                    )
                    return False

            except KeyboardInterrupt:
                click.echo(
                    click.style(
                        "Stopped waiting for job... Run the command again to continue waiting.",
                        fg="yellow",
                        bold=True,
                    )
                )
                return False


def _download_job(job, outfile=None, hide_progress=False):
    """
    Download the compliance job.
    """

    click.echo(
        click.style(
            f"Job {job['id']} is '{job['status']}'. Downloading Results...",
            fg="yellow",
            bold=True,
        ),
        err=True,
    )

    url = job["download_url"]
    if outfile is None:
        outfile = f"{job['type']}_compliance_{job['id']}.json"

    response = requests.get(url, stream=True)

    with open(outfile, "wb") as fout:
        with tqdm(
            disable=hide_progress,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            miniters=1,
            total=int(response.headers.get("content-length", 0)),
        ) as pbar:
            pbar.set_postfix_str(outfile)
            for chunk in response.iter_content(chunk_size=4096):
                fout.write(chunk)
                pbar.update(len(chunk))


def _print_compliance_job(job, verbose=False):
    job_colour = "yellow"

    if job["status"] == "expired" or job["status"] == "failed":
        job_colour = "red"

    if job["status"] == "complete":
        job_colour = "green"

    time_now = datetime.datetime.now(datetime.timezone.utc)

    upload_exp = time_now - datetime.datetime.strptime(
        job["upload_expires_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
    ).replace(tzinfo=datetime.timezone.utc)

    download_exp = time_now - datetime.datetime.strptime(
        job["download_expires_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
    ).replace(tzinfo=datetime.timezone.utc)

    failure = ""
    if "error" in job:
        failure = job["error"]

    job_name = job["name"] if "name" in job else "Job"
    click.echo(
        click.style(
            f"📃 Type: \"{job['type']}\" ID: \"{job['id']}\" Name: \"{job_name}\" Status: \"{job['status']}\" {failure}",
            fg=job_colour,
            bold=True,
        ),
        err=True,
    )
    if verbose:
        click.echo(
            click.style(f"Created at: {job['created_at']}"),
            err=True,
        )
        click.echo(
            click.style(f"Resumable: {job['resumable']}"),
            err=True,
        )
        upload_url = job["upload_url"] if upload_exp.total_seconds() < 0 else "Expired"
        click.echo(
            click.style(
                f"Upload Expiry: {humanize.naturaltime(upload_exp)} URL: {upload_url}"
            ),
            err=True,
        )
        download_url = (
            job["download_url"] if download_exp.total_seconds() < 0 else "Expired"
        )
        click.echo(
            click.style(
                f"Download Expiry: {humanize.naturaltime(download_exp)} URL: {download_url}"
            ),
            err=True,
        )


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


def _write_with_progress(
    func, outfile, limit, hide_progress, progress_total=1, **kwargs
):
    """
    Get results page by page and write them out with a progress bar
    """
    count = 0
    hide_progress = True if (outfile.name == "<stdout>") else hide_progress

    with tqdm(disable=hide_progress, total=progress_total) as progress:
        results = func(**kwargs)
        for result in results:
            _write(result, outfile)
            count += len(result.get("data", []))
            progress.update(len(result.get("data", [])))
            if limit != 0 and count >= limit:
                # Display message when stopped early
                progress.desc = f"Set --limit of {limit} reached"
                break
        # Finish the progress bar
        progress.update(progress.total - progress.n)
