#!/usr/bin/env python

import sys

from dateutil.parser import parse as date_parse
from six import string_types

if sys.version_info[0] < 3:
    try:
        import unicodecsv as csv
    except ImportError:
        sys.exit("unicodecsv is required for python 2")
else:
    import csv


def get_headings():
    return [
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
      'retweet_or_quote_id',
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


def get_row(t, excel=False):
    get = t.get
    user = t.get('user').get
    return [
      get('id_str'),
      tweet_url(t),
      get('created_at'),
      date_parse(get('created_at')),
      user('screen_name'),
      text(t) if not excel else clean_str(text(t)),
      tweet_type(t),
      coordinates(t),
      hashtags(t),
      media(t),
      urls(t),
      favorite_count(t),
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
      user('description') if not excel else clean_str(user('description')),
      user('favourites_count'),
      user('followers_count'),
      user('friends_count'),
      user('listed_count'),
      user('location') if not excel else clean_str(user('location')),
      user('name') if not excel else clean_str(user('name')),
      user('statuses_count'),
      user('time_zone'),
      user_urls(t),
      user('verified'),
    ]


def clean_str(string):
    if isinstance(string, string_types):
        return string.replace('\n', ' ').replace('\r', '')
    return None


def text(t):
    # need to look at original tweets for retweets for full text
    if t.get('retweeted_status'):
        t = t.get('retweeted_status')

    if 'extended_tweet' in t:
        return t['extended_tweet']['full_text']
    elif 'full_text' in t:
        return t['full_text']
    else:
        return t['text']


def coordinates(t):
    if 'coordinates' in t and t['coordinates']:
        return '%f %f' % tuple(t['coordinates']['coordinates'])
    return None


def hashtags(t):
    # If it's a retweet, the hashtags might be cutoff in the retweet object, so check
    # the enclosed original tweet for the full list.
    if 'retweeted_status' in t:
        hashtags = t['retweeted_status']['entities']['hashtags']
    else:
        hashtags = t['entities']['hashtags']
    
    return ' '.join(h['text'] for h in hashtags)


def media(t):
    if 'extended_entities' in t and 'media' in t['extended_entities']:
        return ' '.join([h['media_url_https'] for h in t['extended_entities']['media']])
    elif 'media' in t['entities']: 
        return ' '.join([h['media_url_https'] for h in t['entities']['media']])
    else:
        return None


def urls(t):
    return ' '.join([h['expanded_url'] or '' for h in t['entities']['urls']])


def place(t):
    if 'place' in t and t['place']:
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
    
def favorite_count(t):
    if 'retweeted_status' in t and t['retweeted_status']:
        return t['retweeted_status']['favorite_count']
    else:
        return t['favorite_count']

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

