import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from twarc.expansions import flatten


def test_flatten_tolerates_includes_errors_without_ids():
    response = {
        "data": [{"id": "123", "text": "hello", "author_id": "456"}],
        "includes": {
            "users": [{"id": "456", "username": "someone", "name": "Someone"}],
            "errors": [
                {
                    "detail": "Could not find user with id: [999].",
                    "title": "Not Found Error",
                    "resource_type": "user",
                    "parameter": "id",
                    "value": "999",
                    "type": "https://api.twitter.com/2/problems/resource-not-found",
                }
            ],
        },
        "meta": {"result_count": 1},
    }

    tweets = flatten(response)

    assert len(tweets) == 1
    assert tweets[0]["author"]["username"] == "someone"
