"""
A function for asking the user for their Twitter API keys.
"""

import requests

from requests_oauthlib import OAuth1
from urllib.parse import parse_qs

def handshake():

    # Default empty keys
    consumer_key = ""
    consumer_secret = ""
    access_token = ""
    access_token_secret = ""

    bearer_token = input(
        "Please enter your Bearer Token (leave blank to skip to API key configuration): "
    )

    if bearer_token:
        continue_adding = input(
            "(Optional) Add API keys and secrets for user mode authentication [y or n]? "
        )

        # Save a config with just the bearer_token
        if continue_adding.lower() != "y":
            return {"bearer_token": bearer_token}
        else:
            "Configure API keys and secrets."

    consumer_key = input("Please enter your API key: ")
    consumer_secret = input("Please enter your API secret: ")

    # verify that the keys work to get the bearer token
    url = "https://api.twitter.com/oauth2/token"
    params = {"grant_type": "client_credentials"}
    auth = requests.auth.HTTPBasicAuth(consumer_key, consumer_secret)
    try:
        resp = requests.post(url, params, auth=auth)
        resp.raise_for_status()
        result = resp.json()
        bearer_token = result['access_token']
    except Exception as e:
        return None

    answered = False
    while not answered:
        print("\nHow would you like twarc to obtain your user keys?\n\n1) generate access keys by visiting Twitter\n2) manually enter your access token and secret\n")
        answer = input('Please enter your choice [1 or 2] ')
        if answer == "1":
            answered = True
            generate = True
        elif answer == "2":
            answered = True
            generate = False

    if generate:
        request_token_url = 'https://api.twitter.com/oauth/request_token'
        oauth = OAuth1(consumer_key, client_secret=consumer_secret)
        r = requests.post(url=request_token_url, auth=oauth)

        credentials = parse_qs(r.text)
        if not credentials:
            print("\nError: invalid credentials.")
            print("Please check that you are copying and pasting correctly and try again.\n")
            return

        resource_owner_key = credentials.get('oauth_token')[0]
        resource_owner_secret = credentials.get('oauth_token_secret')[0]

        base_authorization_url = 'https://api.twitter.com/oauth/authorize'
        authorize_url = base_authorization_url + '?oauth_token=' + resource_owner_key
        print('\nPlease log into Twitter and visit this URL in your browser:\n%s' % authorize_url)
        verifier = input('\nAfter you have authorized the application please enter the displayed PIN: ')

        access_token_url = 'https://api.twitter.com/oauth/access_token'
        oauth = OAuth1(consumer_key,
                       client_secret=consumer_secret,
                       resource_owner_key=resource_owner_key,
                       resource_owner_secret=resource_owner_secret,
                       verifier=verifier)
        r = requests.post(url=access_token_url, auth=oauth)
        credentials = parse_qs(r.text)

        if not credentials:
            print('\nError: invalid PIN')
            print('Please check that you entered the PIN correctly and try again.\n')
            return

        access_token = resource_owner_key = credentials.get('oauth_token')[0]
        access_token_secret = credentials.get('oauth_token_secret')[0]

        screen_name = credentials.get('screen_name')[0]
    else:
        access_token = input("Enter your Access Token: ")
        access_token_secret = input("Enter your Access Token Secret: ")
        screen_name = "default"

    return {
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret,
        "access_token": access_token,
        "access_token_secret": access_token_secret,
        "bearer_token": bearer_token,
    }
