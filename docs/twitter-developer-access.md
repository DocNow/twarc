# Twitter Developer Access

If you have established that you would like to use Twitter Data in your study, you will need access to the API. There are several steps required to get access to the API. This is a guide on how best to engage with this process. Allow plenty of time for this.

Twitter has made the process of accessing their API more strict. There are a number of restricted use cases that may require you implement additional safeguards. 

Before applying, the Terms of Service for Developers and the [Restricted Use Cases](https://developer.twitter.com/en/developer-terms/more-on-restricted-use-cases) are very short and relevant to read.

## Step 0: Have a Twitter account in good standing

Create and or edit your Twitter profile to fit your person or organization, preferably in English. Make sure it's public and you do the basic things like verifying your email and phone number (do not use a VoIP service), setting a non default profile picture and header, a description, links to your research group or website, a good description that identifies you as you, and preferably some friends and followers who are already on twitter in your research community. Use a good stable email provider (gmail) or your institution email as long as it is reliable and you can see any emails that may end up in spam, just in case.

## Step 1: Applying for a Developer Account

Fill out the forms for a new developer Account here: <https://developer.twitter.com/en/apply-for-access>. Pay attention to the specifics of each question: especially about sharing data outside of your organization, and with other government entities. Wait for a reply. This may take a couple of weeks.

## Step 2: Apply for the special Academic Access v2 Endpoint

Even if you specify your use case as "Academic" use case in your developer application form, you will not automatically get access to the [new Search endpoint](https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-all) with higher limits for academic use. You must fill in an additional form: <https://developer.twitter.com/en/portal/petition/academic/is-it-right-for-you>

Twitter generally prefers to grant access to faculty and postgrad researchers, not undergrad or masters students or contractors or collaborators. It may be better for the principal investigator or professor to log in from an institution account or their own one, provided it is in good standing and has an obviously identifiable online academic presense.

This application may also take a couple of days or weeks.

## Step 3: Create a Project and App

A Project with Academic Access should be created for you, or if you did not get Academic Access, you can create a new Standard Project. On your Dashboard <https://developer.twitter.com/en/portal/dashboard> you should see "Academic Research" or "Standard" and "Standalone Apps".

Before accessing the v2 API, you will need to create an App or use an existing one and add it to the Academic Access Project first. You can only have 1 App assigned to 1 Project.

When Creating an app, take note of the keys you are given:

API Key: 
```
hCe77nsrgew3gsdhSDGFSgsdf
```

API Secret: 
```
1jWERGWBrtRTWBTwGFDHGFH66SDFGSDFGSSDFGSDFGSSDFGa11
```

Bearer Token: 
```
AAAAAAAAAAAAAAAAAAAAAAAsdfgsAAAAvSDFGSDRgssdfSDFGSDF44gsd4E%3Dkk33345336dfsgsdgsdgsdASGASDGadsGAFAKJGYIUYUIDGGKK
```

These are fake but have the same format as real ones. Note the `%` sign in the Bearer Token - this can often cause errors when copy pasting or providing this token in a command line. Other common causes of errors are including a trailing space, or extra `"` or `'` quotes or not quoting the string in code or command line. This depends on implementation.

These are important to save and [store as you would a password](https://developer.twitter.com/en/docs/authentication/guides/authentication-best-practices).

Continue to "App Settings" and fill in the description field of the app. You don't need to change any other settings here. Generally you will only need Read Only Access and will not need "3-legged OAuth" or callback URLs unlesws you plan on using the [Account Activity API](https://developer.twitter.com/en/docs/twitter-api/enterprise/account-activity-api/overview) if you want to make an interactive Bot for example.

A project must *contain* an app. The difference between a [Project](https://developer.twitter.com/en/docs/projects/overview) and [App](https://developer.twitter.com/en/docs/apps/overview) is sometimes confusing.

*Standalone Apps* are for `v1.1` endpoints, Standard and Academic Access *Projects* are for `v2` endpoints.

## Step 4: Collaborating with Others

Now that you have your keys and tokens, you can start using the API. You may be working with other people on implementations, so you may have to share your keys with someone at some point. Do not share your Twitter user and password details for the Developer Dashboard. This is not a good idea. Currently Twitter's "Teams" functionality is also incompatible with Academic Access. The best way is to provide your colaborator with the keys in a plain text configuration file that you securely share. Or as Environment variables. When someone has your keys, they have full access to the API on your behalf.

Be careful not to commit your keys into a public repository or make them visible to the public - do not include them in a client side js script for example. Most apps will ask for API Key and Secret, but "Consumer Key" is "API Key" and "Consumer Secret" is "API Secret".

For Academic Access, there is only one endpoint that takes Bearer (App Only) authentication, so in most cases, the Bearer Token is all you need to share.

## Step 5: Next Steps

Install `twarc`, and run `twarc2 configure` to set it up.

To make arbitrary API calls for testing, [twurl](https://github.com/twitter/twurl) is a good tool, when combined with [jq](https://stedolan.github.io/jq/).

To get help, a good place is the [Developer Forums](https://twittercommunity.com/), or the [DocNow Slack](https://docs.google.com/forms/d/1Wk0JdF2Cty2VHMqpf_QlJXVKQdUtfeeFhaYRben3qaM/viewform), or [Stackoverflow](https://stackoverflow.com/) for implementation details, or the repository [Issues](https://github.com/DocNow/twarc) if it's an issue with twarc or one of the addons.

To share and publish a Twitter Dataset, extract the Tweet IDs and or User IDs, and format these as 1 ID per line in a plain text file (optionally, you can compress this file). This will make your dataset easier to process for others. See the [DocNow Catalog](https://catalog.docnow.io/) and tools like [Zenodo](https://zenodo.org/) and [Figshare](https://figshare.com/).
