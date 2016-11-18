# -*- coding: utf-8 -*-

from os import path
from datetime import datetime, timedelta
from urlparse import urljoin
from urllib import quote, quote_plus
import hashlib
import bleach
import requests
from pytz import utc, timezone
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from geoip2.errors import AddressNotFoundError
from flask import Markup, request, g, session
from flask.ext.rq import job
from flask.ext.lastuser import signal_user_looked_up
from coaster.utils import uuid1mc
from coaster.sqlalchemy import failsafe_add
from baseframe import _, cache
from baseframe.signals import form_validation_error, form_validation_success

from .. import app, redis_store
from ..models import (agelimit, newlimit, db, JobCategory, JobPost, JobType, POSTSTATUS, BoardJobPost, Tag, JobPostTag,
    Campaign, CampaignView, CampaignAnonView, EventSessionBase, EventSession, UserEventBase, UserEvent, JobImpression,
    JobViewSession, AnonUser, campaign_event_session_table, JobLocation, PAY_TYPE)
from ..utils import scrubemail, redactemail, cointoss


gif1x1 = 'R0lGODlhAQABAJAAAP8AAAAAACH5BAUQAAAALAAAAAABAAEAAAICBAEAOw=='.decode('base64')


@app.route('/_sniffle.gif')
def sniffle():
    return gif1x1, 200, {
        'Content-Type': 'image/gif',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }


def index_is_paginated():
    return request.method == 'POST' and 'startdate' in request.values


@form_validation_success.connect
def event_form_validation_success(form):
    g.event_data['form_validation'] = 'ok'


@form_validation_error.connect
def event_form_validation_error(form):
    g.event_data['form_validation'] = 'error'
    if hasattr(form, 'errors_with_data'):
        g.event_data['form_errors'] = form.errors_with_data()
    else:
        g.event_data['form_errors'] = form.errors  # Dict of field: [errors]


