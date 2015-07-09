twarc
=====

[![Build Status](https://secure.travis-ci.org/edsu/twarc.png)](http://travis-ci.org/edsu/twarc) 
[![Gitter](https://badges.gitter.im/Join Chat.svg)](https://gitter.im/edsu/twarc?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![DOI](https://zenodo.org/badge/12737/edsu/twarc.svg)](http://dx.doi.org/10.5281/zenodo.17385)

twarc is a command line tool and Python library for archiving Twitter JSON
data. Each tweet is represented as a JSON object that is exactly what is
returned from the Twitter API. It runs in three modes: search, stream and
hydrate. When running in each mode twarc will stop and resume activity in
order to work within the Twitter API's [rate limits](https://dev.twitter.com/rest/public/rate-limiting).

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
(roughly) the last weeks worth of Tweets available via its search API, so
time is of the essence if you are trying to collect tweets for something
that has already happened.

## Stream

In stream mode twarc will listen to Twitter's [filter stream API](https://dev.twitter.com/streaming/reference/post/statuses/filter) for
tweets that match a particular filter. Similar to search mode twarc will write
these tweets to stdout as line oriented JSON:

    twarc.py --stream ferguson > tweets.json

Note the syntax for the Twitter's filter queries is slightly different than what queries in their search API. So please consult the [documentation](https://dev.twitter.com/streaming/overview/request-parameters#track) on how best to express the filter.

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

## Use as a Library

If you want you can use twarc programatically as a library to collect
tweets. You first need to create a `Twarc` instance (using your Twitter
credentials), and then use it to iterate through search results, filter
results or lookup results.

```python
from twarc import Twarc

t = Twarc(client_key, client_secret, access_token, access_token_secret)
for tweet in t.search("ferguson"):
    print(tweet["text"])
```

You can do the same for a stream of new tweets:

```python
for tweet in t.stream("ferguson"):
    print(tweet["text"])
```

Similarly you can hydrate tweet identifiers by passing in a list of ids or
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

For example lets say you archive some tweets mentioning "ferguson":

    % twarc.py --search ferguson > tweets.json

This is good for one off collecting but if you would like to periodically
run the same search and have it only collect tweets you previously missed try
the utils/archive.py utility:

    % utils/archive.py ferguson /mnt/tweets/ferguson/

This will search for tweets and write them as:

    /mnt/tweets/ferguson/tweets-0001.json

If you run the same command later it will write any tweets that weren't
archived previously to:

    /mnt/tweets/ferguson/tweets-0002.json

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

Once you unshorten your URLs you can get a ranked list of most tweeted URLs:

    % cat unshortened.json | utils/urls.py | sort | uniq -c | sort -n > urls.txt

## twarc-report

Some further utility scripts to generate csv or json output suitable for
use with [D3.js](http://d3js.org/) visualizations are found in the
[twarc-report](https://github.com/pbinkley/twarc-report) project. The
util directed.py, formerly part of twarc, has moved to twarc-report as
d3graph.py.

Each script can also generate an html demo of a D3 visualization, e.g.
[timelines](https://wallandbinkley.com/twarc/bill10/) or a
[directed graph of retweets](https://wallandbinkley.com/twarc/bill10/directed-retweets.html).
