# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import datetime, timedelta
from werkzeug import cached_property
from flask import url_for, g, escape, Markup
from sqlalchemy import event, DDL
from sqlalchemy.orm import defer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.dialects.postgresql import TSVECTOR
import tldextract
from coaster.sqlalchemy import make_timestamp_columns, Query, JsonDict
from baseframe import cache, _
from baseframe.staticdata import webmail_domains
from .. import redis_store
from . import newlimit, agelimit, db, POSTSTATUS, EMPLOYER_RESPONSE, PAY_TYPE, BaseMixin, TimestampMixin
from .jobtype import JobType
from .jobcategory import JobCategory
from .user import User, AnonUser, EventSession
from ..utils import random_long_key, random_hash_key

__all__ = ['JobPost', 'JobLocation', 'UserJobView', 'AnonJobView', 'JobImpression', 'JobApplication',
    'JobViewSession', 'unique_hash', 'viewstats_by_id_qhour', 'viewstats_by_id_hour', 'viewstats_by_id_day']


def number_format(number, suffix):
    return str(int(number)) + suffix if int(number) == number else str(round(number, 2)) + suffix


def number_abbreviate(number, indian=False):
    if indian:
        if number < 100000:  # < 1 lakh
            return number_format(number / 1000.0, 'k')
        elif number < 10000000:  # < 1 crore
            return number_format(number / 100000.0, 'L')
        else:  # >= 1 crore
            return number_format(number / 10000000.0, 'C')
    else:
        if number < 1000000:  # < 1 million
            return number_format(number / 1000.0, 'k')
        elif number < 100000000:  # < 1 billion
            return number_format(number / 1000000.0, 'm')
        else:  # >= 1 billion
            return number_format(number / 100000000.0, 'b')


