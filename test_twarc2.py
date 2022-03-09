import os
import pytz
import twarc
import dotenv
import pytest
import logging
import pathlib
import datetime
import threading

from unittest import TestCase
from twarc.version import version, user_agent

dotenv.load_dotenv()
consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
bearer_token = os.environ.get("BEARER_TOKEN")
access_token = os.environ.get("ACCESS_TOKEN")
access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")

test_data = pathlib.Path("test-data")
logging.basicConfig(filename="test.log", level=logging.INFO)

# Implicitly test the constructor in application auth mode. This ensures that
# the tests don't depend on test ordering, and allows using the pytest
# functionality to only run a single test at a time.

T = twarc.Twarc2(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
)


def test_version():
    import setup

    assert setup.version == version

    assert user_agent
    assert f"twarc/{version}" in user_agent


def test_auth_types_interaction():
    """
    Test the various options for configuration work as expected.
    """

    # 1. bearer_token auth -> app auth
    tw = twarc.Twarc2(bearer_token=bearer_token)
    assert tw.auth_type == "application"

    for response in tw.user_lookup(range(1, 101)):
        assert response["data"]

    tw.client.close()

    # 2. consumer_keys
    tw = twarc.Twarc2(consumer_key=consumer_key, consumer_secret=consumer_secret)
    assert tw.auth_type == "application"

    for response in tw.user_lookup(range(1, 101)):
        assert response["data"]

    tw.client.close()

    # 3. Full user auth
    tw = twarc.Twarc2(
        access_token=access_token,
        access_token_secret=access_token_secret,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
    )
    assert tw.auth_type == "user"

    for response in tw.user_lookup(range(1, 101)):
        assert response["data"]

    tw.client.close()

    with pytest.raises(twarc.client2.InvalidAuthType):
        tw.sample()


def test_sample():
    # event to tell the filter stream to close
    event = threading.Event()

    for count, result in enumerate(T.sample(event=event)):
        assert int(result["data"]["id"])

        # users are passed by reference an dincluded as includes
        user_id = result["data"]["author_id"]
        assert len(pick_id(user_id, result["includes"]["users"])) == 1

        if count > 10:
            # close the sample
            event.set()

    assert count == 11


def test_search_recent():

    found_tweets = 0
    pages = 0

    for response_page in T.search_recent("#auspol"):
        pages += 1
        tweets = response_page["data"]
        found_tweets += len(tweets)

        if pages == 3:
            break

    assert 200 <= found_tweets <= 300


def test_counts_recent():

    found_counts = 0

    for response_page in T.counts_recent("twitter is:verified", granularity="day"):
        counts = response_page["data"]
        found_counts += len(counts)
        break

    assert 7 <= found_counts <= 8


@pytest.mark.skipif(
    os.environ.get("SKIP_ACADEMIC_PRODUCT_TRACK") != None,
    reason="No Academic Research Product Track access",
)
def test_counts_empty_page():

    found_counts = 0

    for response_page in T.counts_all(
        "beans",
        start_time=datetime.datetime(2006, 3, 21),
        end_time=datetime.datetime(2006, 6, 1),
        granularity="day",
    ):
        counts = response_page["data"]
        found_counts += len(counts)

    assert found_counts == 72


def test_search_times():
    found = False
    now = datetime.datetime.now(tz=pytz.timezone("Australia/Melbourne"))
    # twitter api doesn't resolve microseconds so strip them for comparison
    now = now.replace(microsecond=0)
    end = now - datetime.timedelta(seconds=60)
    start = now - datetime.timedelta(seconds=61)

    for response_page in T.search_recent("tweet", start_time=start, end_time=end):
        for tweet in response_page["data"]:
            found = True
            # convert created_at to datetime with utc timezone
            dt = tweet["created_at"].strip("Z")
            dt = datetime.datetime.fromisoformat(dt)
            dt = dt.replace(tzinfo=datetime.timezone.utc)
            assert dt >= start
            assert dt <= end

    assert found


def test_user_ids_lookup():
    users_found = 0
    users_not_found = 0

    for response in T.user_lookup(range(1, 1000)):

        for profile in response["data"]:
            users_found += 1

        for error in response["errors"]:
            # Note that errors includes lookup of contained entitites within a
            # tweet, so a pinned tweet that doesn't exist anymore results in an
            # additional error entry, even if the profile is present.
            if error["resource_type"] == "user":
                users_not_found += 1

    assert users_found >= 1
    assert users_found + users_not_found == 999


