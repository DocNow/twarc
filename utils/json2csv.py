#!/usr/bin/env python

"""
A sample JSON to CSV program. Multivalued JSON properties are space delimited 
CSV columns. If you'd like it adjusted send a pull request!
"""

import os
import sys
import json
import codecs
import argparse
import fileinput
from dateutil.parser import parse as date_parse

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
    parser.add_argument('--split', '-s', help='if writing to file, split into multiple files with this many lines per '
                                              'file', type=int, default=0)
    parser.add_argument('--extra-field', '-e', help='extra fields to include. Provide a field name and a pointer to '
                                                    'the field. Example: -e verified user.verified',
                        nargs=2, action='append')
    parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
    args = parser.parse_args()

    file_count = 1
    csv_file = None
    if args.output:
        if args.split:
            csv_file = codecs.open(numbered_filepath(args.output, file_count), 'wb', 'utf-8')
            file_count += 1
        else:
            csv_file = codecs.open(args.output, 'wb', 'utf-8')
    else:
        csv_file = sys.stdout
    sheet = csv.writer(csv_file)

    extra_headings = []
    extra_fields = []
    if args.extra_field:
        for heading, field in args.extra_field:
            extra_headings.append(heading)
            extra_fields.append(field)

    sheet.writerow(get_headings(extra_headings=extra_headings))

    files = args.files if len(args.files) > 0 else ('-',)
    for count, line in enumerate(fileinput.input(files, openhook=fileinput.hook_encoded("utf-8"))):
        if args.split and count and count % args.split == 0:
            csv_file.close()
            csv_file = codecs.open(numbered_filepath(args.output, file_count), 'wb', 'utf-8')
            sheet = csv.writer(csv_file)
            sheet.writerow(get_headings(extra_headings=extra_headings))
            file_count += 1
        tweet = json.loads(line)
        sheet.writerow(get_row(tweet, extra_fields=extra_fields))


def numbered_filepath(filepath, num):
    path, ext = os.path.splitext(filepath)
    return os.path.join('{}-{:0>3}{}'.format(path, num, ext))


def get_headings(extra_headings=None):
    fields = [
      'id',
      'tweet_url',
      'created_at',
      'parsed_created_at',
      'user_screen_name',
      'text',
      'tweet_type',
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
      'reweet_or_quote_id',
      'retweet_or_quote_screen_name',
      'retweet_or_quote_user_id',
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
    if extra_headings:
        fields.extend(extra_headings)
    return fields


def get_row(t, extra_fields=None):
    get = t.get
    user = t.get('user').get
    row = [
      get('id_str'),
      tweet_url(t),
      get('created_at'),
      date_parse(get('created_at')),
      user('screen_name'),
      text(t),
      tweet_type(t),
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
      retweet_user_id(t),
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
    for field in extra_fields:
        row.append(extra_field(t, field))
    return row


def text(t):
    return (t.get('full_text') or t.get('extended_tweet', {}).get('full_text') or t['text']).replace('\n', ' ')


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
    elif 'quoted_status' in t and t['quoted_status']:
        return t['quoted_status']['id_str']


def retweet_screen_name(t):
    if 'retweeted_status' in t and t['retweeted_status']:
        return t['retweeted_status']['user']['screen_name']
    elif 'quoted_status' in t and t['quoted_status']:
        return t['quoted_status']['user']['screen_name']


def retweet_user_id(t):
    if 'retweeted_status' in t and t['retweeted_status']:
        return t['retweeted_status']['user']['id_str']
    elif 'quoted_status' in t and t['quoted_status']:
        return t['quoted_status']['user']['id_str']


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


def tweet_type(t):
    # Determine the type of a tweet
    if t.get('in_reply_to_status_id'):
        return 'reply'
    if 'retweeted_status' in t:
        return 'retweet'
    if 'quoted_status' in t:
        return 'quote'
    return 'original'

def extra_field(t, field_str):
    obj = t
    for field in field_str.split('.'):
        if field in obj:
            obj = obj[field]
        else:
            return None
    return obj

if __name__ == "__main__":
    main()
