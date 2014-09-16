import time
import twarc
import pytest
import logging

"""

You will need to have these environment variables set to run these tests:

* CONSUMER_KEY
* CONSUMER_SECRET
* ACCESS_TOKEN
* ACCESS_TOKEN_SECRET

"""

logging.basicConfig(filename="test.log", level=logging.DEBUG)

def test_search():
    count = 0
    for tweet in twarc.search('obama'):
        assert tweet['id_str']
        count +=1
        if count == 10:
            break
    assert count == 10

def test_since_id():
    for tweet in twarc.search('obama'):
        id = tweet['id_str']
        break
    assert id
    time.sleep(5)
    for tweet in twarc.search('obama', since_id=id):
        assert tweet['id_str'] > id

def test_max_id():
    for tweet in twarc.search('obama'):
        id = tweet['id_str']
        break
    assert id
    time.sleep(5)
    count = 0
    for tweet in twarc.search('obama', max_id=id):
        count += 1
        assert tweet['id_str'] <= id
        if count > 100:
            break

def test_max_id_bug():
    pass

 

def test_max_and_since_ids():
    max_id = since_id = None
    count = 0
    for tweet in twarc.search('obama'):
        count += 1
        if not max_id:
            max_id = tweet['id_str']
        since_id = tweet['id_str']
        if count > 500:
            break
    count = 0
    for tweet in twarc.search('obama', max_id=max_id, since_id=since_id):
        count += 1
        assert tweet['id_str'] <= max_id
        assert tweet['id_str'] > since_id

def test_paging():
    # pages are 100 tweets big so if we can get 500 paging is working
    count = 0
    for tweet in twarc.search('obama'):
        count += 1
        if count == 500:
            break
    assert count == 500
 
