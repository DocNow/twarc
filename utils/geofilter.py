#!/usr/bin/env python

from __future__ import print_function

import argparse
import json
import sys

from shapely.geometry import shape


def process(line, has_coordinates=None, has_place=None, fence=None):
    tweet = json.loads(line)

    coordinates = tweet.get('coordinates')
    place = tweet.get('place')

    if any([
        has_coordinates and not coordinates,
        has_coordinates is False and coordinates,
        has_place and not place,
        has_place is False and place,
    ]):
        return

    if fence and (coordinates or place):
        if coordinates:
            location = shape(coordinates)
        else:
            location = shape(place['bounding_box'])

        if not fence.contains(location):
            return

    print(line.strip('\n'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin)
    parser.add_argument('--yes-coordinates', dest='has_coordinates',
                        action='store_true')
    parser.add_argument('--no-coordinates', dest='has_coordinates',
                        action='store_false')
    parser.add_argument('--yes-place', dest='has_place', action='store_true')
    parser.add_argument('--no-place', dest='has_place', action='store_false')
    parser.add_argument('--fence', default=None,
                        help='geojson file with geofence')
    parser.set_defaults(has_coordinates=None, has_place=None)
    args = parser.parse_args()

    fence = None
    if args.fence:
        with open(args.fence, 'r') as f:
            fence = shape(json.loads(f.read()))

    for line in args.infile:
        process(line, args.has_coordinates, args.has_place, fence)


if __name__ == '__main__':
    main()
