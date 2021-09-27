
# twarc2

twarc2 is a command line tool and Python library for archiving Twitter JSON
data. Each tweet is represented as a JSON object that was returned from the
Twitter API. Since Twitter's introduction of their [v2
API](https://developer.twitter.com/en/docs/twitter-api/api-reference-index#v2)
the JSON representation of a tweet is conditional on the types of fields and
expansions that are requested. twarc2 does the work of requesting the highest
fidelity representation of a tweet by requesting all the available data for
tweets. 

Tweets are streamed or stored as [line-oriented
JSON](https://en.wikipedia.org/wiki/JSON_Streaming#Line-delimited_JSON). twarc2
will handle Twitter API's [rate
limits](https://dev.twitter.com/rest/public/rate-limiting) for you. In addition
to letting you collect tweets twarc can also help you collect users and hydrate
tweet ids. It also has a collection of [plugins](plugins) you can use to do
things with the collected JSON data (such as converting it to CSV).

twarc2 was developed as part of the [Documenting the Now](http://www.docnow.io)
project which was funded by the [Mellon Foundation](https://mellon.org/).

## Install

Before using twarc you will need to register an application at
[apps.twitter.com](http://apps.twitter.com). Once you've created your
application, note down the consumer key, consumer secret and then click to
generate an access token and access token secret. With these four variables
in hand you are ready to start using twarc.

1. install [Python 3](http://python.org/download)
2. [pip](https://pip.pypa.io/en/stable/installing/) install twarc:

```
pip install --upgrade twarc
```

### Homebrew (macOS only)

For macOS users, you can also install `twarc` via [Homebrew](https://brew.sh/):

```bash
brew install twarc
```

### Windows

If you installed with pip and see a "failed to create process" when running twarc try reinstalling like this:

    python -m pip install --upgrade --force-reinstall twarc

## Quickstart:

First you're going to need to tell twarc about your application API keys and
grant access to one or more Twitter accounts:

    twarc2 configure

Then try out a search:

    twarc2 search blacklivesmatter search.jsonl

Or maybe you'd like to collect tweets as they happen?

    twarc2 filter blacklivesmatter stream.jsonl

See below for the details about these commands and more.

## Configure

Once you've got your Twitter developer access set up you can tell twarc what they are with the `configure` command.

    twarc2 configure

This will store your credentials in your home directory so you don't have to
keep entering them in. You can most of twarc's functionality by simply
configuring the *bearer token*, but if you want it to be complete you can enter
in the *API key* and *API secret*.

You can also the keys in the system environment (`CONSUMER_KEY`,
`CONSUMER_SECRET`, `ACCESS_TOKEN`, `ACCESS_TOKEN_SECRET`) or using command line
options (`--consumer-key`, `--consumer-secret`, `--access-token`,
`--access-token-secret`).

## Search

This uses Twitter's [tweets/search/recent](https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-recent) and [tweets/search/all](https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-all) endpoints to download *pre-existing* tweets matching a given query. This command will search for any tweets mentioning *blacklivesmatter* from the 7 days.

    twarc2 search blacklivesmatter tweets.jsonl

If you have access to the [Academic Research Product Track](https://developer.twitter.com/en/products/twitter-api/academic-research) you can search the full archive of tweets by using the `--archive` option.

    twarc2 search --archive blacklivesmatter tweets.jsonl 

The queries can be a lot more expressive than matching a single term. For
example this query will search for tweets containing either `blacklivesmatter`
or `blm` that were sent to the user \@deray. 

    twarc2 search 'blacklivesmatter OR blm to:deray' tweets.jsonl

The best way to get familiar with Twitter's search syntax is to consult Twitter's [Building queries for Search Tweets](https://developer.twitter.com/en/docs/twitter-api/tweets/search/integrate/build-a-query) documentation. 

You also should definitely check out Igor Brigadir's *excellent* reference guide
to the Twitter Search syntax:
[Advanced Search on Twitter](https://github.com/igorbrigadir/twitter-advanced-search/blob/master/README.md).
There are lots of hidden gems in there that the advanced search form doesn't
make readily apparent.

### Limit

Because there is a 500,000 tweet limit (5 million for Academic Research Track)
you may want to limit the number of tweets you retrieve by using `--limit`:

    twarc2 search --limit 5000 blacklivesmatter tweets.jsonl

### Time

You can also limit to a particular time range using `--start-time` and/or
`--end-time`, which can be especially useful in conjunction with `--archive`
when you are searching for historical tweets.

    twarc2 search --start-time 2014-07-17 --end-time 2014-07-24 '"eric garner"' tweets.jsonl 

If you leave off --start-time or --end-time it will be open on that side. So
for example to get all "eric garner" tweets before 2014-07-24 you would just
leave off the `--start-time`:

    twarc2 search --end-time 2014-07-24 '"eric garner"' tweets.jsonl 

## Stream

The `stream` command will use Twitter's API
[tweets/search/stream](https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream)
endpoint to collect tweets as they happen. In order to use it you first need to
create one or more [rules]. For example:

    twarc2 stream-rules add blacklivesmatter

You can list your active stream rules:

    twarc2 stream-rules list

And you can collect the data from the stream, which will bring down any tweets that match your rules:

    twarc2 stream stream.jsonl

When you want to stop you use `ctrl-c`. This only stops the stream but doesn't delete your stream rule. To remove a rule you can:

    twarc2 stream-rules delete blacklivesmatter

## Sample

Use the `sample` command to listen to Twitter's [tweets/sample/stream](https://developer.twitter.com/en/docs/twitter-api/tweets/sampled-stream/api-reference/get-tweets-sample-stream) API for a "random" sample of recent public statuses.

    twarc2 sample sample.jsonl

## Users

If you have a file of user ids you can fetch the user metadata for them with
the `users` command:

    twarc users users.txt users.jsonl

If the file contains usernames instead of user ids you can use the `--usernames` option:

    twarc2 users --usernames users.txt users.jsonl

## Followers

You can fetch the followers of an account using the `followers` command:

    twarc2 followers deray users.jsonl

## Following

To get the users that a user is following you can use `following`:

    twarc2 following deray users.jsonl

The result will include exactly one user id per line. The response order is
reverse chronological, or most recent followers first.

## Timeline

The `timeline` command will use Twitter's [user timeline API](https://developer.twitter.com/en/docs/twitter-api/tweets/timelines/api-reference/get-users-id-tweets) to collect the most recent tweets posted by the user indicated by screen_name.

    twarc2 timeline deray tweets.jsonl

## Conversation

You can retrieve a conversation thread using the tweet ID at the head of the
conversation:

    twarc2 conversation 266031293945503744 > conversation.jsonl

## Dehydrate

The `dehydrate` command generates an id list from a file of tweets:

    twarc2 dehydrate tweets.jsonl tweet-ids.txt

## Hydrate

twarc's `hydrate` command will read a file of tweet identifiers and write out the tweet JSON for them using Twitter's [tweets](https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets)
API endpoint:

    twarc2 hydrate ids.txt tweets.jsonl

Twitter API's [Terms of Service](https://dev.twitter.com/overview/terms/policy#6._Be_a_Good_Partner_to_Twitter) discourage people from making large amounts of raw Twitter data available on the Web.  The data can be used for research and archived for local use, but not shared with the world. Twitter does allow files of tweet identifiers to be shared, which can be useful when you would like to make a dataset of tweets available.  You can then use Twitter's API to *hydrate* the data, or to retrieve the full JSON for each identifier. This is particularly important for [verification](https://en.wikipedia.org/wiki/Reproducibility) of social media research.

# Command Line Usage

Below is what you see when you run `twarc2 --help`.

::: mkdocs-click:
  :module: twarc.command2
  :command: twarc2
