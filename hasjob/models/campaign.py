from __future__ import annotations

from datetime import timedelta

from flask import request
from markupsafe import Markup
from sqlalchemy import event
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.orderinglist import ordering_list

from baseframe import __
from baseframe.forms import Form
from coaster.sqlalchemy import JsonDict, StateManager, cached
from coaster.utils import LabeledEnum, utcnow

from . import (
    BaseNameMixin,
    BaseScopedNameMixin,
    Model,
    TimestampMixin,
    backref,
    db,
    make_timestamp_columns,
    relationship,
    sa,
)
from .board import Board
from .flags import UserFlag, UserFlags
from .user import AnonUser, EventSession, User

__all__ = [
    'CAMPAIGN_POSITION',
    'CAMPAIGN_ACTION',
    'BANNER_LOCATION',
    'Campaign',
    'CampaignLocation',
    'CampaignAction',
    'CampaignView',
    'CampaignAnonView',
    'CampaignUserAction',
    'CampaignAnonUserAction',
    'campaign_event_session_table',
]

_marker = object()


board_campaign_table = sa.Table(
    'campaign_board',
    Model.metadata,
    *(
        make_timestamp_columns(timezone=True)
        + (
            sa.Column('board_id', None, sa.ForeignKey('board.id'), primary_key=True),
            sa.Column(
                'campaign_id',
                None,
                sa.ForeignKey('campaign.id'),
                primary_key=True,
                index=True,
            ),
        )
    ),
)


campaign_event_session_table = sa.Table(
    'campaign_event_session',
    Model.metadata,
    sa.Column('campaign_id', None, sa.ForeignKey('campaign.id'), primary_key=True),
    sa.Column(
        'event_session_id',
        None,
        sa.ForeignKey('event_session.id'),
        primary_key=True,
        index=True,
    ),
    sa.Column(
        'created_at',
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        default=sa.func.utcnow(),
    ),
)


class CAMPAIGN_STATE(LabeledEnum):  # noqa: N801
    DISABLED = (False, 'disabled', __("Disabled"))
    ENABLED = (True, 'enabled', __("Enabled"))
    # LIVE (and others) are conditional states in the model


class CAMPAIGN_POSITION(LabeledEnum):  # noqa: N801
    #: Shown in the header of all pages
    HEADER = (0, __("Header"))
    #: Shown in the sidebar of jobs
    SIDEBAR = (1, __("Sidebar"))
    #: Upsell something before the employer posts a job
    BEFOREPOST = (2, __("Before posting a job"))
    #: Shown in the body after the employer posts a job
    AFTERPOST = (3, __("After posting a job"))


class CAMPAIGN_ACTION(LabeledEnum):  # noqa: N801
    LINK = ('L', __("Follow link"))
    RSVP_Y = ('Y', __("RSVP Yes"))
    RSVP_N = ('N', __("RSVP No"))
    RSVP_M = ('M', __("RSVP Maybe"))
    FORM = ('F', __("Show a form"))
    DISMISS = ('D', __("Dismiss campaign"))

    RSVP_TYPES = {RSVP_Y, RSVP_N, RSVP_M}
    DATA_TYPES = {RSVP_Y, RSVP_N, RSVP_M, FORM}


class BANNER_LOCATION(LabeledEnum):  # noqa: N801
    TOP = (0, __("Top"))
    RIGHT = (1, __("Right"))
    BOTTOM = (2, __("Bottom"))
    LEFT = (3, __("Left"))