def test_usernames_lookup():
    users_found = 0
    usernames = ["jack", "barackobama", "rihanna"]
    for response in T.user_lookup(usernames, usernames=True):
        for profile in response["data"]:
            users_found += 1
    assert users_found == 3


def test_tweet_lookup():

    tweets_found = 0
    tweets_not_found = 0

    for response in T.tweet_lookup(range(1000, 2000)):

        for tweet in response["data"]:
            tweets_found += 1

        for error in response["errors"]:
            # Note that errors includes lookup of contained entitites within a
            # tweet, so a pinned tweet that doesn't exist anymore results in an
            # additional error entry, even if the profile is present.
            if error["resource_type"] == "tweet":
                tweets_not_found += 1

    assert tweets_found >= 1
    assert tweets_found + tweets_not_found == 1000


# Alas, fetching the stream in GitHub action yields a 400 HTTP error
# maybe this will go away since it used to work fine.


@pytest.mark.skipif(
    os.environ.get("GITHUB_ACTIONS") != None,
    reason="stream() seems to throw a 400 error under GitHub Actions?!",
)
def test_stream():
    # remove any active stream rules
    rules = T.get_stream_rules()
    if "data" in rules and len(rules["data"]) > 0:
        rule_ids = [r["id"] for r in rules["data"]]
        T.delete_stream_rule_ids(rule_ids)

    # make sure they are empty
    rules = T.get_stream_rules()
    assert "data" not in rules

    # add two rules
    rules = T.add_stream_rules(
        [{"value": "hey", "tag": "twarc-test"}, {"value": "joe", "tag": "twarc-test"}]
    )
    assert len(rules["data"]) == 2

    # make sure they are there
    rules = T.get_stream_rules()
    assert len(rules["data"]) == 2

    # these properties should be set
    assert rules["data"][0]["id"]
    assert rules["data"][0]["tag"] == "twarc-test"
    assert rules["data"][1]["id"]
    assert rules["data"][1]["tag"] == "twarc-test"

    # the order of the values is not guaranteed
    assert "hey" in [r["value"] for r in rules["data"]]
    assert "joe" in [r["value"] for r in rules["data"]]

    # collect some data
    event = threading.Event()
    for count, result in enumerate(T.stream(event=event)):
        assert result["data"]["id"]
        assert result["data"]["text"]
        assert len(result["matching_rules"]) > 0
        for rule in result["matching_rules"]:
            assert rule["id"]
            assert rule["tag"] == "twarc-test"
        if count > 25:
            event.set()
    assert count > 25

    # delete the rules
    rule_ids = [r["id"] for r in rules["data"]]
    T.delete_stream_rule_ids(rule_ids)

    # make sure they are gone
    rules = T.get_stream_rules()
    assert "data" not in rules


def test_timeline():
    """
    Test the user timeline endpoints.

    """
    # get @jack's first pages of tweets and mentions
    found = 0
    for pages, tweets in enumerate(T.timeline(12)):
        found += len(tweets["data"])
        if pages == 3:
            break
    assert found >= 200

    found = 0
    for pages, tweets in enumerate(T.mentions(12)):
        found += len(tweets["data"])
        if pages == 3:
            break
    assert found >= 200


def test_timeline_username():
    """
    Test the user timeline endpoints with username.

    """

    found = 0
    for pages, tweets in enumerate(T.timeline("jack")):
        found += len(tweets["data"])
        if pages == 3:
            break
    assert found >= 200

    found = 0
    for pages, tweets in enumerate(T.mentions("jack")):
        found += len(tweets["data"])
        if pages == 3:
            break
    assert found >= 200


def test_missing_timeline():
    results = T.timeline(1033441111677788160)
    assert len(list(results)) == 0


def test_follows():
    """
    Test followers and and following.

    """

    found = 0
    for pages, users in enumerate(T.following(12)):
        pages += 1
        found += len(users["data"])
        if pages == 2:
            break
    assert found >= 1000

    found = 0
    for pages, users in enumerate(T.followers(12)):
        found += len(users["data"])
        if pages == 2:
            break
    assert found >= 1000


def test_follows_username():
    """
    Test followers and and following by username.

    """

    found = 0
    for pages, users in enumerate(T.following("jack")):
        pages += 1
        found += len(users["data"])
        if pages == 2:
            break
    assert found >= 1000

    found = 0
    for pages, users in enumerate(T.followers("jack")):
        found += len(users["data"])
        if pages == 2:
            break
    assert found >= 1000


