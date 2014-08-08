# -*- coding: utf-8 -*-

from datetime import datetime
from werkzeug import cached_property
from flask import url_for
from sqlalchemy.orm import defer
from coaster.sqlalchemy import timestamp_columns, JsonDict
from baseframe import cache
import tldextract
from . import agelimit, db, POSTSTATUS, EMPLOYER_RESPONSE, PAY_TYPE, BaseMixin, TimestampMixin, webmail_domains
from .jobtype import JobType
from .jobcategory import JobCategory
from .user import User
from ..utils import random_long_key, random_hash_key


class JobPost(BaseMixin, db.Model):
    __tablename__ = 'jobpost'
    idref = 'post'

    # Metadata
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship(User, primaryjoin=user_id == User.id, backref='jobposts')
    hashid = db.Column(db.String(5), nullable=False, unique=True)
    datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Published
    closed_datetime = db.Column(db.DateTime, nullable=True)  # If withdrawn or rejected
    sticky = db.Column(db.Boolean, nullable=False, default=False)
    pinned = db.synonym('sticky')

    # Job description
    headline = db.Column(db.Unicode(100), nullable=False)
    type_id = db.Column(None, db.ForeignKey('jobtype.id'), nullable=False)
    type = db.relation(JobType, primaryjoin=type_id == JobType.id)
    category_id = db.Column(None, db.ForeignKey('jobcategory.id'), nullable=False)
    category = db.relation(JobCategory, primaryjoin=category_id == JobCategory.id)
    location = db.Column(db.Unicode(80), nullable=False)
    parsed_location = db.Column(JsonDict)
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
    fullname = db.Column(db.Unicode(80), nullable=True)
    email = db.Column(db.Unicode(80), nullable=False)
    email_domain = db.Column(db.Unicode(80), nullable=False, index=True)
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
    reviewer_id = db.Column(None, db.ForeignKey('user.id'), nullable=True)
    reviewer = db.relationship(User, primaryjoin=reviewer_id == User.id, backref="reviewed_posts")
    review_datetime = db.Column(db.DateTime, nullable=True)
    review_comments = db.Column(db.Unicode(250), nullable=True)

    # Metadata for classification
    language = db.Column(db.CHAR(2), nullable=True)

    admins = db.relationship(User, secondary=lambda: jobpost_admin_table)

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

        defer('pay_type'),
        defer('pay_currency'),
        defer('pay_cash_min'),
        defer('pay_cash_max'),
        defer('pay_equity_min'),
        defer('pay_equity_max'),
        ]

    @classmethod
    def get(cls, hashid):
        return cls.query.filter_by(hashid=hashid).one_or_none()

    def admin_is(self, user):
        if user is None:
            return False
        return user == self.user or user in self.admins

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

    def is_flagged(self):
        return self.status == POSTSTATUS.FLAGGED

    def is_moderated(self):
        return self.status == POSTSTATUS.MODERATED

    def is_announcement(self):
        return self.status == POSTSTATUS.ANNOUNCEMENT

    def is_old(self):
        return self.datetime <= datetime.utcnow() - agelimit

    def pay_type_label(self):
        return PAY_TYPE.get(self.pay_type)

    def url_for(self, action='view', _external=False):
        if action == 'view':
            return url_for('jobdetail', hashid=self.hashid, _external=_external)
        elif action == 'edit':
            return url_for('editjob', hashid=self.hashid, _external=_external)
        elif action == 'confirm':
            return url_for('confirm', hashid=self.hashid, _external=_external)
        elif action == 'browse':
            if self.email_domain in webmail_domains:
                return url_for('browse_by_email', md5sum=self.md5sum, _external=_external)
            else:
                return url_for('browse_by_domain', domain=self.email_domain, _external=_external)

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
        format = lambda number, suffix: str(int(number)) + suffix if int(number) == number else str(round(number, 2)) + suffix
        def abbreviate(number, indian=False):
            if indian:
                if number < 100000:  # < 1 lakh
                    return format(number / 1000.0, 'k')
                elif number < 10000000:  # < 1 crore
                    return format(number / 100000.0, 'L')
                else:  # >= 1 crore
                    return format(number / 10000000.0, 'C')
            else:
                if number < 1000000:  # < 1 million
                    return format(number / 1000.0, 'k')
                elif number < 100000000:  # < 1 billion
                    return format(number / 1000000.0, 'm')
                else:  # >= 1 billion
                    return format(number / 100000000.0, 'b')

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
                cash = symbol + abbreviate(self.pay_cash_min, indian)
            else:
                cash = symbol + abbreviate(self.pay_cash_min, indian) + "-" + abbreviate(self.pay_cash_max, indian)

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

    def search_mapping(self):
        """
        Returns a dictionary suitable for search indexing.
        """
        content = '\n'.join((self.headline,
                            self.location,
                            self.company_name,
                            self.company_url,
                            self.description,
                            self.perks))

        return {'title': self.headline,
                'content': content,
                'public': self.is_listed(),
                'idref': u'%s/%s' % (self.idref, self.id),
                }

    @cached_property  # For multiple accesses in a single request
    def viewcounts(self):
        return viewcounts_by_id(self.id)

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

    def reports(self):
        if not self.flags:
            return []
        counts = {}
        for flag in self.flags:
            counts[flag.reportcode] = counts.setdefault(flag.reportcode, 0) + 1
        return [{'count': i[2], 'title': i[1]} for i in sorted([(k.seq, k.title, v) for k, v in counts.items()])]


