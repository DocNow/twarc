#!/usr/bin/env python3

"""
oembeds.py will read a stream of tweet JSON and augment .entities.urls with oembed
metadata for the URL. It uses the oembedders python module and a sqlite database 
to prevent multiple lookups for the same URL. Here's an example of how each URL
stanza will be augmented:

{
  "url": "https://t.co/ZX6cE5Xbti",
  "expanded_url": "https://www.youtube.com/watch?v=ybvmu7kM8z0",
  "display_url": "youtube.com/watch?v=ybvmu7…",
  "indices": [
    106,
    129
  ],
  "oembed": {
    "html": "<iframe width=\"480\" height=\"270\" src=\"https://www.youtube.com/embed/ybvmu7kM8z0?fea
ture=oembed\" frameborder=\"0\" allow=\"accelerometer; autoplay; encrypted-media; gyroscope; picture-
in-picture\" allowfullscreen></iframe>",
    "thumbnail_url": "https://i.ytimg.com/vi/ybvmu7kM8z0/hqdefault.jpg",
    "thumbnail_height": 360,
    "width": 480,
    "thumbnail_width": 480,
    "provider_url": "https://www.youtube.com/",
    "type": "video",
    "version": "1.0",
    "title": "Obama knew",
    "provider_name": "YouTube",
    "author_url": "https://www.youtube.com/channel/UCAql2DyGU2un1Ei2nMYsqOA",
    "author_name": "Donald J Trump",
    "height": 270
  }
}

Hopefully your URL won't be political propaganda from a tyrant like this one.
"""

import json
import logging
import sqlite3
import fileinput

from oembedders import embed

def main():
    db = OEmbeds()
    for line in fileinput.input():
        tweet = json.loads(line)
        for ent in tweet['entities']['urls']:
            url = ent.get('unshortened_url') or ent['expanded_url']
            if 'twitter.com' in url:
                continue
            meta, exists = db.get(url)
            if not exists:
                try:
                    meta = embed(url)
                    db.put(url, meta)
                except Exception as e:
                    logging.warn("error while looking up %s: %s", url, e)
            if meta:
                ent['oembed'] = meta
        print(json.dumps(tweet))


class OEmbeds:

    def __init__(self, path="oembeds.db"):
        self.db = sqlite3.connect(path)
        self.db.execute(
            """
            CREATE table IF NOT EXISTS oembeds (
              url text PRIMARY KEY,
              oembed text NOT NULL
            )
            """
        )

    def put(self, url, metadata):
        s = json.dumps(metadata)
        self.db.execute("INSERT INTO oembeds VALUES(?, ?)", [url, s])
        self.db.commit()

    def get(self, url):
        cursor = self.db.execute("SELECT oembed FROM oembeds WHERE url=?", [url])
        result = cursor.fetchone()
        if result is not None:
            return json.loads(result[0]), True
        else:
            return None, False


if __name__ == "__main__":
    main()