@signal_user_looked_up.connect
def load_user_data(user):
    """
    All pre-request utilities, run after g.user becomes available.

    Part 1: Load anon user:

    1. If there's g.user and session['anon_user'], it loads that anon_user and tags with user=g.user, then removes anon
    2. If there's no g.user and no session['anon_user'], sets session['anon_user'] = 'test'
    3. If there's no g.user and there is session['anon_user'] = 'test', creates a new anon user, then saves to cookie
    4. If there's no g.user and there is session['anon_user'] != 'test', loads g.anon_user

    Part 2: Are we in kiosk mode? Is there a preview campaign?
    Part 3: Look up user's IP address location as geonameids for use in targeting.
    """
    g.anon_user = None  # Could change below
    g.event_data = {}   # Views can add data to the current pageview event
    g.esession = None
    g.viewcounts = {}
    g.impressions = session.pop('impressions', {})  # Retrieve from cookie session if present there
    g.campaign_views = []
    g.jobpost_viewed = None, None
    g.bgroup = None
    now = datetime.utcnow()

    if request.endpoint not in ('static', 'baseframe.static'):
        # Loading an anon user only if we're not rendering static resources
        if user:
            if 'au' in session and session['au'] is not None and not unicode(session['au']).startswith(u'test'):
                anon_user = AnonUser.query.get(session['au'])
                if anon_user:
                    anon_user.user = user
            session.pop('au', None)
        else:
            if not session.get('au'):
                session['au'] = u'test-' + unicode(uuid1mc())
                g.esession = EventSessionBase.new_from_request(request)
                g.event_data['anon_cookie_test'] = session['au']
            elif session['au'] == 'test':  # Legacy test cookie, original request now lost
                g.anon_user = AnonUser()
                db.session.add(g.anon_user)
                g.esession = EventSession.new_from_request(request)
                g.esession.anon_user = g.anon_user
                db.session.add(g.esession)
                # We'll update session['au'] below after database commit
            elif unicode(session['au']).startswith('test-'):  # Newer redis-backed test cookie
                # This client sent us back our test cookie, so set a real value now
                g.anon_user = AnonUser()
                db.session.add(g.anon_user)
                g.esession = EventSession.new_from_request(request)
                g.esession.anon_user = g.anon_user
                db.session.add(g.esession)
                g.esession.load_from_cache(session['au'], UserEvent)
                # We'll update session['au'] below after database commit
            else:
                anon_user = AnonUser.query.get(session['au'])
                if not anon_user:
                    # XXX: We got a fake value? This shouldn't happen
                    g.event_data['anon_cookie_test'] = session['au']
                    session['au'] = u'test-' + unicode(uuid1mc())  # Try again
                    g.esession = EventSessionBase.new_from_request(request)
                else:
                    g.anon_user = anon_user

    # Prepare event session if it's not already present
    if g.user or g.anon_user and not g.esession:
        g.esession = EventSession.get_session(uuid=session.get('es'), user=g.user, anon_user=g.anon_user)
    if g.esession:
        session['es'] = g.esession.uuid

    # Don't commit here. It flushes SQLAlchemy's session cache and forces
    # fresh database hits. Let after_request commit. (Commented out 30-03-2016)
    # db.session.commit()
    g.db_commit_needed = True

    if g.anon_user:
        session['au'] = g.anon_user.id
        session.permanent = True
        if 'impressions' in session:
            # Run this in the foreground since we need this later in the request for A/B display consistency.
            # This is most likely being called from the UI-non-blocking sniffle.gif anyway.
            save_impressions(g.esession.id, session.pop('impressions').values(), now)

    # We have a user, now look up everything else

    if session.get('kiosk'):
        g.kiosk = True
    else:
        g.kiosk = False
    g.peopleflow_url = session.get('peopleflow')

    if 'preview' in request.args:
        preview_campaign = Campaign.get(request.args['preview'])
    else:
        preview_campaign = None

    g.preview_campaign = preview_campaign

    # Look up user's location
    if app.geoip:
        ipaddr = session.get('ipaddr')
        ipts = session.get('ipts')
        now = datetime.utcnow()
        if (not ipts or
                ipaddr != request.environ['REMOTE_ADDR'] or
                'geonameids' not in session or
                (ipts < now - timedelta(days=7))):
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
    if hasattr(g, 'db_commit_needed') and g.db_commit_needed:
        db.session.commit()

    # We had a few error reports with g.* variables missing in this function, so now
    # we look again and make note if something is missing. We haven't encountered
    # this problem ever since after several days of logging, but this bit of code
    # remains just in case something turns up in future.
    missing_in_context = []
    now = datetime.utcnow()
    if not hasattr(g, 'esession'):
        g.esession = None
        missing_in_context.append('esession')
    if not hasattr(g, 'response_code'):
        g.response_code = None
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
        g.impressions = {}
        missing_in_context.append('impressions')
    if not hasattr(g, 'jobpost_viewed'):
        g.jobpost_viewed = None, None
        missing_in_context.append('jobpost_viewed')

    if missing_in_context:
        g.event_data['missing_in_context'] = missing_in_context

    # Now log whatever needs to be logged
    if response.status_code in (301, 302, 303, 307, 308):
        g.event_data['location'] = response.headers.get('Location')

    # TODO: Consider moving this to a background job
    if g.campaign_views:
        g.event_data['campaign_views'] = [c.id for c in g.campaign_views]
        if g.esession and g.esession.persistent:
            for campaign in g.campaign_views:
                if g.esession not in campaign.session_views:
                    campaign.session_views.append(g.esession)
            try:
                db.session.commit()
            except IntegrityError:  # Race condition from parallel requests
                db.session.rollback()

    if g.user_geonameids:
        g.event_data['user_geonameids'] = g.user_geonameids

    if g.impressions:
        g.event_data['impressions'] = g.impressions.values()

    if g.user:
        for campaign in g.campaign_views:
            if not CampaignView.exists(campaign, g.user):
                db.session.begin_nested()
                try:
                    db.session.add(CampaignView(campaign=campaign, user=g.user))
                    db.session.commit()
                except IntegrityError:  # Race condition from parallel requests
                    db.session.rollback()
            db.session.commit()
            campaign_view_count_update.delay(campaign_id=campaign.id, user_id=g.user.id)
    elif g.anon_user:
        for campaign in g.campaign_views:
            if not CampaignAnonView.exists(campaign, g.anon_user):
                db.session.begin_nested()
                try:
                    db.session.add(CampaignAnonView(campaign=campaign, anon_user=g.anon_user))
                    db.session.commit()
                except IntegrityError:  # Race condition from parallel requests
                    db.session.rollback()
            db.session.commit()
            campaign_view_count_update.delay(campaign_id=campaign.id, anon_user_id=g.anon_user.id)

    if g.esession:  # Will be None for anon static requests
        if g.user or g.anon_user:
            ue = UserEvent.new_from_request(request)
        else:
            ue = UserEventBase.new_from_request(request)
        ue.status_code = response.status_code
        ue.data = g.event_data or None
        g.esession.events.append(ue)

        if g.esession.persistent:
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

            if g.impressions:
                save_impressions.delay(g.esession.id, g.impressions.values(), now)

            if g.jobpost_viewed != (None, None):
                save_jobview.delay(
                    viewed_time=now,
                    event_session_id=g.esession.id,
                    jobpost_id=g.jobpost_viewed[0],
                    bgroup=g.jobpost_viewed[1])
        else:
            g.esession.save_to_cache(session['au'])
            if g.impressions:
                # Save impressions to user's cookie session to write to db later
                session['impressions'] = g.impressions

    return response


