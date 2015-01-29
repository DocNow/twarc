twarc
=====

[![Build Status](https://secure.travis-ci.org/edsu/twarc.png)](http://travis-ci.org/edsu/twarc) [![Coverage Status](https://coveralls.io/repos/edsu/twarc/badge.png)](https://coveralls.io/r/edsu/twarc) [![Gitter](https://badges.gitter.im/Join Chat.svg)](https://gitter.im/edsu/twarc?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

twarc is a command line tool and Python library for archiving Twitter JSON 
data. Each tweet is represented as a JSON object which is exactly what was 
returned from the Twitter API. It runs in three modes: search, filter and 
hydrate. When running in each mode twarc will stop and resume activity in 
order to respect the Twitter API's [rate limits](https://dev.twitter.com/rest/public/rate-limiting).

### Search

When running in search mode twarc will use Twitter's [search API](https://dev.twitter.com/rest/reference/get/search/tweets) to retrieve
tweets that match a particular query. So for example, to collect all the 
tweets mentioning the keyword Ferguson you would:

    twarc.py --query Ferguson

This command would will walk through each page of the search results and save
them to a distinct file. Twitter's search API only makes (roughly) the
last weeks worth of Tweets available via its search API, so time is of the 
essence if you are trying to collect tweets for something that has already 
happened. 

If you run a query job, and then decide to run it again later twarc will use the
last file to determine when it can stop. This makes it fairly easy to repeatedly
look for new results from cron.

### Stream

In stream mode twarc will listen to Twitter's [filter stream API](https://dev.twitter.com/streaming/reference/post/statuses/filter) for
tweets that match a particular filter. Similar to search mode twarc will save 
the tweets to a file.

    twarc.py --stream --query Ferguson

Note the syntax for the Twitter's filter queries is slightly different than what queries in their search API. So please consult the [documentation](https://dev.twitter.com/streaming/overview/request-parameters#track) on how best to express the filter.

### Hydrate

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
fetch the full JSON for each tweet and output each one as line-oriented JSON:


    twarc.py --hydrate ids.txt > tweets.json

## Install

This is an example of using twarc in search mode: 

1. pip install twarc
1. set CONSUMER\_KEY, CONSUMER\_SECRET, ACCESS\_TOKEN and ACCESS\_TOKEN\_SECRET in your environment.
1. twarc.py --query aaronsw
1. cat aaronsw*.json

## Use as a Library

If you want you can use twarc to get an iterator for tweets from a search as 
JSON and do something else with them. It will handle paging through results and
quotas:

```python
import twarc

for tweet in twarc.search("aaronsw"):
    print tweet["text"]
```

You can do the same for a stream of new tweets:

```python
for tweet in twarc.stream("aaronsw"):
    print tweet["text"]
```

Similarly you can hydrate tweet identifiers by passing in a list of ids or 
or a generator:

```python
for tweet in twarc.hydrate(ids):
  print tweet["text"]
```

## Utilities

In the utils directory there are some simple command line utilities for
working with the line-oriented JSON, like printing out the archived tweets as 
text or html, extracting the usernames, referenced URLs, etc.  If you
create a script that is handy please send a pull request.

For example lets say you want to create a wall of tweets that mention 'nasa':

    % ./twarc.py --query nasa
    % utils/wall.py nasa-20130306102105.json > nasa.html

If you want the tweets ordered from oldest to latest:

    % tail -r nasa-20130306102105.json | utils/wall.py > nasa.html

Or you want to create a word cloud of tweets you collected about nasa:

    % ./twarc.py --query nasa
    % utils/wordcloud.py nasa-20130306102105.json > nasa-wordcloud.html

Or if you want to filter out all the tweets that look like they were from
women, and create a word cloud from them:

    % ./twarc.py --query nasa
    % utils/gender.py --gender female nasa-20130306102105.json | utils/wordcloud.py > nasa-female.html

Or if you want to output [GeoJSON](http://geojson.org/) from tweets where geo coordinates are available:

    % ./twarc.py --query nasa
    % utils/geojson.py nasa-20130306102105.json > nasa-20130306102105.geojson

Or if you have duplicate tweets in your JSON, deduplicate using:

    % ./twarc.py --query nasa
    % utils/deduplicate.py nasa-20130306102105.json > deduped.json

Or if you want to sort by ID, which is analogous to sorting by time:

    % ./twarc.py --query nasa
    % utils/sort_by_id.py nasa-20130306102105.json > sorted.json

Or if you want to filter out all tweets before a certain date (for example, if a hashtag was used for another event before the one you're interested in):

    % ./twarc.py --query "#somehashtag"
    % utils/filter_date.py --mindate 1-may-2014 %23somehashtag-20141020122149.json > filtered.json

Or if you want an HTML list of the clients used:

    % ./twarc.py --query nasa
    % utils/source.py nasa-20130306102105.json > nasa-sources.html

Or remove retweets:

    % ./twarc.py --query nasa
    % utils/noretweets.py nasa-20130306102105.json > tweets_noretweets.json

Or unshorten urls (requires [unshrtn](https://github.com/edsu/unshrtn)):

    % ./twarc.py --query "#JeSuisCharlie"
    % cat %23JeSuisCharlie*json | utils/unshorten.py > %23JeSuisCharlie-ushortened.json

Or get a ranked list of most tweeted URLs:
    
    % ./twarc.py --query "#JeSuisCharlie"
    % cat %23JeSuisCharlie*json | utils/unshorten.py > %23JeSuisCharlie-ushortened.json
    % cat %23JeSuisCharlie-ushortened.json | utils/urls.py | sort | uniq -c | sort -n > urls.txt

## twarc-report

Some further utility scripts to generate csv or json output suitable for
use with [D3.js](http://d3js.org/) visualizations are found in the
[twarc-report](https://github.com/pbinkley/twarc-report) project. The
util directed.py, formerly part of twarc, has moved to twarc-report as d3graph.py.
Each script can also generate an html demo of a D3 visualization, e.g.
[timelines](https://wallandbinkley.com/twarc/bill10/) or a [directed
graph of
retweets](https://wallandbinkley.com/twarc/bill10/directed-retweets.html).

License
-------

* CC0
