from __future__ import annotations

from datetime import timedelta

import tldextract
from flask import url_for
from flask_babel import format_datetime
from markupsafe import Markup, escape
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.associationproxy import association_proxy
from werkzeug.utils import cached_property

from baseframe import __, cache
from baseframe.utils import is_public_email_domain
from coaster.sqlalchemy import JsonDict, Query, StateManager, make_timestamp_columns
from coaster.utils import classmethodproperty, utcnow

from .. import redis_store
from ..utils import random_hash_key, random_long_key
from . import (
    EMPLOYER_RESPONSE,
    PAY_TYPE,
    POST_STATE,
    BaseMixin,
    Model,
    TimestampMixin,
    agelimit,
    backref,
    db,
    newlimit,
    relationship,
    sa,
)
from .jobcategory import JobCategory
from .jobtype import JobType
from .user import AnonUser, EventSession, User

__all__ = [
    'JobPost',
    'JobLocation',
    'UserJobView',
    'AnonJobView',
    'JobImpression',
    'JobApplication',
    'JobViewSession',
    'unique_hash',
    'viewstats_by_id_hour',
    'viewstats_by_id_day',
    'starred_job_table',
]


def number_format(number, suffix):
    return (
        str(int(number)) + suffix
        if int(number) == number
        else str(round(number, 2)) + suffix
    )


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