def session_jobpost_ab():
    """
    Returns the user's B-group assignment (NA, True, False) for all jobs shown to the user
    in the current event session (impressions or views) as a dictionary of {id: bgroup}
    """
    if not g.esession.persistent:
        return {key: value[2] for key, value in session.get('impressions', {}).items()}
    result = {ji.jobpost_id: ji.bgroup for ji in JobImpression.query.filter_by(event_session=g.esession)}
    result.update({jvs.jobpost_id: jvs.bgroup for jvs in JobViewSession.query.filter_by(event_session=g.esession)})
    return result


def bgroup(jobpost_ab, post):
    return (jobpost_ab.get(post.id) or cointoss()) if post.headlineb else None


def cache_viewcounts(posts):
    redis_pipe = redis_store.pipeline()
    viewcounts_keys = [p.viewcounts_key for p in posts]
    for key in viewcounts_keys:
        redis_pipe.hgetall(key)
    viewcounts_values = redis_pipe.execute()
    g.viewcounts = dict(zip(viewcounts_keys, viewcounts_values))


def getposts(basequery=None, pinned=False, showall=False, statuses=None, ageless=False, limit=2000, order=True):
    if ageless:
        pinned = False  # No pinning when browsing archives
    if not statuses:
        statuses = POSTSTATUS.LISTED

    if basequery is None:
        basequery = JobPost.query

    query = basequery.filter(JobPost.status.in_(statuses)).options(*JobPost._defercols).options(db.joinedload('domain'))

    now = datetime.utcnow()

    if g.board:
        # Load into cache
        g.board_jobs = {r.jobpost_id: r for r in
            BoardJobPost.query.join(BoardJobPost.jobpost).filter(
                BoardJobPost.board == g.board, JobPost.datetime > now - agelimit).options(
                    db.load_only('jobpost_id', 'pinned')).all()
        }
        query = query.join(JobPost.postboards).filter(BoardJobPost.board == g.board)

    if not ageless:
        if showall:
            query = query.filter(JobPost.datetime > datetime.utcnow() - agelimit)
        else:
            if pinned:
                if g.board:
                    query = query.filter(
                        db.or_(
                            db.and_(BoardJobPost.pinned == True, JobPost.datetime > now - agelimit),
                            db.and_(BoardJobPost.pinned == False, JobPost.datetime > now - newlimit)))  # NOQA
                else:
                    query = query.filter(
                        db.or_(
                            db.and_(JobPost.pinned == True, JobPost.datetime > now - agelimit),
                            db.and_(JobPost.pinned == False, JobPost.datetime > now - newlimit)))  # NOQA
            else:
                query = query.filter(JobPost.datetime > datetime.utcnow() - newlimit)

    if pinned:
        if g.board:
            query = query.order_by(db.desc(BoardJobPost.pinned))
        else:
            query = query.order_by(db.desc(JobPost.pinned))

    if not order and not limit:
        return query
    return query.order_by(db.desc(JobPost.datetime)).limit(limit)


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
        ).group_by(Tag.id).order_by(db.text('count DESC'))  # NOQA
    if not alltime:
        query = query.filter(JobPost.datetime > datetime.utcnow() - agelimit)
    if g.board:
        query = query.join(JobPost.postboards).filter(BoardJobPost.board == g.board)
    return query.all()


