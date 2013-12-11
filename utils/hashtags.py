import json
import os
import re
import argparse
import sys

def find_tweets(strings, path):
    for filename in os.listdir(path):
        for string in strings:
            if re.match(string, filename) and re.match(".*\.json", filename):
                yield path + filename

def parse(args):
    tweets = set()
    count = 0
    with open(args.output, 'w+') as output:
        for filename in find_tweets(args.strings, args.path):
            print("parsing", filename)
            with open(filename) as data_file:
                for line in data_file:
                    
                    try:
                        json_object = json.loads(line)
                    except ValueError:
                        print("Error in", filename, "file incomplete.")
                        if args.error:
                            print(line)
                        continue
                    
                    hashtags = json_object['entities']['hashtags']
                    identity = json_object['id']
                    if args.duplicate or identity not in tweets:
                        for hashtag in hashtags:                
                            count +=1
                            print(hashtag['text'], file=output)
                        tweets.add(identity)
    
    print("Searched", len(tweets), "tweets and found", count, "hashtags.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extracts hashtags from tweets.')
    parser.add_argument("strings", nargs='*', help="Regular expression for files to parse.")
    parser.add_argument("-p", "--path", default="./", help="Optional path to folder containing tweets.")
    parser.add_argument("-o", "--output", default="./output.txt", help="Optional file to output results.")
    parser.add_argument("-e", "--error", action="store_true", help="Forces application to print out skipped tweets.")
    parser.add_argument("-d", "--duplicate", action="store_false", help="Checks for and avoids duplicate tweets.")
    
    args = parser.parse_args()
    if args.path[-1] != "/":
        args.path = args.path + "/"
    print(args)
    parse(args)