def test_flattened():
    """
    This test uses the search API to test response flattening. It will look
    at each tweet to find evidence that all the expansions have worked. Once it
    finds them all it stops. If it has retrieved 500 tweets and not found any
    of the expansions it stops and assumes that something is not right. This
    500 cutoff or the query may need to be adjusted based on experience.
    """
    found_geo = False
    found_in_reply_to_user = False
    found_attachments_media = False
    found_attachments_polls = False
    found_entities_mentions = False
    found_referenced_tweets = False

    count = 0

    for response in T.search_recent(
        "(vote poll has:hashtags has:mentions -is:retweet) OR (checked into has:images -is:retweet)"
    ):
        # Search api always returns a response of tweets with metadata but flatten
        # will put these in a list
        tweets = twarc.expansions.flatten(response)
        assert len(tweets) > 1

        for tweet in tweets:
            count += 1

            assert "id" in tweet
            logging.info("got search tweet #%s %s", count, tweet["id"])

            author_id = tweet["author_id"]
            assert "author" in tweet
            assert tweet["author"]["id"] == author_id

            if "in_reply_to_user_id" in tweet:
                assert "in_reply_to_user" in tweet
                found_in_reply_to_user = True

            if "attachments" in tweet:
                if "media_keys" in tweet["attachments"]:
                    assert "media" in tweet["attachments"]
                    assert tweet["attachments"]["media"]
                    assert tweet["attachments"]["media"][0]["width"]
                    found_attachments_media = True
                if "poll_ids" in tweet["attachments"]:
                    assert "poll" in tweet["attachments"]
                    assert tweet["attachments"]["poll"]
                    found_attachments_polls = True

            if "geo" in tweet:
                assert tweet["geo"]["place_id"]
                assert tweet["geo"]["place_id"] == tweet["geo"]["id"]
                found_geo = True

            if "entities" in tweet and "mentions" in tweet["entities"]:
                assert tweet["entities"]["mentions"][0]["username"]
                found_entities_mentions = True

            # need to ensure there are no errors because a referenced tweet
            # might be protected or deleted in which case it would not have been
            # included in the response and would not have been flattened
            if "errors" not in response and "referenced_tweets" in tweet:
                assert tweet["referenced_tweets"][0]["text"]
                found_referenced_tweets = True

        if (
            found_geo
            and found_in_reply_to_user
            and found_attachments_media
            and found_attachments_polls
            and found_entities_mentions
            and found_referenced_tweets
        ):
            logging.info("found all expansions!")
        elif count > 10000:
            logging.info("didn't find all expansions in 10000 tweets")

    assert found_geo, "found geo"
    assert found_in_reply_to_user, "found in_reply_to_user"
    assert found_attachments_media, "found media"
    assert found_attachments_polls, "found polls"
    assert found_entities_mentions, "found mentions"
    assert found_referenced_tweets, "found referenced tweets"


def test_ensure_flattened():
    resp = next(T.search_recent("twitter", max_results=20))

    # flatten a response
    flat1 = twarc.expansions.ensure_flattened(resp)
    assert isinstance(flat1, list)
    assert len(flat1) > 1
    assert "author" in flat1[0]

    # flatten the flattened list
    flat2 = twarc.expansions.ensure_flattened(flat1)
    assert isinstance(flat2, list)
    assert len(flat2) == len(flat1)
    assert "author" in flat2[0]

    # flatten a tweet object which will force it into a list
    flat3 = twarc.expansions.ensure_flattened(flat2[0])
    assert isinstance(flat3, list)
    assert len(flat3) == 1

    # flatten an object without includes:
    # List of records, data is a dict:
    flat4 = twarc.expansions.ensure_flattened([{"data": {"fake": "tweet"}}])
    assert isinstance(flat4, list)
    assert len(flat4) == 1
    # 1 record, data is a dict:
    flat5 = twarc.expansions.ensure_flattened({"data": {"fake": "tweet"}})
    assert isinstance(flat5, list)
    assert len(flat5) == 1
    # List of records, data is a list:
    flat6 = twarc.expansions.ensure_flattened([{"data": [{"fake": "tweet"}]}])
    assert isinstance(flat6, list)
    assert len(flat6) == 1
    # 1 record, data is a list:
    flat7 = twarc.expansions.ensure_flattened({"data": [{"fake": "tweet"}]})
    assert isinstance(flat7, list)
    assert len(flat7) == 1
    TestCase().assertDictEqual(flat4[0], flat5[0])
    TestCase().assertDictEqual(flat6[0], flat7[0])
    TestCase().assertDictEqual(flat4[0], flat7[0])

    resp.pop("includes")
    flat8 = twarc.expansions.ensure_flattened(resp)
    assert len(flat8) > 1
    # Flatten worked without includes, wrote empty object:
    assert "author" in flat8[0]
    TestCase().assertDictEqual(flat8[0]["author"], {})

    # If there's some other type of data:
    with pytest.raises(ValueError):
        twarc.expansions.ensure_flattened([[{"data": {"fake": "list_of_lists"}}]])