pay_graph_buckets = {
    'INR': (
        range(0, 200000, 25000) +
        range(200000, 2000000, 50000) +
        range(2000000, 10000000, 100000) +
        range(10000000, 100000000, 1000000) +
        [100000000]),
    'USD': (
        range(0, 200000, 5000) +
        range(200000, 1000000, 50000) +
        range(1000000, 10000000, 100000) +
        [10000000])
    }
pay_graph_buckets['EUR'] = pay_graph_buckets['USD']
pay_graph_buckets['SGD'] = pay_graph_buckets['USD']
pay_graph_buckets['GBP'] = pay_graph_buckets['USD']


def make_pay_graph(currency, posts, rmin=None, rmax=None, minposts=5):
    if currency not in pay_graph_buckets:
        return  # No graph if we don't know about this currency
    pay_data = [(post.pay_cash_min, post.pay_cash_max)
        for post in posts if post.pay_type == PAY_TYPE.RECURRING]
    if len(pay_data) < minposts:
        return  # No graph if less than the minimum required match
    rmin = max(rmin or 0, min([d[0] for d in pay_data]))
    rmax = min(rmax or 10000000, max([d[1] for d in pay_data]))
    rbuckets = [bucket for bucket in pay_graph_buckets[currency] if (bucket >= rmin and bucket <= rmax)]
    buckets = {bucket: 0 for bucket in rbuckets}
    for pmin, pmax in pay_data:
        for bucket in rbuckets:
            if bucket >= pmin and bucket <= pmax:
                buckets[bucket] += 1
    data = sorted(buckets.items())
    if len(data) in (0, 1):
        return

    xlen = len(data)
    xpoints = 5
    xaxis = [data[0][0]] + [data[c * xlen / xpoints][0] for c in range(1, xpoints)] + [data[-1][0]]

    # pruned_data = [data[0]] + [
    #     data[c] for c in range(1, len(data)) if not (data[c][1] == data[c - 1][1] and data[c][1] == data[c + 1][1])
    #     ] + [data[-1]]
    return {'currency': currency, 'data': data, 'xaxis': xaxis}


@job('hasjob')
def save_jobview(event_session_id, jobpost_id, bgroup, viewed_time):
    """
    Save a jobpost view as a background job to ensure this doesn't fire *before* the
    associated save_impressions job. Queue order is important for the cointoss flag
    in A/B testing.
    """
    jvs = JobViewSession.get_by_ids(event_session_id=event_session_id, jobpost_id=jobpost_id)
    if jvs is None:
        jvs = JobViewSession(event_session_id=event_session_id, jobpost_id=jobpost_id, datetime=viewed_time,
            bgroup=bgroup)
        jvs = failsafe_add(db.session, jvs, event_session_id=event_session_id, jobpost_id=jobpost_id)

        # Since this is a new view, is there an existing job impression in the same session
        # which has a bgroup defined? If yes, this view has an associated coin toss.
        ji = JobImpression.get_by_ids(jobpost_id=jobpost_id, event_session_id=event_session_id)
        if ji:
            jvs.cointoss = True
            if ji.bgroup != jvs.bgroup and jvs.bgroup is not None:
                jvs.crosstoss = True
        else:
            jvs.cointoss = False

        db.session.commit()


