# -*- coding: utf-8 -*-

from time import mktime
from datetime import datetime, timedelta
from uuid import UUID
from flask import request
from flask_lastuser.sqlalchemy import UserBase2
from sqlalchemy_utils.types import UUIDType
from coaster.utils import unicode_http_header, uuid1mc
from coaster.sqlalchemy import JsonDict
from baseframe import _, cache
from . import db, BaseMixin
from .. import redis_store

__all__ = ['User', 'UserActiveAt', 'AnonUser', 'EventSessionBase', 'EventSession', 'UserEventBase', 'UserEvent']


class User(UserBase2, db.Model):
    __tablename__ = 'user'

    resume = db.deferred(db.Column(JsonDict, nullable=False, default={}))
    blocked = db.Column(db.Boolean, nullable=False, default=False)


class UserActiveAt(db.Model):
    """
    Track when a user's session was re-verified with Lastuser. This column records the user's presence
    at five minute intervals (when the Redis cache of session verification expires). Since the average
    user is on the site for less than five minutes per session, there will typically be just one entry
    per user per active period.
    """
    __tablename__ = 'user_active_at'
    active_at = db.Column(db.DateTime, nullable=False, default=db.func.utcnow(), primary_key=True)
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=False, primary_key=True, index=True)
    user = db.relationship(User)
    board_id = db.Column(None, db.ForeignKey('board.id'), nullable=True, index=True)


class AnonUser(BaseMixin, db.Model):
    """
    An anonymous user. We know nothing about this person until they choose to login. If they do login,
    we still don't know if this is the same person or someone else at the computer, but we know there's
    a fairly high chance it's the same person. Activities by an anonymous user are not re-linked to a
    known user (except in certain conditions), but if the user does login, we track that so we can understand
    the conditions under which the login happened.
    """
    __tablename__ = 'anon_user'
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=True, index=True)
    user = db.relationship(User, backref=db.backref('anonusers', lazy='dynamic', order_by='AnonUser.id.desc()'))

    def __repr__(self):
        if self.user:
            return '<AnonUser %d: %s>' % (self.id, repr(self.user)[1:-1])
        else:
            return '<AnonUser %d>' % self.id

    @property
    def username(self):
        return None  # Don't return 'anon' or anything cute to avoid unique constraint issues elsewhere

    @property
    def fullname(self):
        return _("Anonymous user")

    name = username
    title = fullname


class EventSessionBase(object):
    persistent = False  # This won't be saved to db

    @classmethod
    def new_from_request(cls, request):
        instance = cls()
        instance.uuid = uuid1mc()  # Don't wait for database commit to generate this
        instance.created_at = datetime.utcnow()
        instance.referrer = unicode_http_header(request.referrer)[:2083] if request.referrer else None
        instance.utm_source = request.args.get('utm_source', u'')[:250] or None
        instance.utm_medium = request.args.get('utm_medium', u'')[:250] or None
        instance.utm_term = request.args.get('utm_term', u'')[:250] or None
        instance.utm_content = request.args.get('utm_content', u'')[:250] or None
        instance.utm_id = request.args.get('utm_id', u'')[:250] or None
        instance.utm_campaign = request.args.get('utm_campaign', u'')[:250] or None
        instance.gclid = request.args.get('gclid', u'')[:250] or None
        instance.active_at = datetime.utcnow()
        instance.events = []
        return instance

    def as_dict(self):
        return {
            'referrer': self.referrer,
            'utm_source': self.utm_source,
            'utm_medium': self.utm_medium,
            'utm_term': self.utm_term,
            'utm_content': self.utm_content,
            'utm_id': self.utm_id,
            'utm_campaign': self.utm_campaign,
            'gclid': self.gclid,
            'events': [e.as_dict() for e in self.events]
            }

    def save_to_cache(self, key):
        # Use cache instead of redis_store because we're too lazy to handle type marshalling
        # manually. Redis only stores string values in a hash and we have some integer data.
        cache.set('anon/' + key, self.as_dict(), timeout=120)

    def load_from_cache(self, key, eventclass):
        result = cache.get('anon/' + key)
        if result:
            for key in result:
                if key != 'events':
                    setattr(self, key, result[key])
                else:
                    self.events = [eventclass(**kwargs) for kwargs in result[key]]


