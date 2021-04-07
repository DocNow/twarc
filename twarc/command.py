from __future__ import print_function

import os
import re
import sys
import json
import signal
import codecs
import logging
import datetime
import argparse
import fileinput

from twarc.client import Twarc
from twarc.version import version
from twarc.json2csv import csv, get_headings, get_row
from dateutil.parser import parse as parse_dt

if sys.version_info[:2] <= (2, 7):
    # Python 2
    pyv = 2
    get_input = raw_input
    str_type = unicode
    import ConfigParser as configparser
else:
    # Python 3
    pyv = 3
    get_input = input
    str_type = str
    import configparser

log = logging.getLogger('twarc')


commands = [
    'configure',
    'dehydrate',
    'filter',
    'followers',
    'friends',
    'help',
    'hydrate',
    'replies',
    'retweets',
    'sample',
    'search',
    'timeline',
    'trends',
    'tweet',
    'users',
    'listmembers',
    'version',
]


def main():
    parser = get_argparser()
    args = parser.parse_args()

    command = args.command
    query = args.query or ""

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    # log and stop when process receives SIGINT
    def stop(signal, frame):
        log.warn('process received SIGNT, stopping')
        sys.exit(0)
    signal.signal(signal.SIGINT, stop)

    if command == "version":
        print("twarc v%s" % version)
        sys.exit()
    elif command == "help" or not command:
        parser.print_help()
        print("\nPlease use one of the following commands:\n")
        for cmd in commands:
            print(" - %s" % cmd)
        print("\nFor example:\n\n    twarc search blacklivesmatter")
        sys.exit(1)

    # Don't validate the keys if the command is "configure"
    if command == "configure" or args.skip_key_validation:
        validate_keys = False
    else:
        validate_keys = True

    t = Twarc(
        consumer_key=args.consumer_key,
        consumer_secret=args.consumer_secret,
        access_token=args.access_token,
        access_token_secret=args.access_token_secret,
        connection_errors=args.connection_errors,
        http_errors=args.http_errors,
        config=args.config,
        profile=args.profile,
        tweet_mode=args.tweet_mode,
        protected=args.protected,
        validate_keys=validate_keys,
        app_auth=args.app_auth,
        gnip_auth=args.gnip_auth
    )

    # calls that return tweets
    if command == "search":
        if len(args.lang) > 0:
            lang = args.lang[0]
        else:
            lang=None

        # if not using a premium endpoint do a standard search
        if not args.thirtyday and not args.fullarchive and not args.gnip_fullarchive:
            things = t.search(
                query,
                since_id=args.since_id,
                max_id=args.max_id,
                lang=lang,
                result_type=args.result_type,
                geocode=args.geocode
            )
        else:
            # parse the dates if given
            from_date = parse_dt(args.from_date) if args.from_date else None
            to_date = parse_dt(args.to_date) if args.to_date else None
            if args.gnip_fullarchive:
                env = args.gnip_fullarchive
                product = 'gnip_fullarchive'
            elif args.thirtyday:
                env = args.thirtyday
                product = '30day'
            else:
                env = args.fullarchive
                product = 'fullarchive'
            things = t.premium_search(
                query,
                product,
                env,
                from_date=from_date,
                to_date=to_date,
                sandbox=args.sandbox,
                limit=args.limit,
            )

    elif command == "filter":
        things = t.filter(
            track=query,
            follow=args.follow,
            locations=args.locations,
            lang=args.lang
        )

    elif command == "dehydrate":
        input_iterator = fileinput.FileInput(
            query,
            mode='r',
            openhook=fileinput.hook_compressed,
        )
        things = t.dehydrate(input_iterator)

    elif command == "hydrate":
        input_iterator = fileinput.FileInput(
            query,
            mode='r',
            openhook=fileinput.hook_compressed,
        )
        things = t.hydrate(input_iterator)

    elif command == "tweet":
        things = [t.tweet(query)]

    elif command == "sample":
        things = t.sample()

    elif command == "timeline":
        kwargs = {"max_id": args.max_id, "since_id": args.since_id}
        if re.match('^[0-9]+$', query):
            kwargs["user_id"] = query
        elif query:
            kwargs["screen_name"] = query
        things = t.timeline(**kwargs)

    elif command == "retweets":
        if os.path.isfile(query):
            iterator = fileinput.FileInput(
                query,
                mode='r',
                openhook=fileinput.hook_compressed,
            )
            things = t.retweets(tweet_ids=iterator)
        else:
            things = t.retweets(tweet_ids=query.split(','))

    elif command == "users":
        if os.path.isfile(query):
            iterator = fileinput.FileInput(
                query,
                mode='r',
                openhook=fileinput.hook_compressed,
            )
            if re.match('^[0-9,]+$', next(open(query))):
                id_type = 'user_id'
            else:
                id_type = 'screen_name'
            things = t.user_lookup(ids=iterator, id_type=id_type)
        elif re.match('^[0-9,]+$', query):
            things = t.user_lookup(ids=query.split(","))
        else:
            things = t.user_lookup(ids=query.split(","), id_type='screen_name')

    elif command == "followers":
        things = t.follower_ids(query)

    elif command == "friends":
        things = t.friend_ids(query)

    elif command == "trends":
        # lookup woeid for geo-coordinate if appropriate
        geo = re.match('^([0-9-.]+),([0-9-.]+)$', query)
        if geo:
            lat, lon = map(float, geo.groups())
            if lat > 180 or lat < -180 or lon > 180 or lon < -180:
                parser.error('LAT and LONG must be within [-180.0, 180.0]')
            places = list(t.trends_closest(lat, lon))
            if len(places) == 0:
                parser.error("Couldn't find WOE ID for %s" % query)
            query = places[0]["woeid"]

        if not query:
            things = t.trends_available()
        else:
            trends = t.trends_place(query)
            if trends:
                things = trends[0]['trends']

    elif command == "replies":
        tweet = t.tweet(query)
        if not tweet:
            parser.error("tweet with id %s does not exist" % query)
        things = t.replies(tweet, args.recursive)

    elif command == "listmembers":
        list_parts = re.match('^https://twitter.com/(.+)/lists/(.+)$', query)
        if not list_parts:
            parser.error("provide the url for the list, e.g., https://twitter.com/USAFacts/lists/us-armed-forces")
        things = t.list_members(slug=list_parts.group(2),
                                owner_screen_name=list_parts.groups(1))

    elif command == "configure":
        t.configure()
        sys.exit()

    else:
        parser.print_help()
        print("\nPlease use one of the following commands:\n")
        for cmd in commands:
            print(" - %s" % cmd)
        print("\nFor example:\n\n    twarc search blacklivesmatter")
        sys.exit(1)

    # get the output filehandle
    if args.output:
        if pyv == 3:
            fh = codecs.open(args.output, 'wb', 'utf8')
        else:
            fh = open(args.output, 'w')
    else:
        fh = sys.stdout

    # optionally create a csv writer
    csv_writer = None
    if args.format in ("csv", "csv-excel") and command not in ["filter", "hydrate", "replies",
            "retweets", "sample", "search", "timeline", "tweet"]:
        parser.error("csv output not available for %s" % command)
    elif args.format in ("csv", "csv-excel"):
        csv_writer = csv.writer(fh)
        csv_writer.writerow(get_headings())

    line_count = 0
    file_count = 0
    for thing in things:

        # rotate the files if necessary
        if args.output and args.split and line_count % args.split == 0:
            file_count += 1
            fh = codecs.open(numbered_filepath(args.output, file_count), 'wb', 'utf8')
            if csv_writer:
                csv_writer = csv.writer(fh)
                csv_writer.writerow(get_headings())

        line_count += 1

        # ready to output

        kind_of = type(thing)
        if kind_of == str_type:
            # user or tweet IDs
            print(thing, file=fh)
            log.info("archived %s" % thing)
        elif 'id_str' in thing:
            # tweets and users
            if (args.format == "json"):
                print(json.dumps(thing), file=fh)
            elif (args.format == "csv"):
                csv_writer.writerow(get_row(thing))
            elif (args.format == "csv-excel"):
                csv_writer.writerow(get_row(thing, excel=True))
            log.info("archived %s", thing['id_str'])
        elif 'woeid' in thing:
            # places
            print(json.dumps(thing), file=fh)
        elif 'tweet_volume' in thing:
            # trends
            print(json.dumps(thing), file=fh)
        elif 'limit' in thing:
            # rate limits
            t = datetime.datetime.utcfromtimestamp(
                float(thing['limit']['timestamp_ms']) / 1000)
            t = t.isoformat("T") + "Z"
            log.warning("%s tweets undelivered at %s",
                         thing['limit']['track'], t)
            if args.warnings:
                print(json.dumps(thing), file=fh)
        elif 'warning' in thing:
            # other warnings
            log.warning(thing['warning']['message'])
            if args.warnings:
                print(json.dumps(thing), file=fh)
        elif 'data' in thing:
            # Labs style JSON schema.
            print(json.dumps(thing), file=fh)


