# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import event
from sqlalchemy.orm import deferred
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.orderinglist import ordering_list
from flask import request, Markup, url_for
from coaster.utils import LabeledEnum
from coaster.sqlalchemy import JsonDict
from baseframe import __
from baseframe.forms import Form
from . import db, TimestampMixin, BaseNameMixin, BaseScopedNameMixin, make_timestamp_columns
from .user import User, AnonUser, EventSession
from .board import Board
from .flags import UserFlags, UserFlag

__all__ = ['CAMPAIGN_POSITION', 'CAMPAIGN_ACTION', 'BANNER_LOCATION',
    'Campaign', 'CampaignLocation', 'CampaignAction', 'CampaignView', 'CampaignAnonView',
    'CampaignUserAction', 'CampaignAnonUserAction', 'campaign_event_session_table']

_marker = object()


board_campaign_table = db.Table('campaign_board', db.Model.metadata,
    *(make_timestamp_columns() + (
        db.Column('board_id', None, db.ForeignKey('board.id'), primary_key=True),
        db.Column('campaign_id', None, db.ForeignKey('campaign.id'), primary_key=True, index=True),
    )))


campaign_event_session_table = db.Table('campaign_event_session', db.Model.metadata,
    db.Column('campaign_id', None, db.ForeignKey('campaign.id'), primary_key=True),
    db.Column('event_session_id', None, db.ForeignKey('event_session.id'), primary_key=True, index=True),
    db.Column('created_at', db.DateTime, nullable=False, default=db.func.utcnow())
    )


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
    start_at = db.Column(db.DateTime, nullable=False, index=True)
    #: When does it go off air?
    end_at = db.Column(db.DateTime, nullable=False, index=True)
    #: Is this campaign live?
    public = db.Column(db.Boolean, nullable=False, default=False)
    #: Position to display campaign in
    position = db.Column(db.SmallInteger, nullable=False, default=CAMPAIGN_POSITION.HEADER)
    #: Boards to run this campaign on
    boards = db.relationship(Board, secondary=board_campaign_table)
    #: Quick lookup locations to run this campaign in
    geonameids = association_proxy('locations', 'geonameid', creator=lambda l: CampaignLocation(geonameid=l))
    #: Is this campaign location-based?
    geotargeted = db.Column(db.Boolean, nullable=False, default=False)
    #: Is a user required? None = don't care, True = user required, False = no user
    user_required = db.Column(db.Boolean, nullable=True, default=None)
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

    # Flags
    flag_is_new_since_day = db.Column(db.Boolean, nullable=True)
    flag_is_new_since_month = db.Column(db.Boolean, nullable=True)
    flag_is_not_new = db.Column(db.Boolean, nullable=True)

    flag_is_candidate_alltime = db.Column(db.Boolean, nullable=True)
    flag_is_candidate_day = db.Column(db.Boolean, nullable=True)
    flag_is_candidate_month = db.Column(db.Boolean, nullable=True)
    flag_is_candidate_past = db.Column(db.Boolean, nullable=True)

    flag_has_jobapplication_response_alltime = db.Column(db.Boolean, nullable=True)
    flag_has_jobapplication_response_day = db.Column(db.Boolean, nullable=True)
    flag_has_jobapplication_response_month = db.Column(db.Boolean, nullable=True)
    flag_has_jobapplication_response_past = db.Column(db.Boolean, nullable=True)

    flag_is_employer_alltime = db.Column(db.Boolean, nullable=True)
    flag_is_employer_day = db.Column(db.Boolean, nullable=True)
    flag_is_employer_month = db.Column(db.Boolean, nullable=True)
    flag_is_employer_past = db.Column(db.Boolean, nullable=True)

    flag_has_jobpost_unconfirmed_alltime = db.Column(db.Boolean, nullable=True)
    flag_has_jobpost_unconfirmed_day = db.Column(db.Boolean, nullable=True)
    flag_has_jobpost_unconfirmed_month = db.Column(db.Boolean, nullable=True)

    flag_has_responded_candidate_alltime = db.Column(db.Boolean, nullable=True)
    flag_has_responded_candidate_day = db.Column(db.Boolean, nullable=True)
    flag_has_responded_candidate_month = db.Column(db.Boolean, nullable=True)
    flag_has_responded_candidate_past = db.Column(db.Boolean, nullable=True)

    flag_is_new_lurker_within_day = db.Column(db.Boolean, nullable=True)
    flag_is_new_lurker_within_month = db.Column(db.Boolean, nullable=True)
    flag_is_lurker_since_past = db.Column(db.Boolean, nullable=True)
    flag_is_lurker_since_alltime = db.Column(db.Boolean, nullable=True)
    flag_is_inactive_since_day = db.Column(db.Boolean, nullable=True)
    flag_is_inactive_since_month = db.Column(db.Boolean, nullable=True)

    # Sessions this campaign has been viewed in
    session_views = db.relationship(EventSession, secondary=campaign_event_session_table, backref='campaign_views',
        order_by=campaign_event_session_table.c.created_at, lazy='dynamic')

    __table_args__ = (db.CheckConstraint('end_at > start_at', name='campaign_start_at_end_at'),)

    @property
    def content(self):
        """Form helper method"""
        return self

    @property
    def flags(self):
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

    def view_for(self, user=None, anon_user=None):
        if user:
            return CampaignView.get(campaign=self, user=user)
        elif anon_user:
            return CampaignAnonView.get(campaign=self, anon_user=anon_user)

    def subject_for(self, user):
        return self.subject.format(user=user)

    def blurb_for(self, user):
        return Markup(self.blurb).format(user=user)

    def description_for(self, user):
        return Markup(self.description).format(user=user)

    def estimated_reach(self):
        """
        Returns the number of users this campaign could potentially reach (assuming users are all active)
        """
        plus_userids = set()
        minus_userids = set()
        for flag in Campaign.supported_flags:
            setting = getattr(self, 'flag_' + flag)
            if setting is True or setting is False:
                query = getattr(UserFlags, flag).user_ids()
            if setting is True:
                userids = set(query.all())
                if plus_userids:
                    plus_userids = plus_userids.intersection(userids)
                else:
                    plus_userids = userids
            elif setting is False:
                userids = set(db.session.query(~User.id.in_(query)).all())
                if minus_userids:
                    minus_userids = minus_userids.union(userids)
                else:
                    minus_userids = userids
        if not plus_userids and not minus_userids:
            return None
        return len(plus_userids - minus_userids)

    def form(self):
        """Convenience method for action form CSRF"""
        return Form()

    @classmethod
    def for_context(cls, position, board=None, user=None, anon_user=None, geonameids=None):
        """
        Return a campaign suitable for this board, user and locations (as geonameids).
        """
        now = datetime.utcnow()
        basequery = cls.query.filter(
            cls.start_at <= now, cls.end_at >= now, cls.position == position).filter_by(public=True)

        if board:
            basequery = basequery.filter(cls.boards.any(id=board.id))

        if user:
            # Look for campaigns that don't target by user or require a user
            basequery = basequery.filter(db.or_(
                cls.user_required == None, cls.user_required == True))  # NOQA
        else:
            # Look for campaigns that don't target by user or require no user
            basequery = basequery.filter(db.or_(
                cls.user_required == None, cls.user_required == False))  # NOQA

        if geonameids:
            basequery = basequery.filter(db.or_(
                cls.geotargeted == False,
                db.and_(
                    cls.geotargeted == True,
                    cls.id.in_(db.session.query(CampaignLocation.campaign_id).filter(
                        CampaignLocation.geonameid.in_(geonameids)))
                )))  # NOQA

            # In the following simpler version, a low priority geotargeted campaign returns above a high priority
            # non-geotargeted campaign, which isn't the intended behaviour. We've therefore commented it out and
            # left it here for reference.

            # basequery = basequery.join(CampaignLocation).filter(db.or_(
            #     cls.geotargeted == False,
            #     db.and_(
            #         cls.geotargeted == True,
            #         CampaignLocation.geonameid.in_(geonameids)
            #     )))  # NOQA
        else:
            basequery = basequery.filter(cls.geotargeted == False)  # NOQA

        # Don't show campaigns that (a) the user has dismissed or (b) the user has encountered on >2 event sessions
        if user is not None:
            # XXX: The more campaigns we run, the more longer this list gets
            basequery = basequery.filter(~cls.id.in_(db.session.query(CampaignView.campaign_id).filter(
                CampaignView.user == user,
                db.or_(CampaignView.dismissed == True, CampaignView.session_count > 2))))  # NOQA

            # Filter by user flags
            for flag, value in user.flags.items():
                if flag in cls.supported_flags:
                    col = getattr(cls, 'flag_' + flag)
                    basequery = basequery.filter(db.or_(col == None, col == value))  # NOQA

        else:
            if anon_user:
                basequery = basequery.filter(~cls.id.in_(db.session.query(CampaignAnonView.campaign_id).filter(
                    CampaignAnonView.anon_user == anon_user,
                    db.or_(CampaignAnonView.dismissed == True, CampaignAnonView.session_count > 2))))  # NOQA
            # Don't show user-targeted campaigns if there's no user
            basequery = basequery.filter_by(**{'flag_' + flag: None for flag in cls.supported_flags})

        return basequery.order_by(cls.priority.desc()).first()

    @classmethod
    def all(cls):
        return cls.query.order_by(db.text('start_at desc, priority desc')).all()

    @classmethod
    def get(cls, name):
        return cls.query.filter_by(name=name).one_or_none()


