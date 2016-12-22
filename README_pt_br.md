twarc
=====

[![Build Status](https://secure.travis-ci.org/DocNow/twarc.png)](http://travis-ci.org/DocNow/twarc)

twarc é uma ferramenta de linha de comando e usa a biblioteca Python para arquivamento de dados do Twitter com JSON.
Cada tweet será representado como um objeto JSON 
[exatamente](https://dev.twitter.com/overview/api/tweets) o que foi devolvido pela
API do Twitter.  Os Tweets serão armazenados como JSON, um por linha.  Twarc controla totalmente a API [limites de uso](https://dev.twitter.com/rest/public/rate-limiting)
para você. Além de permitir que você colete Tweets, Twarc também pode ajudá-lo
Coletar usuários, tendências e hidratar tweet ids. 

twarc Foi desenvolvido como parte [Documenting the Now](https://www.docnow.io)
Projecto financiado pelo [Mellon Foundation](https://mellon.org/).

## Instalação

Antes de usar twarc você precisa registrar um aplicativo em
[apps.twitter.com](http://apps.twitter.com). Depois de criar o aplicativo, anote a [consumer_key], [consumer_secret] e clique em  Gerar um [access_token] e um [access_token_secret]. Com estas quatro variáveis na mão você está pronto para começar a usar twarc. 
OBS: Se tiver alguma dúvida de como criar o aplicativo, consulte [como criar um app](http://blog.difluir.com/2013/06/como-criar-uma-app-no-twitter/)

1. instalação [Python](http://python.org/download) (2 ou 3)
2. pip install twarc

## Início Rápido:

Primeiro você vai precisar configurar o twarc mostrando a ele suas chaves de API:

    twarc configure

Em seguida, experimente uma pesquisa rápida:

    twarc search blacklivesmatter > search.json

Ou talvez você gostaria de coletar tweets como eles acontecem?

    twarc filter blacklivesmatter > stream.json

Veja abaixo os detalhes sobre esses comandos e muito mais.

## Uso

### Configurar

Uma vez que você tem suas chaves de aplicativo, você pode dizer ao twarc quais são com o comando 
`configure`.

    twarc configure 

Isso irá armazenar as credenciais em um arquivo chamado `.twarc` em seu 
diretório home. Este arquivo será usado como padrão em outras chamadas.
Se preferir, você pode fornecer diretamente as chaves (`CONSUMER_KEY`,
`CONSUMER_SECRET`, `ACCESS_TOKEN`, `ACCESS_TOKEN_SECRET`) ou usando a linha de comando 
com as opções (`--consumer_key`, `--consumer_secret`, `--access_token`,
`--access_token_secret`).

### Pesquisar 

Os usuários do Twitter [Pesquisar/tweets](https://dev.twitter.com/rest/reference/get/search/tweets) para baixar *pre-existing* tweets, correspondendo a uma determinada consulta que desejar.

    twarc search blacklivesmatter > tweets.json 

É importante notar que `search` Irá retornar tweets encontrados dentro de uma
Janela de 7 dias imposta pela API de pesquisa do Twitter. Se isso parece uma pequena
Janela,e é, mas você pode estar interessado em coletar tweets como eles acontecem
Usando o `filter` e `sample` comandos abaixo.

A melhor maneira de se familiarizar com a sintaxe de pesquisa do Twitter é experimentando
[Pesquisa Avançada do Twitter](https://twitter.com/search-advanced) E copiar e
colar a consulta resultante da caixa de pesquisa. Por exemplo, aqui está uma
consulta complicada que procura por tweets que contenham
\#blacklivesmatter ou #blm hashtags que foram enviados para deray.

    twarc search '#blacklivesmatter OR #blm to:deray' > tweets.json

O Twitter tenta codificar o idioma de um tweet ou você pode limitar sua pesquisa.
Para um idioma específico caso você queira só português:

    twarc search '#foratemer' --lang pt > tweets.json

Você também pode pesquisar tweets com um determinado local, por exemplo tweets
Mencionando *foratemer* das pessoas situadas a 1 milha na região de Brasília:

    twarc search foratemer --geocode -16.050561,-47.814708,1mi > tweets.json

Se uma consulta de pesquisa não for fornecida`--geocode` Você receberá todos os tweets
Relevantes para esse local e raio:
    
    twarc search --geocode -16.050561,-47.814708,1mi > tweets.json

### Filter

O comando `filter` Vai usar o Twitter [statuses/filter](https://dev.twitter.com/streaming/reference/post/statuses/filter) API to collect tweets as they happen.

    twarc filter foratemer,blm > tweets.json

Observe que a sintaxe para consultas de queries do Twitter é ligeiramente
diferente do que as consultas em sua API de pesquisa. Por favor, consulte a
documentação sobre a melhor forma de expressar a opção de filtro que você deseja.

Use o comando de linha `follow` com argumento se você quer coletar tweets de
um determinado ID de usuário. Isso inclui retweets. Por exemplo, isso vai
coletar tweets e os retweets da CNN:

    twarc filter --follow 759251 > tweets.json

Você também pode coletar tweets usando uma caixa delimitadora. 
Nota: o traço principal precisa ser escapado na caixa delimitadora ou então 
ele será interpretado como um comando de linha como argumento!
Exemplo: escapando com a barra invertida após aspas "\

    twarc filter --locations "\-74,40,-73,41" > tweets.json


Se você combinar opções eles serão um OU outro juntos. 
Por exemplo, isso irá coletar Tweets que usam o hashtags foratemer 
OU blm e também tweets do usuário CNN:

    twarc filter blacklivesmatter,blm --follow 759251 > tweets.json

### Sample

Use o comando de linha `sample` para ouvir/Status do Twitter [statuses/sample](https://dev.twitter.com/streaming/reference/get/statuses/sample) API para uma amostra "aleatória/ramdom" de tweets  públicos recentes. O status será do usuário ativo na API twarc. 

    twarc sample > tweets.json

### Hydrate

O comando do Twarc `hydrate` Lê um arquivo de IDs de tweets identificados e escreve o tweet em JSON para eles usando Twitter [status/lookup](https://dev.twitter.com/rest/reference/get/statuses/lookup) API.

    twarc hydrate ids.txt > tweets.json

O [Termos do Serviço](https://dev.twitter.com/overview/terms/policy#6._Be_a_Good_Partner_to_Twitter) do Twitter API's desencoraja pessoas na busca de grandes quantidades de dados brutos do Twitter e disponíbilizar na Web. Os dados podem ser usados para pesquisa e arquivados para uso local, mas não devem ser compartilhados com o mundo. O Twitter permite que arquivos de identificadores de tweet sejam compartilhados, o que pode ser útil quando você quer fazer um conjunto de dados de tweets disponíveis. Você pode usar a API do Twitter para *hydrate* dados ou para recuperar o JSON completo para cada identificador/usuário ID. Isto é particularmente importante para [verificação](https://en.wikipedia.org/wiki/Reproducibility) da rede social mundial.

### Usuários

O comando `users` retorna metadados do usuário fornecidos na tela,exemplo:

    twarc users deray,Nettaaaaaaaa > users.json

Você também pode usar os ids do usuário:

    twarc users 1232134,1413213 > users.json

Se você quiser, você também pode usar um arquivo com ids de usuário, o que pode ser útil se você estiver
usando o `followers` e o `friends` conforme comando abaixo:

    twarc users ids.txt > users.json

### Seguidores (Quem me segue)

O comando `followers` Vai usar o Twitter [API seguidores ID](https://dev.twitter.com/rest/reference/get/followers/ids) Para coletar os ids dos usuários que estão seguindo exatamente o nome informado na tela. Veja como é feita a solicitação usando o nome do user como argumento:

    twarc followers deray > follower_ids.txt

O resultado incluirá exatamente um ID de usuário por linha. 
A ordem de resposta é Invertida cronológicamente, o mais recente seguidores em primeiro lugar.

### Amigos (Quem eu sigo)

Igual o comando `followers`, o comando` friends` usará o Twitter [API amigos ID](https://dev.twitter.com/rest/reference/get/friends/ids) Para coletar os IDs de usuário amigo/friends com o nome que foi informado na tela no momento da solicitação,conforme especificado abaixo no argumento:

    twarc friends deray > friend_ids.txt

### Trends / tendências 

O comando `trends` permite recuperar informações da API do Twitter sobre hashtags tendências. Você precisa fornecer um  [Onde na Terra](http://developer.yahoo.com/geo/geoplanet/) identificador (`woeid`) para indicar quais as tendências que você está interessado. Por exemplo, aqui é como você pode obter as tendências atuais para St Louis:

    twarc trends 2486982

Usando um `woeid` de 1 irá retornar tendências para todo o planeta, ou trends mundiais:

    twarc trends 1

Se você não tem certeza do que usar como um "woeid", não se preocupe, apenas omita seu valor e você receberá uma lista
de todos os lugares para os quais o Twitter acompanha as tendências:

    twarc trends

Se você já tem uma [geo-location/geo localização], você pode usar diretamente no seu `woedid`.

    twarc trends 39.9062,-79.4679

Por trás das cenas, o twarc buscará o local usando o Twitter [trends/closest](https://dev.twitter.com/rest/reference/get/trends/closest) API para encontrar a `woeid`.

### Timeline

O comando timeline usará do Twitter [API user timeline](https://dev.twitter.com/rest/reference/get/statuses/user_timeline) Para coletar os tweets mais recentes postados pelo usuário indicado por um screen_name.

    twarc timeline deray > tweets.json

Você também pode procurar usuários usando um id de usuário:

    twarc timeline 12345 > tweets.json

## Usar twarc como uma biblioteca

Se você quiser pode usar `twarc` programaticamente como uma biblioteca 
para coletar Tweets. Primeiro você precisa criar uma instância do `Twarc` 
(usando as suas Credenciais do Twitter) e, em seguida, usá-lo para iterar 
através de resultados de pesquisa ou filtrar resultados de pesquisa.

```python
from twarc import Twarc

t = Twarc(consumer_key, consumer_secret, access_token, access_token_secret)
for tweet in t.search("ferguson"):
    print(tweet["text"])
```

Você pode fazer o mesmo para um fluxo de filtro de novos tweets que 
correspondem a uma determinada faixa usando palavra-chave.

```python
for tweet in t.filter(track="ferguson"):
    print(tweet["text"])
```

ou localização:

```python
for tweet in t.filter(locations="-74,40,-73,41"):
    print(tweet["text"])
```

ou IDS do usuário:

```python
for tweet in t.filter(follow='12345,678910'):
    print(tweet["text"])
```

Da mesma forma você pode hidratar os identificadores de tweet passando 
em uma lista de ids ou um gerador:

```python
for tweet in t.hydrate(open('ids.txt')):
    print(tweet["text"])
```

## Utilities

In the utils directory there are some simple command line utilities for
working with the line-oriented JSON, like printing out the archived tweets as
text or html, extracting the usernames, referenced URLs, etc.  If you create a
script that you find handy please send a pull request.

When you've got some tweets you can create a rudimentary wall of them:

    % utils/wall.py tweets.json > tweets.html

You can create a word cloud of tweets you collected about nasa:

    % utils/wordcloud.py tweets.json > wordcloud.html

gender.py is a filter which allows you to filter tweets based on a guess about
the gender of the author. So for example you can filter out all the tweets that
look like they were from women, and create a word cloud for them:

    % utils/gender.py --gender female tweets.json | utils/wordcloud.py > tweets-female.html

You can output [GeoJSON](http://geojson.org/) from tweets where geo coordinates are available:

    % utils/geojson.py tweets.json > tweets.geojson

Optionally you can export GeoJSON with centroids replacing bounding boxes:

    % utils/geojson.py tweets.json --centroid > tweets.geojson

And if you do export GeoJSON with centroids, you can add some random fuzzing:

    % utils/geojson.py tweets.json --centroid --fuzz 0.01 > tweets.geojson

To filter tweets by presence or absence of geo coordinates (or Place, see [API documentation](https://dev.twitter.com/overview/api/places)):

    % utils/geofilter.py tweets.json --yes-coordinates > tweets-with-geocoords.json
    % cat tweets.json | utils/geofilter.py --no-place > tweets-with-no-place.json

To filter tweets by a GeoJSON fence (requires [Shapely](https://github.com/Toblerity/Shapely)):

    % utils/geofilter.py tweets.json --fence limits.geojson > fenced-tweets.json
    % cat tweets.json | utils/geofilter.py --fence limits.geojson > fenced-tweets.json

If you suspect you have duplicate in your tweets you can dedupe them:

    % utils/deduplicate.py tweets.json > deduped.json

You can sort by ID, which is analogous to sorting by time:

    % utils/sort_by_id.py tweets.json > sorted.json

You can filter out all tweets before a certain date (for example, if a hashtag was used for another event before the one you're interested in):

    % utils/filter_date.py --mindate 1-may-2014 tweets.json > filtered.json

You can get an HTML list of the clients used:

    % utils/source.py tweets.json > sources.html

If you want to remove the retweets:

    % utils/noretweets.py tweets.json > tweets_noretweets.json

Or unshorten urls (requires [unshrtn](https://github.com/edsu/unshrtn)):

    % cat tweets.json | utils/unshorten.py > unshortened.json

Once you unshorten your URLs you can get a ranked list of most-tweeted URLs:

    % cat unshortened.json | utils/urls.py | sort | uniq -c | sort -nr > urls.txt

## twarc-report

Some further utility scripts to generate csv or json output suitable for
use with [D3.js](http://d3js.org/) visualizations are found in the
[twarc-report](https://github.com/pbinkley/twarc-report) project. The
util directed.py, formerly part of twarc, has moved to twarc-report as
d3graph.py.

Each script can also generate an html demo of a D3 visualization, e.g.
[timelines](https://wallandbinkley.com/twarc/bill10/) or a
[directed graph of retweets](https://wallandbinkley.com/twarc/bill10/directed-retweets.html).