starred_job_table = sa.Table(
    'starred_job',
    Model.metadata,
    sa.Column('user_id', None, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('jobpost_id', None, sa.ForeignKey('jobpost.id'), primary_key=True),
    sa.Column(
        'created_at',
        sa.TIMESTAMP(timezone=True),
        default=sa.func.utcnow(),
        nullable=False,
    ),
)


def starred_job_ids(user, agelimit=None):
    if agelimit:
        return [
            r[0]
            for r in db.session.query(starred_job_table.c.jobpost_id).filter(
                starred_job_table.c.user_id == user.id,
                starred_job_table.c.created_at > utcnow() - agelimit,
            )
        ]
    else:
        return [
            r[0]
            for r in db.session.query(starred_job_table.c.jobpost_id).filter(
                starred_job_table.c.user_id == user.id
            )
        ]


User.starred_job_ids = starred_job_ids


def has_starred_post(user, post):
    """Checks if user has starred a particular post"""
    if not post:
        return False
    return bool(
        db.session.query(sa.func.count('*'))
        .select_from(starred_job_table)
        .filter(starred_job_table.c.user_id == user.id)
        .filter(starred_job_table.c.jobpost_id == post.id)
        .scalar()
    )


User.has_starred_post = has_starred_post


class JobPost(BaseMixin, Model):
    __tablename__ = 'jobpost'

    # --- Metadata
    user_id = sa.orm.mapped_column(
        None, sa.ForeignKey('user.id'), nullable=True, index=True
    )
    user = relationship(
        User,
        primaryjoin=user_id == User.id,
        backref=backref('jobposts', lazy='dynamic'),
    )

    hashid = sa.orm.mapped_column(sa.String(5), nullable=False, unique=True)
    #: Published time (but created time until it is published)
    datetime = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True),
        default=sa.func.utcnow(),
        nullable=False,
        index=True,
    )
    #: If withdrawn or rejected
    closed_datetime = sa.orm.mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    # Pinned on the home page. Boards use the BoardJobPost.pinned column
    sticky = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False)
    pinned = sa.orm.synonym('sticky')

    # --- Job description
    headline = sa.orm.mapped_column(sa.Unicode(100), nullable=False)
    headlineb = sa.orm.mapped_column(sa.Unicode(100), nullable=True)
    type_id = sa.orm.mapped_column(None, sa.ForeignKey('jobtype.id'), nullable=False)
    type = relationship(JobType, primaryjoin=type_id == JobType.id)  # noqa: A003
    category_id = sa.orm.mapped_column(
        None, sa.ForeignKey('jobcategory.id'), nullable=False
    )
    category = relationship(JobCategory, primaryjoin=category_id == JobCategory.id)
    location = sa.orm.mapped_column(sa.Unicode(80), nullable=False)
    parsed_location = sa.orm.mapped_column(JsonDict)
    # remote_location tracks whether the job is work-from-home/work-from-anywhere
    remote_location = sa.orm.mapped_column(sa.Boolean, default=False, nullable=False)
    relocation_assist = sa.orm.mapped_column(sa.Boolean, default=False, nullable=False)
    description = sa.orm.mapped_column(sa.UnicodeText, nullable=False)
    perks = sa.orm.mapped_column(sa.UnicodeText, nullable=False)
    how_to_apply = sa.orm.mapped_column(sa.UnicodeText, nullable=False)
    hr_contact = sa.orm.mapped_column(sa.Boolean, nullable=True)

    # --- Compensation details
    pay_type = sa.orm.mapped_column(
        sa.SmallInteger, nullable=True
    )  # Value in models.PAY_TYPE
    pay_currency = sa.orm.mapped_column(sa.CHAR(3), nullable=True)
    pay_cash_min = sa.orm.mapped_column(sa.Integer, nullable=True)
    pay_cash_max = sa.orm.mapped_column(sa.Integer, nullable=True)
    pay_equity_min = sa.orm.mapped_column(sa.Numeric, nullable=True)
    pay_equity_max = sa.orm.mapped_column(sa.Numeric, nullable=True)

    # --- Company details
    company_name = sa.orm.mapped_column(sa.Unicode(80), nullable=False)
    company_logo = sa.orm.mapped_column(sa.Unicode(255), nullable=True)
    company_url = sa.orm.mapped_column(sa.Unicode(255), nullable=False, default='')
    twitter = sa.orm.mapped_column(sa.Unicode(15), nullable=True)  # Deprecated
    #: XXX: Deprecated field, used before user_id was introduced
    fullname = sa.orm.mapped_column(sa.Unicode(80), nullable=True)
    email = sa.orm.mapped_column(sa.Unicode(80), nullable=False)
    email_domain = sa.orm.mapped_column(sa.Unicode(80), nullable=False, index=True)
    domain_id = sa.orm.mapped_column(None, sa.ForeignKey('domain.id'), nullable=False)
    md5sum = sa.orm.mapped_column(sa.String(32), nullable=False, index=True)

    # --- Payment, audit and workflow fields
    #: All words in description, perks and how_to_apply
    words = sa.orm.mapped_column(sa.UnicodeText, nullable=True)
    promocode = sa.orm.mapped_column(sa.String(40), nullable=True)
    ipaddr = sa.orm.mapped_column(sa.String(45), nullable=False)
    useragent = sa.orm.mapped_column(sa.Unicode(250), nullable=True)
    edit_key = sa.orm.mapped_column(
        sa.String(40), nullable=False, default=random_long_key
    )
    email_verify_key = sa.orm.mapped_column(
        sa.String(40), nullable=False, default=random_long_key
    )
    email_sent = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False)
    email_verified = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False)
    payment_value = sa.orm.mapped_column(sa.Integer, nullable=False, default=0)
    payment_received = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False)
    reviewer_id = sa.orm.mapped_column(
        None, sa.ForeignKey('user.id'), nullable=True, index=True
    )
    reviewer = relationship(
        User, primaryjoin=reviewer_id == User.id, backref="reviewed_posts"
    )
    review_datetime = sa.orm.mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    review_comments = sa.orm.mapped_column(sa.Unicode(250), nullable=True)

    search_vector = sa.orm.mapped_column(TSVECTOR, nullable=True)

    _state = sa.orm.mapped_column(
        'status',
        sa.Integer,
        StateManager.check_constraint('status', POST_STATE),
        default=POST_STATE.DRAFT,
        nullable=False,
    )
    state = StateManager('_state', POST_STATE, doc="Current state of the job post")

    # --- Metadata for classification
    language = sa.orm.mapped_column(sa.CHAR(2), nullable=True)
    language_confidence = sa.orm.mapped_column(sa.Float, nullable=True)

    admins = relationship(
        User,
        lazy='dynamic',
        secondary=lambda: jobpost_admin_table,
        backref=backref('admin_of', lazy='dynamic'),
    )
    starred_by = relationship(
        User,
        lazy='dynamic',
        secondary=starred_job_table,
        backref=backref('starred_jobs', lazy='dynamic'),
    )
    #: Quick lookup locations this post is referring to
    geonameids = association_proxy(
        'locations',
        'geonameid',
        creator=lambda geonameid: JobLocation(geonameid=geonameid),
    )

    @classmethod
    def get(cls, hashid):
        return cls.query.filter_by(hashid=hashid).one_or_none()

    @classmethod
    def fetch(cls, hashid):
        """Returns a SQLAlchemy query object for JobPost"""
        return cls.query.filter_by(hashid=hashid).options(
            sa.orm.load_only(
                cls.id,
                cls.headline,
                cls.headlineb,
                cls.hashid,
                cls.datetime,
                cls._state,
                cls.email_domain,
                cls.review_comments,
                cls.company_url,
            )
        )

    @classmethodproperty
    def query_listed(cls):  # noqa: N805
        """Returns a SQLAlchemy query for listed jobposts"""
        return cls.query.filter(JobPost.state.LISTED).options(
            sa.orm.load_only(cls.id, cls.hashid)
        )

    @classmethodproperty
    def _defercols(cls):  # noqa: N805
        """Return columns that can be deferred."""
        return [
            sa.orm.defer(cls.user_id),
            sa.orm.defer(cls.closed_datetime),
            sa.orm.defer(cls.parsed_location),
            sa.orm.defer(cls.relocation_assist),
            sa.orm.defer(cls.description),
            sa.orm.defer(cls.perks),
            sa.orm.defer(cls.how_to_apply),
            sa.orm.defer(cls.hr_contact),
            sa.orm.defer(cls.company_logo),
            sa.orm.defer(cls.company_url),
            sa.orm.defer(cls.fullname),
            sa.orm.defer(cls.email),
            sa.orm.defer(cls.words),
            sa.orm.defer(cls.promocode),
            sa.orm.defer(cls.ipaddr),
            sa.orm.defer(cls.useragent),
            sa.orm.defer(cls.edit_key),
            sa.orm.defer(cls.email_verify_key),
            sa.orm.defer(cls.email_sent),
            sa.orm.defer(cls.email_verified),
            sa.orm.defer(cls.payment_value),
            sa.orm.defer(cls.payment_received),
            sa.orm.defer(cls.reviewer_id),
            sa.orm.defer(cls.review_datetime),
            sa.orm.defer(cls.review_comments),
            sa.orm.defer(cls.language),
            sa.orm.defer(cls.language_confidence),
            # These are defined below JobApplication
            sa.orm.defer(cls.new_applications),
            sa.orm.defer(cls.replied_applications),
            sa.orm.defer(cls.viewcounts_viewed),
            sa.orm.defer(cls.viewcounts_opened),
            sa.orm.defer(cls.viewcounts_applied),
            # sa.orm.defer(cls.pay_type),
            # sa.orm.defer(cls.pay_currency),
            # sa.orm.defer(cls.pay_cash_min),
            # sa.orm.defer(cls.pay_cash_max),
            # sa.orm.defer(cls.pay_equity_min),
            # sa.orm.defer(cls.pay_equity_max),
        ]

    def __repr__(self):
        return '<JobPost {hashid} "{headline}">'.format(
            hashid=self.hashid, headline=self.headline
        )

    def admin_is(self, user):
        if user is None:
            return False
        return user == self.user or bool(
            self.admins.options(sa.orm.load_only(JobPost.id))
            .filter_by(id=user.id)
            .count()
        )

    @property
    def expiry_date(self):
        return self.datetime + agelimit

    @property
    def after_expiry_date(self):
        return self.expiry_date + timedelta(days=1)

    # NEW = Posted within last 24 hours
    state.add_conditional_state(
        'NEW',
        state.PUBLIC,
        lambda jobpost: jobpost.datetime >= utcnow() - newlimit,
        label=('new', __("New!")),
    )
    # LISTED = Posted within last 30 days
    state.add_conditional_state(
        'LISTED',
        state.PUBLIC,
        lambda jobpost: jobpost.datetime >= utcnow() - agelimit,
        label=('listed', __("Listed")),
    )
    # OLD = Posted more than 30 days ago
    state.add_conditional_state(
        'OLD',
        state.PUBLIC,
        lambda jobpost: not jobpost.state.LISTED,
        label=('old', __("Old")),
    )
    # Checks if current user has the permission to confirm the jobpost
    state.add_conditional_state(
        'CONFIRMABLE',
        state.UNPUBLISHED,
        lambda jobpost: jobpost.current_permissions.edit,
        label=('confirmable', __("Confirmable")),
    )

    @state.transition(
        state.PUBLIC,
        state.WITHDRAWN,
        title=__("Withdraw"),
        message=__("This job post has been withdrawn"),
        type='danger',
    )
    def withdraw(self):
        self.closed_datetime = sa.func.utcnow()

    @state.transition(
        state.PUBLIC,
        state.CLOSED,
        title=__("Close"),
        message=__("This job post has been closed"),
        type='danger',
    )
    def close(self):
        self.closed_datetime = sa.func.utcnow()

    @state.transition(
        state.UNPUBLISHED_OR_MODERATED,
        state.CONFIRMED,
        title=__("Confirm"),
        message=__("This job post has been confirmed"),
        type='success',
    )
    def confirm(self):
        self.email_verified = True
        self.datetime = sa.func.utcnow()

    @state.transition(
        state.CLOSED,
        state.CONFIRMED,
        title=__("Reopen"),
        message=__("This job post has been reopened"),
        type='success',
    )
    def reopen(self):
        pass

    @state.transition(
        state.PUBLIC,
        state.SPAM,
        title=__("Mark as spam"),
        message=__("This job post has been marked as spam"),
        type='danger',
    )
    def mark_spam(self, reason, user):
        self.closed_datetime = sa.func.utcnow()
        self.review_datetime = sa.func.utcnow()
        self.review_comments = reason
        self.reviewer = user

    @state.transition(
        state.DRAFT,
        state.PENDING,
        title=__("Mark as pending"),
        message=__("This job post is awaiting email verification"),
        type='danger',
    )
    def mark_pending(self):
        pass

    @state.transition(
        state.PUBLIC,
        state.REJECTED,
        title=__("Reject"),
        message=__("This job post has been rejected"),
        type='danger',
    )
    def reject(self, reason, user):
        self.closed_datetime = sa.func.utcnow()
        self.review_datetime = sa.func.utcnow()
        self.review_comments = reason
        self.reviewer = user

    @state.transition(
        state.PUBLIC,
        state.MODERATED,
        title=__("Moderate"),
        message=__("This job post has been moderated"),
        type='primary',
    )
    def moderate(self, reason, user):
        self.closed_datetime = sa.func.utcnow()
        self.review_datetime = sa.func.utcnow()
        self.review_comments = reason
        self.reviewer = user

    def url_for(self, action='view', _external=False, **kwargs):
        if self.state.UNPUBLISHED and action in ('view', 'edit'):
            domain = None
        else:
            domain = self.email_domain

        # A/B test flag for permalinks
        if 'b' in kwargs:
            if kwargs['b'] is not None:
                kwargs['b'] = str(int(kwargs['b']))
            else:
                kwargs.pop('b')

        if action == 'view':
            return url_for(
                'jobdetail',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'reveal':
            return url_for(
                'revealjob',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'apply':
            return url_for(
                'applyjob',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'edit':
            return url_for(
                'editjob',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'withdraw':
            return url_for(
                'withdraw',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'close':
            return url_for(
                'close',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'viewstats':
            return url_for(
                'job_viewstats',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'related_posts':
            return url_for(
                'job_related_posts',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'reopen':
            return url_for(
                'reopen',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'moderate':
            return url_for(
                'moderatejob',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'pin':
            return url_for(
                'pinnedjob',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'reject':
            return url_for(
                'rejectjob',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'confirm':
            return url_for('confirm', hashid=self.hashid, _external=_external, **kwargs)
        elif action == 'logo':
            return url_for(
                'logoimage',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'confirm-link':
            return url_for(
                'confirm_email',
                hashid=self.hashid,
                domain=domain,
                key=self.email_verify_key,
                _external=True,
                **kwargs,
            )
        elif action == 'star':
            return url_for(
                'starjob',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'manage':
            return url_for(
                'managejob',
                hashid=self.hashid,
                domain=domain,
                _external=_external,
                **kwargs,
            )
        elif action == 'browse':
            if self.from_webmail_domain:
                return url_for(
                    'browse_by_email', md5sum=self.md5sum, _external=_external, **kwargs
                )
            else:
                return url_for(
                    'browse_by_domain',
                    domain=self.email_domain,
                    _external=_external,
                    **kwargs,
                )

    def permissions(self, user, inherited=None):
        perms = super().permissions(user, inherited)
        if self.state.PUBLIC:
            perms.add('view')
        if self.admin_is(user):
            if self.state.UNPUBLISHED:
                perms.add('view')
            perms.add('edit')
            perms.add('manage')
            perms.add('withdraw')
        return perms

    @property
    def from_webmail_domain(self):
        return (
            self.domain.is_webmail
            if self.domain
            else is_public_email_domain(self.email_domain, default=False)
        )

    @property
    def company_url_domain_zone(self):
        if not self.company_url:
            return ''
        else:
            r = tldextract.extract(self.company_url)
            return '.'.join([r.domain, r.suffix])

    @property
    def pays_cash(self):
        if self.pay_type is None:  # Legacy record from before `pay_type` was mandatory
            return True
        return (
            self.pay_type != PAY_TYPE.NOCASH
            and self.pay_cash_min is not None
            and self.pay_cash_max is not None
        )

    @property
    def pays_equity(self):
        return self.pay_equity_min is not None and self.pay_equity_max is not None

    def pay_label(self):
        if self.pay_type is None:
            return "NA"
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
                symbol = "₹"
            elif self.pay_currency == "USD":
                symbol = "$"
            elif self.pay_currency == "EUR":
                symbol = "€"
            elif self.pay_currency == "GBP":
                symbol = "£"
            else:
                symbol = "¤"

            if self.pay_cash_min == self.pay_cash_max:
                cash = symbol + number_abbreviate(self.pay_cash_min, indian)
            else:
                cash = (
                    symbol
                    + number_abbreviate(self.pay_cash_min, indian)
                    + "-"
                    + number_abbreviate(self.pay_cash_max, indian)
                )

            if suffix:
                cash = cash + " " + suffix

        if self.pays_equity:
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
        return Markup('\n').join(
            (
                Markup('<div>') + Markup(escape(self.headline)) + Markup('</div>'),
                Markup('<div>') + Markup(self.description) + Markup('</div>'),
                Markup('<div>') + Markup(self.perks) + Markup('</div>'),
            )
        )

    @staticmethod
    def viewcounts_key(jobpost_id):
        if isinstance(jobpost_id, (list, tuple)):
            return ['hasjob/viewcounts/%d' % post_id for post_id in jobpost_id]
        return 'hasjob/viewcounts/%d' % jobpost_id

    def uncache_viewcounts(self, key=None):
        cache_key = JobPost.viewcounts_key(self.id)
        if not key:
            redis_store.delete(cache_key)
        else:
            redis_store.hdel(cache_key, key)

    @cached_property
    def ab_impressions(self):
        results = {'NA': 0, 'A': 0, 'B': 0}
        counts = (
            db.session.query(
                JobImpression.bgroup.label('bgroup'), sa.func.count('*').label('count')
            )
            .filter(JobImpression.jobpost == self)
            .group_by(JobImpression.bgroup)
        )
        for row in counts:
            if row.bgroup is False:
                results['A'] = row.count
            elif row.bgroup is True:
                results['B'] = row.count
            else:
                results['NA'] = row.count
        return results

    @cached_property
    def ab_views(self):
        results = {
            # Conversions (cointoss=True, crosstoss=False)
            'C_NA': 0,
            'C_A': 0,
            'C_B': 0,
            # External (cointoss=False, crosstoss=True OR False [do sum])
            'E_NA': 0,
            'E_A': 0,
            'E_B': 0,
            # Cross toss (cointoss=True, crosstoss=True)
            'X_NA': 0,
            'X_A': 0,
            'X_B': 0,
        }
        counts = (
            db.session.query(
                JobViewSession.bgroup.label('bgroup'),
                JobViewSession.cointoss.label('cointoss'),
                JobViewSession.crosstoss.label('crosstoss'),
                sa.func.count('*').label('count'),
            )
            .filter(JobViewSession.jobpost == self)
            .group_by(
                JobViewSession.bgroup, JobViewSession.cointoss, JobViewSession.crosstoss
            )
        )

        for row in counts:
            if row.cointoss is True and row.crosstoss is False:
                prefix = 'C'
            elif row.cointoss is False:
                prefix = 'E'
            elif row.cointoss is True and row.crosstoss is True:
                prefix = 'X'
            if row.bgroup is False:
                results[prefix + '_A'] += row.count
            elif row.bgroup is True:
                results[prefix + '_B'] += row.count
            else:
                results[prefix + '_NA'] += row.count
        return results

    @property
    def sort_score(self):
        """
        Sort with a gravity of 1.8 using the HackerNews algorithm
        """
        viewcounts = self.viewcounts
        opened = int(viewcounts['opened'])
        applied = int(viewcounts['applied'])
        age = utcnow() - self.datetime
        hours = age.days * 24 + age.seconds // 3600

        return ((applied * 3) + (opened - applied)) / pow((hours + 2), 1.8)

    @cached_property  # For multiple accesses in a single request
    def viewstats(self):
        now = utcnow()
        delta = now - self.datetime
        hourly_stat_limit = 2  # days
        if delta.days < hourly_stat_limit:  # Less than {limit} days
            return 'h', viewstats_by_id_hour(self.id, hourly_stat_limit * 24)
        else:
            return 'd', viewstats_by_id_day(self.id, 30)

    def reports(self):
        if not self.flags:
            return []
        counts = {}
        for flag in self.flags:
            counts[flag.reportcode] = counts.setdefault(flag.reportcode, 0) + 1
        return [
            {'count': i[2], 'title': i[1]}
            for i in sorted((k.seq, k.title, v) for k, v in counts.items())
        ]


def viewstats_helper(jobpost_id, interval, limit, daybatch=False):
    post = JobPost.query.get(jobpost_id)
    if not post.datetime:
        return {}
    viewed = UserJobView.query.filter_by(jobpost_id=jobpost_id).all()
    opened = [v for v in viewed if v.applied is True]
    applied = (
        db.session.query(JobApplication.created_at)
        .filter_by(jobpost_id=jobpost_id)
        .all()
    )

    # Now batch them by size
    now = utcnow()
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
    cbuckets = batches * ['']

    interval_hour = interval // 3600
    # these are used as initial values for hourly stats
    # buckets are like "HH:00 - HH:00"

    # if now is 09:45, bucket ending hour will be 10:00
    to_datetime = now + timedelta(hours=1)
    # starting hour will be, 06:00, if interval is 4 hours
    from_datetime = to_datetime - timedelta(hours=interval_hour)

    for delta in range(batches):
        if daybatch:
            # here delta=0 at first, and last item is the latest date/hour
            cbuckets[batches - delta - 1] = format_datetime(
                (now - timedelta(days=delta)), 'd MMM'
            )
        else:
            from_hour = format_datetime(from_datetime, 'd MMM HH:00')
            to_hour = format_datetime(to_datetime, 'HH:00')
            cbuckets[batches - delta - 1] = "{from_hour} — {to_hour}".format(
                from_hour=from_hour, to_hour=to_hour
            )
            # if current bucket was 18:00-22:00, then
            # previous bucket becomes 14:00-18:00
            to_datetime = from_datetime
            from_datetime = to_datetime - timedelta(hours=interval_hour)

    for clist, source, attr in [
        (cviewed, viewed, 'created_at'),
        (copened, opened, 'updated_at'),
        (capplied, applied, 'created_at'),
    ]:
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
                    clist[int(itemdelta.days / interval)] += 1
                else:
                    clist[int(int(itemdelta.total_seconds()) / interval)] += 1
            except IndexError:
                # Server time got messed up. Ouch! Ignore for now.
                pass

    if limit and batches > limit:
        cviewed = cviewed[:limit]
        copened = copened[:limit]
        capplied = capplied[:limit]
        cbuckets = cbuckets[:limit]

    return {
        'max': max(
            [
                max(cviewed) if cviewed else 0,
                max(copened) if copened else 0,
                max(capplied) if capplied else 0,
            ]
        ),
        'length': max([len(cviewed), len(copened), len(capplied)]),
        'viewed': cviewed,
        'opened': copened,
        'applied': capplied,
        'buckets': cbuckets,
    }


@cache.memoize(timeout=3600)
def viewstats_by_id_hour(jobpost_id, limit=48):
    return viewstats_helper(jobpost_id, 4 * 3600, limit)  # 4 hours interval


@cache.memoize(timeout=86400)
def viewstats_by_id_day(jobpost_id, limit=30):
    return viewstats_helper(jobpost_id, 1, limit, daybatch=True)


jobpost_admin_table = sa.Table(
    'jobpost_admin',
    Model.metadata,
    *(
        make_timestamp_columns(timezone=True)
        + (
            sa.Column('user_id', None, sa.ForeignKey('user.id'), primary_key=True),
            sa.Column(
                'jobpost_id', None, sa.ForeignKey('jobpost.id'), primary_key=True
            ),
        )
    ),
)


class JobLocation(TimestampMixin, Model):
    __tablename__ = 'job_location'
    #: Job post we are tagging
    jobpost_id = sa.orm.mapped_column(
        None, sa.ForeignKey('jobpost.id'), primary_key=True, nullable=False
    )
    jobpost = relationship(
        JobPost, backref=backref('locations', cascade='all, delete-orphan')
    )
    #: Geonameid for this job post
    geonameid = sa.orm.mapped_column(
        sa.Integer, primary_key=True, nullable=False, index=True
    )
    primary = sa.orm.mapped_column(sa.Boolean, default=True, nullable=False)

    def __repr__(self):
        return '<JobLocation %d %s for job %s>' % (
            self.geonameid,
            'primary' if self.primary else 'secondary',
            self.jobpost.hashid,
        )


class UserJobView(TimestampMixin, Model):
    __tablename__ = 'userjobview'
    #: Job post that was seen
    jobpost_id = sa.orm.mapped_column(
        None, sa.ForeignKey('jobpost.id'), primary_key=True
    )
    jobpost = relationship(JobPost)
    #: User who saw this post
    user_id = sa.orm.mapped_column(
        None, sa.ForeignKey('user.id'), primary_key=True, index=True
    )
    user = relationship(User)
    #: Has the user viewed apply instructions?
    applied = sa.orm.mapped_column(sa.Boolean, default=False, nullable=False)

    @classmethod
    def get(cls, jobpost, user):
        return cls.query.get((jobpost.id, user.id))


class AnonJobView(Model):
    __tablename__ = 'anon_job_view'
    query_class = Query

    #: Job post that was seen
    jobpost_id = sa.orm.mapped_column(
        None, sa.ForeignKey('jobpost.id'), primary_key=True
    )
    jobpost = relationship(JobPost)
    #: User who saw this post
    anon_user_id = sa.orm.mapped_column(
        None, sa.ForeignKey('anon_user.id'), primary_key=True, index=True
    )
    anon_user = relationship(AnonUser)
    #: Timestamp
    created_at = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True),
        default=sa.func.utcnow(),
        nullable=False,
        index=True,
    )

    @classmethod
    def get(cls, jobpost, anon_user):
        return cls.query.get((jobpost.id, anon_user.id))


class JobImpression(TimestampMixin, Model):
    __tablename__ = 'job_impression'
    #: Datetime when this activity happened (which is likely much before it was written to the database)
    datetime = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True),
        default=sa.func.utcnow(),
        nullable=False,
        index=True,
    )
    #: Job post that was impressed
    jobpost_id = sa.orm.mapped_column(
        None, sa.ForeignKey('jobpost.id'), primary_key=True
    )
    jobpost = relationship(JobPost)
    #: Event session in which it was impressed
    event_session_id = sa.orm.mapped_column(
        None, sa.ForeignKey('event_session.id'), primary_key=True, index=True
    )
    event_session = relationship(EventSession)
    #: Whether it was pinned at any time in this session
    pinned = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False)
    #: Was this rendering in the B group of an A/B test? (null = no test conducted)
    bgroup = sa.orm.mapped_column(sa.Boolean, nullable=True)

    @classmethod
    def get(cls, jobpost, event_session):
        # See views.helper.save_impressions, which doesn't use this method and depends on
        # (jobpost_id, event_session_id) primary key order.
        return cls.query.get((jobpost.id, event_session.id))

    @classmethod
    def get_by_ids(cls, jobpost_id, event_session_id):
        return cls.query.get((jobpost_id, event_session_id))


class JobViewSession(TimestampMixin, Model):
    __tablename__ = 'job_view_session'
    #: Datetime indicates the time, impression has made
    datetime = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True),
        default=sa.func.utcnow(),
        nullable=False,
        index=True,
    )
    #: Job post that was impressed
    #: Event session in which jobpost was viewed
    #: This takes precedence as we'll be loading all instances
    #: matching the current session in each index request
    event_session_id = sa.orm.mapped_column(
        None, sa.ForeignKey('event_session.id'), primary_key=True
    )
    event_session = relationship(EventSession)
    #: Job post that was viewed
    jobpost_id = sa.orm.mapped_column(
        None, sa.ForeignKey('jobpost.id'), primary_key=True, index=True
    )
    jobpost = relationship(JobPost)
    #: Related impression
    impression = relationship(
        JobImpression,
        primaryjoin='''and_(
            JobViewSession.event_session_id == foreign(JobImpression.event_session_id),
            JobViewSession.jobpost_id == foreign(JobImpression.jobpost_id)
            )''',
        uselist=False,
        viewonly=True,
        backref='view',
    )
    #: Was this view in the B group of an A/B test? (null = no test conducted)
    bgroup = sa.orm.mapped_column(sa.Boolean, nullable=True)
    #: Was the bgroup assigned by coin toss or was it predetermined?
    cointoss = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False)
    #: Does this bgroup NOT match the impression's bgroup?
    crosstoss = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False)

    @classmethod
    def get(cls, event_session, jobpost):
        return cls.query.get((event_session.id, jobpost.id))

    @classmethod
    def get_by_ids(cls, event_session_id, jobpost_id):
        return cls.query.get((event_session_id, jobpost_id))


class JobApplication(BaseMixin, Model):
    __tablename__ = 'job_application'
    #: Hash id (to hide database ids)
    hashid = sa.orm.mapped_column(sa.String(40), nullable=False, unique=True)
    #: User who applied for this post
    # TODO: add unique=True
    user_id = sa.orm.mapped_column(
        None, sa.ForeignKey('user.id'), nullable=True, index=True
    )
    user = relationship(User, foreign_keys=user_id)
    #: Full name of the user (as it was at the time of the application)
    fullname = sa.orm.mapped_column(sa.Unicode(250), nullable=False)
    #: Job post they applied to
    jobpost_id = sa.orm.mapped_column(
        None, sa.ForeignKey('jobpost.id'), nullable=False, index=True
    )
    # jobpost relationship is below, outside the class definition
    #: User's email address
    email = sa.orm.mapped_column(sa.Unicode(80), nullable=False)
    #: User's phone number
    phone = sa.orm.mapped_column(sa.Unicode(80), nullable=False)
    #: User's message
    message = sa.orm.mapped_column(sa.UnicodeText, nullable=False)
    #: User opted-in to experimental features
    optin = sa.orm.mapped_column(sa.Boolean, default=False, nullable=False)
    #: Employer's response code
    _response = sa.orm.mapped_column(
        'response',
        sa.Integer,
        StateManager.check_constraint('response', EMPLOYER_RESPONSE),
        nullable=False,
        default=EMPLOYER_RESPONSE.NEW,
    )
    response = StateManager('_response', EMPLOYER_RESPONSE, doc="Employer's response")
    #: Employer's response message
    response_message = sa.orm.mapped_column(sa.UnicodeText, nullable=True)
    #: Bag of words, for spam analysis
    words = sa.orm.mapped_column(sa.UnicodeText, nullable=True)
    #: Jobpost admin who replied to this candidate
    replied_by_id = sa.orm.mapped_column(
        None, sa.ForeignKey('user.id'), nullable=True, index=True
    )
    replied_by = relationship(User, foreign_keys=replied_by_id)
    #: When they replied
    replied_at = sa.orm.mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)

    candidate_feedback = sa.orm.mapped_column(sa.SmallInteger, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.hashid is None:
            self.hashid = unique_long_hash()

    @response.transition(
        response.NEW,
        response.PENDING,
        title=__("Mark read"),
        message=__("This job application has been read"),
        type='success',
    )
    def mark_read(self):
        pass

    @response.transition(
        response.CAN_REPLY,
        response.REPLIED,
        title=__("Reply"),
        message=__("This job application has been replied to"),
        type='success',
    )
    def reply(self, message, user):
        self.response_message = message
        self.replied_by = user
        self.replied_at = sa.func.utcnow()

    @response.transition(
        response.CAN_REJECT,
        response.REJECTED,
        title=__("Reject"),
        message=__("This job application has been rejected"),
        type='danger',
    )
    def reject(self, message, user):
        self.response_message = message
        self.replied_by = user
        self.replied_at = sa.func.utcnow()

    @response.transition(
        response.CAN_IGNORE,
        response.IGNORED,
        title=__("Ignore"),
        message=__("This job application has been ignored"),
        type='danger',
    )
    def ignore(self):
        pass

    @response.transition(
        response.CAN_REPORT,
        response.FLAGGED,
        title=__("Report"),
        message=__("This job application has been reported"),
        type='danger',
    )
    def flag(self):
        pass

    @response.transition(
        response.FLAGGED,
        response.PENDING,
        title=__("Unflag"),
        message=__("This job application has been unflagged"),
        type='success',
    )
    def unflag(self):
        pass

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
                'rejected': 0,
            }
        date_min = self.created_at - timedelta(days=7)
        date_max = self.created_at + timedelta(days=7)
        grouped = JobApplication.response.group(
            JobApplication.query.filter(JobApplication.user == self.user)
            .filter(
                JobApplication.created_at > date_min,
                JobApplication.created_at < date_max,
            )
            .options(sa.orm.load_only(JobApplication.id))
        )
        counts = {k.label.name: len(v) for k, v in grouped.items()}
        counts['count'] = sum(counts.values())
        return counts

    def url_for(self, action='view', _external=False, **kwargs):
        domain = self.jobpost.email_domain
        if action == 'view':
            return url_for(
                'view_application',
                hashid=self.jobpost.hashid,
                domain=domain,
                application=self.hashid,
                _external=_external,
                **kwargs,
            )
        elif action == 'process':
            return url_for(
                'process_application',
                hashid=self.jobpost.hashid,
                domain=domain,
                application=self.hashid,
                _external=_external,
                **kwargs,
            )
        elif action == 'track-open':
            return url_for(
                'view_application_email_gif',
                hashid=self.jobpost.hashid,
                domain=domain,
                application=self.hashid,
                _external=_external,
                **kwargs,
            )


JobApplication.jobpost = relationship(
    JobPost,
    backref=backref(
        'applications',
        lazy='dynamic',
        order_by=(
            sa.case(
                {
                    EMPLOYER_RESPONSE.NEW: 0,
                    EMPLOYER_RESPONSE.PENDING: 1,
                    EMPLOYER_RESPONSE.IGNORED: 2,
                    EMPLOYER_RESPONSE.REPLIED: 3,
                    EMPLOYER_RESPONSE.REJECTED: 4,
                    EMPLOYER_RESPONSE.FLAGGED: 5,
                    EMPLOYER_RESPONSE.SPAM: 6,
                },
                value=JobApplication._response,
            ),
            sa.desc(JobApplication.created_at),
        ),
        cascade='all, delete-orphan',
    ),
)


JobPost.new_applications = sa.orm.column_property(
    sa.select(sa.func.count(JobApplication.id))
    .where(
        sa.and_(JobApplication.jobpost_id == JobPost.id, JobApplication.response.NEW)
    )
    .scalar_subquery()
)


JobPost.replied_applications = sa.orm.column_property(
    sa.select(sa.func.count(JobApplication.id))
    .where(
        sa.and_(
            JobApplication.jobpost_id == JobPost.id, JobApplication.response.REPLIED
        )
    )
    .scalar_subquery()
)


JobPost.viewcounts_viewed = sa.orm.column_property(
    sa.select(sa.func.count())
    .where(UserJobView.jobpost_id == JobPost.id)
    .scalar_subquery()
)


JobPost.viewcounts_opened = sa.orm.column_property(
    sa.select(sa.func.count())
    .where(sa.and_(UserJobView.jobpost_id == JobPost.id, UserJobView.applied.is_(True)))
    .scalar_subquery()
)


JobPost.viewcounts_applied = sa.orm.column_property(
    sa.select(sa.func.count(JobApplication.id))
    .where(JobApplication.jobpost_id == JobPost.id)
    .scalar_subquery()
)


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


create_jobpost_search_trigger = sa.DDL(
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
    '''
)

event.listen(
    JobPost.__table__,
    'after_create',
    create_jobpost_search_trigger.execute_if(dialect='postgresql'),
)