starred_job_table = db.Table('starred_job', db.Model.metadata,
    db.Column('user_id', None, db.ForeignKey('user.id'), primary_key=True),
    db.Column('jobpost_id', None, db.ForeignKey('jobpost.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow, nullable=False),
    )


def starred_job_ids(user, agelimit):
    return [r[0] for r in db.session.query(starred_job_table.c.jobpost_id).filter(
        starred_job_table.c.user_id == user.id,
        starred_job_table.c.created_at > datetime.utcnow() - agelimit)]


User.starred_job_ids = starred_job_ids


class JobPost(BaseMixin, db.Model):
    __tablename__ = 'jobpost'

    # Metadata
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=True, index=True)
    user = db.relationship(User, primaryjoin=user_id == User.id, backref=db.backref('jobposts', lazy='dynamic'))

    hashid = db.Column(db.String(5), nullable=False, unique=True)
    datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)  # Published
    closed_datetime = db.Column(db.DateTime, nullable=True)  # If withdrawn or rejected
    # Pinned on the home page. Boards use the BoardJobPost.pinned column
    sticky = db.Column(db.Boolean, nullable=False, default=False)
    pinned = db.synonym('sticky')

    # Job description
    headline = db.Column(db.Unicode(100), nullable=False)
    headlineb = db.Column(db.Unicode(100), nullable=True)
    type_id = db.Column(None, db.ForeignKey('jobtype.id'), nullable=False)
    type = db.relation(JobType, primaryjoin=type_id == JobType.id)
    category_id = db.Column(None, db.ForeignKey('jobcategory.id'), nullable=False)
    category = db.relation(JobCategory, primaryjoin=category_id == JobCategory.id)
    location = db.Column(db.Unicode(80), nullable=False)
    parsed_location = db.Column(JsonDict)
    # remote_location tracks whether the job is work-from-home/work-from-anywhere
    remote_location = db.Column(db.Boolean, default=False, nullable=False)
    relocation_assist = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.UnicodeText, nullable=False)
    perks = db.Column(db.UnicodeText, nullable=False)
    how_to_apply = db.Column(db.UnicodeText, nullable=False)
    hr_contact = db.Column(db.Boolean, nullable=True)

    # Compensation details
    pay_type = db.Column(db.SmallInteger, nullable=True)  # Value in models.PAY_TYPE
    pay_currency = db.Column(db.CHAR(3), nullable=True)
    pay_cash_min = db.Column(db.Integer, nullable=True)
    pay_cash_max = db.Column(db.Integer, nullable=True)
    pay_equity_min = db.Column(db.Numeric, nullable=True)
    pay_equity_max = db.Column(db.Numeric, nullable=True)

    # Company details
    company_name = db.Column(db.Unicode(80), nullable=False)
    company_logo = db.Column(db.Unicode(255), nullable=True)
    company_url = db.Column(db.Unicode(255), nullable=False, default=u'')
    twitter = db.Column(db.Unicode(15), nullable=True)
    fullname = db.Column(db.Unicode(80), nullable=True)  # Deprecated field, used before user_id was introduced
    email = db.Column(db.Unicode(80), nullable=False)
    email_domain = db.Column(db.Unicode(80), nullable=False, index=True)
    domain_id = db.Column(None, db.ForeignKey('domain.id'), nullable=False)
    md5sum = db.Column(db.String(32), nullable=False, index=True)

    # Payment, audit and workflow fields
    words = db.Column(db.UnicodeText, nullable=True)  # All words in description, perks and how_to_apply
    promocode = db.Column(db.String(40), nullable=True)
    status = db.Column(db.Integer, nullable=False, default=POSTSTATUS.DRAFT)
    ipaddr = db.Column(db.String(45), nullable=False)
    useragent = db.Column(db.Unicode(250), nullable=True)
    edit_key = db.Column(db.String(40), nullable=False, default=random_long_key)
    email_verify_key = db.Column(db.String(40), nullable=False, default=random_long_key)
    email_sent = db.Column(db.Boolean, nullable=False, default=False)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    payment_value = db.Column(db.Integer, nullable=False, default=0)
    payment_received = db.Column(db.Boolean, nullable=False, default=False)
    reviewer_id = db.Column(None, db.ForeignKey('user.id'), nullable=True, index=True)
    reviewer = db.relationship(User, primaryjoin=reviewer_id == User.id, backref="reviewed_posts")
    review_datetime = db.Column(db.DateTime, nullable=True)
    review_comments = db.Column(db.Unicode(250), nullable=True)

    search_vector = db.Column(TSVECTOR, nullable=True)

    # Metadata for classification
    language = db.Column(db.CHAR(2), nullable=True)
    language_confidence = db.Column(db.Float, nullable=True)

    admins = db.relationship(User, secondary=lambda: jobpost_admin_table,
        backref=db.backref('admin_of', lazy='dynamic'))
    starred_by = db.relationship(User, lazy='dynamic', secondary=starred_job_table,
        backref=db.backref('starred_jobs', lazy='dynamic'))
    #: Quick lookup locations this post is referring to
    geonameids = association_proxy('locations', 'geonameid', creator=lambda l: JobLocation(geonameid=l))

    _defercols = [
        defer('user_id'),
        defer('closed_datetime'),
        defer('parsed_location'),
        defer('relocation_assist'),
        defer('description'),
        defer('perks'),
        defer('how_to_apply'),
        defer('hr_contact'),
        defer('company_logo'),
        defer('company_url'),
        defer('fullname'),
        defer('email'),
        defer('words'),
        defer('promocode'),
        defer('ipaddr'),
        defer('useragent'),
        defer('edit_key'),
        defer('email_verify_key'),
        defer('email_sent'),
        defer('email_verified'),
        defer('payment_value'),
        defer('payment_received'),
        defer('reviewer_id'),
        defer('review_datetime'),
        defer('review_comments'),
        defer('language'),
        defer('language_confidence'),

        # defer('pay_type'),
        # defer('pay_currency'),
        # defer('pay_cash_min'),
        # defer('pay_cash_max'),
        # defer('pay_equity_min'),
        # defer('pay_equity_max'),
        ]

    @classmethod
    def get(cls, hashid):
        return cls.query.filter_by(hashid=hashid).one_or_none()

    def __repr__(self):
        return u'<JobPost {hashid} "{headline}">'.format(hashid=self.hashid, headline=self.headline)

    def admin_is(self, user):
        if user is None:
            return False
        return user == self.user or user in self.admins

    def status_label(self):
        if self.status == POSTSTATUS.DRAFT:
            return _("Draft")
        elif self.status == POSTSTATUS.PENDING:
            return _("Pending")
        elif self.is_new():
            return _("New!")

    def is_draft(self):
        return self.status == POSTSTATUS.DRAFT

    def is_pending(self):
        return self.status == POSTSTATUS.PENDING

    def is_unpublished(self):
        return self.status in POSTSTATUS.UNPUBLISHED

    def is_listed(self):
        now = datetime.utcnow()
        return (self.status in POSTSTATUS.LISTED) and (
            self.datetime > now - agelimit)

    def is_public(self):
        return self.status in POSTSTATUS.LISTED

    def is_flagged(self):
        return self.status == POSTSTATUS.FLAGGED

    def is_moderated(self):
        return self.status == POSTSTATUS.MODERATED

    def is_announcement(self):
        return self.status == POSTSTATUS.ANNOUNCEMENT

    def is_new(self):
        return self.datetime >= datetime.utcnow() - newlimit

    def is_old(self):
        return self.datetime <= datetime.utcnow() - agelimit

    def pay_type_label(self):
        return PAY_TYPE.get(self.pay_type)

    def url_for(self, action='view', _external=False, **kwargs):
        if self.status in POSTSTATUS.UNPUBLISHED and action in ('view', 'edit'):
            domain = None
        else:
            domain = self.email_domain

        # A/B test flag for permalinks
        if 'b' in kwargs:
            if kwargs['b'] is not None:
                kwargs['b'] = unicode(int(kwargs['b']))
            else:
                kwargs.pop('b')

        if action == 'view':
            return url_for('jobdetail', hashid=self.hashid, domain=domain, _external=_external, **kwargs)
        elif action == 'reveal':
            return url_for('revealjob', hashid=self.hashid, domain=domain, _external=_external, **kwargs)
        elif action == 'apply':
            return url_for('applyjob', hashid=self.hashid, domain=domain, _external=_external, **kwargs)
        elif action == 'edit':
            return url_for('editjob', hashid=self.hashid, domain=domain, _external=_external, **kwargs)
        elif action == 'withdraw':
            return url_for('withdraw', hashid=self.hashid, domain=domain, _external=_external, **kwargs)
        elif action == 'moderate':
            return url_for('moderatejob', hashid=self.hashid, domain=domain, _external=_external, **kwargs)
        elif action == 'pin':
            return url_for('pinnedjob', hashid=self.hashid, domain=domain, _external=_external, **kwargs)
        elif action == 'reject':
            return url_for('rejectjob', hashid=self.hashid, domain=domain, _external=_external, **kwargs)
        elif action == 'confirm':
            return url_for('confirm', hashid=self.hashid, _external=_external, **kwargs)
        elif action == 'logo':
            return url_for('logoimage', hashid=self.hashid, domain=domain, _external=_external, **kwargs)
        elif action == 'confirm-link':
            return url_for('confirm_email', hashid=self.hashid, domain=domain,
                key=self.email_verify_key, _external=True, **kwargs)
        elif action == 'star':
            return url_for('starjob', hashid=self.hashid, domain=domain, _external=_external, **kwargs)
        elif action == 'manage':
            return url_for('managejob', hashid=self.hashid, domain=domain, _external=_external, **kwargs)
        elif action == 'browse':
            if self.email_domain in webmail_domains:
                return url_for('browse_by_email', md5sum=self.md5sum, _external=_external, **kwargs)
            else:
                return url_for('browse_by_domain', domain=self.email_domain, _external=_external, **kwargs)

    def permissions(self, user, inherited=None):
        perms = super(JobPost, self).permissions(user, inherited)
        if self.status in POSTSTATUS.LISTED:
            perms.add('view')
        if self.admin_is(user):
            if self.status in POSTSTATUS.UNPUBLISHED:
                perms.add('view')
            perms.add('edit')
            perms.add('manage')
            perms.add('withdraw')
        return perms

    @property
    def from_webmail_domain(self):
        return self.email_domain in webmail_domains

    @property
    def company_url_domain_zone(self):
        if not self.company_url:
            return u''
        else:
            r = tldextract.extract(self.company_url)
            return u'.'.join([r.domain, r.suffix])

    @property
    def pays_cash(self):
        if self.pay_type is None:
            return True
        return self.pay_type != PAY_TYPE.NOCASH and self.pay_cash_min is not None and self.pay_cash_max is not None

    @property
    def pays_equity(self):
        return self.pay_equity_min is not None and self.pay_equity_max is not None

    def pay_label(self):
        if self.pay_type is None:
            return u"NA"
        elif self.pay_type == PAY_TYPE.NOCASH:
            cash = None
            suffix = ""
        else:
            if self.pay_type == PAY_TYPE.RECURRING:
                suffix = "pa"
            else:
                suffix = ""

            indian = False
            if self.pay_currency == "INR":
                indian = True
                symbol = u"₹"
            elif self.pay_currency == "USD":
                symbol = u"$"
            elif self.pay_currency == "EUR":
                symbol = u"€"
            elif self.pay_currency == "GBP":
                symbol = u"£"
            else:
                symbol = u"¤"

            if self.pay_cash_min == self.pay_cash_max:
                cash = symbol + number_abbreviate(self.pay_cash_min, indian)
            else:
                cash = symbol + number_abbreviate(self.pay_cash_min, indian) + "-" + number_abbreviate(self.pay_cash_max, indian)

            if suffix:
                cash = cash + " " + suffix

        if self.pay_equity_min and self.pay_equity_max:
            if self.pay_equity_min == self.pay_equity_max:
                equity = str(self.pay_equity_min) + "%"
            else:
                equity = str(self.pay_equity_min) + "-" + str(self.pay_equity_max) + "%"
        else:
            equity = None

        if cash:
            if equity:
                return ", ".join([cash, equity])
            else:
                return cash
        else:
            if equity:
                return equity
            else:
                return "No pay"

    def tag_content(self):
        return Markup('\n').join((
            Markup('<div>') + Markup(escape(self.headline)) + Markup('</div>'),
            Markup('<div>') + Markup(self.description) + Markup('</div>'),
            Markup('<div>') + Markup(self.perks) + Markup('</div>')
            ))

    @property
    def viewcounts_key(self):
        # Also see views.helper.save_impressions for a copy of this key
        return 'hasjob/viewcounts/%d' % self.id

    @cached_property  # For multiple accesses in a single request
    def viewcounts(self):
        cache_key = self.viewcounts_key
        values = g.viewcounts.get(cache_key) if g else None
        if values is None:
            values = redis_store.hgetall(cache_key)
        if 'impressions' not in values:
            # Also see views.helper.save_impressions for a copy of this query
            values['impressions'] = db.session.query(db.func.count(db.func.distinct(EventSession.user_id))).filter(
                EventSession.user_id != None).join(JobImpression).filter(  # NOQA
                JobImpression.jobpost == self).first()[0]
            redis_store.hset(cache_key, 'impressions', values['impressions'])
            redis_store.expire(cache_key, 86400)
        else:
            values['impressions'] = int(values['impressions'])
        if 'viewed' not in values:
            values['viewed'] = UserJobView.query.filter_by(jobpost=self).count()
            redis_store.hset(cache_key, 'viewed', values['viewed'])
            redis_store.expire(cache_key, 86400)
        else:
            values['viewed'] = int(values['viewed'])
        if 'opened' not in values:
            values['opened'] = UserJobView.query.filter_by(jobpost=self, applied=True).count()
            redis_store.hset(cache_key, 'opened', values['opened'])
            redis_store.expire(cache_key, 86400)
        else:
            values['opened'] = int(values['opened'])
        if 'applied' not in values:
            values['applied'] = JobApplication.query.filter_by(jobpost=self).count()
            redis_store.hset(cache_key, 'applied', values['applied'])
            redis_store.expire(cache_key, 86400)
        else:
            values['applied'] = int(values['applied'])
        # pay_label rendering is extraordinarily slow. We don't know why yet, but it's static data, so cache it
        if 'pay_label' not in values:
            values['pay_label'] = self.pay_label()
            redis_store.hset(cache_key, 'pay_label', values['pay_label'].encode('utf-8'))
            redis_store.expire(cache_key, 86400)
        elif isinstance(values['pay_label'], str):  # Redis appears to return bytestrings, not Unicode
            values['pay_label'] = unicode(values['pay_label'], 'utf-8')
        return values

    def uncache_viewcounts(self, key=None):
        cache_key = self.viewcounts_key
        if not key:
            redis_store.delete(cache_key)
        else:
            redis_store.hdel(cache_key, key)

    @cached_property
    def ab_views(self):
        na_count = JobViewSession.query.filter_by(jobpost=self, bgroup=None).count()
        counts = db.session.query(
            JobViewSession.bgroup.label('bgroup'), db.func.count(JobViewSession.bgroup).label('count')).filter(
            JobViewSession.jobpost == self, JobViewSession.bgroup != None).group_by(JobViewSession.bgroup)  # NOQA
        results = {'NA': na_count, 'A': 0, 'B': 0}
        for row in counts:
            if row.bgroup is False:
                results['A'] = row.count
            elif row.bgroup is True:
                results['B'] = row.count
        return results

    @property
    def sort_score(self):
        """
        Sort with a gravity of 1.8 using the HackerNews algorithm
        """
        viewcounts = self.viewcounts
        opened = int(viewcounts['opened'])
        applied = int(viewcounts['applied'])
        age = datetime.utcnow() - self.datetime
        hours = age.days * 24 + age.seconds / 3600

        return ((applied * 3) + (opened - applied)) / pow((hours + 2), 1.8)

    @cached_property  # For multiple accesses in a single request
    def viewstats(self):
        now = datetime.utcnow()
        delta = now - self.datetime
        if delta.days < 2:  # Less than two days
            if delta.seconds < 21600:  # Less than 6 hours
                return 'q', viewstats_by_id_qhour(self.id)
            else:
                return 'h', viewstats_by_id_hour(self.id)
        else:
            return 'd', viewstats_by_id_day(self.id)

    @property
    def new_applications(self):
        return JobApplication.query.filter_by(jobpost=self, response=EMPLOYER_RESPONSE.NEW).count()

    @property
    def replied_applications(self):
        return JobApplication.query.filter_by(jobpost=self, response=EMPLOYER_RESPONSE.REPLIED).count()

    def reports(self):
        if not self.flags:
            return []
        counts = {}
        for flag in self.flags:
            counts[flag.reportcode] = counts.setdefault(flag.reportcode, 0) + 1
        return [{'count': i[2], 'title': i[1]} for i in sorted([(k.seq, k.title, v) for k, v in counts.items()])]


