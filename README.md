twarc
=====

[![Build Status](https://secure.travis-ci.org/DocNow/twarc.png)](http://travis-ci.org/DocNow/twarc)

*Translations: [Portuguese], [Spanish], [Swahili], [Swedish]*

twarc is a command line tool and Python library for archiving Twitter JSON data.
Each tweet is represented as a JSON object that is
[exactly](https://dev.twitter.com/overview/api/tweets) what was returned from
the Twitter API.  Tweets are stored as [line-oriented JSON](https://en.wikipedia.org/wiki/JSON_Streaming#Line_delimited_JSON).  Twarc will handle
Twitter API's [rate limits](https://dev.twitter.com/rest/public/rate-limiting)
for you. In addition to letting you collect tweets Twarc can also help you
collect users, trends and hydrate tweet ids.

twarc was developed as part of the [Documenting the Now](http://www.docnow.io)
project which was funded by the [Mellon Foundation](https://mellon.org/).

## Install

Before using twarc you will need to register an application at
[apps.twitter.com](http://apps.twitter.com). Once you've created your
application, note down the consumer key, consumer secret and then click to
generate an access token and access token secret. With these four variables
in hand you are ready to start using twarc.

1. install [Python](http://python.org/download) (2 or 3)
2. [pip](https://pip.pypa.io/en/stable/installing/) install twarc

## Quickstart:

First you're going to need to tell twarc about your application API keys and
grant access to one or more Twitter accounts:

    twarc configure

Then try out a search:

    twarc search blacklivesmatter > search.jsonl

Or maybe you'd like to collect tweets as they happen?

    twarc filter blacklivesmatter > stream.jsonl

See below for the details about these commands and more.

## Usage

### Configure

Once you've got your application keys you can tell twarc what they are with the
`configure` command.

    twarc configure

This will store your credentials in a file called `.twarc` in your home
directory so you don't have to keep entering them in. If you would rather supply
them directly you can set them in the environment (`CONSUMER_KEY`,
`CONSUMER_SECRET`, `ACCESS_TOKEN`, `ACCESS_TOKEN_SECRET`) or using command line
options (`--consumer_key`, `--consumer_secret`, `--access_token`,
`--access_token_secret`).

### Search

This uses Twitter's [search/tweets](https://dev.twitter.com/rest/reference/get/search/tweets) to download *pre-existing* tweets matching a given query.

    twarc search blacklivesmatter > tweets.jsonl

It's important to note that `search` will return tweets that are found within a
7 day window that Twitter's search API imposes. If this seems like a small
window, it is, but you may be interested in collecting tweets as they happen
using the `filter` and `sample` commands below.

The best way to get familiar with Twitter's search syntax is to experiment with
[Twitter's Advanced Search](https://twitter.com/search-advanced) and copy and
pasting the resulting query from the search box. For example here is a more
complicated query that searches for tweets containing either the
\#blacklivesmatter or #blm hashtags that were sent to deray.

    twarc search '#blacklivesmatter OR #blm to:deray' > tweets.jsonl

Twitter attempts to code the language of a tweet, and you can limit your search
to a particular language if you want:

    twarc search '#blacklivesmatter' --lang fr > tweets.jsonl

You can also search for tweets with a given location, for example tweets
mentioning *blacklivesmatter* that are 1 mile from the center of Ferguson,
Missouri:

    twarc search blacklivesmatter --geocode 38.7442,-90.3054,1mi > tweets.jsonl

If a search query isn't supplied when using `--geocode` you will get all tweets
relevant for that location and radius:

    twarc search --geocode 38.7442,-90.3054,1mi > tweets.jsonl

### Filter

The `filter` command will use Twitter's [statuses/filter](https://dev.twitter.com/streaming/reference/post/statuses/filter) API to collect tweets as they happen.

    twarc filter blacklivesmatter,blm > tweets.jsonl

Please note that the syntax for the Twitter's track queries is slightly
different than what queries in their search API. So please consult the
documentation on how best to express the filter option you are using.

Use the `follow` command line argument if you would like to collect tweets from
a given user id as they happen. This includes retweets. For example this will
collect tweets and retweets from CNN:

    twarc filter --follow 759251 > tweets.jsonl

You can also collect tweets using a bounding box. Note: the leading dash needs
to be escaped in the bounding box or else it will be interpreted as a command
line argument!

    twarc filter --locations "\-74,40,-73,41" > tweets.jsonl


If you combine options they are OR'ed together. For example this will collect
tweets that use the blacklivesmatter or blm hashtags and also tweets from user
CNN:

    twarc filter blacklivesmatter,blm --follow 759251 > tweets.jsonl

### Sample

Use the `sample` command to listen to Twitter's [statuses/sample](https://dev.twitter.com/streaming/reference/get/statuses/sample) API for a "random" sample of recent public statuses.

    twarc sample > tweets.jsonl

### Dehydrate

The `dehydrate` command generates an id list from a file of tweets:

    twarc dehydrate tweets.jsonl > tweet-ids.txt

### Hydrate

Twarc's `hydrate` command will read a file of tweet identifiers and write out the tweet JSON for them using Twitter's [status/lookup](https://dev.twitter.com/rest/reference/get/statuses/lookup) API.

    twarc hydrate ids.txt > tweets.jsonl

Twitter API's [Terms of Service](https://dev.twitter.com/overview/terms/policy#6._Be_a_Good_Partner_to_Twitter) discourage people from making large amounts of raw Twitter data available on the Web.  The data can be used for research and archived for local use, but not shared with the world. Twitter does allow files of tweet identifiers to be shared, which can be useful when you would like to make a dataset of tweets available.  You can then use Twitter's API to *hydrate* the data, or to retrieve the full JSON for each identifier. This is particularly important for [verification](https://en.wikipedia.org/wiki/Reproducibility) of social media research.

### Users

The `users` command will return User metadata for the given screen names.

    twarc users deray,Nettaaaaaaaa > users.jsonl

You can also give it user ids:

    twarc users 1232134,1413213 > users.jsonl

If you want you can also use a file of user ids, which can be useful if you are
using the `followers` and `friends` commands below:

    twarc users ids.txt > users.jsonl

### Followers

The `followers` command  will use Twitter's [follower id API](https://dev.twitter.com/rest/reference/get/followers/ids) to collect the follower user ids for exactly one user screen name per request as specified as an argument:

    twarc followers deray > follower_ids.txt

The result will include exactly one user id per line. The response order is
reverse chronological, or most recent followers first.

### Friends

Like the `followers` command, the `friends` command will use Twitter's [friend id API](https://dev.twitter.com/rest/reference/get/friends/ids) to collect the friend user ids for exactly one user screen name per request as specified as an argument:

    twarc friends deray > friend_ids.txt

### Trends

The `trends` command lets you retrieve information from Twitter's API about trending hashtags. You need to supply a [Where On Earth](http://developer.yahoo.com/geo/geoplanet/) identifier (`woeid`) to indicate what trends you are interested in. For example here's how you can get the current trends for St Louis:

    twarc trends 2486982

Using a `woeid` of 1 will return trends for the entire planet:

    twarc trends 1

If you aren't sure what to use as a `woeid` just omit it and you will get a list
of all the places for which Twitter tracks trends:

    twarc trends

If you have a geo-location you can use it instead of the `woedid`.

    twarc trends 39.9062,-79.4679

Behind the scenes twarc will lookup the location using Twitter's [trends/closest](https://dev.twitter.com/rest/reference/get/trends/closest) API to find the nearest `woeid`.

### Timeline

The `timeline` command will use Twitter's [user timeline API](https://dev.twitter.com/rest/reference/get/statuses/user_timeline) to collect the most recent tweets posted by the user indicated by screen_name.

    twarc timeline deray > tweets.jsonl

You can also look up users using a user id:

    twarc timeline 12345 > tweets.jsonl

### Retweets

You can get retweets for a given tweet id like so:

    twarc retweets 824077910927691778 > retweets.jsonl

### Replies

Unfortunately Twitter's API does not currently support getting replies to a
tweet. So twarc approximates it by using the search API. Since the search API
does not support getting tweets older than a week twarc can only get all the
replies to a tweet that have been sent in the last week.

If you want to get the replies to a given tweet you can:

    twarc replies 824077910927691778 > replies.jsonl

Using the `--recursive` option will also fetch replies to the replies as well as
quotes.  This can take a long time to complete for a large thread because of
rate limiting by the search API.

    twarc replies 824077910927691778 --recursive

### Lists

To get the users that are on a list you can use the list URL with the
`listmembers` command:

    twarc listmembers https://twitter.com/edsu/lists/bots

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
text or html, extracting the usernames, referenced URLs, etc.  If you create a
script that you find handy please send a pull request.

When you've got some tweets you can create a rudimentary wall of them:

    % utils/wall.py tweets.jsonl > tweets.html

You can create a word cloud of tweets you collected about nasa:

    % utils/wordcloud.py tweets.jsonl > wordcloud.html

If you've collected some tweets using `replies` you can create a static D3
visualization of them with:

    % utils/network.py tweets.jsonl tweets.html

Optionally you can consolidate tweets by user, allowing you to see central accounts:

    % utils/network.py --users tweets.jsonl tweets.html

And if you want to use the network graph in a program like [Gephi](https://gephi.org/),
you can generate a GEXF file with the following:

    % utils/network.py --users tweets.jsonl tweets.gexf

gender.py is a filter which allows you to filter tweets based on a guess about
the gender of the author. So for example you can filter out all the tweets that
look like they were from women, and create a word cloud for them:

    % utils/gender.py --gender female tweets.jsonl | utils/wordcloud.py > tweets-female.html

You can output [GeoJSON](http://geojson.org/) from tweets where geo coordinates are available:

    % utils/geojson.py tweets.jsonl > tweets.geojson

Optionally you can export GeoJSON with centroids replacing bounding boxes:

    % utils/geojson.py tweets.jsonl --centroid > tweets.geojson

And if you do export GeoJSON with centroids, you can add some random fuzzing:

    % utils/geojson.py tweets.jsonl --centroid --fuzz 0.01 > tweets.geojson

To filter tweets by presence or absence of geo coordinates (or Place, see [API documentation](https://dev.twitter.com/overview/api/places)):

    % utils/geofilter.py tweets.jsonl --yes-coordinates > tweets-with-geocoords.jsonl
    % cat tweets.jsonl | utils/geofilter.py --no-place > tweets-with-no-place.jsonl

To filter tweets by a GeoJSON fence (requires [Shapely](https://github.com/Toblerity/Shapely)):

    % utils/geofilter.py tweets.jsonl --fence limits.geojson > fenced-tweets.jsonl
    % cat tweets.jsonl | utils/geofilter.py --fence limits.geojson > fenced-tweets.jsonl

If you suspect you have duplicate in your tweets you can dedupe them:

    % utils/deduplicate.py tweets.jsonl > deduped.jsonl

You can sort by ID, which is analogous to sorting by time:

    % utils/sort_by_id.py tweets.jsonl > sorted.jsonl

You can filter out all tweets before a certain date (for example, if a hashtag was used for another event before the one you're interested in):

    % utils/filter_date.py --mindate 1-may-2014 tweets.jsonl > filtered.jsonl

You can get an HTML list of the clients used:

    % utils/source.py tweets.jsonl > sources.html

If you want to remove the retweets:

    % utils/noretweets.py tweets.jsonl > tweets_noretweets.jsonl

Or unshorten urls (requires [unshrtn](https://github.com/docnow/unshrtn)):

    % cat tweets.jsonl | utils/unshrtn.py > unshortened.jsonl

Once you unshorten your URLs you can get a ranked list of most-tweeted URLs:

    % cat unshortened.jsonl | utils/urls.py | sort | uniq -c | sort -nr > urls.txt

## twarc-report

Some further utility scripts to generate csv or json output suitable for
use with [D3.js](http://d3js.org/) visualizations are found in the
[twarc-report](https://github.com/pbinkley/twarc-report) project. The
util `directed.py`, formerly part of twarc, has moved to twarc-report as
`d3graph.py`.

Each script can also generate an html demo of a D3 visualization, e.g.
[timelines](https://wallandbinkley.com/twarc/bill10/) or a
[directed graph of retweets](https://wallandbinkley.com/twarc/bill10/directed-retweets.html).

[Portuguese]: https://github.com/DocNow/twarc/blob/master/README_pt_br.md
[Spanish]: https://github.com/DocNow/twarc/blob/master/README_es_mx.md
[Swedish]: https://github.com/DocNow/twarc/blob/master/README_sv_se.md
[Swahili]: https://github.com/DocNow/twarc/blob/master/README_sw_ke.md
