twarc
=====

[![Build Status](https://secure.travis-ci.org/DocNow/twarc.png)](http://travis-ci.org/DocNow/twarc)

*Översättningar: [Engelska], [Portugisiska], [Spanska], [Swahili]*

twarc är ett kommandoradsverktyg twarc och ett Pythonbibliotek för arkivering av Twitter JSON data.
Varje tweet är representerat som ett JSON-objekt som är [exakt](https://dev.twitter.com/overview/api/tweets) vad som returneras från Twitters API
Tweets lagras som [line-oriented JSON](https://en.wikipedia.org/wiki/JSON_Streaming#Line-delimited_JSON).  Twarc hanterar
Twitter API:ets [rate limits](https://dev.twitter.com/rest/public/rate-limiting)
åt dig. Förutom att kunna samla in tweets kan även Twarc hjälpa dig att samla in användare, trender och omvandla tweet-id:n till tweets. 

twarc har utvecklats som en del av [Documenting the Now](http://www.docnow.io) 
projektet som finiansierades av [Mellon Foundation](https://mellon.org/).


## Installera

Innan du använder twarc behöver du registrera en applikation hos
[apps.twitter.com](http://apps.twitter.com). När du har skapat din applikation, skriv ner consumer key, consumer secret och klicka för att generera en access token och en access token secret.
Med dessa fyra variabler är du redo att börja använda twarc. 

1. Installera [Python](http://python.org/download) (2 eller 3)
2. pip install twarc (om du uppgraderar: pip install --upgrade twarc)

## Snabbstart:

Först måste du tala om för twarc vad dina API-nycklar är och tillåta åtkomst till ett 
eller flera twitterkonton:

    twarc configure

Prova att köra:

    twarc search blacklivesmatter > search.jsonl

Eller om du vill samla in tweets i samma ögonblick de skapas:

    twarc filter blacklivesmatter > stream.jsonl

Se nedan för detaljer om dessa och fler kommandon. 


## Användning

### Konfigurera

När du har dina applikationsnycklar så kan du tala om för twarc vilka de är med 
`configure` kommandot.

    twarc configure

Detta kommer att lagra dina nycklar i en fil som heter `.twarc` placerad i din hemkatalog så du slipper att skriva in dem varje gång. 
Om du hellre vill tilldela dom direkt så kan du göra det i environment (`CONSUMER_KEY`,
`CONSUMER_SECRET`, `ACCESS_TOKEN`, `ACCESS_TOKEN_SECRET`) eller genom att använda kommandoradsparameter
options (`--consumer_key`, `--consumer_secret`, `--access_token`,
`--access_token_secret`).

### Sök
Detta använder Twitters [search/tweets](https://dev.twitter.com/rest/reference/get/search/tweets) för att ladda ner *redan befintliga* tweets som matchar en given söksträng.

    twarc search blacklivesmatter > tweets.jsonl

Det är viktigt att notera att `search` retunerar tweets som hittas inom det 7-dagarsfönster som 
Twitters sök-API erbjuder. Känns det som ett smalt fönster? Det är det. Men du kanske är intresserad av att samla in tweets i samma ögonblick som de skapas 
genom att använda `filter` och `sample` kommandona nedan.

Det bästa sättet att bekanta sig med Twitters söksyntax är att experimentera med 
[Twitters Advancerade Sök](https://twitter.com/search-advanced) och kopiera och klistra in söksträngen från sökboxen.
Här är till exempel en mer avancerad söksträng som matchar tweets innehållande antingen \#blacklivesmatter eller #blm hashtaggar som skickats till deray

    twarc search '#blacklivesmatter OR #blm to:deray' > tweets.jsonl

Twitter försöker att koda en tweets språk, och du kan begränsa sökningen till ett specifikt språk om du vill:

    twarc search '#blacklivesmatter' --lang fr > tweets.jsonl

Du kan också söka efter tweets inom en given plats, till exempel tweets som nämner *blacklivesmatter*  som är 1 mile från centrala Ferguson, Missouri:

    twarc search blacklivesmatter --geocode 38.7442,-90.3054,1mi > tweets.jsonl

Om inte en söksträng ges när du använder `--geocode` kommer du få alla tweets som är relevanta för den platsen och radien. 

    twarc search --geocode 38.7442,-90.3054,1mi > tweets.jsonl

### Filter

`filter` Kommandot använder Twitters [statuses/filter](https://dev.twitter.com/streaming/reference/post/statuses/filter) API för att samla in tweets i samma ögonblick som de skapas. 

    twarc filter blacklivesmatter,blm > tweets.jsonl

Notera att syntaxen för Twitters track söksträngar är något annorlunda än de som används i sök-API:et
Var god läs dokumentationen för att se hur du bäst kan formulera sökningar. 


Använd `follow` kommandot om du vill samla in tweets från ett specifikt användar-id i samma ögonblick som de skapas. Detta inkluderar retweets. 
Till exempel så samlar detta in tweets och retweets från CNN:

    twarc filter --follow 759251 > tweets.jsonl

Du kan också samla in tweets genom att använda koordinater.  Notera: det inledande bindestrecket behöver ignoreras, annars kommer det tolkas som en kommandoradsparameter!

    twarc filter --locations "\-74,40,-73,41" > tweets.jsonl


Om du kombinerar parametrar så kommer de tolkas som OR 
Till exempel så kommer detta samla in tweets som använder blacklivesmatter eller blm hashtaggen och som också postats av användaren CNN: 

    twarc filter blacklivesmatter,blm --follow 759251 > tweets.jsonl

### Sample

Använd `sample` kommandot för att "lyssna" på Twitters [statuses/sample](https://dev.twitter.com/streaming/reference/get/statuses/sample) API för ett "slumpmässigt" prov av nyligen skapade publika tweets.

    twarc sample > tweets.jsonl

### Dehydrering

`dehydrate` kommandot genererar en lista med identifierare från en fil med tweets:

    twarc dehydrate tweets.jsonl > tweet-ids.txt

### Hydrering

Twarc's `hydrate` kommando läser en fil med tweetidentifierare och skriver ut som tweet JSON genom Twitters [status/lookup](https://dev.twitter.com/rest/reference/get/statuses/lookup) API.

    twarc hydrate ids.txt > tweets.jsonl

Twitter APIs [Terms of Service](https://dev.twitter.com/overview/terms/policy#6._Be_a_Good_Partner_to_Twitter) uppmuntrar inte folk att tillgängliggöra stora mängder av rå Twitterdata på webben.  
Datan kan användas för forskning och arkiveras lokalt, men kan inte delas med världen. Twitter tillåter emellertid att identifierare delas, vilket kan vara bra när du vill tillgängliggöra ett dataset. 
Du kan då använda Twitters API för att *hydrera* datan, eller för att hämta den fulla JSON-objektet för varje identifierare. 
Detta är särskilt viktigt för [verifiering](https://en.wikipedia.org/wiki/Reproducibility) av forskning på social media.

### Användare

`users` kommandot retunerar metadata för angivna screen names.

    twarc users deray,Nettaaaaaaaa > users.jsonl

Du kan också använda användar-id:

    twarc users 1232134,1413213 > users.jsonl

Om du vill kan du också använda en fil med användar-id, vilket kan vara användbart om du använder
`followers` och `friends` kommandona nedan:

    twarc users ids.txt > users.jsonl

### Följare

`followers` kommandot använder Twitters [follower id API](https://dev.twitter.com/rest/reference/get/followers/ids) för att samla in följarens användar-id för exakt ett screen name per request specificerat som ett argument:

    twarc followers deray > follower_ids.txt

Resultatet inkluderar exakt ett användar-id per linje ordnat i omvänd kronologisk ordning, alltså de senaste följarna först. 	


### Vänner

Precis som `followers` kommandot, använder `friends` kommandot Twitters [friend id API](https://dev.twitter.com/rest/reference/get/friends/ids) för att samla in vänners användar-id för exakt ett screen name per request, specificerat som ett argument:

    twarc friends deray > friend_ids.txt

### Trender

`trends` kommandot låter dig hämta information från Twitters API om trendande hashtags. Du måste bifoga en [Where On Earth](http://developer.yahoo.com/geo/geoplanet/) identifierare (`woeid`) 
för att precisera vilka trender du är intresserad av. Till exempel kan du hämta de senaste trenderna för St. Louis på det hör viset:

    twarc trends 2486982

Använder du ett `woeid` på 1 så kommer du få trender för hela världen:

    twarc trends 1

Om du inte är säker på vad du ska använda för `woeid` så kan du helt enkelt utesluta det för att få en lista över alla platser Twitter har trender för:  	

    twarc trends

Om du har en geo-position så kan du använda den istället för `woeid`.

    twarc trends 39.9062,-79.4679

Bakom kulisserna så hjälper twarc dig genom Twitters [trends/closest](https://dev.twitter.com/rest/reference/get/trends/closest) API att hitta närmaste `woeid`.

### Tidslinje

`timeline` kommandot använder Twitters [user timeline API](https://dev.twitter.com/rest/reference/get/statuses/user_timeline)  för att samla in de senaste tweetsen skapade av en användare baserat på screen_name.

    twarc timeline deray > tweets.jsonl

Du kan också använda användar-id:

    twarc timeline 12345 > tweets.jsonl

### Retweets

Du kan samla in retweets för ett givet tweetid genom:

    twarc retweets 824077910927691778 > retweets.jsonl

### Svar

Tyvärr så stödjer inte Twitters API att hämta svar till en tweet. 
Twarc använder istället sök-API:et för detta. Då sök-API:et inte kan användas för att samla in tweets äldre än en vecka kan twarc endast hämta alla svar till en tweet som har postats den senaste veckan. 

Om du vill hämta svaren till en tweet så kan du använda följande: 

    twarc replies 824077910927691778 > replies.jsonl

Genom att använda `--recursive` parametern så hämtas även svar till svar så väl som citerade tweets. Detta kan ta mycket lång tid att köra på stora trådar på grund av 
rate limiting på sök-API:et.

    twarc replies 824077910927691778 --recursive

### Listor

För att hämta användare som är med på en lista kan du använda list-URL:en med
`listmembers` kommandot:

    twarc listmembers https://twitter.com/edsu/lists/bots

## Använd som ett bibliotek

Du kan också använda twarc programatiskt som ett bibliotek för att samla in tweets.
Du behöver först skapa en instans av `Twarc` (genom att använda dina nycklar)
, och sedan använda det för att iterera genom sökresultat, filter och resultat. 

```python
from twarc import Twarc

t = Twarc(consumer_key, consumer_secret, access_token, access_token_secret)
for tweet in t.search("ferguson"):
    print(tweet["text"])
```

Du kan göra samma sak för en ström som matchar ett nyckelord 

```python
for tweet in t.filter(track="ferguson"):
    print(tweet["text"])
```

eller en position:

```python
for tweet in t.filter(locations="-74,40,-73,41"):
    print(tweet["text"])
```

eller användar-id:

```python
for tweet in t.filter(follow='12345,678910'):
    print(tweet["text"])
```

På samma sätt kan du hydrera tweetid:n genom att bearbeta en lista med idn 
eller en generator:

```python
for tweet in t.hydrate(open('ids.txt')):
    print(tweet["text"])
```

## Verktyg

I utils-mappen finns ett antal enkla kommandoradsverktyg för att bearbeta linjeorienterad JSON, så som att skriva ut arkiverade tweets som text eller html, extrahera användarnamn, refererade url:er, m.m. 
Om du skapar ett skript som du tycker är bra så får du gärna skicka en pull request.

När du samlat in lite tweets kan du skapa en rudimentär vägg av dem:

    % utils/wall.py tweets.jsonl > tweets.html

Du kan skapa ett ordmoln baserat på tweets du samlat in:

    % utils/wordcloud.py tweets.jsonl > wordcloud.html

Om du har samlat in tweets genom att använda `replies` kan du skapa en statisk D3
visualisering av dem med:

    % utils/network.py tweets.jsonl tweets.html

Du kan även slå samman tweets per användare, vilket gör att du kan se centrala konton. 

    % utils/network.py --users tweets.jsonl tweets.html

Och om du vill använda nätverksgrafen i ett program som [Gephi](https://gephi.org/), så kan du generera en GEXF-fil med följande:

    % utils/network.py --users tweets.jsonl tweets.gexf

gender.py  är ett filter som låter dig filtrera tweets baserat på en gissining författarens kön. Till exempel kan du filtrera ut alla tweets som 
ser ut som de var skrivna av kvinnor och skapa ett ordmoln:

    % utils/gender.py --gender female tweets.jsonl | utils/wordcloud.py > tweets-female.html

Du kan få ut [GeoJSON](http://geojson.org/) från tweets där geo-koordinater finns tillgängliga:
 
    % utils/geojson.py tweets.jsonl > tweets.geojson

Alternativt kan du exportera GeoJSON med centroider som ersättning för bounding boxes:

    % utils/geojson.py tweets.jsonl --centroid > tweets.geojson

Och om du exporterar GeoJSON med centroider, så kan du lägga till lite slumpmässig fuzz:

    % utils/geojson.py tweets.jsonl --centroid --fuzz 0.01 > tweets.geojson

För att filtrera tweets baserat på tillgänglighet av geo-koordinater (eller plats, se [API documentation](https://dev.twitter.com/overview/api/places)):

    % utils/geofilter.py tweets.jsonl --yes-coordinates > tweets-with-geocoords.jsonl
    % cat tweets.jsonl | utils/geofilter.py --no-place > tweets-with-no-place.jsonl

För att filtrera tweets genom ett GeoJSON-staket (Kräver [Shapely](https://github.com/Toblerity/Shapely)):

    % utils/geofilter.py tweets.jsonl --fence limits.geojson > fenced-tweets.jsonl
    % cat tweets.jsonl | utils/geofilter.py --fence limits.geojson > fenced-tweets.jsonl

Om du misstänker att du har duplikat i dina tweetinsamlingar kan du ta bort duplikaten:

    % utils/deduplicate.py tweets.jsonl > deduped.jsonl

Du kan sortera efter ID, vilket är samma sak som att sortera efter tid.

    % utils/sort_by_id.py tweets.jsonl > sorted.jsonl

Du kan filtrera bort alla tweets före ett specifikt datum (till exempel, om en hashtag användes för en annan händelse före det du är intresserad av):

    % utils/filter_date.py --mindate 1-may-2014 tweets.jsonl > filtered.jsonl

Du kan få en lista i HTML över vilka klienter som använts:

    % utils/source.py tweets.jsonl > sources.html

Om du vill ta bort retweets:

    % utils/noretweets.py tweets.jsonl > tweets_noretweets.jsonl

Eller lösa förkortade url:er (kräver [unshrtn](https://github.com/edsu/unshrtn)):

    % cat tweets.jsonl | utils/unshorten.py > unshortened.jsonl

När du har löst de förkortade url:erna kan du få en ranklista över de mest tweetade url:erna:

    % cat unshortened.jsonl | utils/urls.py | sort | uniq -c | sort -nr > urls.txt

## twarc-report

Ytterligare verktyg för att generera CSV-filer eller json lämpad för att använda med 
[D3.js](http://d3js.org/) visualiseringar kan du hitta i 
[twarc-report](https://github.com/pbinkley/twarc-report) projektet. Verktyget 
 `directed.py`, tidigare en del av twarc, har flyttat till twarc-report som
`d3graph.py`.

Varje skript kan också generera en html-demo av en D3 visualisering, t.ex. 
[timelines](https://wallandbinkley.com/twarc/bill10/) eller en 
[riktad graf av retweets](https://wallandbinkley.com/twarc/bill10/directed-retweets.html).

Översättning: [Andreas Segerberg]

[Engelska]: https://github.com/DocNow/twarc/blob/master/README.md
[Portugisiska]: https://github.com/DocNow/twarc/blob/master/README_pt_br.md
[Spanska]: https://github.com/DocNow/twarc/blob/master/README_es_mx.md
[Swahili]: https://github.com/DocNow/twarc/blob/master/README_sw_ke.md
[Andreas Segerberg]: https://github.com/Segerberg