def mark_dirty_impression_counts(jobpost_ids):
    redis_store.sadd('hasjob/dirty_impression_counts', *jobpost_ids)


def remove_dirty_impression_counts(jobpost_ids):
    redis_store.srem('hasjob/dirty_impression_counts', *jobpost_ids)


def list_dirty_impression_counts():
    return [int(x) for x in redis_store.smembers('hasjob/dirty_impression_counts')]


def update_impression_counts(jobpost_ids):
    for jobpost_id in jobpost_ids:
        # Replicate post.viewcounts's query here because we don't want to load the post from db just to
        # access a class instance method
        redis_store.hset('hasjob/viewcounts/%d' % jobpost_id, 'impressions',
            db.session.query(db.func.count(db.func.distinct(EventSession.user_id)).label('count')
            ).join(JobImpression).filter(JobImpression.jobpost_id == jobpost_id).first().count)


def update_dirty_impression_counts():
    jobpost_ids = list_dirty_impression_counts()
    update_impression_counts(jobpost_ids)
    remove_dirty_impression_counts(jobpost_ids)


@job('hasjob')
def save_impressions(session_id, impressions, viewed_time):
    """
    Save impressions against each job and session.
    """
    with app.test_request_context():
        for pinned, postid, bgroup in impressions:
            ji = JobImpression.get_by_ids(jobpost_id=postid, event_session_id=session_id)
            if ji is None:
                ji = JobImpression(jobpost_id=postid, event_session_id=session_id, datetime=viewed_time, pinned=False, bgroup=bgroup)
                db.session.add(ji)
            # Never set pinned=False on an existing JobImpression instance. The pinned status
            # could change during a session. We are only interested in knowing if it was
            # rendered as pinned at least once during a session.
            if pinned:
                ji.pinned = True
            if bgroup is not None:
                ji.bgroup = bgroup
            # We commit once per impression (typically 32+ impressions per request)
            # This is inefficient, but is the only way to handle integrity errors per item
            # from race conditions in the absence of a database-provided UPSERT. This
            # is why this function runs as a background job instead of in-process.
            try:
                db.session.commit()
            except IntegrityError:  # Parallel request, skip this and move on
                db.session.rollback()
        mark_dirty_impression_counts([postid for pinned, postid, bgroup in impressions])


@job('hasjob')
def campaign_view_count_update(campaign_id, user_id=None, anon_user_id=None):
    if not user_id and not anon_user_id:
        return
    if user_id:
        cv = CampaignView.get_by_ids(campaign_id=campaign_id, user_id=user_id)
        if not cv:
            # Could be missing because of begin_nested introduced in 36070d9e without outer commit
            cv = CampaignView(campaign_id=campaign_id, user_id=user_id)
            db.session.add(cv)
    elif anon_user_id:
        cv = CampaignAnonView.get_by_ids(campaign_id=campaign_id, anon_user_id=anon_user_id)
        if not cv:
            # Could be missing because of begin_nested introduced in 36070d9e without outer commit
            cv = CampaignAnonView(campaign_id=campaign_id, anon_user_id=anon_user_id)
            db.session.add(cv)
    query = db.session.query(db.func.count(campaign_event_session_table.c.event_session_id)).filter(
        campaign_event_session_table.c.campaign_id == campaign_id).join(EventSession)

    # FIXME: Run this in a cron job and de-link from post-request processing
    # query = query.filter(
    #    db.or_(
    #        # Is this event session closed? Criteria: it's been half an hour or the session's explicitly closed
    #        EventSession.ended_at != None,
    #        EventSession.active_at < datetime.utcnow() - timedelta(minutes=30)))  # NOQA

    if user_id:
        query = query.filter(EventSession.user_id == user_id)
    else:
        query = query.filter(EventSession.anon_user_id == anon_user_id)

    cv.session_count = query.first()[0]
    db.session.commit()