class Campaign(BaseNameMixin, Model):
    """
    A campaign runs in the header or sidebar of Hasjob's pages and prompts the user towards some action.
    Unlike announcements, campaigns sit outside the content area of listings.
    """

    __tablename__ = 'campaign'

    # Campaign metadata columns

    #: User who created this campaign
    user_id = sa.orm.mapped_column(None, sa.ForeignKey('user.id'), nullable=False)
    user = relationship(User, backref='campaigns')
    #: When does this campaign go on air?
    start_at = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, index=True
    )
    #: When does it go off air?
    end_at = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, index=True
    )
    #: Is this campaign live?
    public = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False)
    #: StateManager for campaign's state
    state = StateManager('public', CAMPAIGN_STATE)
    #: Position to display campaign in
    position = sa.orm.mapped_column(
        sa.SmallInteger, nullable=False, default=CAMPAIGN_POSITION.HEADER
    )
    #: Boards to run this campaign on
    boards = relationship(Board, secondary=board_campaign_table)
    #: Quick lookup locations to run this campaign in
    geonameids = association_proxy(
        'locations',
        'geonameid',
        creator=lambda geonameid: CampaignLocation(geonameid=geonameid),
    )
    #: Is this campaign location-based?
    geotargeted = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False)
    #: Is a user required? None = don't care, True = user required, False = no user
    user_required = sa.orm.mapped_column(sa.Boolean, nullable=True, default=None)
    #: Priority, lower = less priority
    priority = sa.orm.mapped_column(sa.Integer, nullable=False, default=0)

    # Campaign content columns

    #: Subject (user-facing, unlike the title)
    subject = sa.orm.mapped_column(sa.Unicode(250), nullable=True)
    #: Call to action text (for header campaigns)
    blurb = sa.orm.mapped_column(sa.UnicodeText, nullable=False, default='')
    #: Full text (for read more click throughs)
    description = sa.orm.mapped_column(sa.UnicodeText, nullable=False, default='')
    #: Banner image
    banner_image = sa.orm.mapped_column(sa.Unicode(250), nullable=True)
    #: Banner location
    banner_location = sa.orm.mapped_column(
        sa.SmallInteger, nullable=False, default=BANNER_LOCATION.TOP
    )

    # Flags
    flag_is_new_since_day = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_is_new_since_month = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_is_not_new = sa.orm.mapped_column(sa.Boolean, nullable=True)

    flag_is_candidate_alltime = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_is_candidate_day = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_is_candidate_month = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_is_candidate_past = sa.orm.mapped_column(sa.Boolean, nullable=True)

    flag_has_jobapplication_response_alltime = sa.orm.mapped_column(
        sa.Boolean, nullable=True
    )
    flag_has_jobapplication_response_day = sa.orm.mapped_column(
        sa.Boolean, nullable=True
    )
    flag_has_jobapplication_response_month = sa.orm.mapped_column(
        sa.Boolean, nullable=True
    )
    flag_has_jobapplication_response_past = sa.orm.mapped_column(
        sa.Boolean, nullable=True
    )

    flag_is_employer_alltime = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_is_employer_day = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_is_employer_month = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_is_employer_past = sa.orm.mapped_column(sa.Boolean, nullable=True)

    flag_has_jobpost_unconfirmed_alltime = sa.orm.mapped_column(
        sa.Boolean, nullable=True
    )
    flag_has_jobpost_unconfirmed_day = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_has_jobpost_unconfirmed_month = sa.orm.mapped_column(sa.Boolean, nullable=True)

    flag_has_responded_candidate_alltime = sa.orm.mapped_column(
        sa.Boolean, nullable=True
    )
    flag_has_responded_candidate_day = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_has_responded_candidate_month = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_has_responded_candidate_past = sa.orm.mapped_column(sa.Boolean, nullable=True)

    flag_is_new_lurker_within_day = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_is_new_lurker_within_month = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_is_lurker_since_past = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_is_lurker_since_alltime = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_is_inactive_since_day = sa.orm.mapped_column(sa.Boolean, nullable=True)
    flag_is_inactive_since_month = sa.orm.mapped_column(sa.Boolean, nullable=True)

    # Sessions this campaign has been viewed in
    session_views = relationship(
        EventSession,
        secondary=campaign_event_session_table,
        backref='campaign_views',
        order_by=campaign_event_session_table.c.created_at,
        lazy='dynamic',
    )

    __table_args__ = (
        sa.CheckConstraint('end_at > start_at', name='campaign_start_at_end_at'),
    )

    # Campaign conditional states
    state.add_conditional_state(
        'LIVE',
        state.ENABLED,
        lambda obj: obj.start_at <= utcnow() < obj.end_at,
        lambda cls: sa.and_(
            cls.start_at <= sa.func.utcnow(), cls.end_at > sa.func.utcnow()
        ),
        label=('live', __("Live")),
    )
    state.add_conditional_state(
        'CURRENT',
        state.ENABLED,
        lambda obj: obj.start_at
        <= obj.start_at
        <= utcnow()
        < obj.end_at
        <= utcnow() + timedelta(days=30),
        lambda cls: sa.and_(
            cls.start_at <= sa.func.utcnow(),
            cls.end_at > sa.func.utcnow(),
            cls.end_at <= utcnow() + timedelta(days=30),
        ),
        label=('current', __("Current")),
    )
    state.add_conditional_state(
        'LONGTERM',
        state.ENABLED,
        lambda obj: obj.start_at
        <= obj.start_at
        <= utcnow()
        < utcnow() + timedelta(days=30)
        < obj.end_at,
        lambda cls: sa.and_(
            cls.start_at <= utcnow(), cls.end_at > utcnow() + timedelta(days=30)
        ),
        label=('longterm', __("Long term")),
    )
    state.add_conditional_state(
        'OFFLINE',
        state.ENABLED,
        lambda obj: obj.start_at > utcnow() or obj.end_at <= utcnow(),
        lambda cls: sa.or_(
            cls.start_at > sa.func.utcnow(), cls.end_at <= sa.func.utcnow()
        ),
        label=('offline', __("Offline")),
    )

    @property
    def content(self):
        """Form helper method"""
        return self

    @property
    def flags(self):
        """Form helper method"""
        return self

    def __repr__(self):
        return '<Campaign {} "{}" {}:{}>'.format(
            self.name,
            self.title,
            self.start_at.strftime('%Y-%m-%d'),
            self.end_at.strftime('%Y-%m-%d'),
        )

    def useractions(self, user):
        if user is not None:
            return {
                cua.action.name: cua
                for cua in CampaignUserAction.query.filter_by(user=user)
                .filter(CampaignUserAction.action_id.in_([a.id for a in self.actions]))
                .all()
            }
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
    def for_context(
        cls, position, board=None, user=None, anon_user=None, geonameids=None
    ):
        """
        Return a campaign suitable for this board, user and locations (as geonameids).
        """
        basequery = cls.query.filter(cls.state.LIVE, cls.position == position)

        if board:
            basequery = basequery.filter(cls.boards.any(id=board.id))

        if user:
            # Look for campaigns that don't target by user or require a user
            basequery = basequery.filter(
                sa.or_(cls.user_required.is_(None), cls.user_required.is_(True))
            )
        else:
            # Look for campaigns that don't target by user or require no user
            basequery = basequery.filter(
                sa.or_(cls.user_required.is_(None), cls.user_required.is_(False))
            )

        if geonameids:
            # TODO: The query for CampaignLocation.campaign_id here does not consider
            # if the campaign id is currently live. This will become inefficient as the
            # number of location-targeted campaigns grows. This should be cached.
            basequery = basequery.filter(
                sa.or_(
                    cls.geotargeted.is_(False),
                    sa.and_(
                        cls.geotargeted.is_(True),
                        cls.id.in_(
                            db.session.query(CampaignLocation.campaign_id).filter(
                                CampaignLocation.geonameid.in_(geonameids)
                            )
                        ),
                    ),
                )
            )

            # In the following simpler version, a low priority geotargeted campaign returns above a high priority
            # non-geotargeted campaign, which isn't the intended behaviour. We've therefore commented it out and
            # left it here for reference.

            # basequery = basequery.join(CampaignLocation).filter(sa.or_(
            #     cls.geotargeted.is_(False),
            #     sa.and_(
            #         cls.geotargeted.is_(True),
            #         CampaignLocation.geonameid.in_(geonameids)
            #     )))
        else:
            basequery = basequery.filter(cls.geotargeted.is_(False))

        # Don't show campaigns that (a) the user has dismissed or (b) the user has encountered on >2 event sessions
        if user is not None:
            # TODO: The more campaigns we run, the more longer this list gets. Find something more efficient
            basequery = basequery.filter(
                ~cls.id.in_(
                    db.session.query(CampaignView.campaign_id).filter(
                        CampaignView.user == user,
                        sa.or_(
                            CampaignView.dismissed.is_(True),
                            CampaignView.session_count > 2,
                        ),
                    )
                )
            )

            # Filter by user flags
            for flag, value in user.flags.items():
                if flag in cls.supported_flags:
                    col = getattr(cls, 'flag_' + flag)
                    basequery = basequery.filter(sa.or_(col.is_(None), col == value))

        else:
            if anon_user:
                basequery = basequery.filter(
                    ~cls.id.in_(
                        db.session.query(CampaignAnonView.campaign_id).filter(
                            CampaignAnonView.anon_user == anon_user,
                            sa.or_(
                                CampaignAnonView.dismissed.is_(True),
                                CampaignAnonView.session_count > 2,
                            ),
                        )
                    )
                )
            # Don't show user-targeted campaigns if there's no user
            basequery = basequery.filter_by(
                **{'flag_' + flag: None for flag in cls.supported_flags}
            )

        return basequery.order_by(cls.priority.desc()).first()

    @classmethod
    def get(cls, name):
        return cls.query.filter_by(name=name).one_or_none()