@cache.memoize(timeout=86400)
def viewcounts_by_id(jobpost_id):
    return {
        'viewed': UserJobView.query.filter_by(jobpost_id=jobpost_id).count(),
        'opened': UserJobView.query.filter_by(jobpost_id=jobpost_id, applied=True).count(),
        'applied': JobApplication.query.filter_by(jobpost_id=jobpost_id).count()
        }


def viewstats_helper(jobpost_id, interval, limit, daybatch=False):
    post = JobPost.query.get(jobpost_id)
    if not post.datetime:
        return {}
    viewed = UserJobView.query.filter_by(jobpost_id=jobpost_id).all()
    opened = [v for v in viewed if v.applied == True]
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
                # This happens when the user creates a listing when logged in. Their 'viewed' date will be
                # for the draft, whereas the confirmed listing's datetime will be later. There should
                # be just one instance of this.
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
    *(timestamp_columns + (
    db.Column('user_id', None, db.ForeignKey('user.id'), primary_key=True),
    db.Column('jobpost_id', None, db.ForeignKey('jobpost.id'), primary_key=True)
    )))


class JobLocation(TimestampMixin, db.Model):
    __tablename__ = 'job_location'
    #: Job listing we are tagging
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), primary_key=True, nullable=False)
    jobpost = db.relationship(JobPost, backref=db.backref('locations', cascade='all, delete-orphan'))
    #: Geonameid for this job listing
    geonameid = db.Column(db.Integer, primary_key=True, nullable=False)
    primary = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return '<JobLocation %d %s for job %s>' % (
            self.geonameid,
            'primary' if self.primary else 'secondary',
            self.jobpost.hashid)


class UserJobView(TimestampMixin, db.Model):
    __tablename__ = 'userjobview'
    #: User who saw a listing
    user_id = db.Column(None, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship(User)
    #: Job listing they saw
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), primary_key=True)
    jobpost = db.relationship(JobPost)
    #: Has the user viewed apply instructions?
    applied = db.Column(db.Boolean, default=False, nullable=False)


class JobApplication(BaseMixin, db.Model):
    __tablename__ = 'job_application'
    #: Hash id (to hide database ids)
    hashid = db.Column(db.String(40), nullable=False, unique=True)
    #: User who applied for this listing
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=True)  # TODO: add unique=True
    user = db.relationship(User, foreign_keys=user_id)
    #: Full name of the user (as it was at the time of the application)
    fullname = db.Column(db.Unicode(250), nullable=False)
    #: Job listing they applied to
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'))
    #: User's email address
    email = db.Column(db.Unicode(80), nullable=False)
    #: User's phone number
    phone = db.Column(db.Unicode(80), nullable=False)
    #: User's message
    message = db.Column(db.UnicodeText, nullable=False)
    #: Employer's response code
    response = db.Column(db.Integer, nullable=False, default=EMPLOYER_RESPONSE.NEW)
    #: Employer's response message
    response_message = db.Column(db.UnicodeText, nullable=True)
    #: Bag of words, for spam analysis
    words = db.Column(db.UnicodeText, nullable=True)
    #: Admin who replied for this listing
    replied_by_id = db.Column(None, db.ForeignKey('user.id'), nullable=True)
    replied_by = db.relationship(User, foreign_keys=replied_by_id)

    # candidate_feedback = db.Column(db.Integer, nullable=True)

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
    while 1:
        hashid = random_hash_key()
        if model.query.filter_by(hashid=hashid).count() == 0:
            break
    return hashid


def unique_long_hash(model=JobApplication):
    """
    Returns a long unique hash for a given model
    """
    while 1:
        hashid = random_long_key()
        if model.query.filter_by(hashid=hashid).count() == 0:
            break
    return hashid
