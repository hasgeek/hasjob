# -*- coding: utf-8 -*-

from os import path
from datetime import datetime, timedelta
from urlparse import urljoin
import bleach
import requests
from pytz import utc, timezone
from urllib import quote, quote_plus
from sqlalchemy.exc import IntegrityError
from geoip2.errors import AddressNotFoundError
from flask import Markup, request, url_for, g, session
from flask.ext.rq import job

from baseframe import cache
from baseframe.signals import form_validation_error, form_validation_success

from .. import app, redis_store
from ..models import (agelimit, newlimit, db, JobCategory, JobPost, JobType, POSTSTATUS, BoardJobPost, Tag, JobPostTag,
    Campaign, CampaignView, EventSession, UserEvent, JobImpression)
from ..utils import scrubemail, redactemail


gif1x1 = 'R0lGODlhAQABAJAAAP8AAAAAACH5BAUQAAAALAAAAAABAAEAAAICBAEAOw=='.decode('base64')


@app.route('/_sniffle.gif')
def sniffle():
    return gif1x1, 200, {
        'Content-Type': 'image/gif',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
        }


@form_validation_success.connect
def event_form_validation_success(form):
    g.event_data['form_validation'] = 'ok'


@form_validation_error.connect
def event_form_validation_error(form):
    g.event_data['form_validation'] = 'error'
    g.event_data['form_errors'] = form.errors  # Dict of field: [errors]. Hopefully serializes into JSON


@app.before_request
def request_flags():
    if session.get('kiosk'):
        g.kiosk = True
    else:
        g.kiosk = False
    g.peopleflow_url = session.get('peopleflow')

    g.viewcounts = {}
    g.impressions = []
    if 'preview' in request.args:
        preview_campaign = Campaign.get(request.args['preview'])
    else:
        preview_campaign = None

    g.preview_campaign = preview_campaign
    g.campaign_views = []

    # Look up user's location
    if app.geoip:
        ipaddr = session.get('ipaddr')
        ipts = session.get('ipts')
        now = datetime.utcnow()
        if (not ipts
                or ipaddr != request.environ['REMOTE_ADDR']
                or 'geonameids' not in session
                or (ipts < now - timedelta(days=7))):
            # IP has changed or timed out or wasn't saved to the user's session. Look up location
            ipaddr = request.environ['REMOTE_ADDR']
            try:
                ipdata = app.geoip.city(ipaddr)
                geonameids = [item.geoname_id
                    for sublist in [[ipdata.city], ipdata.subdivisions, [ipdata.country], [ipdata.continent]]
                    for item in sublist
                    if item.geoname_id]
            except AddressNotFoundError:
                # Private IP range (127.0.0.1, etc). Should only happen in dev mode
                geonameids = []
            session['ipaddr'] = ipaddr
            session['geonameids'] = geonameids
            session['ipts'] = now
            g.user_geonameids = geonameids
        else:
            g.user_geonameids = session['geonameids']
    else:
        g.user_geonameids = []


