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
import time
import argparse
import logging
import fileinput
import youtube_dl
import multiprocessing as mp

from urllib.parse import urlparse
from datetime import datetime, timedelta
from youtube_dl.utils import match_filter_func

parser = argparse.ArgumentParser(description='Download videos in Twitter data.')
parser.add_argument('--max-downloads', type=int, help='max downloads per URL')
parser.add_argument('--max-filesize', type=int, help='max filesize to download (bytes)')
parser.add_argument('--ignore-livestreams', action='store_true', default=False)
parser.add_argument('--download-dir', type=str, help='directory to download to', default='youtubedl')
parser.add_argument('--block', action='append', help='hostnames to block')
parser.add_argument('--timeout', type=int, default=0, help='timeout download after n seconds')
parser.add_argument('files', action='append', help='json files to parse')
args = parser.parse_args()

# make download directory
download_dir = args.download_dir
if not os.path.isdir(download_dir):
    os.mkdir(download_dir)

# setup logger
log_file = "{}/youtube.log".format(download_dir)
logging.basicConfig(filename=log_file, level=logging.INFO)
log = logging.getLogger()

# setup youtube_dl config
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
    "outtmpl": "{}/%(extractor)s/%(id)s/%(title)s.%(ext)s".format(download_dir),
    "download_archive": "{}/archive.txt".format(download_dir)
}
if args.max_downloads:
    ydl_opts['max_downloads'] = args.max_downloads
if args.max_filesize:
    ydl_opts['max_filesize'] = args.max_filesize

# keep track of domains to block
blocklist = []
if args.block:
    blocklist = args.block

# read in existing mapping file to know which urls we can ignorej
seen = set()
mapping_file = os.path.join(download_dir, 'mapping.tsv')
if os.path.isfile(mapping_file):
    for line in open(mapping_file):
        url, path = line.split('\t')
        log.info('found %s in %s', url, mapping_file)
        seen.add(url)
results = open(mapping_file, 'a')

# a function to do the download
def download(url, q):
    try:
        ydl = youtube_dl.YoutubeDL(ydl_opts)
        info = ydl.extract_info(url)
        if info:
            filename = ydl.prepare_filename(info)
            log.info('downloaded %s as %s', url, filename)
        else:
            filename = ""
            logging.warning("%s doesn't look like a video", url)
    except youtube_dl.utils.MaxDownloadsReached as e:
        logging.warning('only %s downloads per url allowed', max_downloads)

# loop through the tweets
for line in fileinput.input(args.files):
    tweet = json.loads(line)
    log.info('analyzing %s', tweet['id_str'])
    for e in tweet['entities']['urls']:
        url = e.get('expanded_url')

        # see if we can skip this one
        if not url:
            continue
        if url in seen:
            log.info('already processed %s', url)
            continue
        seen.add(url)
      
        # check for blocks
        uri = urlparse(url)
        if uri.netloc in blocklist:
            logging.warn("%s in block list", url)
            continue

        # set up a multiprocessing queue to manage the download with a timeout
        log.info('processing %s', url)
        q = mp.Queue()
        p = mp.Process(target=download, args=(url, q))
        p.start()

        started = datetime.now()
        while True:
            # if we've exceeded the timeout terminate the process
            if args.timeout and datetime.now() - started > timedelta(seconds=args.timeout):
                log.warning('reached timeout %s', args.timeout)
                p.terminate()
                break
            # if the process is done we can stop
            elif not p.is_alive():
                break
            # otherwise sleep and the check again
            time.sleep(1)

        # if the queue was empty there either wasn't a download or it timed out
        if q.empty():
            filename = ''
        else:
            filename = q.get()
      
        # write the result to the mapping file
        results.write("{}\t{}\n".format(url, filename))

