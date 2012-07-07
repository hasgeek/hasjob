from tweepy import OAuthHandler, API
import bitlyapi
import urllib2
import json
import re
from app import app

def tweet(title, url, location=None):
    auth = OAuthHandler(app.config['TWITTER_CONSUMER_KEY'], app.config['TWITTER_CONSUMER_SECRET'])
    auth.set_access_token(app.config['TWITTER_ACCESS_KEY'], app.config['TWITTER_ACCESS_SECRET'])
    api = API(auth)
    maxlength = 120 # 120 chars plus URL = 140 max for Twitter
    if location:
        # Make a hashtag from the first word in the location
        locationtag = '#'+re.split('\W+', location)[0]
        maxlength -= len(locationtag)+1
    else:
        locationtag = None
    if len(title) > maxlength:
        text = title[:maxlength-3] + '...'
    else:
        text = title[:maxlength]
    text = text + ' ' + shorten(url)
    if locationtag:
        text = text + ' ' + locationtag
    api.update_status(text)


def shorten(url):
    if app.config['BITLY_KEY']:
        b = bitlyapi.BitLy(app.config['BITLY_USER'], app.config['BITLY_KEY'])
        res = b.shorten(longUrl=url)
        return res['url']
    else:
        req = urllib2.Request("https://www.googleapis.com/urlshortener/v1/url",
            headers = {"Content-Type": "application/json",},
            data = json.dumps({'longUrl' : url}))
        request_result = urllib2.urlopen(req)
        result = request_result.read()
        result_json = json.loads(result)
        return result_json['id']
