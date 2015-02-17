#!/bin/bash
# -e: script exits as soon as a command returns a non-zero exit code
# -v: verbose.
set -ev

# Run the utils scripts

# Output isn't verified, this is just a quick test to ensure they can run

# First hydrate some IDs into tweets
python twarc.py --hydrate test/ids.txt > tweets.json

# Now test utils
utils/wall.py tweets.json > tweets.html
utils/wordcloud.py tweets.json > wordcloud.html
# utils/gender.py --gender female tweets.json | utils/wordcloud.py > tweets-female.html
utils/geojson.py tweets.json > tweets.geojson
utils/deduplicate.py tweets.json > deduped.json
utils/sort_by_id.py tweets.json > sorted.json
utils/filter_date.py --mindate 1-may-2014 tweets.json > filtered.json
utils/source.py tweets.json > sources.html
utils/noretweets.py tweets.json > tweets_noretweets.json
# cat tweets.json | utils/unshorten.py > unshortened.json
# cat unshortened.json | utils/urls.py | sort | uniq -c | sort -n > urls.txt
