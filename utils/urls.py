#!/usr/bin/env python

import json
import fileinput
import dateutil.parser
import requests

shorteners = "http://bit.ly/", "http://goo.gl/", "http://t.co/", "http://tinyurl.com/", "http://is.gd/", "http://wp.me/", "http://fb.me/", "http://ow.ly/"

for line in fileinput.input():
    tweet = json.loads(line)
    for url in tweet["entities"]["urls"]:
        if url["expanded_url"]:
            baseurl = url["expanded_url"]
        else:
            baseurl = url
        if baseurl.startswith(shorteners):
        	resp = requests.head(baseurl)
        	if "Location" in resp.headers:
        		print resp.headers["Location"]
        	else:
        		print baseurl
        else:
	        print baseurl
