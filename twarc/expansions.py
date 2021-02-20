"""
This module contains a list of the known Twitter V2+ API expansions and fields for
each expansion, and a function for "flattening" a result set,
including all expansions inline

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


def extract_includes(response, expansion, _id="id"):
    if expansion in response["includes"]:
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
    includes_media = extract_includes(response, "media", "media_key")
    includes_users = extract_includes(response, "users")
    includes_user_names = extract_includes(response, "users", "username")
    includes_polls = extract_includes(response, "polls")
    includes_place = extract_includes(response, "places")
    includes_tweets = extract_includes(response, "tweets")

    def expand_tweet(tweet):
        if "author_id" in tweet:
            tweet["author"] = includes_users[tweet["author_id"]]
        if "in_reply_to_user_id" in tweet:
            tweet["in_reply_to_user"] = includes_users[tweet["in_reply_to_user_id"]]
        if "attachments" in tweet:
            if "media_keys" in tweet["attachments"]:
                tweet["attachments"]["media"] = [
                    includes_media[media_key]
                    for media_key in tweet["attachments"]["media_keys"]
                ]
            if "poll_ids" in tweet["attachments"]:
                tweet["attachments"]["polls"] = [
                    includes_polls[poll_id]
                    for poll_id in tweet["attachments"]["poll_ids"]
                ]
        if "geo" in tweet and len(includes_place) > 0:
            place_id = tweet["geo"]["place_id"]
            tweet["geo"]["place"] = includes_place[place_id]

        if "entities" in tweet:
            if "mentions" in tweet["entities"]:
                tweet["entities"]["mentions"] = [
                    {
                        **referenced_user,
                        **includes_user_names[referenced_user["username"]],
                    }
                    for referenced_user in tweet["entities"]["mentions"]
                ]
        if "referenced_tweets" in tweet:
            tweet["referenced_tweets"] = [
                {**referenced_tweet, **includes_tweets[referenced_tweet["id"]]}
                for referenced_tweet in tweet["referenced_tweets"]
            ]
        return tweet

    # Now expand the included tweets ahead of time using all of the above:
    includes_tweets = (
        defaultdict(
            lambda: {},
            {
                tweet["id"]: expand_tweet(tweet)
                for tweet in response["includes"]["tweets"]
            },
        )
        if "tweets" in response["includes"]
        else defaultdict(lambda: {})
    )

    # flatten a list of tweets or an individual tweet
    if type(response["data"]) == list: 
        response["data"] = list(expand_tweet(tweet) for tweet in response["data"])
    elif type(response["data"]) == dict:
        response["data"] = expand_tweet(response["data"])

    # Hmm, should we do this? All the other changes are additive right?
    response.pop("includes", None) 

    return response
