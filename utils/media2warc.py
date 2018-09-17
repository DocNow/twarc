#!/usr/bin/env python

"""
This utility extracts media urls from tweet jsonl.gz and  save them as warc records.

Warcio (https://github.com/webrecorder/warcio) is a dependency and before you can use it you need to:
% pip install warcio

You run it like this:
% python media2warc.py /mnt/tweets/ferguson/tweets-0001.jsonl.gz /mnt/tweets/ferguson/tweets-0001.warc.gz

The input file will be checked for duplicate urls to avoid duplicates within the input file. Subsequent runs
will  be deduplicated using a sqlite db.  If an identical-payload-digest is found a revist record is created.

The script is able to fetch media resources in multiple threads (maximum 2) by passing --threads <int> (default to a single thread).

Please be careful modifying this script to use more than two threads since it can be interpreted as a DoS-attack.

"""

import os
import gzip
import json
import time
import queue
import hashlib
import logging
import sqlite3
import argparse
import requests
import threading

from datetime import timedelta
from warcio.warcwriter import WARCWriter
from warcio.statusandheaders import StatusAndHeaders

q = queue.Queue()
out_queue = queue.Queue()
BLOCK_SIZE = 25600


class GetResource(threading.Thread):

    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
        self.rlock = threading.Lock()
        self.out_queue = out_queue
        self.d = Dedup()

    def run(self):
        while True:
            host = self.q.get()

            try:
                r = requests.get(host, headers={'Accept-Encoding': 'identity'}, stream=True)
                data = [r.raw.headers.items(), r.raw, host, r.status_code, r.reason]
                print(data[2])
                self.out_queue.put(data)
                self.q.task_done()

            except requests.exceptions.RequestException as e:
                logging.error('%s for %s', e, data[2])
                print(e)
                self.q.task_done()
                continue


class WriteWarc(threading.Thread):

    def __init__(self, out_queue, warcfile):
        threading.Thread.__init__(self)
        self.out_queue = out_queue
        self.lock = threading.Lock()
        self.warcfile = warcfile
        self.dedup = Dedup()

    def run(self):

        with open(self.warcfile, 'ab') as output:
            while True:
                self.lock.acquire()
                data = self.out_queue.get()
                writer = WARCWriter(output, gzip=False)
                headers_list = data[0]
                http_headers = StatusAndHeaders('{} {}'.format(data[3], data[4]), headers_list, protocol='HTTP/1.0')
                record = writer.create_warc_record(data[2], 'response', payload=data[1], http_headers=http_headers)
                h = hashlib.sha1()
                h.update(record.raw_stream.read(BLOCK_SIZE))
                if self.dedup.lookup(h.hexdigest()):
                    record = writer.create_warc_record(data[2], 'revisit',
                                                       http_headers=http_headers)
                    writer.write_record(record)
                    self.out_queue.task_done()
                    self.lock.release()
                else:
                    self.dedup.save(h.hexdigest(), data[2])
                    record.raw_stream.seek(0)
                    writer.write_record(record)
                    self.out_queue.task_done()
                    self.lock.release()

class Dedup:
    """
    Stolen from warcprox
    https://github.com/internetarchive/warcprox/blob/master/warcprox/dedup.py
    """
    def __init__(self):
        self.file = os.path.join(args.archive_dir,'dedup.db')

    def start(self):
        conn = sqlite3.connect(self.file)
        conn.execute(
            'create table if not exists dedup ('
            '  key varchar(300) primary key,'
            '  value varchar(4000)'
            ');')
        conn.commit()
        conn.close()

    def save(self, digest_key, url):
        conn = sqlite3.connect(self.file)
        conn.execute(
            'insert or replace into dedup (key, value) values (?, ?)',
            (digest_key, url))
        conn.commit()
        conn.close()

    def lookup(self, digest_key, url=None):
        result = False
        conn = sqlite3.connect(self.file)
        cursor = conn.execute('select value from dedup where key = ?', (digest_key,))
        result_tuple = cursor.fetchone()
        conn.close()
        if result_tuple:
            result = True

        return result


def parse_extended_entities(extended_entities_dict):
    """Parse media file URL:s form tweet data

    :extended_entities_dict:
    :returns: list of media file urls

    """
    urls = []

    if "media" in extended_entities_dict.keys():
        for item in extended_entities_dict["media"]:

            # add static image
            urls.append(item["media_url_https"])

            # add best quality video file
            if "video_info" in item.keys():
                max_bitrate = -1  # handle twitters occasional bitrate=0
                video_url = None
                for video in item["video_info"]["variants"]:
                    if "bitrate" in video.keys() and "content_type" in video.keys():
                        if video["content_type"] == "video/mp4":
                            if int(video["bitrate"]) > max_bitrate:
                                max_bitrate = int(video["bitrate"])
                                video_url = video["url"]

                if not video_url:
                    print("Error: No bitrate / content_type")
                    print(item["video_info"])
                else:
                    urls.append(video_url)

    return urls


def parse_binlinks_from_tweet(tweetdict):
    """Parse binary file url:s from a single tweet.

    :tweetdict: json data dict for tweet
    :returns: list of urls for media files

    """

    urls = []

    if "user" in tweetdict.keys():
        urls.append(tweetdict["user"]["profile_image_url_https"])
        urls.append(tweetdict["user"]["profile_background_image_url_https"])

    if "extended_entities" in tweetdict.keys():
        urls.extend(parse_extended_entities(tweetdict["extended_entities"]))
    return urls

def main():
    start = time.time()
    if not os.path.isdir(args.archive_dir):
        os.mkdir(args.archive_dir)

    logging.basicConfig(
        filename=os.path.join(args.archive_dir, "media_harvest.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    logging.getLogger(__name__)
    logging.info("Logging media harvest for %s", args.tweet_file)

    urls = []
    d = Dedup()
    d.start()
    uniqueUrlCount = 0
    duplicateUrlCount = 0

    if args.tweet_file.endswith('.gz'):
        tweetfile = gzip.open(args.tweet_file, 'r')
    else:
        tweetfile = open(args.tweet_file, 'r')

    logging.info("Checking for duplicate urls")

    for line in tweetfile:
        tweet = json.loads(line)
        tweet_urls = parse_binlinks_from_tweet(tweet)
        for url in tweet_urls:
            if not url in urls:
                urls.append(url)
                q.put(url)
                uniqueUrlCount +=1
            else:
                duplicateUrlCount += 1

    logging.info("Found %s total media urls %s unique and %s duplicates", uniqueUrlCount+duplicateUrlCount, uniqueUrlCount, duplicateUrlCount)

    threads = int(args.threads)

    if threads > 2:
        threads = 2

    for i in range(threads):
        t = GetResource(q)
        t.setDaemon(True)
        t.start()

    wt = WriteWarc(out_queue, os.path.join(args.archive_dir, 'warc.warc'))
    wt.setDaemon(True)
    wt.start()

    q.join()
    out_queue.join()
    logging.info("Finished media harvest in %s", str(timedelta(seconds=(time.time() - start))))

if __name__ == '__main__':
    parser = argparse.ArgumentParser("archive")
    parser.add_argument("tweet_file", action="store", help="a twitter jsonl.gz input file")
    parser.add_argument("archive_dir", action="store", help="a directory where the resulting warc is stored")
    parser.add_argument("--threads", action="store", default=1, help="Number of threads that fetches media resources")
    args = parser.parse_args()
    main()