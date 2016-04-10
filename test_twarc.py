import os
import re
import json
import time
import logging

from twarc import Twarc

"""

You will need to have these environment variables set to run these tests:

* CONSUMER_KEY
* CONSUMER_SECRET
* ACCESS_TOKEN
* ACCESS_TOKEN_SECRET

"""

logging.basicConfig(filename="test.log", level=logging.INFO)

consumer_key = os.environ.get('CONSUMER_KEY')
consumer_secret = os.environ.get('CONSUMER_SECRET')
access_token = os.environ.get('ACCESS_TOKEN')
access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")
t = Twarc(consumer_key, consumer_secret, access_token, access_token_secret)


def test_search():
    count = 0
    for tweet in t.search('obama'):
        assert tweet['id_str']
        count += 1
        if count == 10:
            break
    assert count == 10


def test_since_id():
    for tweet in t.search('obama'):
        id = tweet['id_str']
        break
    assert id
    time.sleep(5)
    for tweet in t.search('obama', since_id=id):
        assert tweet['id_str'] > id


def test_max_id():
    for tweet in t.search('obama'):
        id = tweet['id_str']
        break
    assert id
    time.sleep(5)
    count = 0
    for tweet in t.search('obama', max_id=id):
        count += 1
        assert tweet['id_str'] <= id
        if count > 100:
            break


def test_max_and_since_ids():
    max_id = since_id = None
    count = 0
    for tweet in t.search('obama'):
        count += 1
        if not max_id:
            max_id = tweet['id_str']
        since_id = tweet['id_str']
        if count > 500:
            break
    count = 0
    for tweet in t.search('obama', max_id=max_id, since_id=since_id):
        count += 1
        assert tweet['id_str'] <= max_id
        assert tweet['id_str'] > since_id


def test_paging():
    # pages are 100 tweets big so if we can get 500 paging is working
    count = 0
    for tweet in t.search('obama'):
        count += 1
        if count == 500:
            break
    assert count == 500


def test_track():
    tweet = next(t.filter(track="obama"))
    json_str = json.dumps(tweet)

    assert re.search('obama', json_str, re.IGNORECASE)

    # reconnect to close streaming connection for other tests
    t.connect()


def test_follow():
    user_ids = [
        "87818409",   # @guardian
        "428333",     # @cnnbrk
        "5402612",    # @BBCBreaking
        "2467791",    # @washingtonpost
        "1020058453", # @BuzzFeedNews
        "23484039",   # WSJbreakingnews
        "384438102",  # ABCNewsLive
        "15108702",   # ReutersLive
        "87416722",   # SkyNewsBreak
        "2673523800", # AJELive
    ]
    found = False

    for tweet in t.filter(follow=','.join(user_ids)):
        assert tweet['id_str']
        if tweet['user']['id_str'] in user_ids:
            found = True
        elif tweet['in_reply_to_user_id_str'] in user_ids:
            found = True
        elif tweet['retweeted_status']['user']['id_str'] in user_ids:
            found = True
        elif 'quoted_status' in tweet and tweet['quoted_status']['user']['id_str'] in user_ids:
            found = True
        break

    if not found:
        print("couldn't find user in response")
        print(json.dumps(tweet, indent=2))

    assert found

    # reconnect to close streaming connection for other tests
    t.connect()


def test_locations():
    # look for tweets from New York ; the bounding box is larger than NYC
    # so hopefully we'll find one from New York in the first 100?
    count = 0
    found = False

    for tweet in t.filter(locations="-74,40,-73,41"):
        if tweet['place']['name'] == 'Manhattan':
            found = True
            break
        if count > 100:
            break
        count += 1

    assert found

    # reconnect to close streaming connection for other tests
    t.connect()