Campaign.supported_flags = [
    key[5:] for key in Campaign.__dict__ if key.startswith('flag_')
]

# Provide a sorted list of choices for use in the campaign form
Campaign.flag_choices = [
    ('flag_' + k, v.title)
    for k, v in sorted(
        (
            (k, v)
            for k, v in UserFlags.__dict__.items()
            if isinstance(v, UserFlag) and k in Campaign.supported_flags
        ),
        key=lambda kv: (kv[1].category, kv[1].title),
    )
]


@event.listens_for(Campaign, 'before_update')
@event.listens_for(Campaign, 'before_insert')
def _set_geotargeted(mapper, connection, target):
    if target.geonameids:
        target.geotargeted = True
    else:
        target.geotargeted = False


class CampaignLocation(TimestampMixin, Model):
    """
    Location tag for campaigns
    """

    __tablename__ = 'campaign_location'
    #: Campaign we are referencing
    campaign_id = sa.orm.mapped_column(
        None, sa.ForeignKey('campaign.id'), primary_key=True, nullable=False
    )
    campaign = relationship(
        Campaign, backref=backref('locations', cascade='all, delete-orphan')
    )

    #: Geonameid for this campaign
    geonameid = sa.orm.mapped_column(
        sa.Integer, primary_key=True, nullable=False, index=True
    )

    def __repr__(self):
        return '<CampaignLocation %d for campaign %s>' % (
            self.geonameid,
            self.campaign.name,
        )


