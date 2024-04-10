#!/usr/bin/env python

"""
Get Twitter access key and secret.
"""

import tweepy

from hasjob import app

auth = tweepy.OAuthHandler(
    app.config['TWITTER_CONSUMER_KEY'], app.config['TWITTER_CONSUMER_SECRET']
)
auth_url = auth.get_authorization_url()
print("Please authorize: " + auth_url)  # noqa: T201
verifier = input('PIN: ').strip()
auth.get_access_token(verifier)
print("TWITTER_ACCESS_KEY = '%s'" % auth.access_token.key)  # noqa: T201
print("TWITTER_ACCESS_SECRET = '%s'" % auth.access_token.secret)  # noqa: T201