def test_hydrate():
    ids = [
        "501064188211765249", "501064196642340864", "501064197632167936",
        "501064196931330049", "501064198005481472", "501064198009655296",
        "501064198059597824", "501064198513000450", "501064180468682752",
        "501064199142117378", "501064171707170816", "501064200186118145",
        "501064200035516416", "501064201041743872", "501064201251880961",
        "501064198973960192", "501064201256071168", "501064202027798529",
        "501064202245521409", "501064201503113216", "501064202363359232",
        "501064202295848960", "501064202380115971", "501064202904403970",
        "501064203135102977", "501064203508412416", "501064203516407810",
        "501064203546148864", "501064203697156096", "501064204191690752",
        "501064204288540672", "501064197396914176", "501064194309906436",
        "501064204989001728", "501064204980592642", "501064204661850113",
        "501064205400039424", "501064205089665024", "501064206666702848",
        "501064207274868736", "501064197686296576", "501064207623000064",
        "501064207824351232", "501064208083980290", "501064208277319680",
        "501064208398573568", "501064202794971136", "501064208789045248",
        "501064209535614976", "501064209551994881", "501064141332029440",
        "501064207387742210", "501064210177331200", "501064210395037696",
        "501064210693230592", "501064210840035329", "501064211855069185",
        "501064192024006657", "501064200316125184", "501064205642903552",
        "501064212547137536", "501064205382848512", "501064213843169280",
        "501064208562135042", "501064214211870720", "501064214467731457",
        "501064215160172545", "501064209648848896", "501064215990648832",
        "501064216241897472", "501064215759568897", "501064211858870273",
        "501064216522932227", "501064216930160640", "501064217667960832",
        "501064211997274114", "501064212303446016", "501064213675012096",
        "501064218343661568", "501064213951823873", "501064219467341824",
        "501064219677044738", "501064210080473088", "501064220415229953",
        "501064220847656960", "501064222340423681", "501064222772445187",
        "501064222923440130", "501064220121632768", "501064222948593664",
        "501064224936714240", "501064225096499201", "501064225142624256",
        "501064225314185216", "501064225926561794", "501064226451259392",
        "501064226816143361", "501064227302674433", "501064227344646144",
        "501064227688558592", "501064228288364546", "501064228627705857",
        "501064229764751360", "501064229915729921", "501064231304065026",
        "501064231366983681", "501064231387947008", "501064231488200704",
        "501064231941570561", "501064232188665856", "501064232449114112",
        "501064232570724352", "501064232700350464", "501064233186893824",
        "501064233438568450", "501064233774510081", "501064235107897344",
        "619172347640201216", "619172347275116548", "619172341944332288",
        "619172340891578368", "619172338177843200", "619172335426244608",
        "619172332100284416", "619172331592773632", "619172331584376832",
        "619172331399725057", "619172328249757696", "619172328149118976",
        "619172326886674432", "619172324600745984", "619172323447324672",
        "619172321564098560", "619172320880533504", "619172320360333312",
        "619172319047647232", "619172314710609920", "619172313846693890",
        "619172312122814464", "619172306338709504", "619172304191401984",
        "619172303654518784", "619172302878408704", "619172300689031168",
        "619172298310840325", "619172295966392320", "619172293936291840",
        "619172293680345089", "619172285501456385", "619172282183725056",
        "619172281751711748", "619172281294655488", "619172278086070272",
        "619172275741298688", "619172274235535363", "619172257789706240",
        "619172257278111744", "619172253075378176", "619172242736308224",
        "619172236134588416", "619172235488718848", "619172232120692736",
        "619172227813126144", "619172221349662720", "619172216349917184",
        "619172214475108352", "619172209857327104", "619172208452182016",
        "619172208355749888", "619172193730199552", "619172193482768384",
        "619172184922042368", "619172182548049920", "619172179960328192",
        "619172175820357632", "619172174872469504", "619172173568053248",
        "619172170233679872", "619172165959708672", "619172163912908801",
        "619172162608463873", "619172158741303297", "619172157197819905",
        "501064235175399425", "501064235456401410", "615973042443956225",
        "618602288781860864"
    ]
    count = 0
    for tweet in t.hydrate(iter(ids)):
        assert tweet['id_str']
        count += 1
    assert count > 100 # may need to adjust as these might get deleted
