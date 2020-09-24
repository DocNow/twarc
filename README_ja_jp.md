twarc
=====

[![Build Status](https://secure.travis-ci.org/DocNow/twarc.png)](http://travis-ci.org/DocNow/twarc)

*翻訳: [英語], [ポルトガル語], [スペイン語], [スワヒリ語], [スウェーデン語]*

Twarcは、TwitterのJSONデータをアーカイブするためのコマンドラインツールおよびPythonライブラリーのプログラムです。

- 各ツイートは、Twitter APIから返された内容を[正確に](https://dev.twitter.com/overview/api/tweets)表すJSONオブジェクトとして表示されます。
- ツイートは[line-oriented JSON](https://en.wikipedia.org/wiki/JSON_Streaming#Line-delimited_JSON)として保存されます。
- TwarcがTwitterのAPI[レート制限](https://dev.twitter.com/rest/public/rate-limiting)を処理してくれます。
- Twarcはツイートを収集できるだけでなく、ユーザー、トレンド、ツイートIDの詳細な情報の収集（hydrate; ハイドレート）にも役立ちます。

Twarcは[Mellon Foundation](https://mellon.org/)によって援助された[Documenting the Now](http://www.docnow.io)プロジェクトの一環として開発されました.

## Install | インストール

Twarcを使う前に[Twitter Developers](http://apps.twitter.com)にあなたのアプリケーションを登録する必要があります.

登録したら, コンシューマーキーとその秘密鍵を控えておきます.
そして「Create my access token」をクリックして、アクセストークンと秘密鍵を生成して控えておいてください.
これら4つの鍵が手元に揃えば, Twarcを使い始める準備は完了です.

1. [Python](http://python.org/download)をインストールする (Version2か3)
2. [pip](https://pip.pypa.io/en/stable/installing/) install twarcする

### Homebrew (macOSだけ)

`twarc`は以下によってインストールできます.

```bash
$ brew install twarc
```

## Quickstart | クイックスタート

まず初めに, アプリケーションのAPIキーをTwarcに教え, 1つ以上のTwitterアカウントへのアクセスを許可する必要があります.

    twarc configure

検索を試してみましょう.

    twarc search blacklivesmatter > search.jsonl

または, 呟かれたツイートを収集したいですか？

    twarc filter blacklivesmatter > stream.jsonl

コマンドなどの詳細については, 以下を参照してください.

## Usage | 用法

### Configure | 設定

`configure`コマンドで, 取得したアプリケーションキーをTwarcに教えることができます.

    twarc configure

これにより, ホームディレクトリの`.twarc`というファイルに資格情報が保存されるため, 常に入力し続ける必要はありません.

直接指定したい場合は, 環境変数(`CONSUMER_KEY`, `CONSUMER_SECRET`, `ACCESS_TOKEN`, `ACCESS_TOKEN_SECRET`)か, コマンドラインオプション(`--consumer_key`, `--consumer_secret`, `--access_token`, `--access_token_secret`)を使用してください.

### Search | 検索

検索には, 与えられたクエリに適合する*既存の*ツイートをダウンロードするために, Twitterの[search/tweets](https://dev.twitter.com/rest/reference/get/search/tweets) APIを使います.

    twarc search blacklivesmatter > tweets.jsonl

ここで重要なのは, `search`コマンドがTwitter検索APIの課す7日間以内の期限中から見つかったツイートを返すということです.
もし期限が「短すぎる」と思うのなら(まあそれはそうですが), 以下の`filter`コマンドや`sample`コマンドを使って収集してみると面白いかもしれません.

Twitterの検索構文についてよく知るためのベストプラクティスは, [Twitter's Advanced Search](https://twitter.com/search-advanced)で試してみて, 検索窓からクエリ文の結果をコピペすることです.

例えば以下の例は, `@deray`に送信された, ハッシュタグ`#blacklivesmatter`か`#blm`かの一方を含むツイートを検索する複雑なクエリです.

    twarc search '#blacklivesmatter OR #blm to:deray' > tweets.jsonl

また, [Igor Brigadir](https://github.com/igorbrigadir)の*素晴らしい*Twitter検索構文のリファレンスを絶対にチェックしておくべきです.（[Advanced Search on Twitter](https://github.com/igorbrigadir/twitter-advanced-search/blob/master/README.md)）
高度な検索フォームには, すぐにはみつからない隠れた宝石がたくさんあります.

Twitterはツイートの言語をコーディングしようとします.  [ISO 639-1]コードを使用すれば, 特定の言語に検索を制限できます.

    twarc search '#blacklivesmatter' --lang fr > tweets.jsonl

特定の場所でのツイートを検索することもできます.
例えば, ミズーリ州ファーガソンの中心から1マイルの`blacklivesmatter`に言及するツイートなどを検索できます.

    twarc search blacklivesmatter --geocode 38.7442,-90.3054,1mi > tweets.jsonl

`--geocode`の使用時に検索クエリが提供されない場合, その場所と半径に関連する全てのツイートを返します.

    twarc search --geocode 38.7442,-90.3054,1mi > tweets.jsonl

### Filter | フィルター

`filter`コマンドは, 呟かれたツイートを収集するために, Twitterの[statuses/filter](https://dev.twitter.com/streaming/reference/post/statuses/filter) APIを使います.

    twarc filter blacklivesmatter,blm > tweets.jsonl

ここで注意すべきなのは, Twitterのトラッククエリの構文は, 検索APIのクエリとは少し異なるということです.
そのため, 使用しているフィルターオプションの最も良い表現方法については, ドキュメントを参照してください.

特定のユーザーIDから呟かれたツイートを収集したい場合は, `follow`引数を使いましょう.
これにはリツイートも含まれます. 例えば, これは`@CNN`のツイート及びリツイートを収集します.

    twarc filter --follow 759251 > tweets.jsonl

境界ボックス座標の数値(バウンディングボックス)を用いてツイートを収集することもできます.
注意: 先頭のダッシュ(`-`)はバウンディングボックス内ではエスケープする必要があります. エスケープしないと, コマンドライン引数として解釈されてしまいます！

    twarc filter --locations "\-74,40,-73,41" > tweets.jsonl

`lang`コマンドライン引数を使用して, 検索を制限する[ISO 639-1]の言語コードを渡すことができます.
フィルターストリームでは, 1つ以上の言語でフィルタリングできるため, 繰り返し可能です.
以下は, フランス語またはスペイン語で呟かれた, パリまたはマドリードに言及しているツイートを収集します.

    twarc filter paris,madrid --lang fr --lang es

フィルタを組み合わせてオプションの後ろに続けた場合には, それらは共にORで結がれます.
例えば, これはハッシュタグ`#blacklivesmatter`または`#blm`を使用するツイート, 及びユーザー`@CNN`からのツイートを収集します.

    twarc filter blacklivesmatter,blm --follow 759251 > tweets.jsonl

ただし, 場所と言語を組み合わせると, 結果的にANDになります.
例えば, これは, スペイン語またはフランス語で呟かれた, ニューヨークあたりからのツイートを収集します.

    twarc filter --locations "\-74,40,-73,41" --lang es --lang fr

### Sample | 抽出

`sample`コマンドは, Twitterの[statuses/sample](https://dev.twitter.com/streaming/reference/get/statuses/sample) APIに直近のパブリックステータスの「無作為な」抽出を尋ねるのに使えます.

    twarc sample > tweets.jsonl

### Dehydrate | デハイドレート

`dehydrate`コマンドはツイートのJSONLファイルからツイートIDのリストを生成します.

    twarc dehydrate tweets.jsonl > tweet-ids.txt

### Hydrate | ハイドレート

Twarcの`hydrate`コマンドは, ツイートの識別子のファイルを読み込んで, Twitterの[status/lookup](https://dev.twitter.com/rest/reference/get/statuses/lookup) APIを用いてそれらのツイートのJSONを書き出します.

    twarc hydrate ids.txt > tweets.jsonl

Twitter APIの[利用規約](https://dev.twitter.com/overview/terms/policy#6._Be_a_Good_Partner_to_Twitter)では, 人々が大量のTwitterの生データをWeb上で利用可能にすることを制限しています.

- データは調査に使用したり, ローカルで使用するためにアーカイブしたりできますが, 世界と共有することはできません.
- Twitterはツイートの識別子ファイルを共有することは許可しておらず, それはツイートのデータセットを利用可能にしたい場合に役立ちます.
- それから, Twitter APIでデータを*ハイドレート*(注:水和)したり, またそれぞれの識別子のフルJSONデータを取得することは許可されています.
- `hydrate`は特に, ソーシャルメディア研究を[検証](https://ja.wikipedia.org/wiki/再現性)する時に重要となります.

### Users | ユーザー

`users`コマンドは, 与えられたスクリーンネームを持つユーザーのメタデータを返します.

    twarc users deray,Nettaaaaaaaa > users.jsonl

またユーザーidも与えることができます.

    twarc users 1232134,1413213 > users.jsonl

また, 望むなら以下のようにユーザーidのファイルを使用可能で, `followers`や`friends`といったコマンドを使っているときに有効です.

    twarc users ids.txt > users.jsonl

### Followers | フォロワー

`followers`コマンドは, Twitterの[follower id API](https://dev.twitter.com/rest/reference/get/followers/ids)を用い, 引数として指定されたリクエストごとに1つだけのスクリーン名を持つユーザーのフォロワーのユーザーIDを収集します.

    twarc followers deray > follower_ids.txt

結果には, 行ごとに1つのユーザーIDが含まれ, その応答順序は逆時系列順, すなわち最新のフォロワーが初めに来ます.

### Friends | 友達

`followers`コマンドと同じく, `friends`コマンドはTwitterの[friend id API](https://dev.twitter.com/rest/reference/get/friends/ids)を用いて, 引数として指定されたリクエストごとに1つだけのスクリーン名を持つユーザーのフレンド(フォロー)ユーザーIDを収集します.

    twarc friends deray > friend_ids.txt

### Trends | トレンド

時に, 興味のあるトレンドの地域を示す[Where On Earth](https://web.archive.org/web/20180102203025/https://developer.yahoo.com/geo/geoplanet/)識別子(`WOE ID`)をオプションに与える必要があります.
例としてセントルイスの現在のトレンドを取得するやり方を示します.

    twarc trends 2486982

`WOE ID`に`１`を用いることで, 全世界のトレンドが取得されます.

    twarc trends 1

`WOE ID`として何を使用すればよいかわからない場合は, 以下のように`WOE ID`を省略することで, Twitterがトレンドを追跡している全ての場所のリストを取得できます.

    twarc trends

Geolocationがあれば, `WOE ID`の代わりにジオロケーションを使用できます.

    twarc trends 39.9062,-79.4679

バックグラウンドでTwarcは, Twitterの[trends/closest](https://dev.twitter.com/rest/reference/get/trends/closest) APIを使用して, 場所を検索し, 最も近い`WOE ID`を見つけます.

### Timeline | タイムライン

`timeline`コマンドは, Twitterの[user timeline API](https://dev.twitter.com/rest/reference/get/statuses/user_timeline)を用いて, スクリーンネームで示されるユーザーが投稿した最新のツイートを収集します.

    twarc timeline deray > tweets.jsonl

また, ユーザーIDからユーザーを調べることもできます.

    twarc timeline 12345 > tweets.jsonl

### Retweets | リツイート

指定されたツイートIDのリツイートを以下のように取得できます.

    twarc retweets 824077910927691778 > retweets.jsonl

### Replies | 返信

残念ながら, TwitterのAPIは現在, ツイートへの返信の取得をサポートしていません.
代わりに, Twarcは検索APIを使用してその機能の近似を行います.

Twitterの検索APIは, 1週間以上前のツイートの取得をサポートしていません.
そのため, Twarcは先週までに送信されたツイートに対する返信のみを取得できます.

特定のツイートへの返信を取得したい場合は以下のようにします.

    twarc replies 824077910927691778 > replies.jsonl

`--recursive`オプションを使用すると, 返信に対する返信や引用も取得されます.
検索APIによるレート制限のために, 長いスレッドの場合は完了するのに長時間かかる場合があります.

    twarc replies 824077910927691778 --recursive

### Lists | リスト

リストにあるユーザを取得するには、`listmembers`コマンドで list URLを使用します。

    twarc listmembers https://twitter.com/edsu/lists/bots

## Premium Search API

Twitterでは、ツイートにTwitterのお金を支払うことができるプレミアム検索APIが導入されました。

[ダッシュボード]（https://developer.twitter.com/en/dashboard）で環境設定をした後、
「Standard Search API」が提供する7日間のウィンドウ外で、30日間とフルアーカイブ
でのエンドポイントを使ってツイートを検索することができます。コマンドラインから
Premium APIを使用するには、使用しているエンドポイントと環境を指定する必要があります。

予算全体を使い果たすことを避けるために、`--to_date`と`--from_date`を使用して
時間範囲を制限することをおすすめします。また、`--limit`を使用して返される
ツイートの最大数を制限することができます。

例えば、（今日が2020年6月1日だと仮定し）2週間前の全てのblacklivesmatterツイートを、
*docnowdev*という名前の環境を使って取得したいが、1000件以上のツイートを取得しない
場合は、次のような操作ができる。

    twarc search blacklivesmatter \
      --30day docnowdev \
      --from_date 2020-05-01 \
      --to_date 2020-05-14 \
      --limit 1000 \
      > tweets.jsonl

同様に、フルアーカイブを使用して2014年のツイートを検索するには、次の方法があります。

    twarc search blacklivesmatter \
      --fullarchive docnowdev \
      --from_date 2014-08-04 \
      --to_date 2014-08-05 \
      --limit 1000 \
      > tweets.jsonl

環境がサンドボックス化されている場合、Twarcが一度に100件以上のツイートを要求しないように、
`--sandbox`を使用する必要があります。（サンドボックス化されていない環境のデフォルトは 500）

    twarc search blacklivesmatter \
      --fullarchive docnowdev \
      --from_date 2014-08-04 \
      --to_date 2014-08-05 \
      --limit 1000 \
      --sandbox \
      > tweets.jsonl

## Use as a Library | ライブラリとして使用

必要で応じてTwarcをプログラム的にライブラリとして使ってツイートを収集することができます。
最初に（Twitterの資格情報を使用して）Twarcインスタンスを作成し、検索結果、フィルタ結果、
または検索結果の反復を処理するために使用できます。

```python
from twarc import Twarc

t = Twarc(consumer_key, consumer_secret, access_token, access_token_secret)
for tweet in t.search("ferguson"):
    print(tweet["text"])
```

trackキーワードに一致する新しいツイートのフィルタストリームに対しても同じことができます。

```python
for tweet in t.filter(track="ferguson"):
    print(tweet["text"])
```

また`location`なら,

```python
for tweet in t.filter(locations="-74,40,-73,41"):
    print(tweet["text"])
```

`user id`なら,

```python
for tweet in t.filter(follow='12345,678910'):
    print(tweet["text"])
```

同様に, IDのリストまたはジェネレーターを渡すことで, ツイートIDをハイドレートできます.

```python
for tweet in t.hydrate(open('ids.txt')):
    print(tweet["text"])
```

## User vs App Auth

TwarcはTwitterによるレート制限を管理しますが、 それらのレート制限は、認証方法によって
異なります。ユーザー認証とアプリ認証の２つのオプションがありますが、Twarcは
デフォルトでユーザー認証を使用するので、アプリ認証を使用するように指示することもできます。

アプリ認証への切り替えは、ツイートを検索するときなんかに便利です。ユーザー認証は
15分ごとに180件(1日あたり160万件)しかリクエストできないのに対し、アプリ認証は450件
(1日あたり430万件)のリクエストができるからです。

ただし注意すべきことは、ハイドレートサブコマンドで使用される`statuses / lookup`
エンドポイントには、ユーザー認証の場合は15分あたり900件までリクエスト、アプリ
認証の場合は15分あたり300件までのリクエストのレート制限があるということです。

自分が何をしているかを知っていて、アプリ認証を強制したい場合は、次のように`--app_auth`
コマンドラインオプションが使用できます。

    twarc --app_auth search ferguson > tweets.jsonl

同様に、Twarcをライブラリとして使用している場合は、次のことができます。

```python
from twarc import Twarc

t = Twarc(app_auth=True)
for tweet in t.search('ferguson'):
    print(tweet['id_str'])
```

## Utilities | ユーティリティ

`utils`ディレクトリには, line-oriented JSONを操作するための簡単なコマンドラインユーティリティがいくつかあります.
例えばアーカイブされたツイートをテキストまたはHTMLとして出力したり, ユーザー名や参照URLなどを抽出したりするものです.

便利なスクリプトを自作したら, 是非プルリクエストをください.

いくつかツイートが手元にある時, それらを用いて初歩的なWallを作成できます.

    utils/wall.py tweets.jsonl > tweets.html

`NASA`について収集したツイートのワードクラウドを作成できます.

    utils/wordcloud.py tweets.jsonl > wordcloud.html

`replies`コマンドを用いていくつかのツイートを収集した場合, それらの静的な`D3.js`を用いたビジュアライゼーションを作成できます.

    utils/network.py tweets.jsonl tweets.html

必要に応じてユーザーごとにツイートを統合し, その中心のアカウントを表示できます.

    utils/network.py --users tweets.jsonl tweets.html

[Gephi](https://gephi.org/)などのプログラムでネットワークグラフを使用する場合は, 次のようにGEXFファイルを生成できます.

    utils/network.py --users tweets.jsonl tweets.gexf

`gender.py`は, 著者の性別に関する推測に基づいてツイートをフィルタリングできるフィルターです.
例えば, 女性からのもののように見えるすべてのツイートを除外し, それらの単語クラウドを作成できます.

    utils/gender.py --gender female tweets.jsonl | utils/wordcloud.py > tweets-female.html

地理座標が利用可能なツイートから[GeoJSON](http://geojson.org/)を出力できます.

    utils/geojson.py tweets.jsonl > tweets.geojson

必要に応じて, バウンディングボックスを置き換える重心を用いたGeoJSONをできます.

    utils/geojson.py tweets.jsonl --centroid > tweets.geojson

また, 重心を用いたGeoJSONをエクスポートする場合に, ランダムファジングを追加することもできます.

    utils/geojson.py tweets.jsonl --centroid --fuzz 0.01 > tweets.geojson

地理座標の有無でツイートをフィルタリングするには, (場所については以下を参照:[API documentation](https://dev.twitter.com/overview/api/places))

    utils/geofilter.py tweets.jsonl --yes-coordinates > tweets-with-geocoords.jsonl
    cat tweets.jsonl | utils/geofilter.py --no-place > tweets-with-no-place.jsonl

GeoJSONのフェンスでツイートをフィルタリングするには, (要:[Shapely](https://github.com/Toblerity/Shapely))

    utils/geofilter.py tweets.jsonl --fence limits.geojson > fenced-tweets.jsonl
    cat tweets.jsonl | utils/geofilter.py --fence limits.geojson > fenced-tweets.jsonl

ツイートに重複があると思われる場合は, 重複の排除が可能です.

    utils/deduplicate.py tweets.jsonl > deduped.jsonl

ID順ソートできます.これは, 時間順ソートに似ています.

    utils/sort_by_id.py tweets.jsonl > sorted.jsonl

特定の日付以前のすべてのツイートを除外できます.
例えば, 以下は関心のあるイベントの前, 別のイベントにハッシュタグが使用されていた場合です.

    utils/filter_date.py --mindate 1-may-2014 tweets.jsonl > filtered.jsonl

使用されているクライアントのHTMLリストを取得できます.

    utils/source.py tweets.jsonl > sources.html

リツイートを削除する場合は,

    utils/noretweets.py tweets.jsonl > tweets_noretweets.jsonl

またはURLの短縮を解除したい場合は, (要:[unshrtn](https://github.com/docnow/unshrtn))

    cat tweets.jsonl | utils/unshrtn.py > unshortened.jsonl

URLを短縮すると, 最もよくツイートされたURLのランキングリストを取得できます.

    cat unshortened.jsonl | utils/urls.py | sort | uniq -c | sort -nr > urls.txt

## twarc-report

[twarc-report](https://github.com/pbinkley/twarc-report)プロジェクトでは, [D3.js](http://d3js.org/)でのビジュアライゼーションでの使用に適したCSVまたはJSONを生成・出力するユーティリティスクリプトを用意しています.
以前はTwarcの一部であった`directed.py`は`d3graph.py`としてtwarc-reportプロジェクトに移管しました.

またそれぞれのスクリプトは, ビジュアライゼーションのHTMLでのデモを生成できます.

具体例として,
  - [タイムライン](https://www.wallandbinkley.com/twarc/bill10/)
  - [リツイートの有向グラフ](https://www.wallandbinkley.com/twarc/bill10/directed-retweets.html)

があります.

---

翻訳クレジット: [Haruna]

[英語]: https://github.com/DocNow/twarc/blob/main/README.md
[ポルトガル語]: https://github.com/DocNow/twarc/blob/main/README_pt_br.md
[スペイン語]: https://github.com/DocNow/twarc/blob/main/README_es_mx.md
[スウェーデン語]: https://github.com/DocNow/twarc/blob/main/README_sv_se.md
[スワヒリ語]: https://github.com/DocNow/twarc/blob/main/README_sw_ke.md
[ISO 639-1]: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
[Haruna]: https://github.com/eggplants