def viewstats_helper(jobpost_id, interval, limit, daybatch=False):
    post = JobPost.query.get(jobpost_id)
    if not post.datetime:
        return {}
    viewed = UserJobView.query.filter_by(jobpost_id=jobpost_id).all()
    opened = [v for v in viewed if v.applied == True]  # NOQA
    applied = db.session.query(JobApplication.created_at).filter_by(jobpost_id=jobpost_id).all()

    # Now batch them by size
    now = datetime.utcnow()
    delta = now - post.datetime
    if daybatch:
        batches, remainder = divmod(delta.days, interval)
        if delta.seconds:
            remainder = True
    else:
        batches, remainder = divmod(int(delta.total_seconds()), interval)

    if remainder or batches == 0:
        batches += 1

    cviewed = batches * [0]
    copened = batches * [0]
    capplied = batches * [0]

    for clist, source, attr in [
            (cviewed, viewed, 'created_at'),
            (copened, opened, 'updated_at'),
            (capplied, applied, 'created_at')]:
        for item in source:
            sourcedate = getattr(item, attr)
            if sourcedate < post.datetime:
                # This happens when the user creates a post when logged in. Their 'viewed' date will be
                # for the draft, whereas the confirmed post's datetime will be later. There should
                # be just one instance of this. This can also happen if the server's clock is reset, such
                # as by an NTP error after reboot (has happened to us).
                sourcedate = post.datetime
            itemdelta = sourcedate - post.datetime
            try:
                if daybatch:
                    clist[int(itemdelta.days // interval)] += 1
                else:
                    clist[int(int(itemdelta.total_seconds()) // interval)] += 1
            except IndexError:
                # Server time got messed up. Ouch! Ignore for now.
                pass

    if limit and batches > limit:
        cviewed = cviewed[:limit]
        copened = copened[:limit]
        capplied = capplied[:limit]

    return {
        'max': max([
            max(cviewed) if cviewed else 0,
            max(copened) if copened else 0,
            max(capplied) if capplied else 0,
            ]),
        'length': max([len(cviewed), len(copened), len(capplied)]),
        'viewed': cviewed,
        'opened': copened,
        'applied': capplied,
        }


@cache.memoize(timeout=900)
def viewstats_by_id_qhour(jobpost_id):
    return viewstats_helper(jobpost_id, 900, 24)


@cache.memoize(timeout=3600)
def viewstats_by_id_hour(jobpost_id):
    return viewstats_helper(jobpost_id, 3600, 48)


@cache.memoize(timeout=86400)
def viewstats_by_id_day(jobpost_id):
    return viewstats_helper(jobpost_id, 1, 30, daybatch=True)


jobpost_admin_table = db.Table('jobpost_admin', db.Model.metadata,
    *(make_timestamp_columns() + (
        db.Column('user_id', None, db.ForeignKey('user.id'), primary_key=True),
        db.Column('jobpost_id', None, db.ForeignKey('jobpost.id'), primary_key=True)
        )))


class JobLocation(TimestampMixin, db.Model):
    __tablename__ = 'job_location'
    #: Job post we are tagging
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), primary_key=True, nullable=False)
    jobpost = db.relationship(JobPost, backref=db.backref('locations', cascade='all, delete-orphan'))
    #: Geonameid for this job post
    geonameid = db.Column(db.Integer, primary_key=True, nullable=False, index=True)
    primary = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return '<JobLocation %d %s for job %s>' % (
            self.geonameid,
            'primary' if self.primary else 'secondary',
            self.jobpost.hashid)


class UserJobView(TimestampMixin, db.Model):
    __tablename__ = 'userjobview'
    #: Job post that was seen
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), primary_key=True)
    jobpost = db.relationship(JobPost)
    #: User who saw this post
    user_id = db.Column(None, db.ForeignKey('user.id'), primary_key=True, index=True)
    user = db.relationship(User)
    #: Has the user viewed apply instructions?
    applied = db.Column(db.Boolean, default=False, nullable=False)

    @classmethod
    def get(cls, jobpost, user):
        return cls.query.get((jobpost.id, user.id))