def test_ensure_user_id():
    """
    Test _ensure_user_id's ability to discriminate correctly between IDs and
    screen names.
    """
    # presumably IDs don't change
    assert T._ensure_user_id("jack") == "12"

    # should hold for all users, even if the screen name exists
    assert T._ensure_user_id("12") == "12"

    # this is a screen name but not an ID
    # would help to find more "stable" example?
    assert T._ensure_user_id("42069") == "17334495"
    # should 42069 passed as int return ID or screen name?

    assert T._ensure_user_id("1033441111677788160") == "1033441111677788160"
    assert T._ensure_user_id(1033441111677788160) == "1033441111677788160"


def test_liking_users():

    # This is one of @jack's tweets about the Twitter API
    likes = T.liking_users(1460417326130421765)

    like_count = 0

    for page in likes:
        assert "data" in page
        # These should be user objects.
        assert "description" in page["data"][0]
        like_count += len(page["data"])
        if like_count > 300:
            break


def test_retweeted_by():

    # This is one of @jack's tweets about the Twitter API
    retweet_users = T.retweeted_by(1460417326130421765)

    retweet_count = 0

    for page in retweet_users:
        assert "data" in page
        # These should be user objects.
        assert "description" in page["data"][0]
        retweet_count += len(page["data"])
        if retweet_count > 150:
            break


def test_liked_tweets():

    # What has @jack liked?
    liked_tweets = T.liked_tweets(12)

    like_count = 0

    for page in liked_tweets:
        assert "data" in page
        # These should be tweet objects.
        assert "text" in page["data"][0]
        like_count += len(page["data"])
        if like_count > 300:
            break


def test_list_lookup():
    parks_list = T.list_lookup(715919216927322112)
    assert "data" in parks_list
    assert parks_list["data"]["name"] == "National-parks"


def test_list_members():
    response = list(T.list_members(715919216927322112))
    assert len(response) == 1
    members = twarc.expansions.flatten(response[0])
    assert len(members) == 8


def test_list_followers():
    response = list(T.list_followers(715919216927322112))
    assert len(response) >= 2
    followers = twarc.expansions.flatten(response[0])
    assert len(followers) > 50


def test_list_memberships():
    response = list(T.list_memberships("64flavors"))
    assert len(response) == 1
    lists = twarc.expansions.flatten(response[0])
    assert len(lists) >= 9


def test_followed_lists():
    response = list(T.followed_lists("nasa"))
    assert len(response) == 1
    lists = twarc.expansions.flatten(response[0])
    assert len(lists) >= 1


def test_owned_lists():
    response = list(T.owned_lists("nasa"))
    assert len(response) >= 1
    lists = twarc.expansions.flatten(response[0])
    assert len(lists) >= 11


def test_twarc_metadata():

    # With metadata (default)
    event = threading.Event()
    for i, response in enumerate(T.sample(event=event)):
        assert "__twarc" in response
        if i == 10:
            event.set()

    for response in T.tweet_lookup(range(1000, 2000)):
        assert "__twarc" in response
        assert "__twarc" in twarc.expansions.flatten(response)[0]

    # Witout metadata
    T.metadata = False
    event = threading.Event()
    for i, response in enumerate(T.sample(event=event)):
        assert "__twarc" not in response
        if i == 10:
            event.set()

    for response in T.tweet_lookup(range(1000, 2000)):
        assert "__twarc" not in response

    T.metadata = True


def test_docs_requirements():
    """
    Make sure that the mkdocs requirements has everything that is in the
    twarc requirements so the readthedocs build doesn't fail.
    """
    twarc_reqs = set(open("requirements.txt").read().split())
    mkdocs_reqs = set(open("requirements-mkdocs.txt").read().split())

    assert twarc_reqs.issubset(mkdocs_reqs)


def test_geo():
    print(T.geo(query="Silver Spring"))


def pick_id(id, objects):
    """pick an object out of a list of objects using its id"""
    return list(filter(lambda o: o["id"] == id, objects))
