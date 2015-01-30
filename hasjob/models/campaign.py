# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy.orm import deferred
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.orderinglist import ordering_list
from flask import request
from coaster.utils import LabeledEnum
from coaster.sqlalchemy import JsonDict
from baseframe import __
from . import db, TimestampMixin, BaseNameMixin, BaseScopedNameMixin, make_timestamp_columns
from .user import User
from .board import Board

__all__ = ['CAMPAIGN_POSITION', 'CAMPAIGN_ACTION', 'BANNER_LOCATION',
    'Campaign', 'CampaignLocation', 'CampaignAction', 'CampaignView', 'CampaignUserAction']

_marker = object()


board_campaign_table = db.Table('campaign_board', db.Model.metadata,
    *(make_timestamp_columns() + (
        db.Column('board_id', None, db.ForeignKey('board.id'), primary_key=True),
        db.Column('campaign_id', None, db.ForeignKey('campaign.id'), primary_key=True, index=True),
    )))


class CAMPAIGN_POSITION(LabeledEnum):
    HEADER = (0, __("Header"))                    # Shown in the header of all pages
    SIDEBAR = (1, __("Sidebar"))                  # Shown in the sidebar of jobs
    BEFOREPOST = (2, __("Before posting a job"))  # Upsell something before the employer posts a job
    AFTERPOST = (3, __("After posting a job"))    # Shown in the body after the employer posts a job


class CAMPAIGN_ACTION(LabeledEnum):
    LINK = ('L', __("Follow link"))
    RSVP_Y = ('Y', __("RSVP Yes"))
    RSVP_N = ('N', __("RSVP No"))
    RSVP_M = ('M', __("RSVP Maybe"))
    FORM = ('F', __("Show a form"))
    DISMISS = ('D', __("Dismiss campaign"))


class BANNER_LOCATION(LabeledEnum):
    TOP = (0, __("Top"))
    RIGHT = (1, __("Right"))
    BOTTOM = (2, __("Bottom"))
    LEFT = (3, __("Left"))


class Campaign(BaseNameMixin, db.Model):
    """
    A campaign runs in the header or sidebar of Hasjob's pages and prompts the user towards some action.
    Unlike announcements, campaigns sit outside the content area of listings.
    """
    __tablename__ = 'campaign'

    # Campaign metadata columns

    #: User who created this campaign
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship(User, backref='campaigns')
    #: When does this campaign go on air?
    start_at = db.Column(db.DateTime, nullable=False)
    #: When does it go off air?
    end_at = db.Column(db.DateTime, nullable=False)
    #: Is this campaign live?
    public = db.Column(db.Boolean, nullable=False, default=False)
    #: Position to display campaign in
    position = db.Column(db.SmallInteger, nullable=False, default=CAMPAIGN_POSITION.HEADER)
    #: Boards to run this campaign on
    boards = db.relationship(Board, secondary=board_campaign_table)
    #: Quick lookup locations to run this campaign in
    geonameids = association_proxy('locations', 'geonameid', creator=lambda l: CampaignLocation(geonameid=l))
    #: Priority, lower = less priority
    priority = db.Column(db.Integer, nullable=False, default=0)

    # Campaign content columns

    #: Subject (user-facing, unlike the title)
    subject = db.Column(db.Unicode(250), nullable=True)
    #: Call to action text (for header campaigns)
    blurb = db.Column(db.UnicodeText, nullable=False, default=u'')
    #: Full text (for read more click throughs)
    description = db.Column(db.UnicodeText, nullable=False, default=u'')
    #: Banner image
    banner_image = db.Column(db.Unicode(250), nullable=True)
    #: Banner location
    banner_location = db.Column(db.SmallInteger, nullable=False, default=BANNER_LOCATION.TOP)

    @property
    def content(self):
        """Form helper method"""
        return self

    def __repr__(self):
        return '<Campaign %s "%s" %s:%s>' % (
            self.name, self.title, self.start_at.strftime('%Y-%m-%d'), self.end_at.strftime('%Y-%m-%d'))

    @property
    def is_live(self):
        now = datetime.utcnow()
        return self.public and self.start_at <= now and self.end_at >= now

    def useractions(self, user):
        if user is not None:
            return dict([(cua.action.name, cua) for cua in CampaignUserAction.query.filter_by(user=user).filter(
                CampaignUserAction.action_id.in_([a.id for a in self.actions])).all()])
        else:
            return {}

    def view_for(self, user):
        if user:
            return CampaignView.get(campaign=self, user=user)

    @classmethod
    def for_context(cls, position, user=None, board=None, post=None):
        """
        Return a campaign suitable for this board and post
        """
        now = datetime.utcnow()
        basequery = cls.query.filter(
            cls.start_at <= now, cls.end_at >= now, cls.position == position).filter_by(public=True)
        if board:
            basequery = basequery.filter(cls.boards.any(id=board.id))

        # TODO: This won't work for campaigns with no location, so defer for later
        # if post and post.geonameids:
        #     basequery = basequery.join(CampaignLocation).filter(CampaignLocation.geonameid.in_(post.geonameids))
        return basequery.order_by(cls.priority.desc()).first()

    @classmethod
    def all(cls):
        return cls.query.order_by('start_at desc, priority desc').all()

    @classmethod
    def get(cls, name):
        return cls.query.filter_by(name=name).one_or_none()


