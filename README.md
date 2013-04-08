twarc
=====

twarc is command line tool for archiving the tweets in a Twitter search result.
Twitter search results live for a week or so, and are highly volatile. Results 
are stored as line-oriented JSON (each line is a complete JSON document), and 
are exactly what is received from the Twitter API.  twarc handles rate limiting 
and paging through large result sets. It also handles repeated runs of the same
query, by using the most recent tweet in the last run to determine when to 
stop.

twarc was originally created to save [tweets related to Aaron Swartz](http://archive.org/details/AaronswRelatedTweets).

How To Use
----------

1. pip install -r requirements.txt
1. cp config.py.example config.py
1. add twitter api credentials to config.py
1. ./twarc.py aaronsw
1. cat aaronsw.json
1. :-(

Scrape Mode
-----------

If you pass the --scrape option to twarc it will use [search.twitter.com](http://search.twitter.com)
to discover tweet ids, and then use the Twitter REST API to fetch the JSON for
each tweet.

The [Twitter Search](http://search.twitter.com) webapp [now supports](http://blog.twitter.com/2013/02/now-showing-older-tweets-in-search.html) 
drilling backwards in time, past the week cutoff of the REST API. Since
individual tweets are still retrieved with the REST API, rate limits apply--
so this is quite a slow process. Still, if you are willing to let it run for 
a while it can be useful to query for older tweets, until the official 
search REST API supports a more historical perspective.

Utils
-----

In the utils directory there are some simple command line utilities for 
working with the json dumps like printing out the archived tweets as text 
or html, extracting the usernames, referenced urls, and the like.  If you 
create a script that is handy please send me a pull request :-)

For example lets say you want to create a wall of tweets that mention 'nasa':

    % ./twarc.py nasa
    % utils/wall.py nasa-20130306102105.json > nasa.html

Or you want to create a word cloud of tweets you collected about nasa:

    % ./twarc.py nasa
    % utils/wordcloud.py nasa-20130306102105.json > nasa-wordcloud.html

Or if you want to filter out all the tweets that look like they were from 
women, and create a word cloud from them:

    % ./twarc.py nasa
    % utils/gender.py --gender female nasa-20130306102105.json | utils/wordcloud.py > nasa-female.html

License
-------

* CC0