class EventSession(EventSessionBase, BaseMixin, db.Model):
    """
    A user's event session. Groups together user activity within a single time period.
    """
    persistent = True  # This will be saved to db

    # See https://support.google.com/analytics/answer/2731565?hl=en for source of inspiration
    __tablename__ = 'event_session'
    # UUID for public lookup
    uuid = db.Column(UUIDType(binary=False), nullable=True, default=uuid1mc, unique=True)
    # Who is this user? If known
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=True, index=True)
    user = db.relationship(User)
    # If unknown
    anon_user_id = db.Column(None, db.ForeignKey('anon_user.id'), nullable=True, index=True)
    anon_user = db.relationship(AnonUser)
    # Where did we get this user? Referrer URL
    referrer = db.Column(db.Unicode(2083), nullable=True)

    # Google Analytics parameters. If any of these is present in the
    # current request and different from the current session, a new session is created
    utm_source = db.Column(db.Unicode(250), nullable=False, default=u'')
    utm_medium = db.Column(db.Unicode(250), nullable=False, default=u'')
    utm_term = db.Column(db.Unicode(250), nullable=False, default=u'')
    utm_content = db.Column(db.Unicode(250), nullable=False, default=u'')
    utm_id = db.Column(db.Unicode(250), nullable=False, default=u'')
    utm_campaign = db.Column(db.Unicode(250), nullable=False, default=u'')
    # Google click id (for AdWords)
    gclid = db.Column(db.Unicode(250), nullable=False, default=u'')

    active_at = db.Column(db.DateTime, nullable=False)
    # This session was closed because the user showed up again under new conditions
    # (timeout or campaign tag)
    ended_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (db.CheckConstraint(
        db.case([(user_id != None, 1)], else_=0) + db.case([(anon_user_id != None, 1)], else_=0) == 1,  # NOQA
        name='user_event_session_user_id_or_anon_user_id'),)

    @classmethod
    def get_session(cls, uuid, user=None, anon_user=None):
        ues = cls.query.filter_by(uuid=uuid).one_or_none() if uuid else None

        # We no longer hard-link sessions to users, so this is commented out:
        # if (not not user) + (not not anon_user) != 1:
        #     raise ValueError("Either user or anon_user must be specified")
        # ues = cls.query.filter_by(
        #     user=user, anon_user=anon_user).filter(
        #     cls.ended_at == None).order_by(cls.created_at.desc()).first()  # NOQA

        if ues:
            # Has this session been inactive for over half an hour? Close it,
            # mark as closed when last active.
            if ues.active_at < datetime.utcnow() - timedelta(minutes=30):
                ues.ended_at = ues.active_at
                # The attribute change goes into the database session's cache,
                # so we can safely discard the local variable assignment here.
                ues = None

            # Campaign parameters changed? End the session again. See Google's documentation for reasoning
            # https://developers.google.com/analytics/devguides/collection/gajs/gaTrackingCampaigns
            if ues is not None:
                for param in ('utm_source', 'utm_medium', 'utm_term', 'utm_content', 'utm_id', 'utm_campaign', 'gclid'):
                    pvalue = request.args.get(param, '')[:250] or None
                    if pvalue and pvalue != getattr(ues, param):
                        ues.ended_at = datetime.utcnow()
                        ues = None
                        break

        if not ues:
            ues = cls.new_from_request(request)
            ues.user = user
            ues.anon_user = anon_user
            db.session.add(ues)
        # ues.active_at = datetime.utcnow()
        session_set_active_at(ues.uuid)
        return ues

    @classmethod
    def get(cls, uuid):
        if isinstance(uuid, basestring):
            uuid = UUID(uuid)
        return cls.query.filter_by(uuid=uuid).one_or_none()

    @classmethod
    def all(cls, uuids):
        uuids = [u if isinstance(u, basestring) else UUID(u) for u in uuids]
        return cls.query.filter(cls.uuid.in_(uuids))

    @classmethod
    def close_all_inactive(cls):
        cls.query.filter(cls.ended_at == None,  # NOQA
        cls.active_at < (datetime.utcnow() - timedelta(minutes=30))).update(
        {cls.ended_at: cls.active_at})


# These should be class or instance methods
def session_set_active_at(sessionid):
    sessionid = unicode(sessionid)  # In case this is a UUID
    now = datetime.utcnow()
    active_at = repr(mktime(now.timetuple()) + now.microsecond / 1e6)  # repr has more precision than unicode in Py2
    redis_store.hset('hasjob/session_active_at', sessionid, active_at)


def session_get_active_at(sessionid=None):
    sessionid = unicode(sessionid)
    if sessionid:
        active_at = redis_store.hget('hasjob/session_active_at', sessionid)
        if active_at:
            return datetime.fromtimestamp(float(active_at))
    else:
        result = redis_store.hgetall('hasjob/session_active_at')
        for sessionid in result:
            result[sessionid] = datetime.fromtimestamp(float(result[sessionid]))
        return result


def session_save_active_at(sessionid=None):
    if sessionid:
        active_at = session_get_active_at(sessionid)
        if active_at:
            session = EventSession.get(sessionid)
            session.active_at = active_at
            db.session.commit()
    else:
        queue = session.get_active_at()  # Returns a dict of sessionid (as UUID string) to active_at (as datetime)
        sessions = EventSession.all(queue.keys())
        for session in sessions:
            session.active_at = queue[unicode(session.uuid)]
        db.session.commit()


class UserEventBase(object):
    @classmethod
    def new_from_request(cls, request):
        instance = cls()
        instance.ipaddr = request and unicode(request.environ['REMOTE_ADDR'][:45])
        instance.useragent = request and unicode_http_header(request.user_agent.string)[:250]
        instance.url = request and request.url[:2038]
        instance.method = request and unicode(request.method[:10])
        instance.name = request and (u'endpoint/' + (request.endpoint or '')[:80])
        return instance

    def as_dict(self):
        return dict(self.__dict__)


class UserEvent(UserEventBase, BaseMixin, db.Model):
    """
    An event, anything from a page load (typical) to an activity within that page load.
    """
    __tablename__ = 'user_event'
    event_session_id = db.Column(None, db.ForeignKey('event_session.id'), nullable=False)
    event_session = db.relationship(EventSession,
        backref=db.backref('events', lazy='dynamic', order_by='UserEvent.created_at'))
    #: User's IP address
    ipaddr = db.Column(db.Unicode(45), nullable=True)
    #: User's browser
    useragent = db.Column(db.Unicode(250), nullable=True)
    #: URL
    url = db.Column(db.Unicode(2038), nullable=True)
    #: Referrer
    referrer = db.Column(db.Unicode(2038), nullable=True,
        default=lambda: request and (unicode_http_header(request.referrer or '')[:2038] or None))
    #: HTTP Method
    method = db.Column(db.Unicode(10), nullable=True)
    #: Status code
    status_code = db.Column(db.SmallInteger, nullable=True)
    #: Event name
    name = db.Column(db.Unicode(80), nullable=False)
    #: Custom event data (null = no data saved)
    data = db.Column(JsonDict, nullable=True)