@cache.memoize(timeout=86400)
def location_geodata(location):
    if 'HASCORE_SERVER' in app.config and location:
        if isinstance(location, (list, tuple)):
            url = urljoin(app.config['HASCORE_SERVER'], '/1/geo/get_by_names')
        else:
            url = urljoin(app.config['HASCORE_SERVER'], '/1/geo/get_by_name')
        response = requests.get(url, params={'name': location}).json()
        if response.get('status') == 'ok':
            result = response.get('result', {})
            if isinstance(result, (list, tuple)):
                result = {r['geonameid']: r for r in result}
            return result
    return {}


def jobpost_location_hierarchy(self):
    locations = []
    for loc in self.geonameids:
        locations.append(location_geodata(loc))  # Call one at a time for better cache performance
    parts = {
        'city': set(),
        'area': set(),
        'state': set(),
        'country': set(),
        'continent': set(),
        }
    for row in locations:
        if row and 'fcode' in row:
            if row['fcode'] in ('PPL', 'PPLA', ):
                parts['city'].add(row['use_title'])
            elif row['fcode'] in ('ADM2'):
                parts['area'].add(row['use_title'])
            elif row['fcode'] in ('ADM1'):
                parts['state'].add(row['use_title'])
            elif row['fcode'] == 'CONT':
                parts['continent'].add(row['use_title'])
            if 'country' in row and row['country']:
                parts['country'].add(row['country'])  # Use 2 letter ISO code, not name

    return {k: tuple(parts[k]) for k in parts}


JobPost.location_hierarchy = property(jobpost_location_hierarchy)


def use_timezone():
    if g and g.user:
        return g.user.tz
    else:
        return timezone(app.config['TIMEZONE'])


@app.template_filter('shortdate')
def shortdate(date):
    return utc.localize(date).astimezone(use_timezone()).strftime('%b %e')


@app.template_filter('longdate')
def longdate(date):
    return utc.localize(date).astimezone(use_timezone()).strftime('%B %e, %Y')


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


def filter_basequery(basequery, filters, exclude_list=[]):
    """
    - Accepts a query of type sqlalchemy.Query, and returns a modified query
    based on the keys in the `filters` object.
    - The keys accepted in the `filters` object are: `locations`, `anywhere`, `categories`, `types,
    `pay_min`, `pay_max`, `currency`, `equity` and `query`.
    - exclude_list is an array of keys that need to be ignored in the `filters` object
    """
    filter_by_location = filters.get('locations') and 'locations' not in exclude_list
    filter_by_anywhere = filters.get('anywhere') and 'anywhere' not in exclude_list
    if filter_by_location:
        job_location_jobpost_ids = db.session.query(JobLocation.jobpost_id).filter(JobLocation.geonameid.in_(filters['locations']))

    if filter_by_location and filter_by_anywhere:
        basequery = basequery.filter(or_(JobPost.id.in_(job_location_jobpost_ids), JobPost.remote_location == True))  # NOQA
    elif filter_by_location:
        basequery = basequery.filter(JobPost.id.in_(job_location_jobpost_ids))
    elif filter_by_anywhere:
        basequery = basequery.filter(JobPost.remote_location == True)  # NOQA

    if filters.get('categories') and 'categories' not in exclude_list:
        job_categoryids_query = db.session.query(JobCategory.id).filter(JobCategory.name.in_(filters['categories']))
        basequery = basequery.filter(JobPost.category_id.in_(job_categoryids_query))
    if filters.get('types') and 'types' not in exclude_list:
        job_typeids_query = db.session.query(JobType.id).filter(JobType.name.in_(filters['types']))
        basequery = basequery.filter(JobPost.type_id.in_(job_typeids_query))
    if filters.get('pay_min') and filters.get('pay_max') and 'pay_min' not in exclude_list:
        basequery = basequery.filter(JobPost.pay_cash_min < filters['pay_max'], JobPost.pay_cash_max >= filters['pay_min'])
    if filters.get('currency'):
        basequery = basequery.filter(JobPost.pay_currency == filters.get('currency'))
    if filters.get('equity') and 'equity' not in exclude_list:
        basequery = basequery.filter(JobPost.pay_equity_min != None)  # NOQA
    if filters.get('query') and 'query' not in exclude_list:
        basequery = basequery.filter(JobPost.search_vector.match(filters['query'], postgresql_regconfig='english'))

    return basequery


