# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import event
from sqlalchemy.ext.associationproxy import association_proxy
from werkzeug import cached_property
from coaster.utils import buid, LabeledEnum
from baseframe import __
from . import db, TimestampMixin, BaseMixin
from .user import User, AnonUser, EventSession
from .jobpost import JobPost, JobImpression


class BID_TYPE(LabeledEnum):
    PIN = (0, __("Pin"))


bid_event_session_table = db.Table('bid_event_session', db.Model.metadata,
    db.Column('bid_id', None, db.ForeignKey('bid.id'), primary_key=True),
    db.Column('event_session_id', None, db.ForeignKey('event_session.id'), primary_key=True, index=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
    )


class Bid(BaseMixin, db.Model):
    """
    A bid to have a post promoted against multiple criteria.
    """
    __tablename__ = 'bid'

    #: Bid type
    bid_type = db.Column(db.SmallInteger, nullable=False, default=BID_TYPE.PIN)
    #: URL name
    name = db.Column(db.Unicode(22), nullable=False, default=buid, unique=True)
    #: User who created this bid
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship(User, backref='bids')
    #: The jobpost this bid is for
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), nullable=False)
    jobpost = db.relationship(JobPost, backref='bids')

    #: When does this bid start from?
    start_at = db.Column(db.DateTime, nullable=False, index=True)
    #: When does it end?
    end_at = db.Column(db.DateTime, nullable=False, index=True)
    #: Is this bid live?
    public = db.Column(db.Boolean, nullable=False, default=False)
    #: The value of this bid (highest matching criteria will be the bid winner)
    value = db.Column(db.Integer, nullable=False)
    #: Available credit balance (must be greater than zero to be selected; updated in batch job)
    balance = db.Column(db.Integer, nullable=False)

    # Targeting criteria

    #: Quick lookup locations to consider this bid in
    geonameids = association_proxy('locations', 'geonameid',
        creator=lambda l: BidLocation(geonameid=l))
    #: Is this bid location-based?
    geotargeted = db.Column(db.Boolean, nullable=False, default=False)

    # Impressions caused by this bid (foreign key is in JobImpression)
    impressions = db.relationship(JobImpression, backref='bid')

    # Sessions this bid has been impressed in
    session_impressions = db.relationship(EventSession, secondary=bid_event_session_table, backref='bid_impressions',
        order_by=bid_event_session_table.c.created_at, lazy='dynamic')

    __table_args__ = (db.CheckConstraint('end_at > start_at', name='bid_start_at_end_at'),)

    @db.validates('value')
    def _set_value(self, key, value):
        assert value > 0
        return value

    @db.validates('start_at')
    def _set_start_at(self, key, value):
        if self.jobpost:
            value = max(value, self.jobpost.datetime)
        return value

    @db.validates('end_at')
    def _set_end_at(self, key, value):
        if self.jobpost:
            value = min(value, self.jobpost.expiry_date)
        return value

    @property
    def is_live(self):
        now = datetime.utcnow()
        return self.public and self.start_at <= now and self.end_at >= now


@event.listens_for(Bid, 'before_update')
@event.listens_for(Bid, 'before_insert')
def _set_geotargeted(mapper, connection, target):
    if target.geonameids:
        target.geotargeted = True
    else:
        target.geotargeted = False


class BidLocation(TimestampMixin, db.Model):
    """
    Location tag for pinning bids
    """
    __tablename__ = 'bid_location'
    #: Bid we are referencing
    bid_id = db.Column(None, db.ForeignKey('bid.id'), primary_key=True, nullable=False)
    bid = db.relationship(Bid, backref=db.backref('locations', cascade='all, delete-orphan'))

    #: Geonameid for this bid
    geonameid = db.Column(db.Integer, primary_key=True, nullable=False, index=True)

    def __repr__(self):
        return '<BidLocation %d for bid %s>' % (self.geonameid, self.bid.name)


