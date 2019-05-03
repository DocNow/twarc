#!/usr/bin/env python3

"""
Uses youtube-dl to download any videos in the tweets. It writes a tab separated mapping of 
URLs to filenames. 
"""

import sys
import json
import urllib
import logging
import fileinput
import youtube_dl

from urllib.parse import urlparse

logging.basicConfig(filename='youtubedl.log', level=logging.INFO)
logger = logging.getLogger()

ydl_opts = {
    "format": "best",
    "logger": logger,
    "restrictfilenames": True,
    "ignoreerrors": True,
    "nooverwrites": True,
    "writedescription": True,
    "writeinfojson": True,
    "writesubtitles": True,
    "writeautomaticsub": True,
    "outtmpl": "youtubedl/%(extractor)s/%(title)s.%(ext)s",
    "download_archive": "youtubedl/archive.txt"
}
ydl = youtube_dl.YoutubeDL(ydl_opts)

results = open('youtubedl/results.tsv', 'w')

for line in sys.stdin:
    tweet = json.loads(line)
    for e in tweet['entities']['urls']:
        url = e.get('unshortened_url') or e['expanded_url']
        info = ydl.extract_info(url, download=True)
        if info:
            filename = ydl.prepare_filename(info)
            ydl.download([url])
            results.write("{}\t{}\n".format(url, filename))
