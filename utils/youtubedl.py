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
log = logging.getLogger()

# TODO: make these configurable with cli options
max_downloads = 5
max_filesize = 100 * 1024 * 1024
output_dir = 'youtubedl'

ydl_opts = {
    "format": "best",
    "logger": log,
    "restrictfilenames": True,
    "ignoreerrors": True,
    "nooverwrites": True,
    "writedescription": True,
    "writeinfojson": True,
    "writesubtitles": True,
    "writeautomaticsub": True,
    "matchfilter": match_filter_func("!is_live"),
    "outtmpl": "youtubedl/%(extractor)s/%(id)s/%(title)s.%(ext)s",
    "download_archive": "youtubedl/archive.txt",
    "max_filesize": max_filesize,
    "max_downloads": max_downloads
}

if not os.path.isdir(output_dir):
    os.mkdir(output_dir)

seen = set()
mapping_file = os.path.join(output_dir, 'mapping.tsv')

if os.path.isfile(mapping_file):
    for line in open(mapping_file):
        url, path = line.split('\t')
        log.info('found %s in %s', url, mapping_file)
        seen.add(url)

results = open(mapping_file, 'a')

for line in sys.stdin:
    tweet = json.loads(line)
    log.info('analyzing %s', tweet['id_str'])
    for e in tweet['entities']['urls']:
        url = e.get('unshortened_url') or e['expanded_url']
        if not url:
            continue
        if url in seen:
            log.info('already processed %s', url)
            continue
        seen.add(url)
        log.info('processing %s', url)
        try:
            ydl = youtube_dl.YoutubeDL(ydl_opts)
            info = ydl.extract_info(url)
            if info:
                filename = ydl.prepare_filename(info)
                log.info('downloaded %s as %s', url, filename)
            else:
                filename = ""
                logging.warn("%s doesn't look like a video", url)
            results.write("{}\t{}\n".format(url, filename))
        except youtube_dl.utils.MaxDownloadsReached as e:
            logging.warn('only %s downloads per url allowed', max_downloads)
