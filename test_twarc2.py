import os
import json
import twarc
import dotenv
import logging
import threading

dotenv.load_dotenv()
logging.basicConfig(filename="test.log", level=logging.INFO)

BEARER_TOKEN = os.environ.get("BEARER_TOKEN")

T = twarc.Twarc2(bearer_token=BEARER_TOKEN)

def test_bearer_token():
    assert BEARER_TOKEN

def test_sample():
    count = 0

    # event to tell the filter stream to close
    event = threading.Event()

    for result in T.sample(event=event):
        assert int(result["data"]["id"])

        # users are passed by reference an dincluded as includes
        user_id = result["data"]["author_id"]
        assert len(pick_id(user_id, result["includes"]["users"])) == 1

        count += 1
        if count > 10:
            # close the sample
            event.set()

    assert count == 11

def test_recent_search():
    """
    Extremely basic search test.
    """

    found_tweets = 0
    pages = 0

    for response_page in T.recent_search("#auspol"):
        pages += 1
        tweets = response_page["data"]
        found_tweets += len(tweets)

        if pages == 3:
            break

    assert 200 <= found_tweets <= 300


def test_user_lookup():

    users_found = 0
    users_not_found = 0

    for response in T.user_lookup(range(1, 1000)):

        for profile in response["data"]:
            users_found += 1

        for error in response["errors"]:
            # Note that errors includes lookup of contained entitites within a tweet,
            # so a pinned tweet that doesn't exist anymore results in an additional
            # error entry, even if the profile is present.
            if error["resource_type"] == "user":
                users_not_found += 1

    assert users_found >= 1
    assert users_found + users_not_found == 999


def test_tweet_lookup():

    tweets_found = 0
    tweets_not_found = 0

    for response in T.tweet_lookup(range(1000, 2000)):

        for tweet in response["data"]:
            print(tweet["id"])
            tweets_found += 1

        for error in response["errors"]:
            # Note that errors includes lookup of contained entitites within a tweet,
            # so a pinned tweet that doesn't exist anymore results in an additional
            # error entry, even if the profile is present.
            if error["resource_type"] == "tweet":
                tweets_not_found += 1
                
    assert tweets_found >= 1
    assert tweets_found + tweets_not_found == 1000


def test_sample_flattened():
    """
    This test uses the sample stream with the flatten option to move the 
    expansions into place into each tweet. It will look at each tweet to find
    evidence that all the expansions have worked. Once it finds them all it
    stops. If it has listened to 5000 tweets and not found them it stops and
    assumes that something is not right. But it could be that it needed to wait
    longer. This 5000 cutoff may need to be adjusted based on experience.
    """
    found_geo = False
    found_in_reply_to_user = False
    found_attachments_media = False
    found_attachments_polls = False
    found_entities_mentions = False
    found_referenced_tweets = False

    count = 0
    event = threading.Event()
    for result in T.sample(flatten=True, event=event):
        tweet = result["data"]
        assert "id" in tweet
        logging.info("got sample tweet #%s %s", count, tweet["id"])

        author_id = tweet["author_id"]
        assert "author" in tweet 
        assert result["data"]["author"]["id"] == author_id

        if "in_reply_to_user_id" in tweet:
            assert "in_reply_to_user" in tweet
            found_in_reply_to_user = True

        if "attachments" in tweet:
            if "media_keys" in tweet["attachments"]:
                assert "media" in tweet["attachments"]
                found_attachments_media = True
            if "poll_ids" in tweet["attachments"]:
                assert "polls" in tweet["attachments"]
                found_attachments_polls = True

        if "geo" in tweet:
            assert tweet["geo"]["place_id"]
            assert tweet["geo"]["place_id"] == tweet["geo"]["place"]["id"]
            found_geo = True

        if "entities" in tweet and "mentions" in tweet["entities"]:
            assert tweet["entities"]["mentions"][0]["username"]
            found_entities_mentions = True

        if "referenced_tweets" in tweet:
            assert tweet["referenced_tweets"][0]["id"]
            found_referenced_tweets = True

        count += 1
        if found_geo and found_in_reply_to_user and found_attachments_media \
                and found_attachments_polls and found_entities_mentions \
                and found_referenced_tweets:
            logging.info("found all expansions!")
            event.set()
        elif count > 5000:
            logging.info("didn't find all expansions in 5000 tweets")
            event.set()

    assert found_geo, "found geo" 
    assert found_in_reply_to_user, "found in_reply_to_user"
    assert found_attachments_media, "found media"
    assert found_attachments_polls, "found polls"
    assert found_entities_mentions, "found mentions"
    assert found_referenced_tweets, "found referenced tweets"

def pick_id(id, objects):
    """pick an object out of a list of objects using its id
    """
    return list(filter(lambda o: o["id"] == id, objects))