def filter_locations(board, filters):
    now = datetime.utcnow()
    basequery = db.session.query(JobLocation.geonameid, db.func.count(JobLocation.geonameid).label('count')
        ).join(JobPost).filter(JobPost.status.in_(POSTSTATUS.LISTED), JobPost.datetime > now - agelimit,
        JobLocation.primary == True).group_by(JobLocation.geonameid).order_by(db.text('count DESC'))  # NOQA
    if board:
        basequery = basequery.join(BoardJobPost).filter(BoardJobPost.board == board)

    geonameids = [jobpost_location.geonameid for jobpost_location in basequery]
    filtered_basequery = filter_basequery(basequery, filters, exclude_list=['locations', 'anywhere'])
    filtered_geonameids = [jobpost_location.geonameid for jobpost_location in filtered_basequery]
    remote_location_available = filtered_basequery.filter(JobPost.remote_location == True).count() > 0  # NOQA
    data = location_geodata(geonameids)
    return [{'name': 'anywhere', 'title': _("Anywhere"), 'available': remote_location_available}] + [{'name': data[geonameid]['name'], 'title': data[geonameid]['picker_title'],
            'available': False if not filtered_geonameids else geonameid in filtered_geonameids}
            for geonameid in geonameids]


def filter_types(basequery, board, filters):
    basequery = filter_basequery(basequery, filters, exclude_list=['types'])
    filtered_typeids = [post.type_id for post in basequery.options(db.load_only('type_id')).distinct('type_id').all()]

    def format_job_type(job_type):
        return {'name': job_type.name, 'title': job_type.title,
                'available': False if not filtered_typeids else job_type.id in filtered_typeids}
    if board:
        return [format_job_type(job_type)
                for job_type in board.types if not job_type.private]
    else:
        return [format_job_type(job_type)
                for job_type in JobType.query.filter_by(private=False, public=True).order_by('seq')]


def filter_categories(basequery, board, filters):
    basequery = filter_basequery(basequery, filters, exclude_list=['categories'])
    filtered_categoryids = [post.category_id for post in basequery.options(db.load_only('category_id')).distinct('category_id').all()]

    def format_job_category(job_category):
        return {'name': job_category.name, 'title': job_category.title,
        'available': False if not filtered_categoryids else job_category.id in filtered_categoryids}
    if board:
        return [format_job_category(job_category)
                for job_category in board.categories if not job_category.private]
    else:
        return [format_job_category(job_category)
                for job_category in JobCategory.query.filter_by(private=False, public=True).order_by('seq')]


@app.context_processor
def inject_filter_options():
    def get_job_filters():
        basequery = getposts(showall=True, order=False, limit=False)
        filters = g.get('event_data', {}).get('filters', {})
        cache_key = 'jobfilters/' + (g.board.name + '/' if g.board else '') + hashlib.sha1(repr(filters)).hexdigest()
        result = cache.get(cache_key)
        if not result:
            result = dict(job_location_filters=filter_locations(g.board, filters),
                job_type_filters=filter_types(basequery, board=g.board, filters=filters),
                job_category_filters=filter_categories(basequery, board=g.board, filters=filters))
            cache.set(cache_key, result, timeout=3600)
        return result

    return dict(job_filters=get_job_filters)
