#!/usr/bin/env python

"""
geojson.py reads in tweets and writes out a corresponding geojson file for the
tweets. Each feature will include the following properties:

* twitter user name
* twitter user screename
* tweet creation time
* tweet status text
* profile image url
* the tweet url

By default both Point and Polygon features will be included, depending on
whether the tweet includes a point or is assigned to a place with a bounding
box.

Optionally you can convert bounding boxes to points with the --centroid
parameter, and can also use --fuzz to randomly place the the point inside the
bounding box.
"""

from __future__ import print_function

import json
import random
import argparse
import fileinput
import dateutil.parser

def text(t):
    return (t.get('full_text') or t.get('extended_tweet', {}).get('full_text') or t['text']).replace('\n', ' ')

parser = argparse.ArgumentParser()

parser.add_argument(
    "-c", 
    "--centroid", 
    dest="centroid",
    action='store_true',
    default=False,
    help="store centroid instead of a bounding box"
)

parser.add_argument(
    "-f", "--fuzz", 
    type=float, 
    dest="fuzz", 
    default=0,
    help="add a random lon and lat shift to bounding box centroids (0-0.1)"
)

parser.add_argument(
    'files',
    nargs='*',
    default=("-",),
    help='files to read, if empty, stdin is used'
)


args = parser.parse_args()

features = []

for line in fileinput.input(files=args.files):
    tweet = json.loads(line)
    t = dateutil.parser.parse(tweet['created_at'])

    f = {
        "type": "Feature",
        "properties": {
            "name": tweet["user"]["name"],
            "screen_name": tweet["user"]["screen_name"],
            "created_at": t.isoformat("T") + "Z",
            "text": text(tweet),
            "profile_image_url": tweet["user"]["profile_image_url"],
            "url": "http://twitter.com/%s/status/%s" % (
                tweet["user"]["screen_name"],
                tweet["id_str"]
            )
        }
    }
    
    if tweet["geo"]:
        f['geometry'] = {
            "type": "Point",
            "coordinates": [
                tweet["geo"]["coordinates"][1],
                tweet["geo"]["coordinates"][0]
            ]
        }

    elif tweet["place"] and any(tweet["place"]["bounding_box"]):
        bbox = tweet["place"]["bounding_box"]["coordinates"][0]

        if args.centroid:
            min_x = bbox[0][0]
            min_y = bbox[0][1]
            max_x = bbox[2][0]
            max_y = bbox[2][1]

            fuzz_x = args.fuzz * random.uniform(-1,1)
            fuzz_y = args.fuzz * random.uniform(-1,1)

            center_x = ((max_x + min_x) / 2.0) + fuzz_x
            center_y = ((max_y + min_y) / 2.0) + fuzz_y

            f['geometry'] = {
                "type": "Point",
                "coordinates": [
                    center_x,
                    center_y
                ]
            }

        else:
            f['geometry'] = {
                "type": "Polygon",
                "coordinates": [
                    [
                        bbox[0],
                        bbox[1],
                        bbox[2],
                        bbox[3],
                        bbox[0]
                    ]
                ],
            }

    if 'geometry' in f:
        features.append(f)

geojson = {"type" : "FeatureCollection", "features": features}
print(json.dumps(geojson, indent=2))