class UserBidImpression(TimestampMixin, db.Model):
    """
    Track users who've viewed an impression as a result of a bid.
    """
    __tablename__ = 'user_bid_impression'
    #: Bid that resulted in an impression
    bid_id = db.Column(None, db.ForeignKey('bid.id'), nullable=False, primary_key=True)
    bid = db.relationship(Bid,
        backref=db.backref('user_impressions', lazy='dynamic', order_by='UserBidImpression.created_at.desc()'))
    #: User who saw the impression
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=False, primary_key=True, index=True)
    user = db.relationship(User, backref=db.backref('bid_impressions', lazy='dynamic'))

    #: Number of sessions in which the user was shown this (updated via a background job)
    session_count = db.Column(db.Integer, nullable=False, default=0)

    @classmethod
    def get(cls, bid, user):
        return cls.query.get((bid.id, user.id))

    @classmethod
    def get_by_ids(cls, bid_id, user_id):
        return cls.query.get((bid_id, user_id))

    @classmethod
    def exists(cls, bid, user):
        return cls.query.filter_by(bid=bid, user=user).notempty()


class AnonBidImpression(TimestampMixin, db.Model):
    """
    Track anon users who've viewed an impression as a result of a bid.
    """
    __tablename__ = 'anon_bid_impression'
    #: Bid that resulted in an impression
    bid_id = db.Column(None, db.ForeignKey('bid.id'), nullable=False, primary_key=True)
    bid = db.relationship(Bid,
        backref=db.backref('anon_impressions', lazy='dynamic', order_by='AnonBidImpression.created_at.desc()'))
    #: User who saw the impression
    anon_user_id = db.Column(None, db.ForeignKey('anon_user.id'), nullable=False, primary_key=True, index=True)
    anon_user = db.relationship(AnonUser, backref=db.backref('bid_impressions', lazy='dynamic'))

    #: Number of sessions in which the user was shown this (updated via a background job)
    session_count = db.Column(db.Integer, nullable=False, default=0)

    @classmethod
    def get(cls, bid, anon_user):
        return cls.query.get((bid.id, anon_user.id))

    @classmethod
    def get_by_ids(cls, bid_id, anon_user_id):
        return cls.query.get((bid_id, anon_user_id))

    @classmethod
    def exists(cls, bid, anon_user):
        return cls.query.filter_by(bid=bid, anon_user=anon_user).notempty()


class CreditTransaction(BaseMixin, db.Model):
    """
    Record of credits transferred into or out of a user's account
    """
    __tablename__ = 'credit_transaction'

    #: Datetime when the transaction happened
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    #: User who has credits
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship(User, foreign_keys=[user_id], backref='credit_transactions')
    #: Site admin who granted credits (if a grant)
    granted_by_id = db.Column(None, db.ForeignKey('user.id'), nullable=True)
    granted_by = db.relationship(User, foreign_keys=[granted_by_id], backref='credit_grants')
    #: Count of credits transferred (positive = user's balance increased, negative = decreased)
    value = db.Column(db.Integer, nullable=False)
    #: Description of credit transaction
    memo = db.Column(db.Unicode(250), nullable=False)

    #: Bid associated with this transaction (if applicable)
    bid_id = db.Column(None, db.ForeignKey('bid.id'), nullable=True)
    bid = db.relationship(Bid, backref='transactions')

    @classmethod
    def get_all(cls, user):
        """Return all transactions for a given user, ordered by date"""
        return cls.query.filter_by(user=user).order_by(cls.datetime)

    @classmethod
    def balance_for(cls, user):
        """Credit balance for the given user"""
        return db.session.query(
            db.func.sum(CreditTransaction.value).label('balance')
            ).filter_by(user=user).first().balance or 0


def _credit_balance(self):
    """User's credit balance"""
    return CreditTransaction.balance_for(self)

User.credit_balance = cached_property(_credit_balance)
