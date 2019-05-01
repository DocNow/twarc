#!/usr/bin/env python3

import json
import plyvel
import fileinput

from oembedders import embed

def main():
    db = plyvel.DB('oembeds.db', create_if_missing=True)
    for line in fileinput.input():
        tweet = json.loads(line)
        for ent in tweet['entities']['urls']:
            url = ent.get('unshortened_url') or ent['expanded_url']
            meta = db.get(url)
            if not meta:
                meta = embed(url)
                db.put(url, meta)
            if meta:
                url['ombed'] = meta
        print(json.dumps(tweet), end='')

if __name__ == "__main__":
    main()
