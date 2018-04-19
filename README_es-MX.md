# twarc

*Translations: [pt-BR](https://github.com/DocNow/twarc/blob/master/README_pt_br.md)*

Twarc es una recurso de línea de commando y catálogo de Python para archivar JSON dato de Twitter. Cada tweet se representa como
un artículo de JSON que es [exactamente](https://developer.twitter.com/en/docs/tweets/data-dictionary/overview/tweet-object) lo que fue capturado del API de Twitter. Los Tweets se archivan como [JSON de linea orientado](https://en.wikipedia.org/wiki/JSON_streaming#Line_delimited_JSON). Twarc se encarga del [límite de tarifa](https://developer.twitter.com/en/docs/basics/rate-limiting) del API de Twitter. 
Twarc también puede falicitar la colleción de usarios, tendencias y detallar los identificaciones de los tweets.

Twarc fue desarroyado como parte del proyecto [Documenting the Now](http://www.docnow.io/) el cual fue financiado por el [Mellon Foundation](https://mellon.org/).

## LA INSTALACION

Antes de usar Twarc es necesario registrarse por [apps.twitter.com](https://apps.twitter.com/). Despues de establecer la solicitud, se anota la clabe del consumidor,
el secreto del consumidor, y entoces clickear para generar un access token y el secretro del access token. Con estos quatros requisitos,
está listo para usar Twarc.
    1. Instala [Python](https://www.python.org/downloads/) (2 ó 3)
    2. Instala Twarc atraves de pip (si estas ascendando de categoría: instala de pip--mejorar twarc)
   
## QUICKSTART:

Para empezar, se nececita dirigir a twarc sobre los claves de API:

  `twarc configure`
  
Prueba una búsqueda:

  `twarc search blacklivesmatter > search.josnl`
  
O quisas, preferirá colecionar tweets en tiempo real?

  `twarc filter blacklivesmatter > stream.josnl`
  
Vea abajo por detalles sobre estos mandos y más.

## USO

### Configura
Una vez que tenga sus claves de applicacion, puede dirigir a twarc lo que son con el mando `configure`.

  `twarc configure`
  
Esto se archiva sus credenciales en un archivo que se llama `.twarc` en su directorio personal
para que no tenga que volver a ingresar los datos. Si prefiere ingresar los datos directamente, se
puede establecerlos en el ambiente `(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)` 
o usando las opciones de linea commando `(--consumer_key, --consumer_secret, --access_token, --access_token_secret)`.

### Search

Esto se usa [las busquedas](https://developer.twitter.com/en/docs/api-reference-index) de Twitter para descargar *preexistente* tweets que corresponde a una consulta en particular.

`twarc search blacklivesmatter > tweets.jsonl`

Es importante a notar que usando a `search` resultera los tweets que se encuentran dentro de una ventana de siete dias como se imposa la busqueda del Twitter API. Si parece una ventana minima, lo es, pero puede ser que el interes es en colecionar tweets en tiempo real usando `filter` y `sample` mandos detallados abajo.

La mejor manera de familiarse con la busqueda de syntax de Twitter es con experementar con el [Búsqueda Avanzada de Twitter](https://twitter.com/search-advanced) y copiar y pegar la consulta de la caja de busqueda. Por ejemplo, abajo hay una consulta mas complicado que busca los tweets que contienen #blacklivesmatter o #blm hastags se enviaron a deray.

`twarc search '#blacklivesmatter OR #blm to:deray' > tweets.jsonl`

Twitter puede codificar el lenguaje de un tweet, y puede limitar su busqueda a un lenguaje particular:

`twarc search '#blacklivesmatter' --lang fr > tweets.jsonl`

Tambien, puede buscar tweets dentro de un sitio geografico, por ejemplo los tweets que menciona blacklivesmatter que estan una milla del centro de Ferguson, Missouri:

`twarc search blacklivesmatter --geocode 38.7442,-90.3054,1mi > tweets.jsonl`

Si una busqueda no esta identificado cuando se usa "--geocode" se regresa los tweets en esa ubicacion y radio:

`twarc search --geocode 38.7442,-90.3054,1mi > tweets.jsonl`

### Filter

El mando "filter" se usa Twitter's ["status/filter"](https://developer.twitter.com/en/docs/tutorials/consuming-streaming-data) API para coleccionar tweets en tiempo real.

`twarc filter blacklivesmatter,blm > tweets.jsonl`

Favor de notar que el sintaxis para los track queries de Twitter es differente de las busquedas en el search API. Favor de consultar la documentación.

Use el mando "follow" para colecionar tweets de un identificacion de usario en particular en tiempo real. Incluye retweets. Por ejemplo, esto coleciona tweets y retweets de CNN:

`twarc filter --follow 759251 > tweets.jsonl`

Tambien se puede colecionar tweets usando un "bounding box". Nota: el primer guión necesita estar escapado en el "bounding box" si no, estara interpretado como un argumento de linea de commando!

`twarc filter --locations "\-74,40,-73,41" > tweets.jsonl`

Si combina las opciones seran "OR'ed" juntos. Por ejemplo, esto coleciona los tweets que usan los hashtags de blacklivesmatter o blm y tambien tweets del usario CNN:

`twarc filter blacklivesmatter,blm --follow 759251 > tweets.jsonl`

### Sample

Usa el mando `sample` para probar a los [statuses/API de muestra](https://developer.twitter.com/en/docs/tutorials/consuming-streaming-data) para una muestra "azar" de tweets recientes. 

`twarc sample > tweets.jsonl`

### Dehydrate

El mando `dehydrate` genera una lista de id's de un archivo de tweets:

`twarc dehydrate tweets.jsonl > tweet-ids.txt`

### Hydrate

El mando `hydrate` busca a través de un archivo de identificadores y regresa el JSON del tweet usando el ["status/lookup API"](https://developer.twitter.com/en/docs/api-reference-index). 

`twarc hydrate ids.txt > tweets.jsonl` 


Twitter API's Terms of Service discourage people from making large amounts of raw Twitter data available on the Web. The data can be used for research and archived for local use, but not shared with the world. Twitter does allow files of tweet identifiers to be shared, which can be useful when you would like to make a dataset of tweets available. You can then use Twitter's API to hydrate the data, or to retrieve the full JSON for each identifier. This is particularly important for verification of social media research.

Users
The users command will return User metadata for the given screen names.

twarc users deray,Nettaaaaaaaa > users.jsonl
You can also give it user ids:

twarc users 1232134,1413213 > users.jsonl
If you want you can also use a file of user ids, which can be useful if you are using the followers and friends commands below:

twarc users ids.txt > users.jsonl
Followers
The followers command will use Twitter's follower id API to collect the follower user ids for exactly one user screen name per request as specified as an argument:

twarc followers deray > follower_ids.txt
The result will include exactly one user id per line. The response order is reverse chronological, or most recent followers first.

Friends
Like the followers command, the friends command will use Twitter's friend id API to collect the friend user ids for exactly one user screen name per request as specified as an argument:

twarc friends deray > friend_ids.txt
Trends
The trends command lets you retrieve information from Twitter's API about trending hashtags. You need to supply a Where On Earth identifier (woeid) to indicate what trends you are interested in. For example here's how you can get the current trends for St Louis:

twarc trends 2486982
Using a woeid of 1 will return trends for the entire planet:

twarc trends 1
If you aren't sure what to use as a woeid just omit it and you will get a list of all the places for which Twitter tracks trends:

twarc trends
If you have a geo-location you can use it instead of the woedid.

twarc trends 39.9062,-79.4679
Behind the scenes twarc will lookup the location using Twitter's trends/closest API to find the nearest woeid.

Timeline
The timeline command will use Twitter's user timeline API to collect the most recent tweets posted by the user indicated by screen_name.

twarc timeline deray > tweets.jsonl
You can also look up users using a user id:

twarc timeline 12345 > tweets.jsonl
Retweets
You can get retweets for a given tweet id like so:

twarc retweets 824077910927691778 > retweets.jsonl
Replies
Unfortunately Twitter's API does not currently support getting replies to a tweet. So twarc approximates it by using the search API. Since the search API does not support getting tweets older than a week twarc can only get all the replies to a tweet that have been sent in the last week.

If you want to get the replies to a given tweet you can:

twarc replies 824077910927691778 > replies.jsonl
Using the --recursive option will also fetch replies to the replies as well as quotes. This can take a long time to complete for a large thread because of rate limiting by the search API.

twarc replies 824077910927691778 --recursive
Lists
To get the users that are on a list you can use the list URL with the listmembers command:

twarc listmembers https://twitter.com/edsu/lists/bots
Use as a Library
If you want you can use twarc programmatically as a library to collect tweets. You first need to create a Twarc instance (using your Twitter credentials), and then use it to iterate through search results, filter results or lookup results.

from twarc import Twarc

t = Twarc(consumer_key, consumer_secret, access_token, access_token_secret)
for tweet in t.search("ferguson"):
    print(tweet["text"])
You can do the same for a filter stream of new tweets that match a track keyword

for tweet in t.filter(track="ferguson"):
    print(tweet["text"])
or location:

for tweet in t.filter(locations="-74,40,-73,41"):
    print(tweet["text"])
or user ids:

for tweet in t.filter(follow='12345,678910'):
    print(tweet["text"])
Similarly you can hydrate tweet identifiers by passing in a list of ids or a generator:

for tweet in t.hydrate(open('ids.txt')):
    print(tweet["text"])
Utilities
In the utils directory there are some simple command line utilities for working with the line-oriented JSON, like printing out the archived tweets as text or html, extracting the usernames, referenced URLs, etc. If you create a script that you find handy please send a pull request.

When you've got some tweets you can create a rudimentary wall of them:

% utils/wall.py tweets.jsonl > tweets.html
You can create a word cloud of tweets you collected about nasa:

% utils/wordcloud.py tweets.jsonl > wordcloud.html
If you've collected some tweets using replies you can create a static D3 visualization of them with:

% utils/network.py tweets.jsonl tweets.html
Optionally you can consolidate tweets by user, allowing you to see central accounts:

% utils/network.py --users tweets.jsonl tweets.html
And if you want to use the network graph in a program like Gephi, you can generate a GEXF file with the following:

% utils/network.py --users tweets.jsonl tweets.gexf
gender.py is a filter which allows you to filter tweets based on a guess about the gender of the author. So for example you can filter out all the tweets that look like they were from women, and create a word cloud for them:

% utils/gender.py --gender female tweets.jsonl | utils/wordcloud.py > tweets-female.html
You can output GeoJSON from tweets where geo coordinates are available:

% utils/geojson.py tweets.jsonl > tweets.geojson
Optionally you can export GeoJSON with centroids replacing bounding boxes:

% utils/geojson.py tweets.jsonl --centroid > tweets.geojson
And if you do export GeoJSON with centroids, you can add some random fuzzing:

% utils/geojson.py tweets.jsonl --centroid --fuzz 0.01 > tweets.geojson
To filter tweets by presence or absence of geo coordinates (or Place, see API documentation):

% utils/geofilter.py tweets.jsonl --yes-coordinates > tweets-with-geocoords.jsonl
% cat tweets.jsonl | utils/geofilter.py --no-place > tweets-with-no-place.jsonl
To filter tweets by a GeoJSON fence (requires Shapely):

% utils/geofilter.py tweets.jsonl --fence limits.geojson > fenced-tweets.jsonl
% cat tweets.jsonl | utils/geofilter.py --fence limits.geojson > fenced-tweets.jsonl
If you suspect you have duplicate in your tweets you can dedupe them:

% utils/deduplicate.py tweets.jsonl > deduped.jsonl
You can sort by ID, which is analogous to sorting by time:

% utils/sort_by_id.py tweets.jsonl > sorted.jsonl
You can filter out all tweets before a certain date (for example, if a hashtag was used for another event before the one you're interested in):

% utils/filter_date.py --mindate 1-may-2014 tweets.jsonl > filtered.jsonl
You can get an HTML list of the clients used:

% utils/source.py tweets.jsonl > sources.html
If you want to remove the retweets:

% utils/noretweets.py tweets.jsonl > tweets_noretweets.jsonl
Or unshorten urls (requires unshrtn):

% cat tweets.jsonl | utils/unshorten.py > unshortened.jsonl
Once you unshorten your URLs you can get a ranked list of most-tweeted URLs:

% cat unshortened.jsonl | utils/urls.py | sort | uniq -c | sort -nr > urls.txt
twarc-report
Some further utility scripts to generate csv or json output suitable for use with D3.js visualizations are found in the twarc-report project. The util directed.py, formerly part of twarc, has moved to twarc-report as d3graph.py.

Each script can also generate an html demo of a D3 visualization, e.g. timelines or a directed graph of retweets.


