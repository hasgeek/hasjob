import re

from atproto import (
    Client as BlueskyClient,
    Session as BlueskySession,
    SessionEvent as BlueskySessionEvent,
    client_utils as atproto_client_utils,
)
from atproto.exceptions import AtProtocolError
from tweepy import API, OAuthHandler

from baseframe import cache

from . import app, rq


@rq.job('hasjob')
def tweet(
    title: str,
    url: str,
    location: str | None = None,
    parsed_location=None,
    username: str | None = None,
) -> None:
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
                    locationtags.append('#' + locname.title().replace(' ', '_'))
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


def get_bluesky_session() -> str | None:
    session_string = cache.get('hasjob:bluesky_session')
    if not isinstance(session_string, str) or not session_string:
        return None
    return session_string


def save_bluesky_session(session_string: str) -> None:
    cache.set('hasjob:bluesky_session', session_string)  # No timeout


def on_bluesky_session_change(
    event: BlueskySessionEvent, session: BlueskySession
) -> None:
    if event in (BlueskySessionEvent.CREATE, BlueskySessionEvent.REFRESH):
        save_bluesky_session(session.export())


def init_bluesky_client() -> BlueskyClient:
    client = BlueskyClient()  # Only support the default `bsky.social` domain for now
    client.on_session_change(on_bluesky_session_change)

    session_string = get_bluesky_session()
    if session_string:
        try:
            client.login(session_string=session_string)
            return client
        except (ValueError, AtProtocolError):  # Invalid session string
            pass
    # Fallback to a fresh login
    client.login(app.config['BLUESKY_USERNAME'], app.config['BLUESKY_PASSWORD'])
    return client


@rq.job('hasjob')
def bluesky_post(
    title: str,
    url: str,
    location: str | None = None,
    parsed_location=None,
    employer: str | None = None,
    employer_url: str | None = None,
):
    locationtags = []
    if parsed_location:
        for token in parsed_location.get('tokens', []):
            if 'geoname' in token and 'token' in token:
                locname = token['token'].strip()
                if locname:
                    locationtags.append(locname.title().replace(' ', '_'))
    if not locationtags and location:
        # Make a hashtag from the first word in the location. This catches
        # locations like 'Anywhere' which have no geonameid but are still valid
        locationtag = re.split(r'\W+', location)[0]
        locationtags.append(locationtag)

    maxlength = 300  # Bluesky allows 300 characters
    if employer:
        maxlength -= len(employer) + 2  # Minus employer name and prefix
    if locationtags:
        # Subtract length of all tags, plus length of visible `#`s  and one space
        maxlength -= len(' '.join(locationtags)) + len(locationtags) + 1

    content = atproto_client_utils.TextBuilder()
    content.link(title[: maxlength - 1] + '…' if len(title) > maxlength else title, url)
    if employer:
        content.text(' –')
        if employer_url:
            content.link(employer, employer_url)
        else:
            content.text(employer)
    if locationtags:
        for loc in locationtags:
            content.text(' ')
            content.tag('#' + loc, loc)
    client = init_bluesky_client()
    client.send_post(content)
