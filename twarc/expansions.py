"""
This module contains a list of the known Twitter V2+ API expansions and fields
for each expansion, and a function for "flattening" a result set, including all
expansions inline

"""

from collections import defaultdict

EXPANSIONS = [
    "author_id",
    "in_reply_to_user_id",
    "referenced_tweets.id",
    "referenced_tweets.id.author_id",
    "entities.mentions.username",
    "attachments.poll_ids",
    "attachments.media_keys",
    "geo.place_id",
]

USER_FIELDS = [
    "created_at",
    "description",
    "entities",
    "id",
    "location",
    "name",
    "pinned_tweet_id",
    "profile_image_url",
    "protected",
    "public_metrics",
    "url",
    "username",
    "verified",
    "withheld",
]

TWEET_FIELDS = [
    "attachments",
    "author_id",
    "context_annotations",
    "conversation_id",
    "created_at",
    "entities",
    "geo",
    "id",
    "in_reply_to_user_id",
    "lang",
    "public_metrics",
    # "non_public_metrics", # private
    # "organic_metrics", # private
    # "promoted_metrics", # private
    "text",
    "possibly_sensitive",
    "referenced_tweets",
    "reply_settings",
    "source",
    "withheld",
]

MEDIA_FIELDS = [
    "duration_ms",
    "height",
    "media_key",
    "preview_image_url",
    "type",
    "url",
    "width",
    # "non_public_metrics", # private
    # "organic_metrics", # private
    # "promoted_metrics", # private
    "public_metrics",
]

POLL_FIELDS = ["duration_minutes", "end_datetime", "id", "options", "voting_status"]

PLACE_FIELDS = [
    "contained_within",
    "country",
    "country_code",
    "full_name",
    "geo",
    "id",
    "name",
    "place_type",
]

EVERYTHING = {
    "expansions": ",".join(EXPANSIONS),
    "user.fields": ",".join(USER_FIELDS),
    "tweet.fields": ",".join(TWEET_FIELDS),
    "media.fields": ",".join(MEDIA_FIELDS),
    "poll.fields": ",".join(POLL_FIELDS),
    "place.fields": ",".join(PLACE_FIELDS),
}

# For endpoints focused on user objects such as looking up users and followers.
# Not all of the expansions are available for these endpoints.
USER_EVERYTHING = {
    "expansions": "pinned_tweet_id",
    "tweet.fields": ",".join(TWEET_FIELDS),
    "user.fields": ",".join(USER_FIELDS),
}


def extract_includes(response, expansion, _id="id"):
    if "includes" in response and expansion in response["includes"]:
        return defaultdict(
            lambda: {},
            {include[_id]: include for include in response["includes"][expansion]},
        )
    else:
        return defaultdict(lambda: {})


def flatten(response):
    """
    Flatten the response. Expects an entire page response from the API (data,
    includes, meta) Defaults: Return empty objects for things missing in
    includes. Doesn't modify tweets, only adds extra data.
    """

    # Users extracted both by id and by username for expanding mentions
    includes_users = defaultdict(
        lambda: {},
        {
            **extract_includes(response, "users", "id"),
            **extract_includes(response, "users", "username"),
        },
    )
    # Media is by media_key, not id
    includes_media = extract_includes(response, "media", "media_key")
    includes_polls = extract_includes(response, "polls")
    includes_places = extract_includes(response, "places")
    # Tweets in includes will themselves be expanded
    includes_tweets = extract_includes(response, "tweets")
    # Errors are returned but unused here for now
    includes_errors = extract_includes(response, "errors")

    def expand_payload(payload):
        """
        Recursively step through an object and sub objects and append extra data.
        Can be applied to any tweet, list of tweets, sub object of tweet etc.
        """

        # Don't try to expand on primitive values, return strings as is:
        if isinstance(payload, (str, bool, int, float)):
            return payload
        # expand list items individually:
        elif isinstance(payload, list):
            payload = [expand_payload(item) for item in payload]
            return payload
        # Try to expand on dicts within dicts:
        elif isinstance(payload, dict):
            for key, value in payload.items():
                payload[key] = expand_payload(value)

        if "author_id" in payload:
            payload["author"] = includes_users[payload["author_id"]]

        if "in_reply_to_user_id" in payload:
            payload["in_reply_to_user"] = includes_users[payload["in_reply_to_user_id"]]

        if "media_keys" in payload:
            payload["media"] = list(
                includes_media[media_key] for media_key in payload["media_keys"]
            )

        if "poll_ids" in payload and len(payload["poll_ids"]) > 0:
            poll_id = payload["poll_ids"][-1]  # only ever 1 poll per tweet.
            payload["poll"] = includes_polls[poll_id]

        if "geo" in payload and "place_id" in payload["geo"]:
            place_id = payload["geo"]["place_id"]
            payload["geo"] = {**payload["geo"], **includes_places[place_id]}

        if "mentions" in payload:
            payload["mentions"] = list(
                {**referenced_user, **includes_users[referenced_user["username"]]}
                for referenced_user in payload["mentions"]
            )

        if "referenced_tweets" in payload:
            payload["referenced_tweets"] = list(
                {**referenced_tweet, **includes_tweets[referenced_tweet["id"]]}
                for referenced_tweet in payload["referenced_tweets"]
            )

        if "pinned_tweet_id" in payload:
            payload["pinned_tweet"] = includes_tweets[payload["pinned_tweet_id"]]

        return payload

    # First, expand the included tweets, before processing actual result tweets:
    for included_id, included_tweet in extract_includes(response, "tweets").items():
        includes_tweets[included_id] = expand_payload(included_tweet)

    # Now flatten the list of tweets or an individual tweet
    if "data" in response:
        response["data"] = expand_payload(response["data"])

        # Add the __twarc metadata to each tweet if it's a result set
        if "__twarc" in response and isinstance(response["data"], list):
            for tweet in response["data"]:
                tweet["__twarc"] = response["__twarc"]

    return response