@app.after_request
def record_views_and_events(response):
    # We're not sure why, but the g.* variables are sometimes missing in production.
    # Keep track so we can investigate
    missing_in_context = []
    if not hasattr(g, 'campaign_views'):
        g.campaign_views = []
        missing_in_context.append('campaign_views')
    if not hasattr(g, 'user'):
        g.user = None
        missing_in_context.append('user')
    if not hasattr(g, 'anon_user'):
        g.anon_user = None
        missing_in_context.append('anon_user')
    if not hasattr(g, 'event_data'):
        g.event_data = {}
        missing_in_context.append('event_data')
    if not hasattr(g, 'user_geonameids'):
        g.user_geonameids = {}
        missing_in_context.append('user_geonameids')
    if not hasattr(g, 'impressions'):
        g.impressions = []
        missing_in_context.append('impressions')

    if missing_in_context:
        g.event_data['missing_in_context'] = missing_in_context

    # Now process the response

    if response.status_code in (301, 302, 303, 307, 308):
        g.event_data['location'] = response.headers.get('Location')

    if g.campaign_views:
        g.event_data['campaign_views'] = [c.id for c in g.campaign_views]

    if g.user_geonameids:
        g.event_data['user_geonameids'] = g.user_geonameids

    if g.impressions:
        g.event_data['impressions'] = g.impressions

    if g.user:
        for campaign in g.campaign_views:
            if not CampaignView.exists(campaign, g.user):
                try:
                    db.session.add(CampaignView(campaign=campaign, user=g.user))
                    db.session.commit()
                except IntegrityError:  # Race condition from parallel requests
                    db.session.rollback()

    if g.user or g.anon_user:
        es = EventSession.get_session(user=g.user, anon_user=g.anon_user)
        es.events.append(UserEvent(status_code=response.status_code, data=g.event_data or None))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

        if g.impressions:
            save_impressions.delay(es.id, g.impressions)

    return response


def cache_viewcounts(posts):
    redis_pipe = redis_store.connection.pipeline()
    viewcounts_keys = [p.viewcounts_key for p in posts]
    for key in viewcounts_keys:
        redis_pipe.hgetall(key)
    viewcounts_values = redis_pipe.execute()
    g.viewcounts = dict(zip(viewcounts_keys, viewcounts_values))


def getposts(basequery=None, pinned=False, showall=False, statuses=None):
    if not statuses:
        statuses = POSTSTATUS.LISTED

    if basequery is None:
        basequery = JobPost.query

    query = basequery.filter(JobPost.status.in_(statuses)).options(*JobPost._defercols)

    if g.board:
        query = query.join(JobPost.postboards).filter(BoardJobPost.board == g.board)

    if showall:
        query = query.filter(JobPost.datetime > datetime.utcnow() - agelimit)
    else:
        if pinned:
            if g.board:
                query = query.filter(
                    db.or_(
                        db.and_(BoardJobPost.pinned == True, JobPost.datetime > datetime.utcnow() - agelimit),
                        db.and_(BoardJobPost.pinned == False, JobPost.datetime > datetime.utcnow() - newlimit)))  # NOQA
            else:
                query = query.filter(
                    db.or_(
                        db.and_(JobPost.pinned == True, JobPost.datetime > datetime.utcnow() - agelimit),
                        db.and_(JobPost.pinned == False, JobPost.datetime > datetime.utcnow() - newlimit)))  # NOQA
        else:
            query = query.filter(JobPost.datetime > datetime.utcnow() - newlimit)

    if pinned:
        if g.board:
            query = query.order_by(db.desc(BoardJobPost.pinned))
        else:
            query = query.order_by(db.desc(JobPost.pinned))

    return query.order_by(db.desc(JobPost.datetime))


def getallposts(order_by=None, desc=False, start=None, limit=None):
    if order_by is None:
        order_by = JobPost.datetime
    filt = JobPost.query.filter(JobPost.status.in_(POSTSTATUS.LISTED))
    count = filt.count()
    if desc:
        filt = filt.order_by(db.desc(order_by))
    else:
        filt = filt.order_by(order_by)
    if start is not None:
        filt = filt.offset(start)
    if limit is not None:
        filt = filt.limit(limit)
    return count, filt


def gettags(alltime=False):
    query = db.session.query(Tag.name.label('name'), Tag.title.label('title'), Tag.public.label('public'),
        db.func.count(Tag.id).label('count')).join(JobPostTag).join(JobPost).filter(
        JobPost.status.in_(POSTSTATUS.LISTED)).filter(Tag.public == True
        ).group_by(Tag.id).order_by('count desc')  # NOQA
    if not alltime:
        query = query.filter(JobPost.datetime > datetime.utcnow() - agelimit)
    if g.board:
        query = query.join(JobPost.postboards).filter(BoardJobPost.board == g.board)
    return query.all()


