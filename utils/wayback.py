#!/usr/bin/env python

#
# Reads a stream of tweets and checks to see if the tweet is archived at
# Internet Archive and optionally requests SavePageNow save it.
#
# usage: ./wayback.py tweets.jsonl
#
# see ./wayback.py --help for details

import re
import json
import time
import requests
import optparse
import fileinput

def main(files, save, force_save, sleep):
    count = 0
    found_count = 0
    for line in fileinput.input(files):
        tweet = json.loads(line)
        url = 'https://twitter.com/{}/status/{}'.format(
            tweet['user']['screen_name'],
            tweet['id_str']
        )
        count += 1

        found = lookup(url)
        if found:
            print('{} last archived at {}'.format(url, found))
            found_count += 1
        else:
            print('{} not archived'.format(url))

        if (not found and save) or force_save:
            archive_url = savepagenow(url)
            if archive_url:
                print('saved {} as {}'.format(url, archive_url))
            else:
                print('save failed for {}'.format(url))

        time.sleep(sleep)

    print('')
    if count > 0:
        print('{}/{} found'.format(found_count, count))

def lookup(url):
    found = None 
    resp = requests.get('https://archive.org/wayback/available?url={}'.format(url))
    if resp.status_code == 200:
        result = resp.json()
        if 'closest' in result['archived_snapshots']:
            found = timestamp(result['archived_snapshots']['closest']['timestamp'])
    return found

def savepagenow(url):
    resp = requests.get('https://web.archive.org/save/' + url)
    if resp.status_code != 200 or 'content-location' not in resp.headers:
        return False
    return 'https://web.archive.org' + resp.headers['content-location']

    


def timestamp(s):
    m = re.match(r'^(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)$', s)
    return '{}-{}-{} {}:{}:{}'.format(*m.groups())

if __name__ == "__main__":
    usage = "usage: %prog [options] tweets.jsonl"
    parser = optparse.OptionParser(usage)
    parser.add_option('--save', action='store_true', dest='save', 
        help='Save tweet at Internet Archive if not archived')
    parser.add_option('--force-save', action='store_true', dest='force_save',
        help='Always save at Internet Archive, whether it is archived already or not')
    parser.add_option('--sleep', dest='sleep', type='int', default=1,
        help='Time to sleep between requests to Internet Archive')

    (opts, args) = parser.parse_args()
    main(args, save=opts.save, force_save=opts.force_save, sleep=opts.sleep)
