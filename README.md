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

Utils
-----

In the utils directory there are some simple command line utilities for 
working with the json dumps like printing out the archived tweets as text 
or html, extracting the usernames, referenced urls, and the like.  If you 
create a script that is handy please send me a pull request :-)

For example lets say you want to create a wall of tweets that mention 'nasa':

    % ./twarc.py nasa
    % utils/wall.py nasa-20130306102105.json > nasa.html

License
-------

* CC0