class CampaignAction(BaseScopedNameMixin, Model):
    """
    Actions available to a user in a campaign
    """

    __tablename__ = 'campaign_action'
    # TODO: Enable UUID primary keys and switch /go URLs to uuid_b58
    #: Campaign
    campaign_id = sa.orm.mapped_column(
        None, sa.ForeignKey('campaign.id'), nullable=False
    )
    campaign = relationship(
        Campaign,
        backref=backref(
            'actions',
            cascade='all, delete-orphan',
            order_by='CampaignAction.seq',
            collection_class=ordering_list('seq'),
        ),
    )
    parent = sa.orm.synonym('campaign')
    #: Sequence number
    seq = sa.orm.mapped_column(sa.Integer, nullable=False, default=0)
    #: Is this action live?
    public = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False)
    #: Action type
    type = sa.orm.mapped_column(  # noqa: A003
        sa.Enum(*CAMPAIGN_ACTION.keys(), name='campaign_action_type_enum'),
        nullable=False,
    )
    # type = sa.orm.mapped_column(sa.Char(1),
    #     sa.CheckConstraint('type IN (%s)' % ', '.join(["'%s'" % k for k in CAMPAIGN_ACTION.keys()])),
    #     nullable=False)
    #: Action category (for buttons)
    category = sa.orm.mapped_column(sa.Unicode(20), nullable=False, default='default')
    #: Icon to accompany text
    icon = sa.orm.mapped_column(sa.Unicode(20), nullable=True)
    #: Group (for RSVP buttons)
    group = sa.orm.mapped_column(sa.Unicode(20), nullable=True)
    #: Target link (for follow link actions; blank = ?)
    link = sa.orm.mapped_column(sa.Unicode(250), nullable=True, deferred=True)
    #: Form
    form = sa.orm.mapped_column(
        JsonDict, nullable=False, server_default='{}', deferred=True
    )
    #: Post action message
    message = sa.orm.mapped_column(sa.UnicodeText, nullable=False, default='')

    __table_args__ = (sa.UniqueConstraint('campaign_id', 'name'),)

    @classmethod
    def get(cls, campaign, name):
        return cls.query.filter_by(campaign=campaign, name=name).one_or_none()

    @property
    def is_data_type(self):
        return self.type in CAMPAIGN_ACTION.DATA_TYPES

    @property
    def is_rsvp_type(self):
        return self.type in CAMPAIGN_ACTION.RSVP_TYPES