class AnonJobView(db.Model):
    __tablename__ = 'anon_job_view'
    query_class = Query

    #: Job post that was seen
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), primary_key=True)
    jobpost = db.relationship(JobPost)
    #: User who saw this post
    anon_user_id = db.Column(None, db.ForeignKey('anon_user.id'), primary_key=True, index=True)
    anon_user = db.relationship(AnonUser)
    #: Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    @classmethod
    def get(cls, jobpost, anon_user):
        return cls.query.get((jobpost.id, anon_user.id))


class JobImpression(TimestampMixin, db.Model):
    __tablename__ = 'job_impression'
    #: Job post that was impressed
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), primary_key=True)
    jobpost = db.relationship(JobPost)
    #: Event session in which it was impressed
    event_session_id = db.Column(None, db.ForeignKey('event_session.id'), primary_key=True, index=True)
    event_session = db.relationship(EventSession)
    #: Whether it was pinned at any time in this session
    pinned = db.Column(db.Boolean, nullable=False, default=False)
    #: Was this rendering in the B group of an A/B test? (null = no test conducted)
    bgroup = db.Column(db.Boolean, nullable=True)

    @classmethod
    def get(cls, jobpost, event_session):
        # See views.helper.save_impressions, which doesn't use this method and depends on
        # (jobpost_id, event_session_id) primary key order.
        return cls.query.get((jobpost.id, event_session.id))