Campaign.supported_flags = [key[5:] for key in Campaign.__dict__ if key.startswith('flag_')]

# Provide a sorted list of choices for use in the campaign form
Campaign.flag_choices = [('flag_' + k, v.title) for k, v in sorted(
    [(k, v) for k, v in UserFlags.__dict__.items() if isinstance(v, UserFlag) and k in Campaign.supported_flags],
    key=lambda kv: (kv[1].category, kv[1].title))]


@event.listens_for(Campaign, 'before_update')
@event.listens_for(Campaign, 'before_insert')
def _set_geotargeted(mapper, connection, target):
    if target.geonameids:
        target.geotargeted = True
    else:
        target.geotargeted = False


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
    # type = db.Column(db.Char(1),
    #     db.CheckConstraint('type IN (%s)' % ', '.join(["'%s'" % k for k in CAMPAIGN_ACTION.keys()])),
    #     nullable=False,
    #     default=CAMPAIGN_ACTION)
    #: Action category (for buttons)
    category = db.Column(db.Unicode(20), nullable=False, default=u'default')
    #: Icon to accompany text
    icon = db.Column(db.Unicode(20), nullable=True)
    #: Group (for RSVP buttons)
    group = db.Column(db.Unicode(20), nullable=True)
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

    def url_for(self, action='view', _external=False, **kwargs):
        if action == 'edit':
            return url_for('campaign_action_edit', campaign=self.campaign.name, action=self.name,
                _external=_external, **kwargs)
        elif action == 'delete':
            return url_for('campaign_action_delete', campaign=self.campaign.name, action=self.name,
                _external=_external, **kwargs)
        elif action == 'csv':
            return url_for('campaign_action_csv', campaign=self.campaign.name, action=self.name,
                _external=_external, **kwargs)


