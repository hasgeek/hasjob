# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from coaster.sqlalchemy import StateManager
from ..utils import random_long_key
from . import db, BaseMixin, LabeledEnum, User, AnonUser

__all__ = ['JobPostSubscription', 'JobPostAlert', 'jobpost_alert_table']


class EMAIL_FREQUENCY(LabeledEnum):
    DAILY = (1, 'Daily')
    WEEKLY = (7, 'Weekly')


class JobPostSubscription(BaseMixin, db.Model):
    __tablename__ = 'jobpost_subscription'

    filterset_id = db.Column(None, db.ForeignKey('filterset.id'), nullable=False)
    filterset = db.relationship('Filterset', backref=db.backref('subscriptions', lazy='dynamic'))
    email = db.Column(db.Unicode(254), nullable=True)
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=True, index=True)
    user = db.relationship(User)
    anon_user_id = db.Column(None, db.ForeignKey('anon_user.id'), nullable=True, index=True)
    anon_user = db.relationship(AnonUser)

    active = db.Column(db.Boolean, nullable=False, default=False, index=True)
    email_verify_key = db.Column(db.String(40), nullable=True, default=random_long_key, unique=True)
    unsubscribe_key = db.Column(db.String(40), nullable=True, default=random_long_key, unique=True)
    subscribed_at = db.Column(db.DateTime, nullable=False, default=db.func.utcnow())
    email_verified_at = db.Column(db.DateTime, nullable=True, index=True)
    unsubscribed_at = db.Column(db.DateTime, nullable=True)

    _email_frequency = db.Column('email_frequency',
        db.Integer, StateManager.check_constraint('email_frequency', EMAIL_FREQUENCY),
        default=EMAIL_FREQUENCY.DAILY, nullable=True)
    email_frequency = StateManager('_email_frequency', EMAIL_FREQUENCY, doc="Email frequency")

    __table_args__ = (db.UniqueConstraint('filterset_id', 'email'),
        db.CheckConstraint(
            db.case([(user_id != None, 1)], else_=0) + db.case([(anon_user_id != None, 1)], else_=0) <= 1,  # NOQA
            name='jobpost_subscription_user_id_or_anon_user_id'))

    @classmethod
    def get(cls, filterset, email):
        return cls.query.filter(cls.filterset == filterset, cls.email == email).one_or_none()

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

    def is_right_time_to_send_alert(self):
        """
        Checks if it's the right time to send this subscriber an alert.
        For now, the time at which the subscription was initiated is taken as the "preferred time" and
        uses a tolerance of 30 minutes
        """
        return ((datetime.utcnow() - self.subscribed_at.time()).total_seconds()/60) <= 30

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
    sent_at = db.Column(db.DateTime, nullable=True)
    failed_at = db.Column(db.DateTime, nullable=True)
    fail_reason = db.Column(db.Unicode(255), nullable=True)

    def register_delivery(self):
        self.sent_at = db.func.utcnow()

    def register_failure(self, fail_reason):
        self.failed_at = db.func.utcnow()
        self.fail_reason = fail_reason
