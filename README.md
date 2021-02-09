# twarc2 🐦🐍💾

twarc2 is a *proposed* evolution of [twarc] custom made for the new Twitter v2 API.
Twitter [substantially changed] their API in July 2020. Twitter plans to deprecate the
v1.1 and premium endpoints. While some of the API calls seem similar the most
significant change is the response payload with is [totally new]. The representation of
a tweet now can take a very different shape depending on what you ask for and how you
ask for it. 

## Design principles for twarc2

- twarc2's primary use case is collection and archiving of Twitter API data, especially
  for research purposes
- twarc2 should be usable and tested as both a library for integration with other
  software, and as a command line tool
- twarc2 by default should capture as comprehensive data as possible from the Twitter 
  API
- twarc2 should encourage workflows that preserve raw Twitter API responses as a 
  reproducible and interoperable baseline for data storage
- Reuse as many of the battletested parts of the current Twarc implementation as 
  possible
- Up to the limitations of the new API, enable an easy migration to the Twitter V2 API
  endpoints
- Release early and release often to allow people to test and work against new 
  functionality/identify problems as soon as possible
- Listen to users to find the right balance between simplicity and ease of use against 
  flexibility and additional functionality

## Data Collection Architecture and Components

The proposed architecture is broadly aligned with existing twarc functionality:

- A new Twarc2 client, parallel to the existing Twarc client
- Functionality to read configuration details (whether from the existing config files or
  elsewhere is to be determined).
- A command line interface module that calls and configures the Twarc2 client


## Transition Plan

Maintain Twarc classic as is - as long as v1.1 endpoints are still supported, there 
will be a v1.1 compatible client. However, as Twitter deprecates functionality, the
corresponding twarc functionality will be removed, with a transitional stub describing a
way forward in twarc2. For example, calling `twarc.sample` after the streams endpoints
are removed could raise an error describing the `twarc2.sample` method. This should also
be supported through the command line.

## Implementation Plan

This is a proposed set of things to be done, in an approximate order. Once the initial
client and command line structure is in place, it should be straightforward to build
out the rest of the API functionality on that baseline.

- Layout a minimal Twarc2 client object. This allows us to tackle the work of
interacting with the new API as soon as possible so we can get a better community
understanding of the technical issues, as well as collecting new format data to work
with other tools. 
- Layout the new CLI for data collection on top of the client, resolving the initial
needs for configuration and/or profile management. 
- Implement a tentative workflow for data transformation/conformance between v1.1 and v2
collected data


## Command Line Interface

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

## Utilities and Data Formats

Since the v2 Twitter API changes the data formats in a fundamental way, existing tools
and pipelines, including the utilities scripts will no longer work with Twitter data
collected through twarc2. Since it is likely that during the transition period and
afterwards there will be many mixed data collections, instead of porting existing
utilities to the new data format it is proposed that data handling is supported by twarc
as additional functionality, separate from data collection, and working in a readonly
fashion on collected data. As additional advantages, this also makes it easier to 
support future changes in the Twitter API by updating only the transform process, and
allows a starting point for external packages to extend the utils.

To support this, and better handle future change, we propose: 

- providing a workflow that can process v1.1 and v2 data into a common schema (such as
  into an SQLite database)
- port the existing utilities to read from that schema
- provide some architectural support, to elevate the utilities folder from a set of 
  scripts in a github repo to a part of twarc itself.

A hypothetical example of this workflow might be:

```shell
# Collect some data using the search API
twarc2 search auspol --output auspol_v2.jsonl

# Preprocess the data into the common schema, including some existing data
# This is a non-destructive operation, the existing files are only read.
# The transform process handles common data quality issues like deduplication of tweets.
twarc2 transform auspol.db --files auspol_v2.jsonl auspol_v1.1.jsonl

# Read a flat file from that data
twarc2 utils to_csv auspol.db --output output.csv

# Generate a hashtag cooccurrence network
twarc2 utils hashtag_cooccurrence auspol.db --output hashtag_network.graphml
```

This common schema could also be a base for further analysis (for example natively 
through SQLite/programming languages), or through tools like Tableau and Excel that 
can read from the database directly.

[twarc]: https://github.com/docnow/twarc
[substantially changed]: https://blog.twitter.com/developer/en_us/topics/tools/2020/introducing_new_twitter_api.html
[totally new]: https://blog.twitter.com/developer/en_us/topics/tips/2020/understanding-the-new-tweet-payload.html
[filter]: https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/introduction
[compliance]: https://developer.twitter.com/en/docs/twitter-api/tweets/compliance/introduction
[extended entities]: https://developer.twitter.com/en/docs/twitter-api/v1/data-dictionary/object-model/extended-entities
