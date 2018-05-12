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

