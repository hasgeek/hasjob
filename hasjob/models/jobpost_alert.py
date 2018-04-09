# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
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
    __table_args__ = (db.UniqueConstraint('filterset_id', 'email'),)

    filterset_id = db.Column(None, db.ForeignKey('filterset.id'), nullable=False)
    filterset = db.relationship('Filterset', backref=db.backref('subscriptions',
        lazy='dynamic'))
    email = db.Column(db.Unicode(254), nullable=False)

    active = db.Column(db.Boolean, nullable=False, default=False, index=True)
    email_verify_key = db.Column(db.String(40), nullable=True, default=random_long_key, unique=True)
    unsubscribe_key = db.Column(db.String(40), nullable=True, default=random_long_key, unique=True)
    email_verified_at = db.Column(db.DateTime, nullable=True, index=True)
    unsubscribed_at = db.Column(db.DateTime, nullable=True)

    _email_frequency = db.Column('email_frequency',
            db.Integer, StateManager.check_constraint('email_frequency', EMAIL_FREQUENCY),
        default=EMAIL_FREQUENCY.DAILY, nullable=True)
    email_frequency = StateManager('_email_frequency', EMAIL_FREQUENCY, doc="Email frequency")

    def verify_email(self):
        self.active = True
        self.email_verified_at = db.func.utcnow()

    def unsubscribe(self):
        self.active = False
        self.unsubscribed_at = db.func.utcnow()

    @classmethod
    def get_active_subscriptions(cls):
        return cls.query.filter(cls.active == True, cls.email_verified_at != None)

    def has_recent_alert(self):
        return JobPostAlert.query.filter(
            JobPostAlert.jobpost_subscription == self,
            JobPostAlert.sent_at >= datetime.utcnow() - timedelta(days=self.email_frequency.value)
        ).order_by('created_at desc').notempty()


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
