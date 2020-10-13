import re

from tweepy import API, OAuthHandler

from . import app, rq


@rq.job('hasjob')
def tweet(title, url, location=None, parsed_location=None, username=None):
    auth = OAuthHandler(
        app.config['TWITTER_CONSUMER_KEY'], app.config['TWITTER_CONSUMER_SECRET']
    )
    auth.set_access_token(
        app.config['TWITTER_ACCESS_KEY'], app.config['TWITTER_ACCESS_SECRET']
    )
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
        text = title[: maxlength - 1] + '…'
    else:
        text = title[:maxlength]
    text = text + ' ' + url  # Don't shorten URLs, now that there's t.co
    if locationtag:
        text = text + ' ' + locationtag
    if username:
        text = text + ' @' + username
    api.update_status(text)
