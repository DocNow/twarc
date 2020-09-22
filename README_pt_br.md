twarc
=====

[![Build Status](https://secure.travis-ci.org/DocNow/twarc.png)](http://travis-ci.org/DocNow/twarc)

*Traduções: [Espanhol], [Inglês], [Japonês], [Suaíli], [Sueco]*

twarc é uma ferramenta de linha de comando e usa a biblioteca Python para arquivamento de dados do Twitter com JSON.
Cada tweet será representado como um objeto JSON
[exatamente](https://dev.twitter.com/overview/api/tweets) o que foi devolvido pela
API do Twitter.  Os Tweets serão armazenados como [JSON, um por linha](https://en.wikipedia.org/wiki/JSON_Streaming#Line-delimited_JSON).  Twarc controla totalmente a API [limites de uso](https://dev.twitter.com/rest/public/rate-limiting)
para você. Além de permitir que você colete Tweets, Twarc também pode ajudá-lo
Coletar usuários, tendências e hidratar tweet ids.

twarc Foi desenvolvido como parte [Documenting the Now](http://www.docnow.io)
Projecto financiado pelo [Mellon Foundation](https://mellon.org/).

## Instalação

Antes de usar twarc você precisa registrar um aplicativo em
[apps.twitter.com](http://apps.twitter.com). Depois de criar o aplicativo, anote a [consumer_key], [consumer_secret] e clique em  Gerar um [access_token] e um [access_token_secret]. Com estas quatro variáveis na mão você está pronto para começar a usar twarc.
OBS: Se tiver alguma dúvida de como criar o aplicativo, consulte [como criar um app](http://blog.difluir.com/2013/06/como-criar-uma-app-no-twitter/)

1. instalação [Python](http://python.org/download) (2 ou 3)
2. pip install twarc

### Homebrew (macOS apenas)

Para usuários do macOS, você pode instalar o `twarc` via:

```bash
$ brew install twarc
```

## Início Rápido:

Primeiro você vai precisar configurar o twarc mostrando a ele suas chaves de API:

    twarc configure

Em seguida, experimente uma pesquisa rápida:

    twarc search blacklivesmatter > search.jsonl

Ou talvez você gostaria de coletar tweets como eles acontecem?

    twarc filter blacklivesmatter > stream.jsonl

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

    twarc search blacklivesmatter > tweets.jsonl

É importante notar que `search` Irá retornar tweets encontrados dentro de uma
Janela de 7 dias imposta pela API de pesquisa do Twitter. Se isso parece uma pequena
Janela,e é, mas você pode estar interessado em coletar tweets como eles acontecem
Usando o `filter` e `sample` comandos abaixo.

A melhor maneira de se familiarizar com a sintaxe de pesquisa do Twitter é experimentando
[Pesquisa Avançada do Twitter](https://twitter.com/search-advanced) E copiar e
colar a consulta resultante da caixa de pesquisa. Por exemplo, aqui está uma
consulta complicada que procura por tweets que contenham
\#blacklivesmatter ou #blm hashtags que foram enviados para deray.

    twarc search '#blacklivesmatter OR #blm to:deray' > tweets.jsonl

Você definitivamente também deve consultar o *excelente* guia de referência de
Igor Brigadir à sintaxe de busca do Twitter:

[Busca Avançada no Twitter](https://github.com/igorbrigadir/twitter-advanced-search/blob/master/README.md)

Lá existem várias pérolas escondidas que não estão muito evidentes no
formulário de pesquisa avançada.

O Twitter tenta codificar a linguagem de um tweet e você pode limitar sua
pesquisa para um idioma específico se quiser usando um código [ISO 639-1]:

    twarc search '#forabolsonaro' --lang pt > tweets.jsonl

Você também pode pesquisar tweets com um determinado local, por exemplo tweets
Mencionando *foratemer* das pessoas situadas a 1 milha na região de Brasília:

    twarc search foratemer --geocode -16.050561,-47.814708,1mi > tweets.jsonl

Se uma consulta de pesquisa não for fornecida`--geocode` Você receberá todos os tweets
Relevantes para esse local e raio:

    twarc search --geocode -16.050561,-47.814708,1mi > tweets.jsonl

### Filter

O comando `filter` Vai usar o Twitter [statuses/filter](https://dev.twitter.com/streaming/reference/post/statuses/filter) API to collect tweets as they happen.

    twarc filter foratemer,blm > tweets.jsonl

Observe que a sintaxe para consultas de queries do Twitter é ligeiramente
diferente do que as consultas em sua API de pesquisa. Por favor, consulte a
documentação sobre a melhor forma de expressar a opção de filtro que você deseja.

Use o comando de linha `follow` com argumento se você quer coletar tweets de
um determinado ID de usuário. Isso inclui retweets. Por exemplo, isso vai
coletar tweets e os retweets da CNN:

    twarc filter --follow 759251 > tweets.jsonl

Você também pode coletar tweets usando uma caixa delimitadora.
Nota: o traço principal precisa ser escapado na caixa delimitadora ou então
ele será interpretado como um comando de linha como argumento!
Exemplo: escapando com a barra invertida após aspas "\

    twarc filter --locations "\-74,40,-73,41" > tweets.jsonl

Se você combinar opções eles serão um OU outro juntos.
Por exemplo, isso irá coletar Tweets que usam o hashtags foratemer
OU blm e também tweets do usuário CNN:

    twarc filter blacklivesmatter,blm --follow 759251 > tweets.jsonl

Mas combinar locais e idiomas resultará efetivamente em um E. Para
exemplo, isso irá coletar tweets da grande área de Nova York que estão em
Espanhol ou francês:

    twarc filter --locations "\-74,40,-73,41" --lang es --lang fr

### Sample

Use o comando `sample` para ouvir/Status do Twitter [statuses/sample](https://dev.twitter.com/streaming/reference/get/statuses/sample) API para uma amostra "aleatória/ramdom" de tweets públicos recentes. O status será do usuário ativo na API twarc.

    twarc sample > tweets.jsonl

### Dehydrate

O comando `dehydrate` gera uma lista de id de um arquivo de tweets:

    twarc dehydrate tweets.jsonl > tweet-ids.txt

### Hydrate

O comando do Twarc `hydrate` Lê um arquivo de IDs de tweets e escreve o tweet em JSON para eles usando Twitter [status/lookup](https://dev.twitter.com/rest/reference/get/statuses/lookup) API.

    twarc hydrate ids.txt > tweets.jsonl

O [Termos do Serviço](https://dev.twitter.com/overview/terms/policy#6._Be_a_Good_Partner_to_Twitter) do Twitter API's desencoraja pessoas na busca de grandes quantidades de dados brutos do Twitter e disponíbilizar na Web. Os dados podem ser usados para pesquisa e arquivados para uso local, mas não devem ser compartilhados com o mundo. O Twitter permite que arquivos de identificadores de tweet sejam compartilhados, o que pode ser útil quando você quer fazer um conjunto de dados de tweets disponíveis. Você pode usar a API do Twitter para *hydrate* dados ou para recuperar o JSON completo para cada identificador/usuário ID. Isto é particularmente importante para [verificação](https://en.wikipedia.org/wiki/Reproducibility) da rede social mundial.

### Usuários

O comando `users` retorna metadados do usuário fornecidos na tela,exemplo:

    twarc users deray,Nettaaaaaaaa > users.jsonl

Você também pode usar os ids do usuário:

    twarc users 1232134,1413213 > users.jsonl

Se você quiser, você também pode usar um arquivo com ids de usuário, o que
pode ser útil se você estiver usando o `followers` e o `friends` conforme
comando abaixo:

    twarc users ids.txt > users.jsonl

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

    twarc timeline deray > tweets.jsonl

Você também pode procurar usuários usando um id de usuário:

    twarc timeline 12345 > tweets.jsonl

### Retuítes

Você pode obter retuítes para um determinado id de tweet como este:

    twarc retweets 824077910927691778 > retweets.jsonl

Se você tiver tweet_ids para os quais gostaria de buscar os retuítes, você pode:

    twarc retweets ids.txt > retweets.jsonl

### Repostas

Infelizmente, a API do Twitter não suporta atualmente a obtenção de respostas
para um tweet. Portanto, o twarc o aproxima usando a API de pesquisa. Como
a API de pesquisa não suporta a obtenção de tweets com mais de uma semana,
o twarc só pode obter todas as respostas a um tweet que foram enviadas na
última semana.

Se você deseja obter respostas para um determinado tweet, você pode:

    twarc replies 824077910927691778 > replies.jsonl

Usar a opção `--recursive` também irá buscar respostas para as respostas, bem
como citações. Isso pode levar muito tempo para ser concluído em um thread
grande por causa de limitação de taxa pela API de pesquisa.

    twarc replies 824077910927691778 --recursive

### Listas

Para obter os usuários que estão em uma lista, você pode usar o URL da lista com o
comando `listmembers`:

    twarc listmembers https://twitter.com/edsu/lists/bots

## Premium Search API

O Twitter introduziu uma API de pesquisa premium que permite que você pague dinheiro 
ao Twitter por tweets. Depois de configurar um ambiente em seu
[painel] (https://developer.twitter.com/en/dashboard) você pode usar seus 30 dias
e endpoints fullarchive para pesquisar tweets fora da janela de 7 dias fornecida
pela API de pesquisa padrão. Para usar a API premium na linha de comando, você
precisará indicar qual terminal você está usando e o ambiente.

Para evitar usar todo o seu orçamento, você provavelmente desejará limitar o
intervalo de tempo usando `--to_date` e` --from_date`. Além disso, você pode
limitar o número máximo de tweets retornados usando `--limit`.

Por exemplo, se eu quisesse obter todos os tweets blacklivesmatter de um
semanas atrás (supondo que hoje seja 1 de Junho de 2020) usando meu ambiente
chamado *docnowdev*, mas não recuperando mais de 1000 tweets, eu poderia:

    twarc search blacklivesmatter \
      --30day docnowdev \
      --from_date 2020-05-01 \
      --to_date 2020-05-14 \
      --limit 1000 \
      > tweets.jsonl

Da mesma forma, para encontrar tweets de 2014 usando o arquivo completo, você
pode:

    twarc search blacklivesmatter \
      --fullarchive docnowdev \
      --from_date 2014-08-04 \
      --to_date 2014-08-05 \
      --limit 1000 \
      > tweets.jsonl

Se o seu ambiente for sandbox, você precisará usar `--sandbox` para que o
twarc saiba que não deve solicitar mais de 100 tweets por vez (o padrão para
ambientes sem sandbox é 500)

    twarc search blacklivesmatter \
      --fullarchive docnowdev \
      --from_date 2014-08-04 \
      --to_date 2014-08-05 \
      --limit 1000 \
      --sandbox \
      > tweets.jsonl

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

## User x App Auth

Twarc gerenciará a limitação de taxas pelo Twitter. No entanto, você deve
saber que a limitação de taxa varia de acordo com a maneira como você
autentica. As duas opções são User Auth e App Auth. O padrão do Twarc é usar a
autenticação do usuário, mas você pode dizer a ele para usar o App Auth.

Mudar para App Auth pode ser útil em algumas situações, como quando você está
pesquisando tweets, já que o User Auth só pode emitir 180 solicitações a cada
15 minutos (1,6 milhões de tweets por dia), mas o App Auth pode emitir 450 (4,
3 milhões de tweets por dia).

Mas tenha cuidado: o endpoint `statuses / lookup` usado pelo subcomando
hydrate tem um limite de taxa de 900 solicitações por 15 minutos para
autenticação do usuário e 300 solicitações por 15 minutos para App Auth.

Se você sabe o que está fazendo e deseja forçar o App Auth, pode usar o opção
de linha de comando `--app_auth`:

    twarc --app_auth search ferguson > tweets.jsonl

Da mesma forma, se você estiver usando Twarc como uma biblioteca, você pode:

```python
from twarc import Twarc

t = Twarc(app_auth=True)
for tweet in t.search('ferguson'):
    print(tweet['id_str'])
```

## Utilitários

No diretório utils existem alguns utilitários via linha de comando simples para
Trabalhar com o JSON gravando linha por por linha, tais como.
- Imprimir os tweets arquivados como Texto ou html.
- Extraindo os nomes de usuários.
- URLs referenciadas.
- Etc.
Se você criar um Script e achar útil, por favor envie um pedido de pull no github do projeto.

Quando você tem alguns tweets você pode criar um paralelo rudimentar deles:

    utils/wall.py tweets.jsonl > tweets.html

Você pode criar uma nuvem de palavras de tweets coletados sobre a nasa:

    utils/wordcloud.py tweets.jsonl > wordcloud.html

Se você coletou alguns tweets usando `respostas`, você pode criar uma
visualização estática D3 deles com:

    utils/network.py tweets.jsonl tweets.html

Opcionalmente, você pode consolidar tweets por usuário, permitindo que você
veja contas centrais:

    utils/network.py --users tweets.jsonl tweets.html

Além disso, você pode criar uma rede de hashtags, permitindo que você
visualize sua alocação:

    utils/network.py --hashtags tweets.jsonl tweets.html

E se você quiser usar o gráfico de rede em um programa como 
[Gephi] (https://gephi.org/), você pode gerar um arquivo GEXF com o seguinte:

    utils/network.py --users tweets.jsonl tweets.gexf
    utils/network.py --hashtags tweets.jsonl tweets.gexf

gender.py É um filtro que permite filtrar tweets com base em um palpite sobre
o gênero do autor. Assim, por exemplo, você pode filtrar todos os tweets que
em tese foram feitos por mulheres, e criar uma nuvem de palavras para eles:

    utils/gender.py --gender female tweets.jsonl | utils/wordcloud.py > tweets-female.html

Você pode com [GeoJSON](http://geojson.org/) ver os tweets de determinadas coordenadas geográficas:

    utils/geojson.py tweets.jsonl > tweets.geojson

Opcionalmente você pode exportar GeoJSON com centróides substituindo as caixas delimitadoras:

    utils/geojson.py tweets.jsonl --centroid > tweets.geojson

E se você exportar GeoJSON com centróides, você pode adicionar alguns fuzzing aleatórios:

    utils/geojson.py tweets.jsonl --centroid --fuzz 0.01 > tweets.geojson

Para filtrar tweets pela presença ou ausência de coordenadas geográficas (Ou Local, veja [Documentação da API locais](https://dev.twitter.com/overview/api/places)):

    utils/geofilter.py tweets.jsonl --yes-coordinates > tweets-with-geocoords.jsonl
    cat tweets.jsonl | utils/geofilter.py --no-place > tweets-with-no-place.jsonl

Para filtrar tweets por uma área com GeoJSON (Requer [Shapely](https://github.com/Toblerity/Shapely)):

    utils/geofilter.py tweets.jsonl --fence limits.geojson > fenced-tweets.jsonl
    cat tweets.jsonl | utils/geofilter.py --fence limits.geojson > fenced-tweets.jsonl

Se você suspeitar ter duplicado seus tweets, você pode remove-los:

    utils/deduplicate.py tweets.jsonl > deduped.jsonl

Você pode classificar por ID, o que é análogo à classificação por tempo:

    utils/sort_by_id.py tweets.jsonl > sorted.jsonl

Você pode filtrar todos os tweets antes de uma determinada data (por exemplo, se uma hashtag foi usada para outro evento antes do que você está interessado):

    utils/filter_date.py --mindate 1-may-2014 tweets.jsonl > filtered.jsonl

Você pode obter uma lista HTML dos usuários usados:

    utils/source.py tweets.jsonl > sources.html

Se você quiser remover os retweets:

    utils/noretweets.py tweets.jsonl > tweets_noretweets.jsonl

Ou unshorten urls (Requer [unshrtn](https://github.com/edsu/unshrtn)):

    cat tweets.jsonl | utils/unshorten.py > unshortened.jsonl

Depois de desfazer masca de seus URLs, você pode obter uma lista classificada dos URLs mais tweeted:

    cat unshortened.jsonl | utils/urls.py | sort | uniq -c | sort -nr > urls.txt

## twarc-report

Alguns scripts de utilitários adicionais para gerar saída csv ou json adequada foi
feito com [D3.js](http://d3js.org/) Visualizações são encontradas
[twarc-report](https://github.com/pbinkley/twarc-report) projeto. O
Util direct.py, anteriormente parte do twarc, mudou-se para twarc-report como
d3graph.py.

Cada script também pode gerar uma demo html de uma visualização D3, e.g.
[timelines](https://wallandbinkley.com/twarc/bill10/) or a
[directed graph of retweets](https://wallandbinkley.com/twarc/bill10/directed-retweets.html).

---

Tradução créditos: [Wilson Jr]

[Espanhol]: https://github.com/DocNow/twarc/blob/main/README_es_mx.md
[Inglês]: https://github.com/DocNow/twarc/blob/main/README.md
[Japonês]: https://github.com/DocNow/twarc/blob/main/README_ja_jp.md
[Sueco]: https://github.com/DocNow/twarc/blob/main/README_sv_se.md
[Suaíli]: https://github.com/DocNow/twarc/blob/main/README_sw_ke.md
[ISO 639-1]: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
[Wilson Jr]: https://github.com/py3in
