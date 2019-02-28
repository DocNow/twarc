#!/usr/bin/env python

"""
Print out the URLs of images uploaded to Twitter in a tweet json stream.
Useful for piping to wget or curl to mass download. In Bash:

% wget $(./utils/image_urls.py tweets.jsonl)
"""
from __future__ import print_function

import json
import fileinput

for line in fileinput.input(openhook=fileinput.hook_encoded("utf8")):
    tweet = json.loads(line)
    id = tweet['id_str']

    if 'media' in tweet['entities']:
        for media in tweet['entities']['media']:
            if media['type'] == 'photo':
                print(id, media['media_url_https'])

    if 'extended_entities' in tweet and 'media' in tweet['extended_entities']:
        for media in tweet['extended_entities']['media']:

            if media['type'] == 'animated_gif':
                print(id, media['media_url_https'])

            if 'video_info' in media:
                for v in media['video_info']['variants']:
                    print(id, v['url'])
