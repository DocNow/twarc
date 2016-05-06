twarc
=====

[![Build Status](https://secure.travis-ci.org/edsu/twarc.png)](http://travis-ci.org/edsu/twarc) 
[![Gitter](https://badges.gitter.im/Join Chat.svg)](https://gitter.im/edsu/twarc?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![DOI](https://zenodo.org/badge/12737/edsu/twarc.svg)](http://dx.doi.org/10.5281/zenodo.17385)

twarc is a command line tool and Python library for archiving Twitter JSON
data. Each tweet is represented as a JSON object that is exactly what was 
returned from the Twitter API. Tweets are stored as line-oriented JSON. Twarc runs in three modes: search, filter stream and hydrate. When running in 
each mode twarc will stop and resume activity in order to work within the 
Twitter API's [rate limits](https://dev.twitter.com/rest/public/rate-limiting).

## Install

1. install [Python](http://python.org/download) (2 or 3)
1. pip install twarc

## Twitter API Keys

Before using twarc you will need to register an application at
[apps.twitter.com](http://apps.twitter.com). Once you've created your
application, note down the consumer key, consumer secret and then click to
generate an access token and access token secret. With these four variables
in hand you are ready to start using twarc. 

The first time you run twarc it will prompt you for these keys and store them 
in a `.twarc` file in your home directory. Sometimes it can be handy to store
multiple authorization keys for different Twitter accounts in your config
file.  So if you can have multiple profiles to your `.twarc` file, for 
example:

    [main]
    consumer_key=lksdfljklksdjf
    consumer_secret=lkjsdflkjsdlkfj
    access_token=lkslksjksljk3039jklj
    access_token_secret=lksdjfljsdkjfsdlkfj 

    [another]
    consumer_key=lkjsdflsj
    consumer_secret=lkjsdflkj
    access_token=lkjsdflkjsdflkjj
    access_token_secret=lkjsdflkjsdflkj

You then use the other profile with the `--profile` option:

    twarc.py --profile another --search ferguson

twarc will also look for authentication keys in the environment if you 
would prefer to set them there using the following names:

* CONSUMER\_KEY
* CONSUMER\_SECRET
* ACCESS\_TOKEN
* ACCESS\_TOKEN\_SECRET

And finally you can pass the authorization keys as arguments to twarc:

    twarc.py --consumer_key foo --consumer_secret bar --access_token baz --access_token_secret bez --search ferguson

## Search

When running in search mode twarc will use Twitter's [search
API](https://dev.twitter.com/rest/reference/get/search/tweets) to retrieve as
many tweets it can find that match a particular query. So for example, to collect all the tweets mentioning the keyword "ferguson" you would:

    twarc.py --search ferguson > tweets.json

This command will walk through each page of the search results and write
each tweet to stdout as line oriented JSON. Twitter's search API only makes
(roughly) the last week's worth of Tweets available via its search API, so
time is of the essence if you are trying to collect tweets for something
that has already happened.

## Filter Stream

In filter stream mode twarc will listen to Twitter's [filter stream API](https://dev.twitter.com/streaming/reference/post/statuses/filter) for
tweets that match a particular filter. You can filter by keywords using
`--track`, user identifiers using `--follow` and places using `--locations`. 
Similar to search mode twarc will write these tweets to stdout as line 
oriented JSON:

### Stream tweets containing a keyword

    twarc.py --track "ferguson,blacklivesmatter" > tweets.json

### Stream tweets from/to users

Note: you must use the user identifiers, for example these are the 
user ids for the @guardian and @nytimes:

    twarc.py --follow "87818409,807095" > tweets.json

### Stream tweets from a location

Note: the leading dash needs to be escaped in the bounding box
or else it will be interpreted as a command line argument!

    twarc.py --locations "\-74,40,-73,41" > tweets.json

Note the syntax for the Twitter's filter queries is slightly different than what queries in their search API. So please consult the [documentation](https://dev.twitter.com/streaming/reference/post/statuses/filter) on how best to express the filter option you are using. Note: the options can be combined, which has the effect of a boolean `or`.

## Hydrate

The Twitter API's [Terms of Service](https://dev.twitter.com/overview/terms/policy#6._Be_a_Good_Partner_to_Twitter)
prevent people from making large amounts of raw Twitter data available on the
Web. The data can be used for research and archived for local use, but not
shared with the world. Twitter does allow files of tweet identifiers to be
shared, which can be useful when you would like to make a dataset of tweets
available. You can then use Twitter's API to *hydrate* the data, or to retrieve
the full JSON for each identifier. This is particularly important for
[verification](https://en.wikipedia.org/wiki/Reproducibility) of social media
research.

In hydrate mode twarc will read a file of tweet identifiers and use Twitter's
[lookup](https://dev.twitter.com/rest/reference/get/statuses/lookup) API to
fetch the full JSON for each tweet and write it to stdout as line-oriented JSON:

    twarc.py --hydrate ids.txt > tweets.json

## Archive

In addition to `twarc.py` when you install twarc you will also get the 
`twarc-archive.py` command line tool. This uses twarc as a library to
periodically collect data matching a particular search query. It's useful if you
don't necessarily want to collect tweets as they happen with the streaming
api, and are content to run it periodically from cron to collect what you can.
You will want to adjust the schedule so that it at least runs every 7 days (the
search API window), and often enough to match the volume of tweets being
collected. The script will keep the files organized, and is smart enough to
use the most recent file to determine when it can stop collecting so there are
no duplicates.

For example this will collect all the tweets mentioning the word "ferguson" from
the search API and write them to a unique file in `/mnt/tweets/ferguson`.

    twarc-archive.py ferguson /mnt/tweets/ferguson 

## Use as a Library

If you want you can use twarc programmatically as a library to collect
tweets. You first need to create a `Twarc` instance (using your Twitter
credentials), and then use it to iterate through search results, filter
results or lookup results.

```python
from twarc import Twarc

t = Twarc(consumer_key, consumer_secret, access_token, access_token_secret)
for tweet in t.search("ferguson"):
    print(tweet["text"])
```

You can do the same for a filter stream of new tweets that match a track
keyword

```python
for tweet in t.filter(track="ferguson"):
    print(tweet["text"])
```

or location:

```python
for tweet in t.filter(locations="-74,40,-73,41"):
    print(tweet["text"])
```

or user ids:

```python
for tweet in t.filter(follow='12345,678910'):
    print(tweet["text"])
```

Similarly you can hydrate tweet identifiers by passing in a list of ids
or a generator:

```python
for tweet in t.hydrate(open('ids.txt')):
    print(tweet["text"])
```

## Utilities

In the utils directory there are some simple command line utilities for
working with the line-oriented JSON, like printing out the archived tweets as
text or html, extracting the usernames, referenced URLs, etc.  If you
create a script that is handy please send a pull request.

When you've got some tweets you can create a rudimentary wall of them:

    % utils/wall.py tweets.json > tweets.html

You can create a word cloud of tweets you collected about nasa:

    % utils/wordcloud.py tweets.json > wordcloud.html

gender.py is a filter which allows you to filter tweets based on a guess about
the gender of the author. So for example you can filter out all the tweets that
look like they were from women, and create a word cloud for them:

    % utils/gender.py --gender female tweets.json | utils/wordcloud.py > tweets-female.html

You can output [GeoJSON](http://geojson.org/) from tweets where geo coordinates are available:

    % utils/geojson.py tweets.json > tweets.geojson

Optionally you can export GeoJSON with centroids replacing bounding boxes:

    % utils/geojson.py tweets.json --centroid > tweets.geojson

And if you do export GeoJSON with centroids, you can add some random fuzzing:

    % utils/geojson.py tweets.json --centroid --fuzz 0.01 > tweets.geojson

If you suspect you have duplicate in your tweets you can dedupe them:

    % utils/deduplicate.py tweets.json > deduped.json

You can sort by ID, which is analogous to sorting by time:

    % utils/sort_by_id.py tweets.json > sorted.json

You can filter out all tweets before a certain date (for example, if a hashtag was used for another event before the one you're interested in):

    % utils/filter_date.py --mindate 1-may-2014 tweets.json > filtered.json

You can get an HTML list of the clients used:

    % utils/source.py tweets.json > sources.html

If you want to remove the retweets:

    % utils/noretweets.py tweets.json > tweets_noretweets.json

Or unshorten urls (requires [unshrtn](https://github.com/edsu/unshrtn)):

    % cat tweets.json | utils/unshorten.py > unshortened.json

Once you unshorten your URLs you can get a ranked list of most-tweeted URLs:

    % cat unshortened.json | utils/urls.py | sort | uniq -c | sort -nr > urls.txt

## twarc-report

Some further utility scripts to generate csv or json output suitable for
use with [D3.js](http://d3js.org/) visualizations are found in the
[twarc-report](https://github.com/pbinkley/twarc-report) project. The
util directed.py, formerly part of twarc, has moved to twarc-report as
d3graph.py.

Each script can also generate an html demo of a D3 visualization, e.g.
[timelines](https://wallandbinkley.com/twarc/bill10/) or a
[directed graph of retweets](https://wallandbinkley.com/twarc/bill10/directed-retweets.html).