class CampaignView(TimestampMixin, Model):
    """
    Track users who've viewed a campaign
    """

    __tablename__ = 'campaign_view'
    #: Datetime when this activity happened (which is likely much before it was written to the database)
    datetime = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True),
        default=sa.func.utcnow(),
        nullable=False,
        index=True,
    )
    #: Campaign
    campaign_id = sa.orm.mapped_column(
        None, sa.ForeignKey('campaign.id'), nullable=False, primary_key=True
    )
    campaign = relationship(
        Campaign,
        backref=backref(
            'campaign_views', lazy='dynamic', order_by='CampaignView.created_at.desc()'
        ),
    )
    #: User who saw this campaign
    user_id = sa.orm.mapped_column(
        None, sa.ForeignKey('user.id'), nullable=False, primary_key=True, index=True
    )
    user = relationship(User, backref=backref('campaign_views', lazy='dynamic'))
    #: User dismissed this campaign. Don't show it
    dismissed = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False)
    #: Number of sessions in which the user was shown this (null = unknown)
    #: Updated via a background job
    session_count = cached(sa.orm.mapped_column(sa.Integer, nullable=False, default=0))
    #: The last time this campaign was viewed. If the campaign has a refresh time (say, 30 days)
    #: and the view is older than that, we'll reset the session_count and dismissed flag (via a
    #: background job) so that the campaign shows again.
    last_viewed_at = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True), default=sa.func.utcnow(), nullable=False
    )
    #: The last time view counts were reset
    reset_at = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True), default=sa.func.utcnow(), nullable=False
    )
    #: TODO: Maybe we need a permanently dismissed flag now, for when a user indicates they really
    #: don't want to see this again, and not just because they want it "done for now".

    @classmethod
    def get(cls, campaign, user):
        return cls.query.get((campaign.id, user.id))

    @classmethod
    def get_by_ids(cls, campaign_id, user_id):
        return cls.query.get((campaign_id, user_id))

    @classmethod
    def exists(cls, campaign, user):
        return cls.query.filter_by(campaign=campaign, user=user).notempty()


class CampaignAnonView(TimestampMixin, Model):
    """
    Track anon users who've viewed a campaign
    """

    __tablename__ = 'campaign_anon_view'
    #: Datetime when this activity happened (which is likely much before it was written to the database)
    datetime = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True),
        default=sa.func.utcnow(),
        nullable=False,
        index=True,
    )
    #: Campaign
    campaign_id = sa.orm.mapped_column(
        None, sa.ForeignKey('campaign.id'), nullable=False, primary_key=True
    )
    campaign = relationship(
        Campaign,
        backref=backref(
            'anonviews', lazy='dynamic', order_by='CampaignAnonView.created_at.desc()'
        ),
    )
    #: Anon user who saw this campaign
    anon_user_id = sa.orm.mapped_column(
        None,
        sa.ForeignKey('anon_user.id'),
        nullable=False,
        primary_key=True,
        index=True,
    )
    anon_user = relationship(
        AnonUser, backref=backref('campaign_views', lazy='dynamic')
    )
    #: Anon user dismissed this campaign. Don't show it again
    dismissed = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False)
    #: Number of sessions in which the anon user was shown this (null = unknown)
    #: Updated via a background job
    session_count = cached(sa.orm.mapped_column(sa.Integer, nullable=False, default=0))
    #: The last time this campaign was viewed. If the campaign has a refresh time (say, 30 days)
    #: and the view is older than that, we'll reset the session_count and dismissed flag (via a
    #: background job) so that the campaign shows again.
    last_viewed_at = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True), default=sa.func.utcnow(), nullable=False
    )
    #: The last time view counts were reset
    reset_at = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True), default=sa.func.utcnow(), nullable=False
    )
    #: TODO: Maybe we need a permanently dismissed flag now, for when a user indicates they really
    #: don't want to see this again, and not just because they want it "done for now".

    @classmethod
    def get(cls, campaign, anon_user):
        return cls.query.get((campaign.id, anon_user.id))

    @classmethod
    def get_by_ids(cls, campaign_id, anon_user_id):
        return cls.query.get((campaign_id, anon_user_id))

    @classmethod
    def exists(cls, campaign, anon_user):
        return cls.query.filter_by(campaign=campaign, anon_user=anon_user).notempty()


