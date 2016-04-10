#!/usr/bin/env python
from __future__ import print_function

import json
import fileinput
import argparse
import random

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input",
        dest="filename", required=True,
        help="Input file. Output is written to std out.")
parser.add_argument("-c", "--centroid", 
					dest="centroid", type=bool, choices=[True, False], default=False,
                    help="If True, store centroid instead of a bounding box for 'place' attribute")
parser.add_argument("-f", "--fuzz", 
					dest="fuzz", type=float, default=0,
                    help="Setting fuzz to something between 0 and 0.1 (0.01 recommended) will add a random lon and lat shift to bounding box centroids.")
args = parser.parse_args()

#Store the features in an array ready for output.
features = []

for line in fileinput.input(args.filename):
    tweet = json.loads(line)
    if tweet["geo"] and any(tweet["geo"]["coordinates"]):
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    tweet["geo"]["coordinates"][1],
                    tweet["geo"]["coordinates"][0]
                ],
            },
            "properties": {
                "name": tweet["user"]["name"],
                "screen_name": tweet["user"]["screen_name"],
                "created_at": tweet["created_at"],
                "text": tweet["text"],
                "profile_image_url": tweet["user"]["profile_image_url"],
                "url": "http://twitter.com/%s/status/%s" % (
                    tweet["user"]["screen_name"],
                    tweet["id_str"],
                )
            }
        })
    elif tweet["place"] and any(tweet["place"]["bounding_box"]):
        bbox = tweet["place"]["bounding_box"]["coordinates"][0]

        #If we want a centroid, calculate the centroid of the bounding box.
        if(args.centroid):
	        minX = bbox[0][0]
	        minY = bbox[0][1]
	        maxX = bbox[2][0]
	        maxY = bbox[2][1]
	        fuzzX = args.fuzz * random.uniform(-1,1)
	        fuzzY = args.fuzz * random.uniform(-1,1)
	        centerX = ((maxX + minX) / 2.0) + fuzzX
	        centerY = ((maxY + minY) / 2.0) + fuzzY

	        features.append({
	            "type": "Feature",
	            "geometry": {
	                "type": "Point",
	                "coordinates": [
	                    centerX,
	                    centerY
	                ],
	            },
	            "properties": {
	                "name": tweet["user"]["name"],
	                "screen_name": tweet["user"]["screen_name"],
	                "created_at": tweet["created_at"],
	                "text": tweet["text"],
	                "profile_image_url": tweet["user"]["profile_image_url"],
	                "url": "http://twitter.com/%s/status/%s" % (
	                    tweet["user"]["screen_name"],
	                    tweet["id_str"],
	                )
	            }
	        })
        #If we don't want centroids, pass through a polygon feature.
        else:
        	features.append({
	            "type": "Feature",
	            "geometry": {
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
	            },
	            "properties": {
	                "name": tweet["user"]["name"],
	                "screen_name": tweet["user"]["screen_name"],
	                "created_at": tweet["created_at"],
	                "text": tweet["text"],
	                "profile_image_url": tweet["user"]["profile_image_url"],
	                "url": "http://twitter.com/%s/status/%s" % (
	                    tweet["user"]["screen_name"],
	                    tweet["id_str"],
	                )
	            }
	        })

geojson = {"type" : "FeatureCollection", "features": features}
print(json.dumps(geojson, indent=2))