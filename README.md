twarc
=====

[![Build Status](https://secure.travis-ci.org/edsu/twarc.png)](http://travis-ci.org/edsu/twarc)

twarc is command line tool for archiving the tweets in a Twitter search result.
Twitter search results live for a week or so, and are highly volatile. Results
are stored as line-oriented JSON (each line is a complete JSON document), and
are exactly what is received from the Twitter API.  twarc handles rate limiting
and paging through large result sets. It also handles repeated runs of the same
query, by using the most recent tweet in the last run to determine when to
stop.

twarc was originally created to save [tweets related to Aaron Swartz](http://archive.org/details/AaronswRelatedTweets).

## How To Use

1. pip install twarc
1. set CONSUMER\_KEY, CONSUMER\_SECRET, ACCESS\_TOKEN and ACCESS\_TOKEN\_SECRET in your environment.
1. twarc.py aaronsw
1. cat aaronsw*.json

## Stream Mode

By default twarc will search backwards in time as far as it can go. But if
you would like to start capturing tweets that match a query from the live
stream you can run in stream mode:

    twarc.py --stream aaronsw

## Use as a Library

If you want you can use twarc to get a stream of tweets from a search as JSON
and do something else with them. It will handle paging through results and
quotas:

```python

import twarc

for tweet in twarc.search("aaronsw"):
    print tweet["text"]
```

## Scrape Mode

The first time you fetch tweets for a query if you pass the --scrape option
it will use [search.twitter.com](http://search.twitter.com) to discover tweet
ids, and then use the Twitter REST API to fetch the JSON for each tweet. This
is an expensive operation because each ID needs to be fetched from the API
which counts as a request against your quota.

[Twitter Search](http://search.twitter.com) [now supports](http://blog.twitter.com/2013/02/now-showing-older-tweets-in-search.html) drilling backwards in time, past the week cutoff of the REST API. Since individual tweets are still retrieved with the REST API, rate limits apply--so this is quite a slow process. Still, if you are willing to let it run for a while it can be useful to query for older tweets, until the official search REST API supports a more historical perspective.

## Utils

In the utils directory there are some simple command line utilities for
working with the json dumps like printing out the archived tweets as text
or html, extracting the usernames, referenced urls, and the like.  If you
create a script that is handy please send me a pull request :-)

For example lets say you want to create a wall of tweets that mention 'nasa':

    % ./twarc.py nasa
    % utils/wall.py nasa-20130306102105.json > nasa.html

If you want the tweets ordered from oldest to latest:

    % tail -r nasa-20130306102105.json | utils/wall.py > nasa.html

Or you want to create a word cloud of tweets you collected about nasa:

    % ./twarc.py nasa
    % utils/wordcloud.py nasa-20130306102105.json > nasa-wordcloud.html

Or if you want to filter out all the tweets that look like they were from
women, and create a word cloud from them:

    % ./twarc.py nasa
    % utils/gender.py --gender female nasa-20130306102105.json | utils/wordcloud.py > nasa-female.html

Or if you want to create a [D3](http://d3js.org/) directed graph of mentions
or retweets, in which nodes are users and arrows point from the original user
to the user who mentions or retweets them:

	% ./twarc.py nasa
	% utils/directed.py --mode mentions nasa-20130306102105.json > nasa-directed-mentions.html
	% utils/directed.py --mode retweets nasa-20130306102105.json > nasa-directed-retweets.html
	% utils/directed.py --mode replies nasa-20130306102105.json > nasa-directed-replies.html

Or if you want to output [GeoJSON](http://geojson.org/) from tweets where geo coordinates are available:

    % ./twarc.py nasa
    % utils/geojson.py nasa-20130306102105.json > nasa-20130306102105.geojson

Or if you have duplicate tweets in your JSON, deduplicate using:

    % ./twarc.py --scrape nasa
    % utils/deduplicate.py nasa-20130306102105.json > deduped.json

Or if you want to sort by ID, which is analogous to sorting by time:

    % ./twarc.py --scrape nasa
    % utils/sort_by_id.py nasa-20130306102105.json > sorted.json

Or if you want to filter out all tweets before a certain date (for example, if a hashtag was used for another event before the one you're interested in):

    % ./twarc.py --scrape #somehashtag
    % utils/filter_date.py --mindate 1-may-2014 %23somehashtag-20141020122149.json > filtered.json

License
-------

* CC0
