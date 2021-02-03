# twarc2 🐦🐍💾

twarc2 is a *proposed* new version of [twarc] custom made for the new
Twitter v2 API. Twitter [substantially changed] their API in July 2020.
They have deprecated the v1.1 and premium endpoints. While some of the API
calls seem similar the most significant change is the response payload with
is [totally new]. The representation of a tweet now can take a very
different shape depending on what you ask for and how you ask for it. 

As with twarc the goal of twarc2 is to make it easy to continue to get the
fullest representation of tweets and Twitter users, with the minimum amount
of fuss, and maximum amount of reliability. Here's a sketch of what the
command line API could look like.

### Search

```shell
twarc2 search blacklivesmatter > tweets.jsonl
```

If you have academic search turned on for your account:

```shell
twarc2 search blacklivesmatter --all > tweets.jsonl
```

### Filter

The [filter] API works a bit different in v2 because you first create a set
of rules (optionally tagged) and then you connect to the filter stream to
retrieve all the tweets that match those rules.

First you need to add a rule:

```shell
twarc2 add-filter-rule blacklivesmatter
```

List your rules:

```shell
twarc2 list-filter-rules
```

Start collecting tweets:

```
twarc2 filter > tweets.jsonl
```

Delete one of your rules using an id from the the output of `list-rules`:

```shell
twarc2 remove-filter-rule <rule-id>
```

### Sample

```shell
twarc2 sample > tweets.jsonl
```

### Followers

```shell
twarc2 followers jack > users.jsonl
```

### Following/Friends

```shell
twarc2 friends jack > users.jsonl
```

*Question: is being able to pipe to `twarc2 users` useful?*

### Users

Get users for user ids:

```shell
twarc2 users ids.txt > users.jsonl
```

Or get users for usernames:

```shell
twarc2 users usernames.txt > users.jsonl
```

### Timeline

```shell
twarc2 timeline jack > tweets.jsonl
```

### Mentions

```shell
twarc2 mentions jack > tweets.jsonl
```

### Hydrate

```shell
twarc2 hydrate ids.txt > tweets.jsonl
```

### Compliance

The [compliance] API is new and allows users to upload tweet id datasets
and get back information about whether the tweets are still available.
Since this can take some time for large datasets the ids are first uploaded
and then fetched.

First upload a set of tweet ids to check:

```shell
twarc2 add-compliance-job ids.txt
```

List the current compliance jobs, including their id and their status:

```shell
twarc2 list-compliance-jobs
```

Download and output the results of a completed compliance job:

```shell
twarc2 get-compliance-job <job-id>
```

### Stitching

The big difference with the v2 API is that some information (users, media,
etc) are not included inline in the tweets and are included as a separate
[extended entities] objects. This cuts down on duplication of information in
a payload (e.g. information about the same user, repeated over and over)
but it also means your output stream will contain individual tweets followed
by an entities object.

If you would like entities to replace the id references in tweets you
can use the `--stitch` option. Depending on your use case this could make
downstream processing easier since it can expect each line to contain
a complete tweet.

```shell
twarc2 search blacklivesmatter --stitch > tweets.jsonl
```

The proposed behavior is that this not be the default behavior, since twarc has been used in the past to display exactly what has been retrieved from the Twitter API.

[twarc]: https://github.com/docnow/twarc
[substantially changed]: https://blog.twitter.com/developer/en_us/topics/tools/2020/introducing_new_twitter_api.html
[totally new]: https://blog.twitter.com/developer/en_us/topics/tips/2020/understanding-the-new-tweet-payload.html
[filter]: https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/introduction
[compliance]: https://developer.twitter.com/en/docs/twitter-api/tweets/compliance/introduction
[extended entities]: https://developer.twitter.com/en/docs/twitter-api/v1/data-dictionary/object-model/extended-entities
