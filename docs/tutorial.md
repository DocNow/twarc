# Twarc Tutorial

- Who this tutorial is for
- Scope and purpose: where will we be at the end of this tutorial?
- Introduction to Twitter and social media data
- Note that this tutorial can be done with the standard API track - academic access is not required, but some parts will point out additional functionality/approaches that can be done with academic access

By the end of this tutorial, you will have:

1. Setup twarc so you can collect data from the Twitter API
2. Constructed two Twitter search queries to address a specific research question
3. Collected data for those two queries
4. Processed the collected data into formats suitable for other analysis
5. Performed basic quantitative evaluation on the two collections

## Motivating Example

This tutorial is built around collecting data from Twitter to address the following research question:

	Which monotreme is the coolest - the echidna or the platypus?


## Before We Begin

- responsibilities when working with social media data
- Twitter terms of service
- Copyright
- Expectations of Privacy


## Setup

### Twitter Developer Access

### Installation

#### Install Python

#### Install Twarc and Plugins


### Configuring Twarc

Now that we have twarc installed, and our Twitter developer access sorted, we need to configure


## What Can We Do with the Twitter API?

- Tour of Different API endpoints and how they map to platform affordances
- Different data types (primarily user focused/tweet focused endpoints)
- Different entity types on the Twitter platforms (URLs, hashtags, mentions, conversations etc)


## Introduction to Twitter Search

- Twitter search is boolean search!
- Overview of some useful operators and examples
- count first, retrieve tweets later
- End by actually collecting some data?

twarc2 search echidna echidna.json
twarc2 search platypus platypus.json


## Handling Twitter JSON data

- Twitter JSON is complex relational data
- twarc-csv plugin as a starting point for some data transformation - other options
- Common gotchas with Twitter data (opening in excel breaks things)
- End with a transformation or exploratory analysis that shows something worth looking into further.

twarc2 csv echidna.json echidna.csv
twarc2 csv platypus.json platypus.csv

twarc2 csv --output-columns id,created_at,author_id,text,referenced_tweets.retweeted.id,public_metrics.like_count echidna.json echidna_minimal.csv
twarc2 csv --output-columns id,created_at,author_id,text,referenced_tweets.retweeted.id,public_metrics.like_count platypus.json platypus_minimal.csv

## Enriching Collected Data

- Based on analysis from the interlude, do something more collected, drawing on the advanced twarc2 CLI functionality likes searches, timelines or conversations


## Final Section: Use the Collected Data to Address the Movating Example

- Needs a better title
- Actually come up with an answer/insight/direction for future work using the collected data to address the question


## Closing: Suggested Next Steps and Resources

Link to suggested "next tutorials" that lead on from this one, without tightly coupling them.
