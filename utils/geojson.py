#!/usr/bin/env python
from __future__ import print_function

import sys
import json
import fileinput
import optparse
import dateutil.parser
from dateutil import tz

opt_parser = optparse.OptionParser(usage="geojson.py [options] filename")
opt_parser.add_option("-f", "--format-time", action="store_true", dest="format_time",
		        help="Format 'created_at' time as Y-%m-%d %H:%M:%S. Or pass -c option with a custom format")
opt_parser.add_option("-c", "--custom-format", dest="custom_format",
		        default='%Y-%m-%d %H:%M:%S', help="Custom format to use for'created_at' time")

opts, args = opt_parser.parse_args()

def formatTime(time, custom_format):
    to_zone = tz.tzlocal()
    created_at = dateutil.parser.parse(time)
    created_at = created_at.astimezone(to_zone)
    return created_at.strftime(custom_format)

features = []

for line in fileinput.input(sys.argv[-1]):
    tweet = json.loads(line)
    if tweet["geo"] and any(tweet["geo"]["coordinates"]):
	if opts.format_time:
            tweet["created_at"] = formatTime(tweet["created_at"], opts.custom_format)
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



