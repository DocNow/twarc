# Examples of using twarc2 as a library

Please see [client2](client2.md) docs for the full list of available functions. Here are some minimal working snippets of code that use twarc2 as a library.

## Search 

The client implements the API as closely as possible - so if the API docs expect a parameter in a certain way, so does the twarc2 library.

```python
import datetime

from twarc.client2 import Twarc2
from twarc.expansions import ensure_flattened

# Your bearer token here
t = Twarc2(bearer_token="A...z")

# Start and end times must be in UTC
start_time = datetime.datetime(2021, 3, 21, 0, 0, 0, 0, datetime.timezone.utc)
end_time = datetime.datetime(2021, 3, 22, 0, 0, 0, 0, datetime.timezone.utc)

# search_results is a generator, max_results is max tweets per page, 100 max for full archive search with all expansions.
search_results = t.search_all(query="dogs lang:en -is:retweet", start_time=start_time, end_time=end_time, max_results=100)

# Get all results page by page:
for page in search_results:
    # Do something with the whole page of results:
    # print(page)
    # or alternatively, "flatten" results returning 1 tweet at a time, with expansions inline:
    for tweet in ensure_flattened(page):
        # Do something with the tweet
        print(tweet)

    # Stop iteration prematurely, to only get 1 page of results.
    break
```

## Working with Generators

Twarc will try to retrieve all available results and handle retries and rate limits for you. This can potentially retrieve more tweets than your monthly limit will allow. The command line interface has a `--limit` option, but the library returns generator functions and it is upto you to stop iterating when you have retrieved enough results.

For example, to only get 2 "pages" of followers max per user:

```python
from twarc.client2 import Twarc2

# Your bearer token here
t = Twarc2(bearer_token="A...z")

user_ids = [12, 2244994945, 4503599627370241] # @jack, @twitterdev, @overflow64

# Iterate over our target users
for user_id in user_ids:

    # Iterate over pages of followers
    for i, follower_page in enumerate(t.followers(user_id)):

         # Do something with the follower_page here
         print(f"Fetched a page of {len(follower_page['data'])} followers for {user_id}")

         if i == 1: # Only retrieve the first two pages (enumerate starts from 0)
               break
```

## twarc CSV

`twarc-csv` is an extra plugin you can install:

```
pip install twarc-csv
```

This can also be used as a library, for example:

If you have a bunch of data, and want a DataFrame:

```
from twarc_csv import DataFrameConverter

# Default options for Dataframe converter
converter = DataFrameConverter()

# this can be a list or generator of individual tweets or pages or results.
json_objects = [...] 

df = converter.process(json_objects)
```

This doesn't save any files, and converts everything in memory.

If you have a large file, you should use `CSVConverter` as before

```
from twarc_csv import CSVConverter

with open("input.json", "r") as infile:
    with open("output.csv", "w") as outfile:
        converter = CSVConverter(infile=infile, outfile=outfile)
        converter.process()
```

or with additional options:

```
from twarc_csv import CSVConverter, DataFrameConverter

converter = DataFrameConverter(
    input_data_type="tweets",
    json_encode_all=False,
    json_encode_text=False,
    json_encode_lists=True,
    inline_referenced_tweets=True,
    merge_retweets=True,
    allow_duplicates=False,
)

with open("results.jsonl", "r") as infile:
    with open("results.csv", "w") as outfile:
        converter = CSVConverter(infile=infile, outfile=outfile, converter=converter)
        converter.process()

```

`DataFrameConverter` parameters correspond to the command line options: https://github.com/DocNow/twarc-csv#extra-command-line-options

The full list of valid `output_columns` are: https://github.com/DocNow/twarc-csv/blob/main/dataframe_converter.py#L13-L85 when using `input_data_type="tweets"` and https://github.com/DocNow/twarc-csv/blob/main/dataframe_converter.py#L90-L115 when using `input_data_type="users"`. Note that it won't extract users from tweets, these have to be already extracted from the JSON. `twarc-csv` can also process compliance output and counts output.

## Search and write results to CSV example

Here is a complete working example that searches for all recent tweets in the last few hours, writes a `results.jsonl` with the original responses, and then converts this to CSV:

```python
import json
from datetime import datetime, timezone, timedelta

from twarc.client2 import Twarc2
from twarc_csv import CSVConverter

# Your bearer token here
t = Twarc2(bearer_token="A...z")

# Start and end times must be in UTC
start_time = datetime.now(timezone.utc) + timedelta(hours=-3)
# end_time cannot be immediately now, has to be at least 30 seconds ago.
end_time = datetime.now(timezone.utc) + timedelta(minutes=-1)

query = "dogs lang:en -is:retweet has:media"

print(f"Searching for \"{query}\" tweets from {start_time} to {end_time}...")

# search_results is a generator, max_results is max tweets per page, not total, 100 is max when using all expansions.
search_results = t.search_recent(query=query, start_time=start_time, end_time=end_time, max_results=100)

# Get all results page by page:
for page in search_results:
    # Do something with the page of results:
    with open("dogs_results.jsonl", "w+") as f:
        f.write(json.dumps(page) + "\n")
    print("Wrote a page of results...")

print("Converting to CSV...")

# This assumes `results.jsonl` is finished writing.
with open("dogs_results.jsonl", "r") as infile:
    with open("dogs_output.csv", "w") as outfile:
        converter = CSVConverter(infile, outfile)
        converter.process()

print("Finished.")
```
