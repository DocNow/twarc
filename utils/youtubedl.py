#!/usr/bin/env python3

"""
This utility uses youtube-dl to download any videos in the tweets. Despite its name
youtube-dl is able to download video from a wide variety of websites, including
from Twitter itself. In addition to downloading the video a JSON metadata for
each video is saved as well as a WebVTT transcript if available. It writes a tab separated
mapping of URLs to filenames so that the URLs in tweets can be matched up again
with the files on disk.

    cat tweet.jsonl | utils/youtubedl.py

"""

import os
import sys
import json
import logging
import youtube_dl

from youtube_dl.utils import match_filter_func

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
    "matchfilter": match_filter_func("!is_live"),
    "outtmpl": "youtubedl/%(extractor)s/%(id)s/%(title)s.%(ext)s",
    "download_archive": "youtubedl/archive.txt"
}
ydl = youtube_dl.YoutubeDL(ydl_opts)

# TODO: configure output directory?
if not os.path.isdir('youtubedl'):
    os.mkdir('youtubedl')

results = open('youtubedl/results.tsv', 'w')
seen = set()

for line in sys.stdin:
    tweet = json.loads(line)
    logger.info('analyzing %s', tweet['id_str'])
    for e in tweet['entities']['urls']:
        url = e.get('unshortened_url') or e['expanded_url']
        if url in seen:
            logging.info('already processed %s', url)
            continue
        logging.info('processing %s', url)
        info = ydl.extract_info(url, download=True)
        if info:
            filename = ydl.prepare_filename(info)
            ydl.download([url])
            results.write("{}\t{}\n".format(url, filename))
            seen.add(url)
