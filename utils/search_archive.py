#!/usr/bin/env python

import twarc
import argparse

def main():
    parser = argparse.ArgumentParser("search_archive")
    parser.add_argument("search", dest="search", action="store",
                        help="search for tweets matching a query")
    parser.add_argument("archive_dir", dest="archive_dir", action="store",
                        help="place where twitter files are kept")
    args = parser.parse_args()

    if not os.path.isdir(args.archive_dir):
        print "no such directory: %s" % args.archive_dir

    logging.basicConfig(
        filename=os.path.join(args.archive_log, "search_archive.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    max_id_archived, filename = inspect(args.archive_dir)
    fh = open(filename, "w")

    t = Twarc()
    for tweet in t.search(args.search, min_id=max_id_archived):
        logging.info("archived %s", tweet["id_str"])
        fw.write(json.dumps(tweet))

if __name__ == "__main__":
    main()


