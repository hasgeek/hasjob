#!/usr/bin/env python

"""
Get Twitter access key and secret.
"""

import tweepy
import settings

auth = tweepy.OAuthHandler(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET)
auth_url = auth.get_authorization_url()
print 'Please authorize: ' + auth_url
verifier = raw_input('PIN: ').strip()
auth.get_access_token(verifier)
print "TWITTER_ACCESS_KEY = '%s'" % auth.access_token.key
print "TWITTER_ACCESS_SECRET = '%s'" % auth.access_token.secret