@job('hasjob')
def save_impressions(sessionid, impressions):
    """
    Save impressions against each job and session.
    """
    with app.test_request_context():
        for pinned, postid in impressions:
            ji = JobImpression.query.get((postid, sessionid))
            new_impression = False
            if ji is None:
                ji = JobImpression(jobpost_id=postid, event_session_id=sessionid, pinned=False)
                db.session.add(ji)
                new_impression = True
            # Never set pinned=False on an existing JobImpression instance. The pinned status
            # could change during a session. We are only interested in knowing if it was
            # rendered as pinned at least once during a session.
            if pinned:
                ji.pinned = True
            # We commit once per impresssion (typically 32+ impressions per request)
            # This is inefficient, but is the only way to handle integrity errors per item
            # from race conditions in the absence of a database-provided UPSERT. This
            # is why this function runs as a background job instead of in-process.
            try:
                db.session.commit()

                # Replicate post.viewcounts's query here because we don't want to load the post from db just to
                # access a class instance method
                if new_impression:
                    redis_store.hset('hasjob/viewcounts/%d' % postid, 'impressions',
                        db.session.query(db.func.count(db.func.distinct(EventSession.user_id))).filter(
                            EventSession.user_id != None).join(JobImpression).filter(
                            JobImpression.jobpost_id == postid).first()[0])  # NOQA
            except IntegrityError:  # Parallel request, skip this and move on
                db.session.rollback()


@cache.memoize(timeout=86400)
def location_geodata(location):
    if 'HASCORE_SERVER' in app.config:
        url = urljoin(app.config['HASCORE_SERVER'], '/1/geo/get_by_name')
        response = requests.get(url, params={'name': location}).json()
        if response.get('status') == 'ok':
            return response.get('result', {})
    return {}


@app.template_filter('urlfor')
def url_from_ob(ob):
    if isinstance(ob, JobPost):
        return ob.url_for()
    elif isinstance(ob, JobType):
        return url_for('browse_by_type', name=ob.name)
    elif isinstance(ob, JobCategory):
        return url_for('browse_by_category', name=ob.name)


@app.template_filter('shortdate')
def shortdate(date):
    tz = timezone(app.config['TIMEZONE'])
    return utc.localize(date).astimezone(tz).strftime('%b %e')


@app.template_filter('longdate')
def longdate(date):
    tz = timezone(app.config['TIMEZONE'])
    return utc.localize(date).astimezone(tz).strftime('%B %e, %Y')


@app.template_filter('cleanurl')
def cleanurl(url):
    if url.startswith('http://'):
        url = url[7:]
    elif url.startswith('https://'):
        url = url[8:]
    if url.endswith('/') and url.count('/') == 1:
        # Remove trailing slash if applied to end of domain name
        # but leave it in if it's a path
        url = url[:-1]
    return url


@app.template_filter('urlquote')
def urlquote(data):
    if isinstance(data, unicode):
        return quote(data.encode('utf-8'))
    else:
        return quote(data)


@app.template_filter('urlquoteplus')
def urlquoteplus(data):
    if isinstance(data, unicode):
        return quote_plus(data.encode('utf-8'))
    else:
        return quote_plus(data)


@app.template_filter('scrubemail')
def scrubemail_filter(data, css_junk=''):
    return Markup(scrubemail(unicode(bleach.linkify(bleach.clean(data))), rot13=True, css_junk=css_junk))


@app.template_filter('hideemail')
def hideemail_filter(data, message='[redacted]'):
    return redactemail(data, message)


@app.template_filter('usessl')
def usessl(url):
    """
    Convert a URL to https:// if SSL is enabled in site config
    """
    if not app.config.get('USE_SSL'):
        return url
    if url.startswith('//'):  # //www.example.com/path
        return 'https:' + url
    if url.startswith('/'):  # /path
        url = path.join(request.url_root, url[1:])
    if url.startswith('http:'):  # http://www.example.com
        url = 'https:' + url[5:]
    return url
