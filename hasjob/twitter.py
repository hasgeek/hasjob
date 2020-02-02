# -*- coding: utf-8 -*-

from tweepy import OAuthHandler, API
import urllib.request, urllib.error, urllib.parse
import json
import re
from hasjob import app, rq


@rq.job('hasjob')
def tweet(title, url, location=None, parsed_location=None, username=None):
    auth = OAuthHandler(app.config['TWITTER_CONSUMER_KEY'], app.config['TWITTER_CONSUMER_SECRET'])
    auth.set_access_token(app.config['TWITTER_ACCESS_KEY'], app.config['TWITTER_ACCESS_SECRET'])
    api = API(auth)
    urllength = 23  # Current Twitter standard for HTTPS (as of Oct 2014)
    maxlength = 140 - urllength - 1  # == 116
    if username:
        maxlength -= len(username) + 2
    locationtag = ''
    if parsed_location:
        locationtags = []
        for token in parsed_location.get('tokens', []):
            if 'geoname' in token and 'token' in token:
                locname = token['token'].strip()
                if locname:
                    locationtags.append('#' + locname.title().replace(' ', ''))
        locationtag = ' '.join(locationtags)
        if locationtag:
            maxlength -= len(locationtag) + 1
    if not locationtag and location:
        # Make a hashtag from the first word in the location. This catches
        # locations like 'Anywhere' which have no geonameid but are still valid
        locationtag = '#' + re.split(r'\W+', location)[0]
        maxlength -= len(locationtag) + 1

    if len(title) > maxlength:
        text = title[:maxlength - 1] + '…'
    else:
        text = title[:maxlength]
    text = text + ' ' + url  # Don't shorten URLs, now that there's t.co
    if locationtag:
        text = text + ' ' + locationtag
    if username:
        text = text + ' @' + username
    api.update_status(text)


# TODO: Delete this function
def shorten(url):
    if app.config['BITLY_KEY']:
        b = bitlyapi.BitLy(app.config['BITLY_USER'], app.config['BITLY_KEY'])
        res = b.shorten(longUrl=url)
        return res['url']
    else:
        req = urllib2.Request("https://www.googleapis.com/urlshortener/v1/url",
            headers={"Content-Type": "application/json"},
            data=json.dumps({'longUrl': url}))
        request_result = urllib2.urlopen(req)
        result = request_result.read()
        result_json = json.loads(result)
        return result_json['id']