class UserActionFormData:
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


class CampaignUserAction(TimestampMixin, Model):
    """
    Track the actions users undertook (could be more than one)
    """

    __tablename__ = 'campaign_user_action'
    #: Action the user selected
    action_id = sa.orm.mapped_column(
        None, sa.ForeignKey('campaign_action.id'), primary_key=True
    )
    action = relationship(
        CampaignAction,
        backref=backref(
            'useractions',
            cascade='all, delete-orphan',
            lazy='dynamic',
            order_by='CampaignUserAction.created_at.desc()',
        ),
    )
    #: User who performed an action
    user_id = sa.orm.mapped_column(
        None, sa.ForeignKey('user.id'), nullable=False, primary_key=True, index=True
    )
    user = relationship(User, backref=backref('campaign_useractions', lazy='dynamic'))
    #: User's IP address
    ipaddr = sa.orm.mapped_column(
        sa.String(45),
        nullable=True,
        default=lambda: request and request.environ['REMOTE_ADDR'][:45],
    )
    #: User's browser
    useragent = sa.orm.mapped_column(
        sa.Unicode(250),
        nullable=True,
        default=lambda: request and request.user_agent.string[:250],
    )
    #: Data the user submitted
    data = sa.orm.mapped_column(
        JsonDict, nullable=False, server_default='{}', deferred=True
    )

    @property
    def formdata(self):
        return UserActionFormData(self.data)

    @classmethod
    def get(cls, action, user):
        return cls.query.get((action.id, user.id))


class CampaignAnonUserAction(TimestampMixin, Model):
    """
    Track the actions users undertook (could be more than one)
    """

    __tablename__ = 'campaign_anon_user_action'
    #: Action the user selected
    action_id = sa.orm.mapped_column(
        None, sa.ForeignKey('campaign_action.id'), primary_key=True
    )
    action = relationship(
        CampaignAction,
        backref=backref(
            'anonuseractions',
            cascade='all, delete-orphan',
            lazy='dynamic',
            order_by='CampaignAnonUserAction.created_at.desc()',
        ),
    )
    #: User who performed an action
    anon_user_id = sa.orm.mapped_column(
        None,
        sa.ForeignKey('anon_user.id'),
        nullable=False,
        primary_key=True,
        index=True,
    )
    anon_user = relationship(
        AnonUser, backref=backref('campaign_useractions', lazy='dynamic')
    )
    #: User's IP address
    ipaddr = sa.orm.mapped_column(
        sa.String(45),
        nullable=True,
        default=lambda: request and request.environ['REMOTE_ADDR'][:45],
    )
    #: User's browser
    useragent = sa.orm.mapped_column(
        sa.Unicode(250),
        nullable=True,
        default=lambda: request and request.user_agent.string[:250],
    )
    #: Data the user submitted
    data = sa.orm.mapped_column(
        JsonDict, nullable=False, server_default='{}', deferred=True
    )

    @property
    def formdata(self):
        return UserActionFormData(self.data)

    @classmethod
    def get(cls, action, anon_user):
        return cls.query.get((action.id, anon_user.id))