class JobViewSession(TimestampMixin, db.Model):
    __tablename__ = 'job_view_session'
    #: Event session in which jobpost was viewed
    #: This takes precedence as we'll be loading all instances
    #: matching the current session in each index request
    event_session_id = db.Column(None, db.ForeignKey('event_session.id'), primary_key=True)
    event_session = db.relationship(EventSession)
    #: Job post that was viewed
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), primary_key=True, index=True)
    jobpost = db.relationship(JobPost)
    #: Was this view in the B group of an A/B test? (null = no test conducted)
    bgroup = db.Column(db.Boolean, nullable=True)

    @classmethod
    def get(cls, event_session, jobpost):
        return cls.query.get((event_session.id, jobpost.id))


class JobApplication(BaseMixin, db.Model):
    __tablename__ = 'job_application'
    #: Hash id (to hide database ids)
    hashid = db.Column(db.String(40), nullable=False, unique=True)
    #: User who applied for this post
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=True, index=True)  # TODO: add unique=True
    user = db.relationship(User, foreign_keys=user_id)
    #: Full name of the user (as it was at the time of the application)
    fullname = db.Column(db.Unicode(250), nullable=False)
    #: Job post they applied to
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), nullable=False, index=True)
    # jobpost relationship is below, outside the class definition
    #: User's email address
    email = db.Column(db.Unicode(80), nullable=False)
    #: User's phone number
    phone = db.Column(db.Unicode(80), nullable=False)
    #: User's message
    message = db.Column(db.UnicodeText, nullable=False)
    #: User opted-in to experimental features
    optin = db.Column(db.Boolean, default=False, nullable=False)
    #: Employer's response code
    response = db.Column(db.Integer, nullable=False, default=EMPLOYER_RESPONSE.NEW)
    #: Employer's response message
    response_message = db.Column(db.UnicodeText, nullable=True)
    #: Bag of words, for spam analysis
    words = db.Column(db.UnicodeText, nullable=True)
    #: Jobpost admin who replied to this candidate
    replied_by_id = db.Column(None, db.ForeignKey('user.id'), nullable=True, index=True)
    replied_by = db.relationship(User, foreign_keys=replied_by_id)
    #: When they replied
    replied_at = db.Column(db.DateTime, nullable=True)

    candidate_feedback = db.Column(db.SmallInteger, nullable=True)

    def __init__(self, **kwargs):
        super(JobApplication, self).__init__(**kwargs)
        if self.hashid is None:
            self.hashid = unique_long_hash()

    @property
    def status(self):
        return EMPLOYER_RESPONSE[self.response]

    def is_new(self):
        return self.response == EMPLOYER_RESPONSE.NEW

    def is_pending(self):
        return self.response == EMPLOYER_RESPONSE.PENDING

    def is_ignored(self):
        return self.response == EMPLOYER_RESPONSE.IGNORED

    def is_replied(self):
        return self.response == EMPLOYER_RESPONSE.REPLIED

    def is_flagged(self):
        return self.response == EMPLOYER_RESPONSE.FLAGGED

    def is_spam(self):
        return self.response == EMPLOYER_RESPONSE.SPAM

    def is_rejected(self):
        return self.response == EMPLOYER_RESPONSE.REJECTED

    def can_reply(self):
        return self.response in (EMPLOYER_RESPONSE.NEW, EMPLOYER_RESPONSE.PENDING, EMPLOYER_RESPONSE.IGNORED)

    def can_reject(self):
        return self.response in (EMPLOYER_RESPONSE.NEW, EMPLOYER_RESPONSE.PENDING, EMPLOYER_RESPONSE.IGNORED)

    def can_ignore(self):
        return self.response in (EMPLOYER_RESPONSE.NEW, EMPLOYER_RESPONSE.PENDING)

    def can_report(self):
        return self.response in (EMPLOYER_RESPONSE.NEW, EMPLOYER_RESPONSE.PENDING,
            EMPLOYER_RESPONSE.IGNORED, EMPLOYER_RESPONSE.REJECTED)

    def application_count(self):
        """Number of jobs candidate has applied to around this one"""
        if not self.user:
            # Kiosk submission, no data available
            return {
                'count': 0,
                'ignored': 0,
                'replied': 0,
                'flagged': 0,
                'spam': 0,
                'rejected': 0
                }
        date_min = self.created_at - timedelta(days=7)
        date_max = self.created_at + timedelta(days=7)
        counts = defaultdict(int)
        for r in db.session.query(JobApplication.response).filter(JobApplication.user == self.user).filter(
                JobApplication.created_at > date_min, JobApplication.created_at < date_max):
            counts[r.response] += 1

        return {
            'count': sum(counts.values()),
            'ignored': counts[EMPLOYER_RESPONSE.IGNORED],
            'replied': counts[EMPLOYER_RESPONSE.REPLIED],
            'flagged': counts[EMPLOYER_RESPONSE.FLAGGED],
            'spam': counts[EMPLOYER_RESPONSE.SPAM],
            'rejected': counts[EMPLOYER_RESPONSE.REJECTED],
            }

    def url_for(self, action='view', _external=False, **kwargs):
        domain = self.jobpost.email_domain
        if action == 'view':
            return url_for('view_application', hashid=self.jobpost.hashid, domain=domain, application=self.hashid,
                _external=_external, **kwargs)
        elif action == 'process':
            return url_for('process_application', hashid=self.jobpost.hashid, domain=domain, application=self.hashid,
                _external=_external, **kwargs)
        elif action == 'track-open':
            return url_for('view_application_email_gif', hashid=self.jobpost.hashid, domain=domain, application=self.hashid,
                _external=_external, **kwargs)


