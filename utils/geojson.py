#!/usr/bin/env python

import json
import fileinput
import dateutil.parser

latitude = []
longitude = []
name = []
screen_name = []

for line in fileinput.input():
    tweet = json.loads(line)
    if tweet["geo"]:
      longitude.append(tweet["geo"]["coordinates"][0])
      latitude.append(tweet["geo"]["coordinates"][1])
      name.append((tweet["user"]["name"]).encode('utf-8'))
      screen_name.append((tweet["user"]["screen_name"]).encode('utf-8'))

i = 0
features = [] 
while i < len(name):
  feature = {"geometry" : {
    "coordinates" : [
      latitude[i],
      longitude[i]
      ],
    "type" : "Point"
    },
    "type" : "Feature",
    "properties" : {
      "Name" : name[i],
      "Screen name" : screen_name[i]
      }
    }
  features.append(feature)
  i = i + 1

geojson = ({ "features" : features, "type" : "FeatureCollection" })
print(json.dumps(geojson, indent=2))
