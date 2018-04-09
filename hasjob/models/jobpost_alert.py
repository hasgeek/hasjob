# -*- coding: utf-8 -*-

from coaster.sqlalchemy import StateManager
from ..utils import random_long_key
from . import db, BaseMixin, LabeledEnum

__all__ = ['JobPostSubscription', 'JobPostAlert', 'jobpost_alert_table']


class EMAIL_FREQUENCY(LabeledEnum):
    DAILY = (1, 'Daily')
    WEEKLY = (7, 'Weekly')
    MONTHLY = (30, 'Monthly')


class JobPostSubscription(BaseMixin, db.Model):
    __tablename__ = 'jobpost_subscription'
    __table_args__ = (db.UniqueConstraint('user_id', 'user_type', 'filterset_id'),)

    user_id = db.Column(None, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('subscriptions',
        lazy='dynamic', cascade='all, delete-orphan'))
    user_type = db.Column(db.Unicode(8), nullable=False, default=u'User')
    filterset_id = db.Column(None, db.ForeignKey('filterset.id'))
    filterset = db.relationship('Filterset', backref=db.backref('subscriptions',
        lazy='dynamic'))
    active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    email = db.Column(db.Boolean, nullable=True, default=True, index=True)
    _email_frequency = db.Column('email_frequency',
            db.Integer, StateManager.check_constraint('email_frequency', EMAIL_FREQUENCY),
        default=EMAIL_FREQUENCY.DAILY, nullable=True)
    email_frequency = StateManager('_email_frequency', EMAIL_FREQUENCY, doc="Email frequency")
    email_verify_key = db.Column(db.String(40), nullable=True, default=random_long_key)
    email_verified_at = db.Column(db.DateTime, nullable=True, index=True)
    deactivated_at = db.Column(db.DateTime, nullable=True)
    reactivated_at = db.Column(db.DateTime, nullable=True)

    def verify_email(self):
        self.email_verified_at = db.func.utcnow()

    def deactivate(self):
        self.active = False
        self.deactivated = db.func.utcnow()

    def reactivate(self):
        if self.email_verified:
            self.active = True
            self.reactivated_at = db.func.utcnow()


jobpost_alert_table = db.Table('jobpost_jobpost_alert', db.Model.metadata,
    db.Column('jobpost_id', None, db.ForeignKey('jobpost.id'), primary_key=True),
    db.Column('jobpost_alert_id', None, db.ForeignKey('jobpost_alert.id'), primary_key=True),
    db.Column('created_at', db.DateTime, nullable=False, default=db.func.utcnow())
)


class JobPostAlert(BaseMixin, db.Model):
    __tablename__ = 'jobpost_alert'

    jobpost_subscription_id = db.Column(None, db.ForeignKey('jobpost_subscription.id'),
        index=True)
    jobpost_subscription = db.relationship(JobPostSubscription, backref=db.backref('alerts',
        lazy='dynamic', cascade='all, delete-orphan'))
    jobposts = db.relationship('JobPost', lazy='dynamic', secondary=jobpost_alert_table,
        backref=db.backref('alerts', lazy='dynamic'))
    sent_at = db.Column(db.DateTime, nullable=False, default=db.func.utcnow())
