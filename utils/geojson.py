#!/usr/bin/env python

import json
import fileinput
import dateutil.parser
import geojson

print"""
{
  "features" : [
"""

for line in fileinput.input():
    tweet = json.loads(line)
    if tweet["geo"]:
      #coordinates = geojson.Point(tweet["geo"]["coordinates"])
      latitude = (tweet["geo"]["coordinates"][0])
      longitude = (tweet["geo"]["coordinates"][1])
      name = (tweet["user"]["name"]).encode('utf-8')
      screen_name = (tweet["user"]["screen_name"]).encode('utf-8')
      print """
      {
        "geometry" : {
          "coordinates" : [
            "%s",
            "%s"
            ],
          "type" : "Point"
        },
        "type" : "Feature",
        "properties" : {
          "Name" : "%s",
          "Screen name" : "%s"
        }
      },""" % (latitude, longitude, name, screen_name)
print """
  ],
  "type" : "FeatureCollection"
}"""
