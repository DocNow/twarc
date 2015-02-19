#!/usr/bin/env python
from __future__ import print_function

import json
import fileinput

features = []

for line in fileinput.input():
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

geojson = {"type" : "FeatureCollection", "features": features}
print(json.dumps(geojson, indent=2))
