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


