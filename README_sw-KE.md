twarc
=====

[![Build Status](https://secure.travis-ci.org/DocNow/twarc.png)]
(http://travis-ci.org/DocNow/twarc)

*Translations: [sw-KE]*

twarc ni chombo ya command-line na Python Library ya kuhifadhi Twitter JSON
data. Kila Tweet ita akilishwa kama kitu ya JSON ita onyeshwa
[hivi](https://dev.twitter.com/overview/api/tweets) kutoka kwa Twitter API.
Tweets zita wekwa kama [line-oriented
JSON](https://en.wikipedia.org/wiki/JSON_Streaming#Line_delimited_JSON). Twarc
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
