#!/usr/bin/env python

"""
A sample JSON to CSV program. Multivalued JSON properties are space delimited 
CSV columns. If you'd like it adjusted send a pull request!
"""

import sys
import json
import codecs
import argparse
import fileinput

if sys.version_info[0] < 3:
    try:
        import unicodecsv as csv
    except ImportError:
        sys.exit("unicodecsv is required for python 2")
else:
    import csv

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o', help='write output to file instead of stdout')
    parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
    args = parser.parse_args()

    if args.output:
        sheet = csv.writer(codecs.open(args.output, 'wb', 'utf-8'))
    else:
        sheet = csv.writer(sys.stdout)

    sheet.writerow(get_headings())

    files = args.files if len(args.files) > 0 else ('-',)
    for line in fileinput.input(files, openhook=fileinput.hook_encoded("utf-8")):

        tweet = json.loads(line)
        sheet.writerow(get_row(tweet))

def get_headings():
    return [
      'id',
      'tweet_url',
      'created_at',
      'user_screen_name',
      'text',
      'coordinates',
      'hashtags',
      'media',
      'urls',
      'favorite_count',
      'in_reply_to_screen_name',
      'in_reply_to_status_id',
      'in_reply_to_user_id',
      'lang',
      'place',
      'possibly_sensitive',
      'retweet_count',
      'reweet_id',
      'retweet_screen_name',
      'source',
      'user_id',
      'user_created_at',
      'user_default_profile_image',
      'user_description',
      'user_favourites_count',
      'user_followers_count',
      'user_friends_count',
      'user_listed_count',
      'user_location',
      'user_name',
      'user_statuses_count',
      'user_time_zone',
      'user_urls',
      'user_verified',
    ]

def get_row(t):
    get = t.get
    user = t.get('user').get
    row = [
      get('id_str'),
      tweet_url(t),
      get('created_at'),
      user('screen_name'),
      text(t),
      coordinates(t),
      hashtags(t),
      media(t),
      urls(t),
      get('favorite_count'),
      get('in_reply_to_screen_name'),
      get('in_reply_to_status_id'),
      get('in_reply_to_user_id'),
      get('lang'),
      place(t),
      get('possibly_sensitive'),
      get('retweet_count'),
      retweet_id(t),
      retweet_screen_name(t),
      get('source'),
      user('id_str'),
      user('created_at'),
      user('default_profile_image'),
      user('description'),
      user('favourites_count'),
      user('followers_count'),
      user('friends_count'),
      user('listed_count'),
      user('location'),
      user('name'),
      user('statuses_count'),
      user('time_zone'),
      user_urls(t),
      user('verified'),
    ]
    return row

def text(t):
    if 'full_text' in t:
        return t['full_text']
    return t['text']

def coordinates(t):
    if 'coordinates' in t and t['coordinates']:
        return '%f %f' % tuple(t['coordinates']['coordinates'])
    return None

def hashtags(t):
    return ' '.join([h['text'] for h in t['entities']['hashtags']])

def media(t):
    if 'extended_entities' in t and 'media' in t['extended_entities']:
        return ' '.join([h['expanded_url'] for h in t['extended_entities']['media']])
    elif 'media' in t['entities']: 
        return ' '.join([h['expanded_url'] for h in t['entities']['media']])
    else:
        return None

def urls(t):
    return ' '.join([h['expanded_url'] or '' for h in t['entities']['urls']])

def place(t):
    if t['place']:
        return t['place']['full_name']

def retweet_id(t):
    if 'retweeted_status' in t and t['retweeted_status']:
        return t['retweeted_status']['id_str']

def retweet_screen_name(t):
    if 'retweeted_status' in t and t['retweeted_status']:
        return t['retweeted_status']['user']['screen_name']

def tweet_url(t):
    return "https://twitter.com/%s/status/%s" % (t['user']['screen_name'], t['id_str'])

def user_urls(t):
    u = t.get('user')
    if not u:
        return None
    urls = []
    if 'entities' in u and 'url' in u['entities'] and 'urls' in u['entities']['url']:
        for url in u['entities']['url']['urls']:
            if url['expanded_url']:
                urls.append(url['expanded_url'])
    return ' '.join(urls)


if __name__ == "__main__":
    main()
