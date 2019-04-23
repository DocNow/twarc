twarc
=====

[![Build Status](https://secure.travis-ci.org/DocNow/twarc.png)](http://travis-ci.org/DocNow/twarc)

*Tafsiri: [Kiingereza], [Kihispania], [Kireno], [Swedish]*

twarc ni chombo ya command-line na Python Library ya kuhifadhi Twitter JSON
data. Kila Tweet ita akilishwa kama kitu ya JSON ita onyeshwa
[hivi](https://dev.twitter.com/overview/api/tweets) kutoka kwa Twitter API.
Tweets zita wekwa kama [line-oriented
JSON](https://en.wikipedia.org/wiki/JSON_Streaming#Line-delimited_JSON). Twarc
ita kusaidia ku chunga [rate
limits](https://dev.twitter.com/rest/public/rate-limiting) ya API ya Twitter.
Twarc pia ita sanya tweets, watumiaji wa Twitter, uwenendo za Twitter na ita
hydrate tweet ids.

twarc imeundwa kama sehemu ya [Documenting the Now](http://www.docnow.io) ambayo
ilifadhiliwa na [Mellon Foundation](https://mellon.org/).

## Weka

Kabla kutumia twarc utahitaji kujiandikisha kwa
[apps.twitter.com](http://apps.twitter.com). Mara baada ya kuunda programu yako
andika `consumer key` and `consumer secret` yako alafu bonyeza kuzalisha `access
token` na `access token secret`. Uta hitaji hizi vigezo nne ku tumia twarc

1. weka [Python](http://python.org/download) (2 or 3)
2. pip install twarc (ama kuboresha: pip install --upgrade twarc)

## Haraka Haraka

Utahitaji kuambia twarc vifunguo ya API ya Twitter

    twarc configure

alafu jaribu kuchungua na:

    twarc search blacklivesmatter > search.jsonl

Ama wataka kusanya ma tweets kama zinatoka

    twarc filter blacklivesmatter > stream.jsonl

Endelea kusoma ku pata maelezo kuhusu utumizi wa twarc

## Matumizi

### Sanidi

Mara tu una vifunguo vya Twitter unaweza kuambia twarc ukitumia command ya
`configure`.

    twarc configure

twarc ita andika sifa zako kwenye file itayo itwa `.twarc` kwa saraka ya home.
Kama hutaki ama huwezi kuandika file hiyo unaweza kutumia command inayo tumia
mazingira yako. (`CONSUMER_KEY`,
`CONSUMER_SECRET`, `ACCESS_TOKEN`, `ACCESS_TOKEN_SECRET`) ama chagua command line
(`--consumer_key`, `--consumer_secret`, `--access_token`,
`--access_token_secret`).

### Uchunguzi

Hutumia [uchunguzi wa
tweets](https://dev.twitter.com/rest/reference/get/search/tweets) kupakua tweets
zilizoandikwa zinazo swala

    twarc search blacklivesmatter > tweets.jsonl

Ni muhimu kukumbuka swali yako ita pakua tweets za mda wa siku 7 inayo tiwa na
API ya Twitter. Kama swali yako inataka mda wa siku nane au zaidi waeza kutumia
`filter` ama `sample` commands kama hizi.

Njia bora ya kujifunza na uchunguzi wa Twitter Search API ni ku jaribu
[Twitter's Advanced Search](https://twitter.com/search-advanced) alafu kuitumia
kwa twarc. Kwa mfano hapa tuna tafuta ma tweets zinazo \#blacklivesmatter ama
#blm hashtags zilizo tumwa kwa deray.

    twarc search '#blacklivesmatter OR #blm to:deray' > tweets.jsonl

Twitter hujaribu kuweka lugha ya tweet na unaweza kupunguza kikoma yako kwa
lugha ukitaka

    twarc search '#blacklivesmatter' --lang fr > tweets.jsonl

Unaweza pia kutafuta tweets za mahali fulani kwa mfano tweets zinazo taja
*blacklivesmatter* zilizo maili 1 kutoka katikati ya Ferguson, Missouri:

    twarc search blacklivesmatter --geocode 38.7442,-90.3054,1mi > tweets.jsonl

Ikiwa swali yako haina maneno lakini umetumia `--geocode` utapata tweets zote za
eneo hio.

    twarc search --geocode 38.7442,-90.3054,1mi > tweets.jsonl

### Chuja

Utumizi wa `filter` command husanya tweets zikiandikwa no hutumia
[statuses/filter](https://dev.twitter.com/streaming/reference/post/statuses/filter)
API.

    twarc filter blacklivesmatter,blm > tweets.jsonl

Tafadhali kumbuka kuwa syntax ya Twitter ni tofauti na Twitter ya uchunguzi.
Tafadhali wasiliana na nyaraka jinsi ya kueleza chujia unayo tumia

Tumia command ya `follow` kama wataka kusanya tweets kutoka kwa mtumiaji kama
zinatokea. Hi inajumuisha retweets. Kwa mfano hii itasanya tweets na retweets za
CNN:

    twarc filter --follow 759251 > tweets.jsonl

Waeza kusanya tweets kwa kutumia sanduku linalozingatia. Kumbuka: dash
inayoongoza inahitaji kutoroka katika sanduku linalozingatia ama ita fasiriwa
kama command line argument!

    twarc filter --locations "\-74,40,-73,41" > tweets.jsonl

Ikiwa unachanganya chaguzi yako au OR'ed pamoja. Kwa mfano hii ita sanya tweets
zinasotumia blacklivesmatter ama blm na pia tweets kutoka mtumiaji CNN:

    twarc filter blacklivesmatter,blm --follow 759251 > tweets.jsonl

### Sampuli

Tumia `sample` command kusikiliza kwa sampuli ya Twitter
[statuses/sample](https://dev.twitter.com/streaming/reference/get/statuses/sample)
statuses hivi karibuni

    twarc sample > tweets.jsonl

### Punguza maji

twarc ina `dehydrate` command ita tengeneza orodha ya id kutoka faili ya tweets:

    twarc dehydrate tweets.jsonl > tweet-ids.txt

### Hydrate

twarc pia ina `hydrate` command ita soma faili inayo id na ita andika faili mpya
ya tweet JSON kwa kutumiya Twitter [status/lookup](https://dev.twitter.com/rest/reference/get/statuses/lookup) API.

    twarc hydrate ids.txt > tweets.jsonl

API ya Twitter [Masharti ya
Huduma](https://dev.twitter.com/overview/terms/policy#6._Be_a_Good_Partner_to_Twitter)
huwazuia watu kutengeza kiasi kubwa ya Twitter data ipatikane kwenye Web. Hiyo
data yaeza kutumiwa kwa uchunguzi bora isi shirikiana na ulimwengu. Twitter
huruhusu mafaili ya tweet identifiers kugawanywa no hiyo inaweza kuwa na
manufaa. Waeza kutumia API ya Twitter ku *hydrate* hiyo data ama kupata kamili
ya JSON. Hi ni muhimu kwa
[uthibitishaji](https://en.wikipedia.org/wiki/Reproducibility) ya social media
research.

### Watumiaji

Utumizi was `users` command hurudisha metadata ya majina ya skrini iliyopewa

    twarc users deray,Nettaaaaaaaa > users.jsonl

Waeza pia kuipatia ids za watumiaji

    twarc users 1232134,1413213 > users.jsonl

Waeza kutumia faili iliyo na ids za watumiaji kwa mfano wataka `followers` na
`friends` commands

    twarc users ids.txt > users.jsonl

### Wafuasi

Utumizi wa `followers` hutegemeya [follower id
API](https://dev.twitter.com/rest/reference/get/followers/ids) ku kusanya ids za
mfuasi moja kwa kila ombi. Kwa mfano:

    twarc followers deray > follower_ids.txt

ita rudisha mfuasi moja kwa kila laini. Faili yako ita andikwa na wafuasi wa
hivi karibuni kwanza.

### Mwelekeo

Utumizi wa `trends` hutegemeya API ya Twitter ya mwelekeo wa hashtags. Unahitaji
kuipatia [Where On Earth](http://developer.yahoo.com/geo/geoplanet/) identifier
(`woeid`) kuiambia mwenendo unayopenda. Kwa mfano kama wataka maelekeo ya St.
Louis:

    twarc trends 2486982

Ukitumia `woeid` ya 1 itarudisha mwenendo wa dunia yote.

    twarc trends 1

Ikiwa hujui nini cha kutumia ya `woeid` iache na utapata maeneo yote ambayo
Twitter hufuata:

    twarc trends

Kama una geo-location waeza kuitimia badala ya `woeid`

    twarc trends 39.9062,-79.4679

Twitter ita tumia API ya [trends/closest](https://dev.twitter.com/rest/reference/get/trends/closest) ili kupata `woeid` iliyo karibu nawe

### Muda wa wakati

Utumiaji wa `timeline` command hutegemeya kwa API ya [user timeline
API](https://dev.twitter.com/rest/reference/get/statuses/user_timeline)
kukusanya Tweets za mtumiaji alionyeshwa na `screen_name`:

    twarc timeline deray > tweets.jsonl

Unaweza pia kuangalia juu ya watumiaji kwa kutumia id ya mtumiaji

    twarc timeline 12345 > tweets.jsonl

### Retweets

Unaweza kupata retweets kwa kuipeya id ya tweet hivi:

    twarc retweets 824077910927691778 > retweets.jsonl

### Majibu

Twitter haina API ambayo inaweza kupata majibu za tweet. twarc hujaribu kwa
kutumia search API. Lakino search API haiwezi kupata majibu zaidi ya siku saba.
Ikiwa unataka kupata majibu ya tweets fanya hivi:

    twarc replies 824077910927691778 > replies.jsonl

Utumizi wa `--recursive` utapata majibu ya majibu na quotes. Hii inaweza
kuchukua muda mrefu kukamilisha kama una majibu mengi kwa sababu ya kiwango cha
kupunguzwa search API.

    twarc replies 824077910927691778 --recursive

### Orodha

Ili kupata watumiaji walio kwenye orodha unaweza kutumia URL ya orodha na
command ya `listmembers`

    twarc listmembers https://twitter.com/edsu/lists/bots

## Tumia kama Maktaba

Ikiwa unataka kutumia twarc programatically kama maktaba kukusanya tweets.
Kwanza utahitaji kuunda `twarc` instance yako. (utatumia sifa zako za Twitter),
alafu utaitumia kutafuta matokeo ya utafutaji, futa matokeo au matokeo ya
kufuatilia.

```python
from twarc import Twarc

t = Twarc(consumer_key, consumer_secret, access_token, access_token_secret)
for tweet in t.search("ferguson"):
    print(tweet["text"])
```

Unaweza kufanya hivyo kwa mkondo wa machujio ya tweets ambazo zinafanana na
kufuatilio neno muhimu:

```python
for tweet in t.filter(track="ferguson"):
    print(tweet["text"])
```

au mahali

```python
for tweet in t.filter(locations="-74,40,-73,41"):
    print(tweet["text"])
```

au ids za watumiaji

```python
for tweet in t.filter(follow='12345,678910'):
    print(tweet["text"])
```

Vivyo hivyo unaweza ku hydrate tweet identifiers kwa kupitisha orodha ya ids au
jenereta:

```python
for tweet in t.hydrate(open('ids.txt')):
    print(tweet["text"])
```

## Vya Kutumia

Katika saraka `utils` kuna commands zinazo weza kukusaidia kufanya kazi na
line-oriented JSON kama kuchapisha ma tweets kwa text au html, kuchimba majina
za watumiaji, URLS. If tengeneza script yako tafadhali tushirikiana na PR.

Unapopata tweets unaweza kuunda ukuta mzuri wako:

    % utils/wall.py tweets.jsonl > tweets.html

Unaweza kuunda wingu ya maneno ya tweets ulizo sanya ambayo in neno nasa 

    % utils/wordcloud.py tweets.jsonl > wordcloud.html

Ikiwa umekusanya tweets kwa kutumia `majibu` unaweza kuunda taswira ya D3 na:

    % utils/network.py tweets.jsonl tweets.html

Unaweza kuimarisha tweets za mtumiaji, kukuruhusu kuona akaunti kuu:

    % utils/network.py --users tweets.jsonl tweets.html

Na kama unataka kutumia grafu ya mtandao katika mpango kama
[Gephi](https://gephi.org/), unaweza kuuna faili ya GEXF na

    % utils/network.py --users tweets.jsonl tweets.gexf

`gender.py` ni chujio kinachokuwezesha kufuta tweets kulingana na nadhani kuhusu
jinsia ya mwandishi. Kwa mfano unaweza kufuta tweets zote ambazo
kuangalia kama walikuwa kutoka kwa wanawake, na kuunda wingu neno na:

    % utils/gender.py --gender female tweets.jsonl | utils/wordcloud.py > tweets-female.html

Unaweza kutoa [GeoJSON](http://geojson.org/) ya tweets kama geo coordinates
ziko:

    % utils/geojson.py tweets.jsonl > tweets.geojson

Unaweza pia kuto GeoJSON na centriods, kubadilisha nafasi ya masanduku:

    % utils/geojson.py tweets.jsonl --centroid > tweets.geojson

Na ukitoa GeoJSON na centroids, unaweza kuongeza random fuzzing:

    % utils/geojson.py tweets.jsonl --centroid --fuzz 0.01 > tweets.geojson

Ili kufuta tweets kwa kuwepo au kutokuwepo kwa kuratibu za geo (au Mahali, angalia nyaraka za [API](https://dev.twitter.com/overview/api/places)):

    % utils/geofilter.py tweets.jsonl --yes-coordinates > tweets-with-geocoords.jsonl
    % cat tweets.jsonl | utils/geofilter.py --no-place > tweets-with-no-place.jsonl

Ili kufuta tweets na uzio wa GeoJSON (inahitaji [Shapely](https://github.com/Toblerity/Shapely)):

    % utils/geofilter.py tweets.jsonl --fence limits.geojson > fenced-tweets.jsonl
    % cat tweets.jsonl | utils/geofilter.py --fence limits.geojson > fenced-tweets.jsonl

Ikiwa unadhani una duplicate kwenye tweets zako unaweza kuwapunguza:

    % utils/deduplicate.py tweets.jsonl > deduped.jsonl

Unaweza kuchagua na ID, ambayo ni sawa na kutatua kwa wakati:

    % utils/sort_by_id.py tweets.jsonl > sorted.jsonl

Unaweza kufuta tweets zote kabla ya tarehe fulani (kwa mfano, kama hashtag ilitumiwa kwa tukio lingine kabla ya moja unayopenda):

    % utils/filter_date.py --mindate 1-may-2014 tweets.jsonl > filtered.jsonl

Unaweza kupata orodha ya HTML ya wateja kutumika:

    % utils/source.py tweets.jsonl > sources.html

Ikiwa unataka kuondoa retweets:

    % utils/noretweets.py tweets.jsonl > tweets_noretweets.jsonl

Au unshorten urls (requires [unshrtn](https://github.com/docnow/unshrtn)):

    % cat tweets.jsonl | utils/unshorten.py > unshortened.jsonl

Mara baada ya kufuta URL zako unaweza kupata orodha ya vya URL inayo tweets nyingi zaidi:

    % cat unshortened.jsonl | utils/urls.py | sort | uniq -c | sort -nr > urls.txt

## twarc-report

Baadhi ya scripts zaidi ya huduma ili kuzalisha csv au json pato yanafaa kwa
kutumia na [D3.js](http://d3js.org/) visualizations hupatikana katika
[twarc-report](https://github.com/pbinkley/twarc-report). `directed.py` ilikuwa
sehemu ya twarc imehama kwa twarc-report kama `d3graph.py`. 

Kila script pia inaweza kuzalisha demo html ya taswira ya D3, kwa mfano. [timelines](https://wallandbinkley.com/twarc/bill10/) or a
[directed graph of retweets](https://wallandbinkley.com/twarc/bill10/directed-retweets.html).

[Kiingereza]: https://github.com/DocNow/twarc/blob/master/README.md
[Kireno]: https://github.com/DocNow/twarc/blob/master/README_pt_br.md
[Kihispania]: https://github.com/DocNow/twarc/blob/master/README_es_mx.md
[Swedish]: https://github.com/DocNow/twarc/blob/master/README_sw_ke.md
