# twarc

*Translations: [pt-BR](https://github.com/DocNow/twarc/blob/master/README_pt_br.md)*

Twarc es una recurso de línea de commando y catálogo de Python para archivar JSON dato de Twitter. Cada tweet se representa como
un artículo de JSON que es [exactamente](https://developer.twitter.com/en/docs/tweets/data-dictionary/overview/tweet-object) lo que fue capturado del API de Twitter. Los Tweets se archivan como [JSON de línea orientado](https://en.wikipedia.org/wiki/JSON_streaming#Line_delimited_JSON). Twarc se encarga del [límite de tarifa](https://developer.twitter.com/en/docs/basics/rate-limiting) del API de Twitter. Twarc también puede facilitar la colección de usuarios, tendencias y detallar las identificaciones de los tweets.

Twarc fue desarrollado como parte del proyecto [Documenting the Now](http://www.docnow.io/) el cual fue financiado por el [Mellon Foundation](https://mellon.org/).

## La Instalación

Antes de usar Twarc es necesario registrarse por [apps.twitter.com](https://apps.twitter.com/). Después de establecer la solicitud, se anota el clabe del consumidor, el secreto del consumidor, y entoces clickear para generar un access token y el secretro del access token. Con estos quatros requisitos, está listo para usar Twarc.
1. Instala [Python](https://www.python.org/downloads/) (2 ó 3)
2. Instala Twarc atraves de pip (si estas acezando de categoría: pip install --upgrade twarc)

## Quickstart:

Para empezar, se nececita dirigir a twarc sobre los claves de API:

  `twarc configure`
  
Prueba una búsqueda:

  `twarc search blacklivesmatter > search.josnl`
  
¿O quizás, preferirá coleccionar tweets en tiempo real?

  `twarc filter blacklivesmatter > stream.josnl`
  
Vea abajo por detalles sobre estos commandos y más.

## Uso

### Configure
Una vez que tenga sus claves de aplicación, puede dirigir a twarc lo que son con el commando `configure`.

  `twarc configure`
  
Esto archiva sus credenciales en un archivo que se llama `.twarc` en su directorio personal
para que no tenga que volver a ingresar los datos. Si prefiere ingresar los datos directamente, se
puede establecer en el ambiente `(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)` 
o usando las opciones de línea commando `(--consumer_key, --consumer_secret, --access_token, --access_token_secret)`.

### Search

Esto se usa para [las búsquedas](https://developer.twitter.com/en/docs/api-reference-index) de Twitter para descargar *preexistentes* tweets que corresponde a una consulta en particular.

`twarc search blacklivesmatter > tweets.jsonl`

Es importante a notar que este `search` dara resultados los tweets que se encuentran dentro de una ventana de siete dias como se imponga la búsqueda del Twitter API. Si parece una ventana mínima, lo es, pero puede ser que el interés es en coleccionar tweets en tiempo real usando `filter` y `sample` commandos detallados abajo.

La mejor manera de familiares con la búsqueda de syntax de Twitter es experimentado con el [Búsqueda Avanzada de Twitter](https://twitter.com/search-advanced) y copiar y pegar la consulta de la caja de búsqueda. Por ejemplo, abajo hay una consulta más complicada que busca los tweets que contienen #blacklivesmatter OR #blm hastags que se enviaron a deray.

`twarc search '#blacklivesmatter OR #blm to:deray' > tweets.jsonl`

Twitter puede codificar el lenguaje de un tweet, y puede limitar su búsqueda a un lenguaje particular:

`twarc search '#blacklivesmatter' --lang fr > tweets.jsonl`

También, puede buscar tweets dentro de un lugar geográfico, por ejemplo, los tweets que menciona blacklivesmatter que están a una milla del centro de Ferguson, Missouri:

`twarc search blacklivesmatter --geocode 38.7442,-90.3054,1mi > tweets.jsonl`

Si una bsqueda no está identificado cuando se usa "--geocode" se regresa a los tweets en esa ubicación y radio:

`twarc search --geocode 38.7442,-90.3054,1mi > tweets.jsonl`

### Filter

El commando "filter" se usa Twitter's ["status/filter"](https://developer.twitter.com/en/docs/tutorials/consuming-streaming-data) API para coleccionar tweets en tiempo real.

`twarc filter blacklivesmatter,blm > tweets.jsonl`

Favor de notar que el sintaxis para los track queries de Twitter es differente de las búsquedas en el search API. Favor de consultar la documentación.

Use el commando `follow` para coleccionar tweets de una identificación de usuario en particular en tiempo real. Incluye retweets. Por ejemplo, esto colecciona tweets y retweets de CNN:

`twarc filter --follow 759251 > tweets.jsonl`

También se puede coleccionar tweets usando un "bounding box". Nota: ¡el primer guion necesita estar escapado en el "bounding box" si no, estará interpretado como un argumento de línea de commando!

`twarc filter --locations "\-74,40,-73,41" > tweets.jsonl`

Si combina las opciones serán "OR'ed" juntos. Por ejemplo, esto colecciona los tweets que usan los hashtags de blacklivesmatter o blm y tambien tweets del usario CNN:

`twarc filter blacklivesmatter,blm --follow 759251 > tweets.jsonl`

### Sample

Usa el commando `sample` para probar a los [statuses/API de muestra](https://developer.twitter.com/en/docs/tutorials/consuming-streaming-data) para una muestra "azar" de tweets recientes. 

`twarc sample > tweets.jsonl`

### Dehydrate

El commando `dehydrate` genera una lista de id's de un archivo de tweets:

`twarc dehydrate tweets.jsonl > tweet-ids.txt`

### Hydrate

El mando `hydrate` busca a través de un archivo de identificadores y regresa el JSON del tweet usando el ["status/lookup API"](https://developer.twitter.com/en/docs/api-reference-index). 

`twarc hydrate ids.txt > tweets.jsonl` 

Los [términos de servicio](https://developer.twitter.com/en/developer-terms/policy#6._Be_a_Good_Partner_to_Twitter) del API de Twitter desalientan los usuarios a hacer público por el internet los datos de Twitter. Los datos se pueden usar para el estudio y archivado para uso local, pero no para compartir público. Aún, Twitter permite archivos de identificadores de Twitter ser compartidos. Puede usar el API de Twitter para hidratar los datos, o recuperar el completo JSON dato. Esto es importante para la [verificación](https://en.wikipedia.org/wiki/Reproducibility) del estudio de los redes sociales.

### Users

El commando `user` regresa metadata de usuario para los nobres de pantalla.

`twarc users deray,Nettaaaaaaaa > users.jsonl`

También puede acceder ids de usuario:

`twarc users 1232134,1413213 > users.jsonl`

Si quiere, también se puede usar un archivo de user ids:

`twarc users ids.txt > users.jsonl`

### Followers

El commando `followers` usa el [follower id API](https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/get-followers-ids) para coleccionar los user ids para un nombre de pantalla por búsqueda:

`twarc followers deray > follower_ids.txt`

El resultado incluye un user id por cada línea. El orden es en reversa cronológica, o los followers más recientes.

### Friends

El commando `friends` usa el [friend id API](https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/get-friends-ids) de Twitter para coleccionar los friend user ids para un nombre de pantalla por búsqueda:

`twarc friends deray > friend_ids.txt`

### Trends

El commando `trends` regresa información del Twitter API sobre los hashtags populares. Necesita ingresar un [Where on Earth idenfier (`woeid`)](https://en.wikipedia.org/wiki/WOEID) para indicar cual temas quieres buscar. Por ejemplo:

`twarc trends 2486982`

Usando un woeid de 1 regresara temas para el planeta:

`twarc trends 1`

También se puede omitir el `woeid` y los datos que regresan serán una lista de los lugares por donde Twitter localiza las temas:

`twarc trends`

Si tiene un geo-location, puede usarlo.

`twarc trends 39.9062,-79.4679` 

Twarc buscara el lugar usando el [trends/closest](https://developer.twitter.com/en/docs/api-reference-index) API para encontrar el `woeid` más cerca.

### Timeline

El commando `timeline` usa el [user timeline API](https://developer.twitter.com/en/docs/api-reference-index) para coleccionar los tweets más recientes del usuario indicado por el nombre de pantalla.

`twarc timeline deray > tweets.jsonl`

También se puede buscar usuarios usando un user id:

`twarc timeline 12345 > tweets.jsonl`

### Retweets

Se puede buscar retweets de un tweet específico:

`twarc retweets 824077910927691778 > retweets.jsonl`

### Replies

Desafortunadamente, el API de Twitter no soporte buscando respuestas a un tweet. Entonces, twarc usa el search API. EL search API no regresa tweets mayores de siete días.

Si quieres buscar las respuestas de un tweet:

`twarc replies 824077910927691778 > replies.jsonl`

El commando `--recursive` regresa respuestos a los respuestos. Esto puede tomar mucho tiempo para un thread muy grande porque el rate liming por el search API.

`twarc replies 824077910927691778 --recursive`

### Lists

Para conseguir los usuarios en una lista, se puede usar el list URL con el commando `listmembers`.

`twarc listmembers https://twitter.com/edsu/lists/bots`

## Use as a Library
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


