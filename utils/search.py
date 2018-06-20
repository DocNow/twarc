#!/usr/bin/env python

"""
Filter tweet JSON based on a regular expression to apply to the text of the 
tweet.

    search.py <regex> file1

Or if you want a case insensitive match:

    search.py -i <regex> file1

"""

from __future__ import print_function

import re
import sys
import json
import argparse
import fileinput

from twarc import json2csv

if len(sys.argv) == 1:
    sys.exit("usage: search.py <regex> file1 file2")

parser = argparse.ArgumentParser(description="filter tweets by regex")

parser.add_argument('-i', '--ignore', dest='ignore', action='store_true',
                    help='ignore case')

parser.add_argument('regex')

parser.add_argument('files', metavar='FILE', nargs='*', default=['-'], help='files to read, if empty, stdin is used')

args = parser.parse_args()

flags = 0
if args.ignore:
    flags = re.IGNORECASE

try:
    regex = re.compile(args.regex, flags)
except Exception as e:
    sys.exit("error: regex failed to compile: {}".format(e))

for line in fileinput.input(files=args.files):
    tweet = json.loads(line)
    text = json2csv.text(tweet)
    if regex.search(text):
        print(line, end='')
