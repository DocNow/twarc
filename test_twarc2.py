import os
import json
import twarc
import dotenv
import logging

dotenv.load_dotenv()
logging.basicConfig(filename="test.log", level=logging.INFO)

T = None
BEARER_TOKEN = os.environ.get('BEARER_TOKEN')

def test_bearer_token():
    assert BEARER_TOKEN

def test_constructor():
    global T
    T = twarc.Twarc2(bearer_token=BEARER_TOKEN)

def test_sample():
    count = 0
    for result in T.sample():
        count += 1
        assert int(result['data']['id'])
        if count > 10:
            break
    assert count == 11