JobApplication.jobpost = db.relationship(JobPost,
    backref=db.backref('applications', order_by=(
        db.case(value=JobApplication.response, whens={
            EMPLOYER_RESPONSE.NEW: 0,
            EMPLOYER_RESPONSE.PENDING: 1,
            EMPLOYER_RESPONSE.IGNORED: 2,
            EMPLOYER_RESPONSE.REPLIED: 3,
            EMPLOYER_RESPONSE.REJECTED: 4,
            EMPLOYER_RESPONSE.FLAGGED: 5,
            EMPLOYER_RESPONSE.SPAM: 6
            }),
        db.desc(JobApplication.created_at)), cascade='all, delete-orphan'))


def unique_hash(model=JobPost):
    """
    Returns a unique hash for a given model
    """
    with db.session.no_autoflush:
        while 1:
            hashid = random_hash_key()
            if not hashid.isdigit() and model.query.filter_by(hashid=hashid).isempty():
                break
    return hashid


def unique_long_hash(model=JobApplication):
    """
    Returns a long unique hash for a given model
    """
    with db.session.no_autoflush:
        while 1:
            hashid = random_long_key()
            if not hashid.isdigit() and model.query.filter_by(hashid=hashid).isempty():
                break
    return hashid


create_jobpost_search_trigger = DDL(
    '''
    CREATE FUNCTION jobpost_search_vector_update() RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'INSERT' THEN
            NEW.search_vector = to_tsvector('english', COALESCE(NEW.company_name, '') || ' ' || COALESCE(NEW.headline, '') || ' ' || COALESCE(NEW.headlineb, '') || ' ' || COALESCE(NEW.description, '') || ' ' || COALESCE(NEW.perks, ''));
        END IF;
        IF TG_OP = 'UPDATE' THEN
            IF NEW.headline <> OLD.headline OR COALESCE(NEW.headlineb, '') <> COALESCE(OLD.headlineb, '') OR NEW.description <> OLD.description OR NEW.perks <> OLD.perks THEN
                NEW.search_vector = to_tsvector('english', COALESCE(NEW.company_name, '') || ' ' || COALESCE(NEW.headline, '') || ' ' || COALESCE(NEW.headlineb, '') || ' ' || COALESCE(NEW.description, '') || ' ' || COALESCE(NEW.perks, ''));
            END IF;
        END IF;
        RETURN NEW;
    END
    $$ LANGUAGE 'plpgsql';

    CREATE TRIGGER jobpost_search_vector_trigger BEFORE INSERT OR UPDATE ON jobpost
    FOR EACH ROW EXECUTE PROCEDURE jobpost_search_vector_update();

    CREATE INDEX ix_jobpost_search_vector ON jobpost USING gin(search_vector);
    ''')

event.listen(JobPost.__table__, 'after_create',
    create_jobpost_search_trigger.execute_if(dialect='postgresql'))
