# Twarc Tutorial

TODO: Sentence case for all of the titles.

Twarc is a command line tool for collecting Twitter data via Twitter's web Application Programmer Interface (API). This tutorial is aimed at researchers who are new to collecting social media data, and who might be unfamiliar with command line interfaces.

By the end of this tutorial, you will have:

1. Familiarised yourself with interacting with a command line application via a terminal
2. Setup twarc so you can collect data from the Twitter API
3. Constructed two Twitter search queries to address a specific research question
4. Collected data for those two queries
5. Processed the collected data into formats suitable for other analysis
6. Performed a simple quantitative comparison of the two collections using Python
7. Prepared a dataset of tweet identifiers that can be shared with other researchers


## Motivating example

This tutorial is built around collecting data from Twitter to address the following research question:

	Which monotreme is currently the coolest - the echidna or the platypus?

We'll answer this question with a simple quantitative approach to analysing the collected data - we won't attempt to address all of the different ways that this question could be answered. At the end of this tutorial there are some additional links and resources that provide insight into different analytical approaches that can be taken.

TODO: make this more concrete here: include how the "coolest" is being operationalised in this context via quantitative summation of like counts.

## Before we begin

Before we dive into the details, it's worth mentioning some broader issues you will need to keep in mind when working with social media data. This is by no means an exhaustive list of issues and is intended as a starting point for further enquiry.

### What is an API?

Brief explanation of an API, especially a web API. Also need to include a link to a primer somewhere else.

TODO: Is this the right section? Maybe it should go in with the introduction to twarc so the explanation is in context?

### What can you do with the Twitter API?

To start working with the Twitter API it's best to refresh our memory of what a tweet is. Most of the functionality available in the Twitter API focuses on finding and retrieving tweets, or the users who post them.

![Annotated screenshot of a tweet showing affordances]()

This will be a high level description of what you can do with the Twitter API - not endpoint by endpoint.

EG:

- Historical tweets containing particular content like words or phrases
- Live tweets matching ...
- Tweets using hashtags or mentioning particular users
- Tweets made by a particular user
- likes/retweets
- followers/followees

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
- streaming

The rest of this tutorial is going to focus on using the Twitter search API to retrieve tweets containing content relevant to the research question. We've chosen to focus on this because:

1. With the rich functionality available in the search API the data collection for many projects can be condensed down to a few carefully chosen searches.
2. With the academic access track it's possible to search the entire Twitter archive, making search uniquely powerful among the endpoints Twitter supports. 

### Ethical use of "public" communication

