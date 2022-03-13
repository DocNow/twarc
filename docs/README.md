# twarc

twarc is a command line tool and Python library for collecting and archiving Twitter JSON
data via the Twitter API. It has separate commands (twarc and twarc2) for working with the older
v1.1 API and the newer v2 API and Academic Access (respectively). It also has an ecosystem of [plugins](plugins) for doing things with the collected data. 

See the `twarc` documentation for running commands: [twarc2](twarc2_en_us.md) and [twarc1](twarc2_en_us.md) for using the v1.1 API. If you aren't sure about which one to use you'll want to start with twarc2 since the v1.1 is scheduled to be retired.

## Install

If you have python installed, you can install twarc from a terminal (such as the Windows Command Prompt available in the "start" menu, or the [OSX Terminal application](https://support.apple.com/en-au/guide/terminal/apd5265185d-f365-44cb-8b09-71a064a42125/mac)):

```
pip3 install twarc
```

Once installed, you should be able to use the twarc and twarc2 command line utilities, or use it as a Python library - check the examples [here](api/library.md) for that.

## Other Tools

Twarc is purpose build for working with the twitter API for archiving and studying digital trace data. It is not built as a general purpose API library for Twitter. While the primary use is academic, it works just as well with "Standard" v2 API and "Premium" v1.1 APIs.

For a list of general purpose Twitter Libraries in different languages see the [Twitter Documentation](https://developer.twitter.com/en/docs/twitter-api/tools-and-libraries). For Python, [TwitterAPI](https://github.com/geduldig/TwitterAPI) and [tweepy](https://github.com/tweepy/tweepy) are both up to date and maintained. They also support v2 APIs, and their data format with expansions may differ from twarc. There is also a reference implementation of the [v2 Academic Access Search](https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-all) and [v1.1 Premium Search](https://developer.twitter.com/en/docs/twitter-api/premium/search-api/overview) from Twitter [here](https://github.com/twitterdev/search-tweets-python/). The [v2 version](https://github.com/twitterdev/search-tweets-python/tree/v2) of this script is compatible with twarc.

For `R` there is [academictwitteR](https://cran.r-project.org/web/packages/academictwitteR/vignettes/academictwitteR-intro.html). Unlike twarc, it focuses solely on querying the Twitter Academic Research Product Track v2 API endpoint. Data gathered in twarc can be imported into `R` for analysis as a dataframe if you export the data into CSV using [twarc-csv](https://pypi.org/project/twarc-csv/).

## Getting Help

Check the [tutorials](tutorials.md) to get started, or follow along with this [recorded stream](https://tube.nocturlab.fr/videos/watch/1d98d20e-a4fd-4594-aa94-9b1b1301cead) introducing twarc. If you run into trouble, feel free to make a post on the [Twarc Repository](https://github.com/DocNow/twarc/issues) or on the [Twitter Developer Forums](https://twittercommunity.com/c/academic-research/62).
