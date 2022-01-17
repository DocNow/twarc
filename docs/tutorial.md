# Twarc Tutorial

Twarc is a command line tool for collecting Twitter data via Twitter's web Application Programmer Interface (API). This tutorial is aimed at researchers who are new to collecting social media data, and who might be unfamiliar with command line interfaces.

By the end of this tutorial, you
 will have:

1. Familiarised yourself with interacting with a command line application via a terminal
2. Setup twarc so you can collect data from the Twitter API
3. Constructed two Twitter search queries to address a specific research question
4. Collected data for those two queries
5. Processed the collected data into formats suitable for other analysis
6. Performed a simple quantitative comparison of the two collections


## Motivating Example

This tutorial is built around collecting data from Twitter to address the following research question:

	Which monotreme is currently the coolest - the echidna or the platypus?

We'll answer this question with a simple quantitative approach to analysing the collected data - we won't attempt to address all of the different ways that this question could be answered. At the end of this tutorial there are some additional links and resources that provide insight into different analytical approaches that can be taken.


## Before We Begin

Before we dive into the details, it's worth mentioning some broader issues you will need to keep in mind when working with social media data. This is by no means an exhaustive list of issues and is intended as a starting point for further enquiry.

### Ethical use of "Public" Communication

Even though most tweets on Twitter and public, in that they're accessible to anyone on the web, most users of Twitter don't have any expectation that researchers will be reading their tweets for the purpose of research. Researchers need to be mindful of this when working with data from Twitter, and user expectations should be considered as part of the study design. The Association of Internet Researchers has established [Ethical Guidelines for Internet Research](https://aoir.org/ethics/) which are a good starting point for the higher level considerations.

Work has also been done specifically looking at [Twitter users' expectations](https://journals.sagepub.com/doi/10.1177/2056305118763366), with a number of key concerns outlined. For this tutorial we're going to be taking a high level quantitative evaluation of very recent Twitter data, which distances ourselves from the specific tweets and users creating them and aligns with these broader ethical considerations.

Finally, because tweets (and the internet more generally) are searchable, we need to keep in mind that quoting a tweet in whole or part might allow easy reidentification of any specific user or tweet. For this reason care needs to be taken when reporting material from tweets, and common practices in qualitative research may not align with Twitter users' interests or expectations.


### Copyright

This may vary according to where you are in the world but tweets, including the text of the tweet and attached photos and videos are likely to be protected by copyright. As well as the Twitter Developer Agreement considerations in the next section, this may limit what you can do with tweets and media downloaded from Twitter.


### Twitter's Terms of Service

When you signed up for a Twitter developer account you agreed to follow Twitter's [Developer Agreement and Policy](https://developer.twitter.com/en/developer-terms/agreement-and-policy). This agreement constrains how you can use and share Twitter data. While the primary purpose of this agreement is to protect Twitter the company, this policy also incorporates some elements aimed at protecting users of Twitter.

Some particular things to note from the Developer Agreement are:

- Limits on how geolocation data can be used
- How to share data Twitter
- Dealing with deleted Tweets

Note that researchers using deleted tweets were also key concerns for [Twitter users](https://journals.sagepub.com/doi/10.1177/2056305118763366). This tutorial won't cover geolocation data at all, but will cover approaches to addressing data Twitter data and removing deleted material from collections.


### What is an API?

Brief explanation of an API, especially a web API. Also need to include a link to a primer somewhere else.


## Setup

### Twitter Developer Access

### Installing Twarc

#### Install Python

#### Install Twarc and Plugins


## Introduction to Twarc

Explain what a Command Line Interface is

Why use a command line interface?
	- repeatability
	- automation

Provide some brief orientation notes
	- opening a terminal on different platforms
	- a few brief commands that are useful for finding yourself in the system (windows and mac)
	- notes on conventions + reading alound commands
	- structure of a command for a CLI
	- getting help


## What Can We Do With the Twitter API?

Start by outlining what a tweet is? Identify specific affordances.

Tweet vs user focused

- Tour of Different API endpoints and how they map to platform affordances
	+ search
	+ users
	+ hydrate an existing dataset
- Different data types (primarily user focused/tweet focused endpoints)
- Different entity types on the Twitter platforms (URLs, hashtags, mentions, conversations etc)

Endpoints:

- search
- timelines
- followers/following


## Introduction to Twitter Search

- Twitter search is boolean search!
- Overview of some useful operators and examples
- count first, retrieve tweets later
- End by actually collecting some data?

twarc2 search echidna echidna.json
twarc2 search platypus platypus.json


## Understanding and Transforming Twitter JSON data

- Twitter JSON is complex relational data
- twarc-csv plugin as a starting point for some data transformation - other options
- Common gotchas with Twitter data (opening in excel breaks things)
- End with a transformation or exploratory analysis that shows something worth looking into further.

twarc2 csv echidna.json echidna.csv
twarc2 csv platypus.json platypus.csv

twarc2 csv --output-columns id,created_at,author_id,text,referenced_tweets.retweeted.id,public_metrics.like_count echidna.json echidna_minimal.csv
twarc2 csv --output-columns id,created_at,author_id,text,referenced_tweets.retweeted.id,public_metrics.like_count platypus.json platypus_minimal.csv


Note on opening csvs in spreadsheet applications.


## Which Monotreme is the Coolest?

- Needs a better title
- Actually come up with an answer/insight/direction for future work using the collected data to address the question


## Prepare a Dataset for Sharing / Using a Shared Dataset

Having performed this analysis and come to a conclusion, it is good practice to share the underlying data so other people can reproduce these results <footnote: with some caveats>. Noting that we want to preserve Twitter user's agency over the availability of their content, and Twitter's Developer Agreement, we can do this by creating a dataset of tweet IDs. Instead of sharing the content of the tweets, we can share the unique ID for that tweet, which allows others to `hydrate` the tweets by retrieving them again from the Twitter API.

This can be done as follows using twarc's `dehydrate` command:

```
twarc2 dehydrate --id-type tweets platypus.json platypus_ids.txt
twarc2 dehydrate --id-type tweets echidna.json echidna_ids.txt
```

These commands will produce the two text files, with each line in these files containing the unique ID of the tweet.

To `hydrate`, or retrieve the tweets again, we can use the corresponding commands:

```
twarc2 hydrate platypus_ids.txt platypus_hydrated.json
twarc2 hydrate echidna_ids.txt echidna_hydrated.json
```

Note that the hydrated files will include fewer tweets: tweets that have been deleted, or tweets by accounts that have been deleted, suspended, or protected, will not be included in the file.

<Consider deleting the raw tweets when no longer needed>

## Closing: Suggested Next Steps and Resources

Link to suggested "next tutorials" that lead on from this one, without tightly coupling them.
