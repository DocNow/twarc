from __future__ import print_function

import os
import re
import sys
import json
import codecs
import logging
import argparse
import fileinput

from twarc import __version__
from twarc.client import Twarc
from twarc.json2csv import csv, get_headings, get_row

if sys.version_info[:2] <= (2, 7):
    # Python 2
    get_input = raw_input
    str_type = unicode
    import ConfigParser as configparser
else:
    # Python 3
    get_input = input
    str_type = str
    import configparser


commands = [
    "configure",
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

    if command == "version":
        print("twarc v%s" % __version__)
        sys.exit()
    elif command == "help" or not command:
        parser.print_help()
        print("\nPlease use one of the following commands:\n")
        for cmd in commands:
            print(" - %s" % cmd)
        print("\nFor example:\n\n    twarc search blacklivesmatter")
        sys.exit(1)

    t = Twarc(
        consumer_key=args.consumer_key,
        consumer_secret=args.consumer_secret,
        access_token=args.access_token,
        access_token_secret=args.access_token_secret,
        connection_errors=args.connection_errors,
        http_errors=args.http_errors,
        config=args.config,
        profile=args.profile,
        tweet_mode=args.tweet_mode
    )

    # calls that return tweets
    if command == "search":
        things = t.search(
            query,
            since_id=args.since_id,
            max_id=args.max_id,
            lang=args.lang,
            result_type=args.result_type,
            geocode=args.geocode
        )

    elif command == "filter":
        things = t.filter(
            track=query,
            follow=args.follow,
            locations=args.locations
        )

    elif command == "dehydrate":
        input_iterator = fileinput.FileInput(
            query,
            mode='rU',
            openhook=fileinput.hook_compressed,
        )
        things = t.dehydrate(input_iterator)

    elif command == "hydrate":
        input_iterator = fileinput.FileInput(
            query,
            mode='rU',
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
        else:
            kwargs["screen_name"] = query
        things = t.timeline(**kwargs)

    elif command == "retweets":
        things = t.retweets(query)

    elif command == "users":
        if os.path.isfile(query):
            iterator = fileinput.FileInput(
                query,
                mode='rU',
                openhook=fileinput.hook_compressed,
            )
            things = t.user_lookup(iterator=iterator)
        elif re.match('^[0-9,]+$', query):
            things = t.user_lookup(user_ids=query.split(","))
        else:
            things = t.user_lookup(screen_names=query.split(","))

    elif command == "followers":
        things = t.follower_ids(query)

    elif command == "friends":
        things = t.friend_ids(query)

    elif command == "trends":
        # lookup woeid for geo-coordinate if appropriate
        geo = re.match('^([0-9\-\.]+),([0-9\-\.]+)$', query)
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

    elif command == "configure":
        t.input_keys()
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
        fh = codecs.open(args.output, 'wb', 'utf8')
    else:
        fh = sys.stdout

    # optionally create a csv writer
    csv_writer = None
    if args.format == "csv" and command not in ["filter", "hydrate", "replies",
            "retweets", "sample", "search", "timeline", "tweet"]:
        parser.error("csv output not available for %s" % command)
    elif args.format == "csv":
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
            logging.info("archived %s" % thing)
        elif 'id_str' in thing:
            # tweets and users
            if (args.format == "json"):
                print(json.dumps(thing), file=fh)
            elif (args.format == "csv"):
                csv_writer.writerow(get_row(thing))
            logging.info("archived %s", thing['id_str'])
        elif 'woeid' in thing:
            # places
            print(json.dump(thing), file=fh)
        elif 'tweet_volume' in thing:
            # trends
            print(json.dump(thing), file=fh)
        elif 'limit' in thing:
            # rate limits
            t = datetime.datetime.utcfromtimestamp(
                float(thing['limit']['timestamp_ms']) / 1000)
            t = t.isoformat("T") + "Z"
            logging.warn("%s tweets undelivered at %s",
                         thing['limit']['track'], t)
            if args.warnings:
                print(json.dump(thing), file=fh)
        elif 'warning' in thing:
            # other warnings
            logging.warn(thing['warning']['message'])
            if args.warnings:
                print(json.dump(thing), file=fh)


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
    parser.add_argument('--profile', default='main',
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
    parser.add_argument("--lang", dest="lang",
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
    parser.add_argument("--output", action="store", default=None,
                        dest="output", help="write output to file path")
    parser.add_argument("--format", action="store", default="json",
                        dest="format", choices=["json", "csv"],
                        help="set output format")
    parser.add_argument("--split", action="store", type=int, default=0,
                        help="used with --output to split into numbered files")

    return parser


def numbered_filepath(filepath, num):
    path, ext = os.path.splitext(filepath)
    return os.path.join('{}-{:0>3}{}'.format(path, num, ext))

