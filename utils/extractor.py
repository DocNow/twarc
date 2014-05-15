#!/usr/bin/env python3
from datetime import datetime
import json
import os
import re
import argparse
import csv
import copy

class attriObject:
    """Class object for attribute parser."""
    def __init__(self,raw, entity, user, text):
        self.raw = raw
        self.user = user
        self.entity = entity
        self.text = text

def tweets_files(string, path):
    """Iterates over json files in path."""
    for filename in os.listdir(path):
        if re.match(string, filename) and re.match(".*\.json", filename):
            yield path + filename

def parse(args):
    with open(args.output, 'w+') as output:
        csv_writer = csv.writer(output, dialect=args.dialect)
        titles = [a.raw for a in args.attributes]
        csv_writer.writerow(titles)
        count = 0
        tweets = set()
        
        for filename in tweets_files(args.string, args.path):
            print("parsing", filename)
            with open(filename) as data_file:
                for line in data_file:
                    try:
                        json_object = json.loads(line)
                    except ValueError:
                        print("Error in", filename, "file incomplete.")
                        continue
                    
                    identity = json_object['id']
                    if identity in tweets:
                        continue
                    tweets.add(identity)
                    if args.start or args.end:
                        tweet_time = datetime.strptime(json_object['created_at'],'%a %b %d %H:%M:%S +0000 %Y')
                        if args.start and args.start > tweet_time:
                            continue
                        if args.end and args.end < tweet_time:
                            continue
                
                    count += extract(json_object, args, csv_writer)
                        
        print("Searched", len(tweets), "tweets and recorded", count, "items.")
        print("largest id:", max(tweets))

def extract(json_object, args, csv_writer):
    """Extract and write found attributes."""
    found = [[]]
    for attribute in args.attributes:
        try:
            if attribute.user:
                item = json_object["user"][attribute.text]
            elif attribute.entity:
                item = json_object["entities"][attribute.entity]
            else:
                item = json_object[attribute.text]
        except:
            item = "NA"
        
        if isinstance(item, list):
            if len(item) < 2:
                value = item[0][attribute.text] if item else "NA"
                for row in found:
                    row.append(value)
            else:
                found1 = []
                for value in item:
                    new = copy.deepcopy(found)
                    for row in new:
                        row.append(value[attribute.text])
                    found1.extend(new)
                found = found1    
        else:
            for row in found:
                row.append(item)
            
    for row in found:
        csv_writer.writerow(row)
    return len(found)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extracts attributes from tweets.')
    parser.add_argument("attributes", nargs='*', help="Attributes to search for. Attributes inside the user namespace should be prefixed by u: (example: u|screen_name.). Entities should be prefixed by e: (example: e:hashtags:text)")
    parser.add_argument("-dialect", default="excel", help="Sets dialect for csv output. Defaults to excel. See python module csv.list_dialects()")
    parser.add_argument("-string", default="", help="Regular expression for files to parse. Defaults to empty string.")
    parser.add_argument("-path", default="./", help="Optional path to folder containing tweets. Defaults to current folder.")
    parser.add_argument("-output", default="output.csv", help="Optional file to output results. Defaults to output.csv.")
    parser.add_argument("-start", default="", help="Define start date for tweets. Format (mm:dd:yyyy)")
    parser.add_argument("-end", default="", help="Define end date for tweets. Format (mm:dd:yyyy)")
    args = parser.parse_args()
    
    if args.path[-1] != "/":
        args.path = args.path + "/"
    if args.start:
        args.start = datetime.strptime(args.start, '%m:%d:%Y')
    else:
        args.start = False
    if args.end:
        args.end = datetime.strptime(args.end, '%m:%d:%Y')
    else:
        args.end = False
    
    attributes = []
    for string in args.attributes:
        type_ = string[0]
        entity = False
        user = False
        if type_ == "u":
            user = True
            text = string[2:]
        elif type_ == "e":
            found = re.search("(?<=:).*(?=:)", string)
            entity = found.group()
            text = string[found.end() + 1:]
        else:
            text = string
        attributes.append(attriObject(string, entity, user, text))
    args.attributes = attributes
    parse(args)