def get_argparser():
    """
    Get the command line argument parser.
    """

    parser = argparse.ArgumentParser("twarc")
    parser.add_argument('command', choices=commands)
    parser.add_argument('query', nargs='?', default=None)
    parser.add_argument("--log", dest="log",
                        default="twarc.log", help="log file")
    parser.add_argument("--consumer_key",
                        default=None, help="Twitter API consumer key")
    parser.add_argument("--consumer_secret",
                        default=None, help="Twitter API consumer secret")
    parser.add_argument("--access_token",
                        default=None, help="Twitter API access key")
    parser.add_argument("--access_token_secret",
                        default=None, help="Twitter API access token secret")
    parser.add_argument('--config',
                        help="Config file containing Twitter keys and secrets")
    parser.add_argument('--profile',
                        help="Name of a profile in your configuration file")
    parser.add_argument('--warnings', action='store_true',
                        help="Include warning messages in output")
    parser.add_argument("--connection_errors", type=int, default="0",
                        help="Number of connection errors before giving up")
    parser.add_argument("--http_errors", type=int, default="0",
                        help="Number of http errors before giving up")
    parser.add_argument("--max_id", dest="max_id",
                        help="maximum tweet id to search for")
    parser.add_argument("--since_id", dest="since_id",
                        help="smallest id to search for")
    parser.add_argument("--result_type", dest="result_type",
                        choices=["mixed", "recent", "popular"],
                        default="recent", help="search result type")
    parser.add_argument("--lang", dest="lang", action='append', default=[],
                        help="limit to ISO 639-1 language code"),
    parser.add_argument("--geocode", dest="geocode",
                        help="limit by latitude,longitude,radius")
    parser.add_argument("--locations", dest="locations",
                        help="limit filter stream to location(s)")
    parser.add_argument("--follow", dest="follow",
                        help="limit filter to tweets from given user id(s)")
    parser.add_argument("--recursive", dest="recursive", action="store_true",
                        help="also fetch replies to replies")
    parser.add_argument("--tweet_mode", action="store", default="extended",
                        dest="tweet_mode", choices=["compat", "extended"],
                        help="set tweet mode")
    parser.add_argument("--protected", dest="protected", action="store_true",
                        help="include protected tweets")
    parser.add_argument("--output", action="store", default=None,
                        dest="output", help="write output to file path")
    parser.add_argument("--format", action="store", default="json",
                        dest="format", choices=["json", "csv", "csv-excel"],
                        help="set output format")
    parser.add_argument("--split", action="store", type=int, default=0,
                        help="used with --output to split into numbered files")
    parser.add_argument("--skip_key_validation", action="store_true",
                        help="skip checking keys are valid on startup")
    parser.add_argument("--app_auth", action="store_true", default=False,
                        help="run in App Auth mode instead of User Auth")
    parser.add_argument("--gnip_auth", action="store_true", default=False,
                        help="run in Gnip Auth mode (for enterprise APIs)")
    parser.add_argument("--30day", action="store", dest="thirtyday", 
                        help="environment to use to search 30day premium endpoint")
    parser.add_argument("--fullarchive", action="store",
                        help="environment to use to search fullarchive premium endpoint"),
    parser.add_argument("--gnip_fullarchive", action="store",
                        help="environment to use to search gnip fullarchive enterprise endpoint"),
    parser.add_argument("--from_date", action="store", default=None,
                        help="limit premium search to date e.g. 2012-05-01 03:04:01")
    parser.add_argument("--to_date", action="store", default=None,
                        help="limit premium search to date e.g. 2012-05-01 03:04:01")
    parser.add_argument("--limit", type=int, default=0,
                        help="limit number of tweets returned by Premium API")
    parser.add_argument("--sandbox", action="store_true", default=False,
                        help="indicate that Premium API endpoint is a sandbox")

    return parser


def numbered_filepath(filepath, num):
    path, ext = os.path.splitext(filepath)
    return os.path.join('{}-{:0>3}{}'.format(path, num, ext))