class CampaignView(TimestampMixin, db.Model):
    """
    Track users who've viewed a campaign
    """
    __tablename__ = 'campaign_view'
    #: Datetime when this activity happened (which is likely much before it was written to the database)
    datetime = db.Column(db.DateTime, default=db.func.utcnow(), nullable=False, index=True)
    #: Campaign
    campaign_id = db.Column(None, db.ForeignKey('campaign.id'), nullable=False, primary_key=True)
    campaign = db.relationship(Campaign, backref=db.backref('views', lazy='dynamic',
        order_by='CampaignView.created_at.desc()'))
    #: User who saw this campaign
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=False, primary_key=True, index=True)
    user = db.relationship(User, backref=db.backref('campaign_views', lazy='dynamic'))
    #: User dismissed this campaign. Don't show it
    dismissed = db.Column(db.Boolean, nullable=False, default=False)
    #: Number of sessions in which the user was shown this (null = unknown)
    #: Updated via a background job
    session_count = db.Column(db.Integer, nullable=False, default=0)

    @classmethod
    def get(cls, campaign, user):
        return cls.query.get((campaign.id, user.id))

    @classmethod
    def get_by_ids(cls, campaign_id, user_id):
        return cls.query.get((campaign_id, user_id))

    @classmethod
    def exists(cls, campaign, user):
        return cls.query.filter_by(campaign=campaign, user=user).notempty()


