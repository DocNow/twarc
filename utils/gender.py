#!/usr/bin/env python

"""
filters tweets based on a guess about the users gender
"""
from __future__ import print_function

import json
import optparse
import fileinput
from genderator.detector import Detector, MALE, FEMALE, ANDROGYNOUS

usage = "usage: gender.py --gender [male|female|unknown] tweet_file *"
opt_parser = optparse.OptionParser(usage=usage)
opt_parser.add_option("-g", "--gender", dest="gender", choices=["male", "female", "unknown"], action="store")
options, args = opt_parser.parse_args()

if not options.gender:
    opt_parser.error("must supply --gender")

d = Detector()
for line in fileinput.input(args):
    line = line.strip()
    tweet = json.loads(line)
    name = tweet['user']['name']
    first_name = name.split(" ")[0]
    gender = d.getGender(first_name)
    if options.gender == "male" and gender == MALE:
        print(line.encode('utf-8'))
    elif options.gender == "female" and gender == FEMALE:
        print(line.encode('utf-8'))
    elif options.gender == "unknown" and gender == ANDROGYNOUS:
        print(line.encode('utf-8'))
