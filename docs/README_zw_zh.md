twarc
=====

twarc 是一个用来处理并存档推特 JSON 数据的命令行工具和 Python 包。

[正如](https://dev.twitter.com/overview/api/tweets)推特 API 返回的一样，twarc 处理的每一条推文都用一个 JSON 对象来表示。twarc 会自动处理推特 API 的[流量限制](https://dev.twitter.com/rest/public/rate-limiting)。除了可以让你收集推文之外，twarc 还可以帮助你收集用户信息、当下流行的标签和根据 id 获得推文的详细信息。

twarc 是作为 [Mellon Foundation](https://mellon.org/) 资助下的 [Documenting the Now](http://www.docnow.io) 项目的一部分开发的。

## 安装

在使用 twarc 之前，你需要在 [apps.twitter.com](http://apps.twitter.com) 注册一个应用。一旦你注册了你的应用，记下你的 `consumer key` 和 `consumer secret` 并点击生成一组 `access token` 和 `access token secret`. 这四个数据在手你就可以开始使用 twarc 了。

1. 安装 [Python](http://python.org/download) (2 或者 3)
2. [pip](https://pip.pypa.io/en/stable/installing/) install twarc

### 使用Homebrew (仅限macOS 系统)

macOS系统用户, 你可以通过Homebrew安装 `twarc` :

```shell
$ brew install twarc
```

## 快速开始:

首先你需要告诉 twarc 你的应用 keys 并授权它访问一个或者多个推特账号：

```shell
twarc configure
```

然后尝试搜索

```shell
twarc search blacklivesmatter > search.jsonl
```

或者你想试试实时搜索?

```shell
twarc filter blacklivesmatter > stream.jsonl
```

请阅读下文了解更多这些命令的意义和更多内容。

## 使用

### 配置

在获得应用 keys 之后你可以通过 `configure` 命令来告诉 twarc 它们的值。

```shell
twarc configure
```

这样做会在你的 `~` 目录下创建一个名为 `.twarc` 的文件来储存你的这些凭证，这样你就不必每次使用 twarc 的时候输入它们。如果你倾向于每次使用 twarc 的时候输入 keys，你可以使用环境变量 (`CONSUMER_KEY`,
`CONSUMER_SECRET`, `ACCESS_TOKEN`, `ACCESS_TOKEN_SECRET`) 或者使用命令行工具选项 (`--consumer_key`, `--consumer_secret`, `--access_token`,
`--access_token_secret`).

### 搜索

搜索功能使用推特的[搜索推文](https://dev.twitter.com/rest/reference/get/search/tweets) API endpoint 来下载*已经存在*的符合搜索字符串的推文。

```shell
twarc search blacklivesmatter > tweets.jsonl
```

尤其需要注意的是 `search` 返回的是过去七天内的推文：这是推特搜索 API 的限制。如果你觉得这太短了——我们也觉得——你或许会更愿意尝试使用下文提到的 `filter` 和 `sample` 命令。

最好的快速上手推特搜索语法的方法是实验[推特高级搜索](https://twitter.com/search-advanced)这个页面上的样例。你可以复制粘贴搜索框里的查询语句。比如这里有一个比较复杂的查询语句，它搜索包含有 `#blacklivesmatter` 和 `#blm` 关键字并发给 [deray](https://twitter.com/deray) 的推文。

```shell
twarc search '#blacklivesmatter OR #blm to:deray' > tweets.jsonl
```

你还应当看一看 Igor Brigadir 关于推特高级搜索语法`精彩绝伦`的指南: [推特高级搜索 (英文)](https://github.com/igorbrigadir/twitter-advanced-search/blob/master/README.md). 这份指南里包含了很多阅读推特搜索文档后依然不显然的玄妙之处。

推特尝试显式地定义推文的语言。你可以尝试使用 [ISO 639-1] 规范限制你获得的推文的语言。

```shell
twarc search '#blacklivesmatter' --lang fr > tweets.jsonl
```

你还可以通过位置来搜索。比如你可以搜索包含 `#blacklivesmatter` 且位置定位在密苏里弗格森半径1英里之内的推文。

```shell
twarc search blacklivesmatter --geocode 38.7442,-90.3054,1mi > tweets.jsonl
```

如果一个包含 `--geocode` 的搜索没有包含要查询的字符串，那么你将得到所有与该位置和其半径相关的推文。

```shell
twarc search --geocode 38.7442,-90.3054,1mi > tweets.jsonl
```

### 过滤

`filter` 命令使用推特的 [状态/过滤](https://dev.twitter.com/streaming/reference/post/statuses/filter) API 来搜集实时推文。

```shell
twarc filter blacklivesmatter,blm > tweets.jsonl
```

请注意推特的 `track` 查询语句的语法和搜索 API 里的语法略有不同。请使用官方文档来了解如何最好地表达你的过滤命令选项。

使用 `follow` 命令行参数和用户的 id 来实时收集某个具体用户的推文。注意这个命令的结果包含转推。举个例子，下面的命令搜索 `CNN` 的推文和转推。

```shell
twarc filter --follow 759251 > tweets.jsonl
```

你还可以限制一个地理上的矩形边界来收集推文。注意经纬度数据中的短横线必须用`\`转义，否则它将被理解成一个命令行参数！

```shell
twarc filter --locations "\-74,40,-73,41" > tweets.jsonl
```

你可以使用 `lang` 命令行参数来传入 [ISO 639-1] 语言代码来限制语言。你还可以多次使用这个参数指定多种语言。下面的例子实时收集提到了巴黎和马德里的法语推文和西班牙语推文：

```shell
twarc filter paris,madrid --lang fr --lang es
```

`filter` 和 `follow` 命令是**或**关系。下面的例子将收集包含 `blacklivesmatter` 或者 `blm` 关键字的推文，或者是来自 CNN 的推文。

```shell
twarc filter blacklivesmatter,blm --follow 759251 > tweets.jsonl
```

但是将位置和语言限制合并将得到**和**的关系，下面的例子收集来自纽约且被标记为法语或者西班牙语的推文。

```shell
twarc filter --locations "\-74,40,-73,41" --lang es --lang fr
```

### 采样

使用 `sample` 命令来监听推特的 [状态/采样](https://dev.twitter.com/streaming/reference/get/statuses/sample) API 来“随机“采样最近的、公开的推文。

```shell
twarc sample > tweets.jsonl
```

### `脱水`

所谓的脱水 `dehydrate` 命令读取一个推文的 jsonl 文件，生成一个包含推文 id 的列表。

```shell
twarc dehydrate tweets.jsonl > tweet-ids.txt
```

### `补水`

twarc 所谓的补水命令 `hydrate` 是 `dehydrate` 的反过程，它读取一个包含推文 id 的文件，使用推特的 [状态/检索](https://dev.twitter.com/rest/reference/get/statuses/lookup) API 重建包含完整推文 json 的 jsonl 文件。

```shell
twarc hydrate ids.txt > tweets.jsonl
```

推特 API 的[服务条款](https://dev.twitter.com/overview/terms/policy#6._Be_a_Good_Partner_to_Twitter) 反对用户将大量原始推文数据公布在网络上。数据可以被用来研究使用和保存在本地，但是不可以和世界分享。不过，推特确实允许用户大量地将推文 id 公开分享，而这些 id 可以用来重建推文 JSON 数据——通过 `hydrate` 命令和推特的 API. 这一点对于社交媒体研究中的[复现](https://en.wikipedia.org/wiki/Reproducibility)尤为重要。

### 用户

用户 `users` 命令可以返回（多个）用户的元数据。用户的名称由推特上的屏幕名称唯一确认。（译者注：屏幕名称即你 @ 某用户时所显示的字符串）。

```shell
twarc users deray,Nettaaaaaaaa > users.jsonl
```

你也可以使用用户的 id.

```shell
twarc users 1232134,1413213 > users.jsonl
```

你也可以使用一个包含用户 id 的文件作为输入，这在你同时使用 `followers` 和 `friends` 命令时尤其有用。举例如下：

```shell
twarc users ids.txt > users.jsonl
```

### 粉丝

粉丝 `followers` 命令使用推特的 [粉丝 id](https://dev.twitter.com/rest/reference/get/followers/ids) API 来收集推特用户粉丝的 id 信息。该命令的输入只能是一个用户的屏幕名称。举例如下：

```shell
twarc followers deray > follower_ids.txt
```

输出的结果每一行是一个粉丝用户 id. 最新的粉丝将出现在最前面，依时间顺序倒序排列。

### 朋友

和粉丝 `followers` 命令类似，朋友 `friends` 命令将使用推特的 [朋友 id](https://dev.twitter.com/rest/reference/get/friends/ids) API 收集推特用户朋友的 id 信息。该命令的输入只能是一个用户的屏幕名称。举例如下：

```shell
twarc friends deray > friend_ids.txt
```

### 当下流行

当下流行 `trends` 命令可以用来搜索当下流行的标签。你需要一个 [地球上哪里](https://web.archive.org/web/20180102203025/https://developer.yahoo.com/geo/geoplanet/) 的 id (woeid) 来指明你对哪个地理位置的当下流行标签感兴趣。下面这个例子中的 `2486982` 代表圣路易斯：

```shell
twarc trends 2486982
```

令 `woeid` 为 1 即为搜索全球范围内当下流行的标签：

```shell
twarc trends 1
```

如果你不确定 `woeid`, 可以留空，这样推特会返回一个列表，包括全球各地的当下流行标签。

```shell
twarc trends
```

如果你已经知道确切的地理信息，可以用它来替代 `woeid`. 

```shell
twarc trends 39.9062,-79.4679
```

这里的原理是 twarc 将使用推特的[趋势/最近位置](https://dev.twitter.com/rest/reference/get/trends/closest) API 找到距离指定地点最近的 `woeid`.

### 时间线

时间线 `timeline` 命令将通过推特的[时间线](https://dev.twitter.com/rest/reference/get/statuses/user_timeline) API 收集某个用户最近的推文。用户名称由其屏幕名称指定。

```shell
twarc timeline deray > tweets.jsonl
```

你也可以使用用户 id.

```shell
twarc timeline 12345 > tweets.jsonl
```

### 转推

你可以使用下面这个例子的格式来获得 id 为 `824077910927691778` 这条推文的转推。

```shell
twarc retweets 824077910927691778 > retweets.jsonl
```

输入也可以是一个包含推文 id 的文本。

```shell
twarc retweets ids.txt > retweets.jsonl
```

### 回复

推特的 API 不支持获得回复，但是 twarc 可以通过搜索 API 来近似模拟这一功能。因为搜索 API 的搜索时间区间只有过去一周所以 twarc 只能得到某条推文过去一周的回复。

下面这个例子使用推文 id 作为输入。

```shell
twarc replies 824077910927691778 > replies.jsonl
```

使用 `--recursive` 选项可以获得回复的回复以及引用。注意这可能会花费很长时间因为推特的搜索 API 有流量限制。

```shell
twarc replies 824077910927691778 --recursive
```

### 列表

你可以将推特用户列表的 URL 传入 `listmembers` 命令得到列表中的用户：

```shell
twarc listmembers https://twitter.com/edsu/lists/bots
```

## 付费搜索 API

推特引入了付费搜索 API. 它可以让你通过付款的方式实现更高级的搜索功能。你需要在[仪表板](https://developer.twitter.com/en/dashboard) 配置一个环境。在此之后，你可以搜索不限于最近7天内的推文的过去30天内的备份甚至完整推文备份。如果需要在命令行实现这一功能，你需要告诉 twarc 你在使用哪一个 endpoint 和环境。

为了控制预算，你可能需要限制搜索的时间段：使用 `--to_date` 和 `--frome_date`. 再次之外，你还可以使用 `--limit` 参数来限制返回的推文数目上限。

举例来看，假设今天是2020年6月1日，如果你想搜索不超过1000条从2020年5月1日到2020年5月14日所有提到 `blacklivesmatter` 的推文。如果我们的环境名为 `docnowdev`， 那么这个命令如下，注意我们使用了 `--30day` 这个 endpoint:

```shell
twarc search blacklivesmatter \
    --30day docnowdev \
    --from_date 2020-05-01 \
    --to_date 2020-05-14 \
    --limit 1000 \
    > tweets.jsonl
```

类似的，如果你要搜索超过30天期限的全部推文备份，你需要使用 fullarchive, 举例如下：

```shell
twarc search blacklivesmatter \
    --fullarchive docnowdev \
    --from_date 2014-08-04 \
    --to_date 2014-08-05 \
    --limit 1000 \
    > tweets.jsonl
```

如果你的环境在沙盒之中，你需要使用 `--sandbox` 参数来告诉 twarc 不要获得超过100条推文。默认的非沙盒环境的上限是500条。

```shell
twarc search blacklivesmatter \
    --fullarchive docnowdev \
    --from_date 2014-08-04 \
    --to_date 2014-08-05 \
    --limit 1000 \
    --sandbox \
    > tweets.jsonl
```
## Gnip 企业级 API

twarc 支持和 Gnip 推特全备份企业级 API 的完全整合。你需要使用 `--gnip_auth` 参数并设置好 `GNIP_USERNAME`、 `GNIP_PASSWORD`、 `GNIP_ACCOUNT` 三个环境变量。举例如下：

```shell
twarc search blacklivesmatter \
    --gnip_auth \
    --gnip_fullarchive prod \
    --from_date 2014-08-04 \
    --to_date 2015-08-05 \
    --limit 1000 \
    > tweets.jsonl
```

## 作为一个 Python 包的 twarc

如果你想在你自己的代码里使用 twarc 的话，你需要首先创建一个 `twarc` 实例，传入你的推特应用凭证然后用它进行搜索、过滤和检索。 举例如下：

```python
from twarc import Twarc

t = Twarc(consumer_key, consumer_secret, access_token, access_token_secret)
for tweet in t.search("ferguson"):
    print(tweet["text"])
```

你还可以用同样的语法过滤满足关键字匹配的实时信息流。举例如下：

```python
for tweet in t.filter(track="ferguson"):
    print(tweet["text"])
```

或者地点：

```python
for tweet in t.filter(locations="-74,40,-73,41"):
    print(tweet["text"])
```

或者用户 id:

```python
for tweet in t.filter(follow='12345,678910'):
    print(tweet["text"])
```

类似的，你还可以传入一个包含推特 id 的文件，“补水”以获得完整信息。举例如下：

```python
for tweet in t.hydrate(open('ids.txt')):
    print(tweet["text"])
```

## 基于用户的验证和基于应用的验证

twarc 自动处理推特的流量限制。但是你应该了解流量限制会因为验证方式的不同而不同。推特有两种验证方式分别是基于用户的验证和基于应用的验证。 twarc 默认使用基于用户的验证方式但是你可以告诉 twarc 使用基于应用的验证。

举个例子，转为基于应用的验证可以显著提高搜索功能的效率。基于用户的验证每分钟可以发出180个请求（每天160万条结果），而基于应用的验证每分钟可以发出450个请求（每天430万个结果）。

需要注意的是，用 “补水”功能访问 `状态/检索 (status/lookup)` 这个 API endpoint 在基于用户的验证下有每15分钟900个请求的限制，而在基于应用的验证下是每15分钟300个。

如果你确认你要使用基于应用的验证，你可以使用 `--app_auth` 这个命令行选项。举例如下：

```shell
twarc --app_auth search ferguson > tweets.jsonl
```

类似的功能也可以在你的 Python 代码中实现。

```python
from twarc import Twarc

t = Twarc(app_auth=True)
for tweet in t.search('ferguson'):
    print(tweet['id_str'])
```

## 实用工具


在 `utils` 文件夹下你可以找到几个脚本。这些脚本可以作用于 jsonl 文件上实现一些非常实用的功能：比如将 JSON 格式的推文输出为文本或者 HTML 格式, 提取用户名或者推文中引用的 URL 等等。如果你创作了一个好用的脚本，欢迎提出 PR.

下面的命令可以创作一个简单的推文墙。

```shell
utils/wall.py tweets.jsonl > tweets.html
```

下面的命令可以创作一个简单的词云。

```shell
utils/wordcloud.py tweets.jsonl > wordcloud.html
```

如果你用 `replies` 命令收集了一些推文，你可以用下面的命令创作一个静态的 D3 可视化。

```shell
utils/network.py tweets.jsonl tweets.html
```

你可以增加可选参数根据用户组织推文，这样你可看到这个网络中的核心账号。

```shell
utils/network.py --users tweets.jsonl tweets.html
```

额外的，你可以创作一个标签的网络，从而看到它们彼此之间的（共存）关系。

```shell
utils/network.py --hashtags tweets.jsonl tweets.html
```

如果你想使用网络作图软件 [Gephi](https://gephi.org/),你可以用下面的命令生成一个 `GEXF` 格式的文件。

```shell
utils/network.py --users tweets.jsonl tweets.gexf
utils/network.py --hashtags tweets.jsonl tweets.gexf
```

额外的，如果你想将网络转换成一个随时间线动态变化（节点会出现和消失）的动态网络，你可以在 Gephi 中打开生成的 `GEXF` 文件，跟随这个[教程](https://seinecle.github.io/gephi-tutorials/generated-html/converting-a-network-with-dates-into-dynamic.html)实现。注意在 `tweets.gexf` 文件里，仅有 `start_date` 一栏但是却没有 `end_date` 一栏，这会导致节点出现在屏幕上后便不再消失。对于 Gephi 中的 `Time interval creation options` 跳出窗口，`Start time column` 应该是 `start_date`, 而 `End time column` 则是空白的。`Parse dates` 应该勾选，同时选择最后一个日期格式选项：`dd/MM/yyyy HH:mm:ss`, 如下图所示。

`gender.py` 是一个可以猜测推文作者性别的脚本。比如下面的例子展示了如何保留看上去像是女性发出的推文并生成一个词云。

```shell
utils/gender.py --gender female tweets.jsonl | utils/wordcloud.py >
tweets-female.html
```

你可以用含有地理定位信息的推文生成 [GeoJSON](http://geojson.org/) 格式的文件。

```shell
utils/geojson.py tweets.jsonl > tweets.geojson
```

你还可以用地理边界的[形心](https://en.wikipedia.org/wiki/Centroid)来取代地理位置矩形的边界。

```shell
utils/geojson.py tweets.jsonl --centroid > tweets.geojson
```

在此基础上你还可以加一些随机模糊。

```shell
utils/geojson.py tweets.jsonl --centroid --fuzz 0.01 > tweets.geojson
```

欲了解更多关于利用地理坐标（或地点）的存在与否过滤推文的内容，请参考[文档](https://dev.twitter.com/overview/api/places)。下面是两个例子。

```shell
utils/geofilter.py tweets.jsonl --yes-coordinates > tweets-with-geocoords.jsonl

cat tweets.jsonl | utils/geofilter.py --no-place > tweets-with-no-place.jsonl
```

欲通过 GeoJson 的边界过滤推文，请参考下面的例子。注意你需要安装 [Shapely](https://github.com/Toblerity/Shapely).

```shell
utils/geofilter.py tweets.jsonl --fence limits.geojson > fenced-tweets.jsonl

cat tweets.jsonl | utils/geofilter.py --fence limits.geojson > fenced-tweets.jsonl
```

如果你怀疑你有重复的推文，可以用下面的命令去重。

```shell
utils/deduplicate.py tweets.jsonl > deduped.jsonl
```

你可以用下面的命令像根据时间线排序一样根据推文 id 排序。

```shell
utils/sort_by_id.py tweets.jsonl > sorted.jsonl
```

You can filter out all tweets before a certain date (for example, if a hashtag was used for another event before the one you're interested in):

你可以过滤调某一具体日期前的推文，举个例子，有可能这一日期前某个标签的含义并不是你感兴趣的意思。

```shell
utils/filter_date.py --mindate 1-may-2014 tweets.jsonl > filtered.jsonl
```

你还能够以列表的形式得到客户端信息。

```shell
utils/source.py tweets.jsonl > sources.html
```

下面的命令去除了转推。

```shell
utils/noretweets.py tweets.jsonl > tweets_noretweets.jsonl
```

或者复原原始的 URL 的长度（需要安装[unshrtn](https://github.com/docnow/unshrtn)）。

```shell
cat tweets.jsonl | utils/unshrtn.py > unshortened.jsonl
```

一旦你获得了原始的 URL, 你可以根据推文中提到的次数对这些 URL  排序。

```shell
cat unshortened.jsonl | utils/urls.py | sort | uniq -c | sort -nr > urls.txt
```

## twarc-report 项目

还有一些可以生成 csv 或者 json 输出以供 [D3.js](http://d3js.org/) 可视化使用的脚本可以在 [twarc-report](https://github.com/pbinkley/twarc-report) 项目中找到。原本属于 twarc 一部分的 `directed.py` 脚本也已经被转移到了 twarc-report 项目并被重命名为 `d3graph.py`.

下面的这两个链接包含了两个生成 HTML 格式的 D3 可视化文件的例子。 

1. [timelines](https://wallandbinkley.com/twarc/bill10/)
2. [directed graph of retweets](https://wallandbinkley.com/twarc/bill10/directed-retweets.html)

[英语]: https://github.com/DocNow/twarc/blob/main/README.md
[日语]: https://github.com/DocNow/twarc/blob/main/README_ja_jp.md
[葡萄牙语]: https://github.com/DocNow/twarc/blob/main/README_pt_br.md
[西班牙语]: https://github.com/DocNow/twarc/blob/main/README_es_mx.md
[瑞典语]: https://github.com/DocNow/twarc/blob/main/README_sv_se.md
[斯瓦希里语]: https://github.com/DocNow/twarc/blob/main/README_sw_ke.md
[ISO 639-1]: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
