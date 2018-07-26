#!/usr/bin/env python
"""
Filters tweets posted by a list of users.

The list is supplied in a file. The file can contain:
* screen names
* user ids
* screen name,user id
* user id,screen name
where each appears on a separate line.

When a user id is provided, it will be used. Otherwise, screen name
will be used.

There is also an option to filter by tweets NOT posted by the list of users.
"""

import argparse
import fileinput
import json
import logging


def read_user_list_file(user_list_filepath):
    screen_names = set()
    user_ids = set()

    with open(user_list_filepath) as f:
        for count, line in enumerate(f):
            split_line = line.rstrip('\n\r').split(',')
            if _is_header(count, split_line):
                continue
            if split_line[0].isdigit():
                user_ids.add(split_line[0])
            else:
                screen_names.add(split_line[0])
                if len(split_line) > 1 and split_line[1].isdigit():
                    user_ids.add(split_line[1])

    assert screen_names or user_ids
    return user_ids, screen_names


def _is_header(count, split_line):
    # If this is first line and there is more than one part and none are all digit, then a header
    if count == 0:
        for part in split_line:
            if part.isdigit():
                return False
        return True
    return False


def main(files, user_ids, screen_names, positive_match=True):
    for count, line in enumerate(fileinput.input(files=files)):
        try:
            tweet = json.loads(line.rstrip('\n'))
            match = False
            if user_ids and tweet['user']['id_str'] in user_ids:
                match = True
            elif tweet['user']['screen_name'] in screen_names:
                match = True

            if not positive_match:
                match = not match

            if match:
                print(line.rstrip('\n'))

            if count % 100000 == 0:
                logging.info("processed {:,} tweets".format(count))

        except json.decoder.JSONDecodeError:
            pass


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    parser = argparse.ArgumentParser()
    parser.add_argument('--neg-match', action='store_true', help='Return tweets that do not match users')
    parser.add_argument('user_list_file', help='file containing list of users to filter tweets by')
    parser.add_argument('tweet_files', metavar='FILE', nargs='*', help='file containing tweets to filter, if empty, '
                                                                       'stdin is used')
    args = parser.parse_args()
    m_user_ids, m_screen_names = read_user_list_file(args.user_list_file)
    main(args.tweet_files if len(args.tweet_files) > 0 else ('-',), m_user_ids, m_screen_names,
         positive_match=not args.neg_match)
