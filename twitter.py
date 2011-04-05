from tweepy import OAuthHandler, API
import urllib2
import json
from app import app

def tweet(title, url):
    auth = OAuthHandler(app.config['CONSUMER_KEY'], app.config['CONSUMER_SECRET'])
    auth.set_access_token(app.config['ACCESS_KEY'], app.config['ACCESS_SECRET'])
    api = API(auth)
    if len(title) > 120:
        text = title[:117] + '...'
    else:
        text = title[:117]
    text = text + ' ' + shorten(url)
    api.update_status(text)

def shorten(url):
    req = urllib2.Request("https://www.googleapis.com/urlshortener/v1/url, 
        headers = {"Content-Type": "application/json",},
        data = json.dumps({'longUrl' : url}))
    request_result = urllib2.urlopen(req)
    result = request_result.read()
    result_json = json.loads(result)
    return result_json['id']