class CampaignLocation(TimestampMixin, db.Model):
    """
    Location tag for campaigns
    """
    __tablename__ = 'campaign_location'
    #: Campaign we are referencing
    campaign_id = db.Column(None, db.ForeignKey('campaign.id'), primary_key=True, nullable=False)
    campaign = db.relationship(Campaign, backref=db.backref('locations', cascade='all, delete-orphan'))

    #: Geonameid for this campaign
    geonameid = db.Column(db.Integer, primary_key=True, nullable=False, index=True)

    def __repr__(self):
        return '<CampaignLocation %d for campaign %s>' % (self.geonameid, self.campaign.name)


class CampaignAction(BaseScopedNameMixin, db.Model):
    """
    Actions available to a user in a campaign
    """
    __tablename__ = 'campaign_action'
    #: Campaign
    campaign_id = db.Column(None, db.ForeignKey('campaign.id'), nullable=False)
    campaign = db.relationship(Campaign,
        backref=db.backref('actions', cascade='all, delete-orphan',
            order_by='CampaignAction.seq',
            collection_class=ordering_list('seq')))
    parent = db.synonym('campaign')
    #: Sequence number
    seq = db.Column(db.Integer, nullable=False, default=0)
    #: Is this action live?
    public = db.Column(db.Boolean, nullable=False, default=False)
    #: Action type
    type = db.Column(db.Enum(*CAMPAIGN_ACTION.keys(), name='campaign_action_type_enum'), nullable=False,
        default=CAMPAIGN_ACTION)
    #: Action category (for buttons)
    category = db.Column(db.Unicode(20), nullable=False, default=u'default')
    #: Icon to accompany text
    icon = db.Column(db.Unicode(20), nullable=True)
    #: Target link (for follow link actions; blank = ?)
    link = deferred(db.Column(db.Unicode(250), nullable=True))
    #: Form
    form = deferred(db.Column(JsonDict, nullable=False, server_default='{}'))
    #: Post action message
    message = db.Column(db.UnicodeText, nullable=False, default=u'')

    __table_args__ = (db.UniqueConstraint('campaign_id', 'name'),)

    @classmethod
    def get(cls, campaign, name):
        return cls.query.filter_by(campaign=campaign, name=name).one_or_none()


class CampaignView(TimestampMixin, db.Model):
    """
    Track users who've viewed a campaign
    """
    __tablename__ = 'campaign_view'
    #: Campaign
    campaign_id = db.Column(None, db.ForeignKey('campaign.id'), nullable=False, primary_key=True)
    campaign = db.relationship(Campaign, backref=db.backref('views', lazy='dynamic',
        order_by='CampaignView.created_at.desc()'))
    #: User who saw this campaign
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=False, primary_key=True)
    user = db.relationship(User, backref=db.backref('campaign_views', lazy='dynamic'))
    #: User dismissed this campaign. Don't show it
    dismissed = db.Column(db.Boolean, nullable=False, default=False)

    @classmethod
    def get(cls, campaign, user):
        return cls.query.get((campaign.id, user.id))

    @classmethod
    def exists(cls, campaign, user):
        return cls.query.filter_by(campaign=campaign, user=user).notempty()


class UserActionFormData(object):
    """
    Form data access helper for campaign user actions
    """
    def __init__(self, data):
        self.__dict__['_data'] = data

    def __getattr__(self, attr, default=_marker):
        if default is _marker:
            try:
                return self._data[attr]
            except KeyError:
                raise AttributeError(attr)
        else:
            return self._data.get(attr, default)

    def __setattr__(self, attr, value):
        self._data[attr] = value


class CampaignUserAction(TimestampMixin, db.Model):
    """
    Track the actions users undertook (could be more than one)
    """
    __tablename__ = 'campaign_user_action'
    #: Action the user selected
    action_id = db.Column(None, db.ForeignKey('campaign_action.id'), primary_key=True)
    action = db.relationship(CampaignAction,
        backref=db.backref('useractions', cascade='all, delete-orphan', lazy='dynamic',
            order_by='CampaignUserAction.created_at.desc()'))
    #: User who performed an action, null if anonymous
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=False, primary_key=True, index=True)
    user = db.relationship(User, backref=db.backref('campaign_useractions', lazy='dynamic'))
    #: User's IP address
    ipaddr = db.Column(db.String(45), nullable=True, default=lambda: request and request.environ['REMOTE_ADDR'])
    #: User's browser
    useragent = db.Column(db.Unicode(250), nullable=True, default=lambda: request and request.user_agent.string)
    #: Data the user submitted
    data = deferred(db.Column(JsonDict, nullable=False, server_default='{}'))

    @property
    def formdata(self):
        return UserActionFormData(self.data)

    @classmethod
    def get(cls, action, user):
        return cls.query.get((action.id, user.id))
