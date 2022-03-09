
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

Before using twarc you will need to create an application and attach it to an
project on your [Twitter Developer Portal](https://developer.twitter.com/en/portal/projects-and-apps). A ["Project"](https://developer.twitter.com/en/docs/projects/overview) is like a container for an "Application" with a specific purpose.

If you have Academic Access you should see an "Academic Research" Project,
if not, you should see only "Standard" Project. Academic Access is a separate endpoint, see [here](twitter-developer-access.md) for notes on this.

Once you've created your application, note down the Bearer token, and or the consumer key, consumer secret,
which may also be called API Key and API Secret and then optionally click to
generate an access token and access token secret. With these four variables
in hand you are ready to start using twarc.

1. install [Python 3](http://python.org/download)
2. [pip](https://pip.pypa.io/en/stable/installing/) install twarc from a terminal (such as the Windows Command Prompt available in the "start" menu, or the [OSX Terminal application](https://support.apple.com/en-au/guide/terminal/apd5265185d-f365-44cb-8b09-71a064a42125/mac)):

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

    twarc2 search "blacklivesmatter" results.jsonl

Or maybe you'd like to collect tweets as they happen?

    twarc2 filter "blacklivesmatter" results.jsonl

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

    twarc2 search "blacklivesmatter" results.jsonl

If you have access to the [Academic Research Product Track](https://developer.twitter.com/en/products/twitter-api/academic-research) you can search the full archive of tweets by using the `--archive` option.

    twarc2 search --archive "blacklivesmatter" results.jsonl 

The queries can be a lot more expressive than matching a single term. For
example this query will search for tweets containing either `blacklivesmatter`
or `blm` that were sent to the user \@deray. 

    twarc2 search "(blacklivesmatter OR blm) to:deray" results.jsonl

The best way to get familiar with Twitter's search syntax is to consult Twitter's [Building queries for Search Tweets](https://developer.twitter.com/en/docs/twitter-api/tweets/search/integrate/build-a-query) documentation. 

You also should definitely check out Igor Brigadir's *excellent* reference guide
to the Twitter Search syntax:
[Advanced Search on Twitter](https://github.com/igorbrigadir/twitter-advanced-search/blob/master/README.md).
There are lots of hidden gems in there that the advanced search form doesn't
make readily apparent.

### Limit

Because there is a 500,000 tweet limit (5, or sometimes 10 million for Academic Research Track)
you may want to limit the number of tweets you retrieve by using `--limit`:

    twarc2 search --limit 5000 "blacklivesmatter" results.jsonl

### Time

You can also limit to a particular time range using `--start-time` and/or
`--end-time`, which can be especially useful in conjunction with `--archive`
when you are searching for historical tweets.

    twarc2 search --start-time 2014-07-17 --end-time 2014-07-24 '"eric garner"' tweets.jsonl 

If you leave off --start-time or --end-time it will be open on that side. So
for example to get all "eric garner" tweets before 2014-07-24 you would just
leave off the `--start-time`:

    twarc2 search --end-time 2014-07-24 '"eric garner"' tweets.jsonl 

## Searches

Searches works like the [search](#search) command, but instead of taking a single query, it reads from a file containing many queries. You can use the same limit and time options just like a single search command, but it will be applied to every query.

The input file for this command needs to be a plain text file, with one line for each query you want to run, for example you might have a file called `animals.txt` with the following lines:

    cat
    dog
    mouse OR mice

Note that each line will be passed through directly to the Twitter API - if you have quoted strings, they will be treated as a phrase search by the Twitter API, which might not be what you intended.

If you run the following `searches` command, `animals.json` will contain at least 100 tweets for each query in the input file:

    twarc2 searches --limit 100 animals.txt animals.json

You can use the `--archive` and `--start-time` flags just like a regular search command too, in this case to search the full archive of all tweets for the first day of 2020:

    twarc2 searches --archive --start-time 2020-01-01 --end-time 2020-01-02 animals.txt animals.json

You can also use the `--counts-only` flag to check volumes first. This produces a csv file in the same format as the [counts](#counts) command with the `--csv` flag, with the addition of a column containing the query for that row.

    twarc2 searches --counts-only animals.txt animals_counts.csv

One more thing - if you have a lot searches you want to run, you might want to consider using the `--combine-queries` flag. This combines consecutive queries into the file into a single longer query, meaning you issue fewer API calls and potentially collect fewer duplicate tweets that match more than one query. Using this on the `animals.txt` file as input will combine the three queries into the single longer query `(cat) OR (dog) OR (mouse OR mice)`, and only issue one logical query.

    twarc2 searches --combine-queries animals.txt animals_combined.json

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

Use the `sample` command to listen to Twitter's [tweets/sample/stream](https://developer.twitter.com/en/docs/twitter-api/tweets/sampled-stream/api-reference/get-tweets-sample-stream) API for a "random" sample of recent public statuses. The sampling is based on the millisecond part of the tweet timestamp.

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

## Likes

Twarc supports the two approaches that the Twitter API exposes for collecting likes via the `liked-tweets` and `liking-users` commands. 

The `liked-tweets` command returns the tweets that have been liked by a specific account. The account is specified by the user ID of that account, in the following example is the account of Twitter's founder:

    twarc2 liked-tweets 12 jacks-likes.jsonl

In this case the output file contains all of the likes of publicly accessible tweets. Note that the order of likes is not guaranteed by the API, but is probably reverse chronological, or most recent likes by that account first. The underlying tweet objects contain no information about when the tweet was liked.

The `liking-users` command returns the user profiles of the accounts that have liked a specific tweet (specified by the ID of the tweet):

    twarc2 liking-users 1460417326130421765 liking-users.jsonl

In this example the output file contains all of the user profiles of the publicly accessible accounts that have liked that specific tweet. Note that the order of profiles is not guaranteed by the API, but is probably reverse chronological, or the profile of the most recent like for that account first. The underlying profile objects contain no information about when the tweet was liked.

Note that likes of tweets that are not publicly accessible, or likes by accounts that are protected will not be retrieved by either of these methods. Therefore, the metrics available on a tweet object (under the `public_metrics.like_count` field) will likely be higher than the number of likes you can retrieve via the Twitter API using these endpoints.

## Retweets

You can retrieve the user profiles of publicly accessible accounts that have retweeted a specific tweet, using the `retweeted_by` command and the ID of the tweet as an identifier. For example:

    twarc2 retweeted-by 1460417326130421765 retweeting-users.jsonl

Unfortunately this only returns the user profiles (presumably in reverse chronological order) of the retweeters of that tweet - this means that important information, like when the tweet was retweeted is not present in the returned object. 

## Dehydrate

The `dehydrate` command generates an id list from a file of tweets:

    twarc2 dehydrate tweets.jsonl tweet-ids.txt

## Hydrate

twarc's `hydrate` command will read a file of tweet identifiers and write out the tweet JSON for them using Twitter's [tweets](https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets)
API endpoint:

    twarc2 hydrate ids.txt tweets.jsonl
    
The input file, `ids.txt` is expected to be a file that contains a tweet identifier on each line, without quotes or a header:

```
919505987303886849
919505982882844672
919505982602039297
```

Twitter API's [Terms of Service](https://dev.twitter.com/overview/terms/policy#6._Be_a_Good_Partner_to_Twitter) discourage people from making large amounts of raw Twitter data available on the Web.  The data can be used for research and archived for local use, but not shared with the world. Twitter does allow files of tweet identifiers to be shared, which can be useful when you would like to make a dataset of tweets available.  You can then use Twitter's API to *hydrate* the data, or to retrieve the full JSON for each identifier. This is particularly important for [verification](https://en.wikipedia.org/wiki/Reproducibility) of social media research.

## Places

The search and stream APIs allow you to search by places. But in order to use
them you need to know the identifier for a specific place. twarc's
`places` command will let you search by the place name, geo coordinates, or ip
address. For example: 

    twarc2 places Ferguson                 

Which will output something like:

```shell
$ twarc2 places Ferguson                 
Ferguson, MO, United States [id=0a62ce0f6aa37536]
Ruisseau-Ferguson, Québec, Canada [id=25283a1f59449e8f]
Ferguson, Victoria, Australia [id=2538e66b7e5c082c]
Ferguson Road Initiative, Dallas, United States [id=368aad647311292a]
Ferguson, Western Australia, Australia [id=45f20c78d803ad84]
Ferguson, PA, United States [id=00c92e14361c9674]
Ferguson, KY, United States [id=0190ea5612aaae32]
```

You can then use one of the ids in a search:

    twarc2 search "place:0a62ce0f6aa37536" tweets.jsonl

You can also search by geo-coordinates (lat,lon) and IP address. If you would prefer to see the full JSON response with the bounding boxes use the `--json` option.

## Command Line Usage

Below is what you see when you run `twarc2 --help`.

::: mkdocs-click:
  :module: twarc.command2
  :command: twarc2
  :depth: 1