Even though most tweets on Twitter and public, in that they're accessible to anyone on the web, most users of Twitter don't have any expectation that researchers will be reading their tweets for the purpose of research. Researchers need to be mindful of this when working with data from Twitter, and user expectations should be considered as part of the study design. The Association of Internet Researchers has established [Ethical Guidelines for Internet Research](https://aoir.org/ethics/) which are a good starting point for the higher level considerations.

Work has also been done specifically looking at [Twitter users' expectations](https://journals.sagepub.com/doi/10.1177/2056305118763366), with a number of key concerns outlined. For this tutorial we're going to be taking a high level quantitative evaluation of very recent Twitter data, which distances ourselves from the specific tweets and users creating them and aligns with these broader ethical considerations.

Finally, because tweets (and the internet more generally) are searchable, we need to keep in mind that quoting a tweet in whole or part might allow easy reidentification of any specific user or tweet. For this reason care needs to be taken when reporting material from tweets, and common practices in qualitative research may not align with Twitter users' interests or expectations.

### Copyright

This may vary according to where you are in the world but tweets, including the text of the tweet and attached photos and videos are likely to be protected by copyright. As well as the Twitter Developer Agreement considerations in the next section, this may limit what you can do with tweets and media downloaded from Twitter.


### Twitter's terms of service

When you signed up for a Twitter developer account you agreed to follow Twitter's [Developer Agreement and Policy](https://developer.twitter.com/en/developer-terms/agreement-and-policy). This agreement constrains how you can use and share Twitter data. While the primary purpose of this agreement is to protect Twitter the company, this policy also incorporates some elements aimed at protecting users of Twitter.

Some particular things to note from the Developer Agreement are:

- Limits on how geolocation data can be used
- How to share Twitter data
- Dealing with deleted tweets

Note that researchers using deleted tweets were also key concerns for [Twitter users](https://journals.sagepub.com/doi/10.1177/2056305118763366). This tutorial won't cover geolocation data at all, but will cover approaches to sharing Twitter data and removing deleted material from collections.


## Setup

Twarc is a command line application, written in the Python programming language. To get Twarc running on our machines, we're going to need to install Python, then install Twarc itself, and we will also need to setup a Twitter developer account.

### Twitter developer access

[Start here](https://developer.twitter.com/en/apply-for-access) to apply for a Twitter developer account and follow the steps in [our developer access guide](twitter-developer-access.md). For this tutorial, you can skip step 2, as we won't require academic access.

Once you have the `bearer_token` you are ready for the next step. This token is like a password, so you shouldn't share it with other people. You will also need to be able to enter this token once to configure Twarc, so it would be best to copy and paste it to a text file on your local machine until we've finished configuration.

### Install Python

#### Windows

Install the latest version [for Windows](https://www.python.org/downloads/windows/). You will need to set the path, as shown in the screenshot below.

![Screenshot showing the path selection settings on window]()

#### Mac

Install the latest version [for Mac](https://www.python.org/downloads/macos/). No additional setup should be necessary for Python.


### Install Twarc and other utilities

For this tutorial we're going to install three Python packages, `twarc`, an extension called `twarc-csv`, and `pandas`, a Python library for data analysis. We will use a command line interface to install these packages. On Windows we will use the `cmd` console, which can be found by searching for `cmd` from the start menu - you should see a prompt like the below screenshot. On Mac you can open the `Terminal` app.

![Screenshot showing the opening of the cmd window on windows]()
![Screenshot showing the open cmd prompt]()

Once you have a terminal open we can run the following command to install the necessary packages:

> pip install twarc twarc-csv pandas

You should see output similar to the following:

![Screenshot showing the output of installing twarc and twarc-csv]()


## Introduction to Twarc

Twarc is at it's core an application for interacting with the Twitter API, reading results from the different functionality the API offers, and safely writing the collected data to your machine for further analysis. Twarc handles the mechanical details of interacting with the Twitter API like including information to authenticate yourself, making HTTP requests to the API, formatting data in the right way, and retrying when things on the internet fail. Your job is to work out 1.) Which endpoint you want to call on from the Twitter API 2.) Which data you want to retrieve from that endpoint.

Twarc is a command line based application - to use twarc you type a command specifying a particular action, and the results of that command are shown as text on screen. If you haven't used a command line interface before, don't worry! Although there is a bit of a learning curve at the beginning, you will quickly get the hang of it - and because everything is a typed command, it is very easy to record and share _exactly_ how you collected data with other people. 

### Our first command/making sure everything is working

Let's open a terminal and get started - just like when installing twarc, you will want to use the `cmd` application on windows and the `Terminal` application on Mac.

The first command we want to run is to check if everything in twarc is installed and working correctly. We'll use twarc's builtin `help` for this. Running the following command should show you a brief overview of the functionality that the twarc2 command provides and some of the options available:

```
twarc2 --help
```

![Screenshot showing the default help output on windows]()

Twarc is structured like many other command line applications: there is a single main command, `twarc2`, to launch the application, and then you provide a subcommand, or additional arguments, or flags to provide additional context about what that command should actually do. In this case we're only launching the `twarc2` command, and providing a single _flag_ `--help` (the double-dash syntax is usually used for this). Most terminal applications will have a `--help` or `-h` flag that will provide some useful information about the application you're running. This often includes example usage, options, and a short description.

Note also that often when reading commands out loud, the space in between words is not mentioned explicitly: the command above might be read as "twarc-two dash dash help".

Though we won't cover the command line outside of using Twarc in this tutorial, your operating systems command line functionality is extensive and can help you automate a lot of otherwise tedious tasks. If you're interested in learning more the [Software Carpentry lesson on the shell](https://swcarpentry.github.io/shell-novice/) is a good starting point.


### Configuring twarc with our bearer token

The next thing we want to do is tell twarc about our bearer token so we can authenticate ourselves with the Twitter API. This can be done using twarc's `configure` command. In this case we're going to use the `twarc2` main command, and provide it with the subcommand `configure` to tell twarc we want to start the configuration process.

```
twarc2 configure
```

On running this command twarc will prompt us to paste our bearer token, as shown in the screenshot below. After entering our token, we will be prompted to enter additional information - this is not necessary for this tutorial, so we will skip this step by typing the letter `n` and hitting `enter`.

![Redacted output of what twarc configure looks like]()


## Introduction to Twitter Search and Counts

To tackle the research question we're interesting in we're going to use the search endpoint to retrieve two sets of tweets: those using the word echidna, and those using the word platypus.

There are two key commands that the Twitter API provides for search: a `search` endpoint to retrieve tweets matching a particular, and a `counts` endpoint to tell you how many tweets match that query over time. It's always a good idea to start with the `counts` endpoint first, because:

- it lets you establish early on how many tweets you will need to deal with: too many or too few matching tweets will help you determine whether your search strategy is reasonable
- it can take a long time to retrieve large numbers of tweets and its better to know in advance how much data you will need to deal with
- the count and trend over time is useful in and of itself
- if you accidentally search for the wrong thing you can consume your monthly quota of tweets without collecting anything useful

Let's get started with the `counts` API - in twarc this is accessible by the command `counts`. As before `twarc2` is our entry command, `counts` is the subcommand we're interested in, and the `echidna` is what we're interested in searching for on Twitter (the query). 

`twarc2 counts echidna`

You should see something like the below screenshot - and yes, this output isn't very readable! By default twarc shows us the response in the JSON format directly from the Twitter API, so it's not great for using directly on the command line.

![screenshot of the first command run in a query]()

Let's improve this by updating our command to:

`twarc2 counts echidna --text --granularity day`

And we should see output like below. Note that the `--text` and `--granularity` are optional flags provided to the `twarc2 counts` command, we can see other options by running `twarc2 counts --help`. In this case `--text` returns a simplified text output for easier reading, and `--granularity day` is passed to the Twitter API to specify that we're interested only in daily counts of tweets, not the default hourly count.

<table of results>

Note that this is only the count for the last seven days - this is the level of search functionality available for all developers via the standard track of the Twitter API. If you have access to the Twitter Academic track (TODO: link), you can switch to searching the full Twitter archive from the `counts` and `search` commands by adding the `--archive` flag.

Twitter search is powerful and provides many rich options. However it also functions a little differently to most other search engines, because Twitter search does not focus on _ranking_ tweets by relevance (like a web search engine does), but retrieving all matching tweets in chronological order. 

- Twitter search is boolean search!
- Overview of some useful operators and examples

(Probably worth mentioning that most of this can be tried on the web interface)

Progression of commands/ :


twarc2 counts "echidna echidna's echidnas" --granularity day --text # Problem solving: capture plurals, use quotes for complicated queries
twarc2 counts "echidna OR echidna's OR echidnas" --granularity day --text # -operator excludes tweets that match this, so is:retweet is only retweets, -is:retweet excludes retweets. Default search combination is AND - no results unless we tell it otherwise
twarc2 counts "echidna OR echidna's OR echidnas -is:retweet" --granularity day --text   # Need brackets otherwise the and is applied first, 
twarc2 counts "(echidna OR echidna's OR echidnas) -is:retweet"

Then for platypus we could do the same thing:
twarc2 counts "(platypus OR platpus's OR platypi OR platypusses) -is:retweet"

Or we could go even further, and make sure we exclude tweets that mention the other animal - we won't use this for this example but it might be important for some use cases.
Lesson: you can build long and complicated queries for Twitter search.
twarc2 counts "(platypus OR platpus's OR platypi OR platypusses) -(echidna OR echidna's OR echidnas) -is:retweet"

Actually perform the search!
First run without the 
twarc2 search "(echidna OR echidna's OR echidnas) -is:retweet" echidna.json


### Recap

- search operators we used and brief mention that there are other options like hashtags aand urls, see twitter docs
- the workflow/iterative steps we used

## Understanding and Transforming Twitter JSON data

Now that we've collected some data, it's time to take a look at it. Let's start by viewing the collected data in it's plainest form: as a text file. Although we named the file with an extension of `.json`, this is just a convention: the actual file content is a plain text in the [JSON](https://en.wikipedia.org/wiki/JSON) format. Let's open this file with our inbuilt text editor (notepad on Windows, ... on Mac).

![Screenshot of the json file in notepad]()

You'll notice immediately that there is a *lot* of data in that file: tweets are rich objects, and we mentioned that twarc by default captures as much information as Twitter makes available. Further, the Twitter API provides data in a format that makes it convenient for machines to work with, but not so much for humans.

## Making a CSV file from our collected tweets

We don't recommend trying to manually parse this raw data unless you have specific needs that aren't covered by existing tools. So we're going to use the `twarc-csv` package that we installed earlier to do the heavy lifting of transforming the collected JSON into a more friendly comma-separated value ([CSV](https://en.wikipedia.org/wiki/Comma-separated_values)) file. CSV is a simple plaintext format, but unlike JSON format is easy to import or open with a spreadsheet. 

The `twarc-csv` package lets us use a `csv` command to transform the files from twarc:

```
twarc2 csv echidna.json echidna.csv
twarc2 csv platypus.json platypus.csv
```

If we look at these files in our text editor again, we'll see a nice structure of one line per tweet, with all of the many columns for that tweet. 

![Screenshot of the plaintext CSV file in notepad]()

Since we're going to do more analysis with the Pandas library to answer our question, we will want to create the CSV with only the columns of interest. This will reduce the time and amount of RAM you need to load your dataset. For example, the following commands produce CSV files with a small number of fields: 

```
twarc2 csv --output-columns id,created_at,author_id,text,referenced_tweets.retweeted.id,public_metrics.like_count echidna.json echidna_minimal.csv
twarc2 csv --output-columns id,created_at,author_id,text,referenced_tweets.retweeted.id,public_metrics.like_count platypus.json platypus_minimal.csv
```

### The problem with Excel

It's tempting to try to open these CSV files directly in Excel, but if you do you're probably going to notice one or more of the following problems, as illustrated below:

1. The ID columns are likely to be broken.
2. Emoji and languages that don't use latin characters may not appear correctly.
3. Tweets may be broken up on newlines.
4. Excel can only support 1,048,576 rows - it's very easy to collect tweet datasets bigger than this.

![Screenshot of the broken CSV file opened directly in excel]()

If you save a file from Excel with any of those problems that file is no longer useful for most purposes (this is a common and longstanding problem with using spreadsheet software, that affects many fields. For example in genomics: https://www.nature.com/articles/d41586-021-02211-4). While it is possible to make Excel do the right thing with your data, it takes more work, and a single mistake can lead to loss of important data. Therefore our recommendation is, if possible, to avoid the use of spreadsheets for analysing Twitter data.

### Working with Pandas

To avoid the issues with Excel we're going to use the Python library [Pandas](https://pandas.pydata.org/). This is used to load and manipulate data like we have in our CSV file. Note that for this section we're going to run a very simple computation, the references will have links to more extensive resources for learning more.

TODO: Decide whether to run as a script, or interactively.

```python
import pandas

echidna = pandas.read_csv("echidna_minimal.csv")
platypus = pandas.read_csv("platypus_minimal.csv")

echidna_likes = echidna["public_metrics.like_count"].sum()
platypus_likes = platypus["public_metrics.like_count"].sum()

print(f"Total likes on echidna tweets: {echidna_likes}. Total likes on platypus tweets: {platypus_likes}.")
```

Run this script through Python to see which of the monotremes is the coolest:

`python process_monotremes.py`

### Answering the research question: which monotreme is the coolest?

At the time of creating this tutorial, the above script run with the just collected data leads to the following result:

`Total likes on echidna tweets: 1787652. Total likes on platypus tweets: 3462715.`

On that basis, we can conclude that at the time of running this search the platypus is nearly twice as cool as measured by Twitter likes. 

Of course this is a simplistic approach to answering this specific research question - we could have made many other choices. Even using a simple quantitative approach looking at metrics: we could have chosen to look at other engagement counts like the number of retweets, or looked at the number of followers of the accounts tweeting about each animal (because a "cooler" account will have more followers). Much of the challenge in using Twitter for research is both about asking the right research question and also the choosing the right approach to the data to address that research question.

## Prepare a Dataset for Sharing / Using a Shared Dataset

Having performed this analysis and come to a conclusion, it is good practice to share the underlying data so other people can reproduce these results (with some caveats). Noting that we want to preserve Twitter user's agency over the availability of their content, and Twitter's Developer Agreement, we can do this by creating a dataset of tweet IDs. Instead of sharing the content of the tweets, we can share the unique ID for that tweet, which allows others to `hydrate` the tweets by retrieving them again from the Twitter API.

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

Note that the hydrated files will include fewer tweets: tweets that have been deleted, or tweets by accounts that have been deleted, suspended, or protected, will not be included in the file. Note also that hydrating a dataset also means that engagement metrics like retweets and likes will be up to date for tweets that are still available.


## Next Steps and Suggested Resources

TODO: Link to suggested "next tutorials" that lead on from this one, without tightly coupling them.
