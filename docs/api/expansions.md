# twarc.expansions

[Expansions](https://developer.twitter.com/en/docs/twitter-api/expansions) are how the new v2 Twitter API includes optional metadata about Tweets. In contrast to v1.1, where each Tweet JSON object is self-contained, in v2 metadata about a whole "page" of requests is included in the response. This means that to get a self-contained Tweet JSON, additional processing is needed to look up each piece of extra metadata. Different tools and libraries may implement this in different ways. In twarc, the goal was to retain the original JSON format and only append extra fields, so that any code that expects original JSON will still work.

::: twarc.expansions
  handler: python