class CampaignAnonView(TimestampMixin, db.Model):
    """
    Track anon users who've viewed a campaign
    """
    __tablename__ = 'campaign_anon_view'
    #: Datetime when this activity happened (which is likely much before it was written to the database)
    datetime = db.Column(db.DateTime, default=db.func.utcnow(), nullable=False, index=True)
    #: Campaign
    campaign_id = db.Column(None, db.ForeignKey('campaign.id'), nullable=False, primary_key=True)
    campaign = db.relationship(Campaign, backref=db.backref('anonviews', lazy='dynamic',
        order_by='CampaignAnonView.created_at.desc()'))
    #: Anon user who saw this campaign
    anon_user_id = db.Column(None, db.ForeignKey('anon_user.id'), nullable=False, primary_key=True, index=True)
    anon_user = db.relationship(AnonUser, backref=db.backref('campaign_views', lazy='dynamic'))
    #: Anon user dismissed this campaign. Don't show it again
    dismissed = db.Column(db.Boolean, nullable=False, default=False)
    #: Number of sessions in which the anon user was shown this (null = unknown)
    #: Updated via a background job
    session_count = db.Column(db.Integer, nullable=False, default=0)

    @classmethod
    def get(cls, campaign, anon_user):
        return cls.query.get((campaign.id, anon_user.id))

    @classmethod
    def get_by_ids(cls, campaign_id, anon_user_id):
        return cls.query.get((campaign_id, anon_user_id))

    @classmethod
    def exists(cls, campaign, anon_user):
        return cls.query.filter_by(campaign=campaign, anon_user=anon_user).notempty()


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
    #: User who performed an action
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=False, primary_key=True, index=True)
    user = db.relationship(User, backref=db.backref('campaign_useractions', lazy='dynamic'))
    #: User's IP address
    ipaddr = db.Column(db.String(45), nullable=True, default=lambda: request and request.environ['REMOTE_ADDR'][:45])
    #: User's browser
    useragent = db.Column(db.Unicode(250), nullable=True, default=lambda: request and request.user_agent.string[:250])
    #: Data the user submitted
    data = deferred(db.Column(JsonDict, nullable=False, server_default='{}'))

    @property
    def formdata(self):
        return UserActionFormData(self.data)

    @classmethod
    def get(cls, action, user):
        return cls.query.get((action.id, user.id))


class CampaignAnonUserAction(TimestampMixin, db.Model):
    """
    Track the actions users undertook (could be more than one)
    """
    __tablename__ = 'campaign_anon_user_action'
    #: Action the user selected
    action_id = db.Column(None, db.ForeignKey('campaign_action.id'), primary_key=True)
    action = db.relationship(CampaignAction,
        backref=db.backref('anonuseractions', cascade='all, delete-orphan', lazy='dynamic',
            order_by='CampaignAnonUserAction.created_at.desc()'))
    #: User who performed an action
    anon_user_id = db.Column(None, db.ForeignKey('anon_user.id'), nullable=False, primary_key=True, index=True)
    anon_user = db.relationship(AnonUser, backref=db.backref('campaign_useractions', lazy='dynamic'))
    #: User's IP address
    ipaddr = db.Column(db.String(45), nullable=True, default=lambda: request and request.environ['REMOTE_ADDR'][:45])
    #: User's browser
    useragent = db.Column(db.Unicode(250), nullable=True, default=lambda: request and request.user_agent.string[:250])
    #: Data the user submitted
    data = deferred(db.Column(JsonDict, nullable=False, server_default='{}'))

    @property
    def formdata(self):
        return UserActionFormData(self.data)

    @classmethod
    def get(cls, action, anon_user):
        return cls.query.get((action.id, anon_user.id))
