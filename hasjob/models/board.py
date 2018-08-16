# -*- coding: utf-8 -*-

from pytz import timezone
from werkzeug import cached_property
from flask import url_for, Markup
from sqlalchemy.ext.associationproxy import association_proxy
from coaster.sqlalchemy import make_timestamp_columns
from . import db, TimestampMixin, BaseNameMixin
from .user import User, UserActiveAt
from .jobpost import JobPost
from .jobtype import JobType
from .jobcategory import JobCategory
from .tag import Tag


__all__ = ['Board', 'BoardJobPost', 'BoardAutoDomain', 'BoardAutoLocation', 'board_auto_tag_table',
    'board_auto_jobtype_table', 'board_auto_jobcategory_table']


board_jobtype_table = db.Table('board_jobtype', db.Model.metadata,
    *(make_timestamp_columns() + (
        db.Column('board_id', None, db.ForeignKey('board.id'), primary_key=True),
        db.Column('jobtype_id', None, db.ForeignKey('jobtype.id'), primary_key=True)
    )))


board_jobcategory_table = db.Table('board_jobcategory', db.Model.metadata,
    *(make_timestamp_columns() + (
        db.Column('board_id', None, db.ForeignKey('board.id'), primary_key=True),
        db.Column('jobcategory_id', None, db.ForeignKey('jobcategory.id'), primary_key=True)
    )))


board_users_table = db.Table('board_user', db.Model.metadata,
    *(make_timestamp_columns() + (
        db.Column('board_id', None, db.ForeignKey('board.id'), primary_key=True),
        db.Column('user_id', None, db.ForeignKey('user.id'), primary_key=True),
    )))


board_auto_tag_table = db.Table('board_auto_tag', db.Model.metadata,
    db.Column('tag_id', None, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('board_id', None, db.ForeignKey('board.id'), primary_key=True),
    db.Column('created_at', db.DateTime, nullable=False, default=db.func.utcnow())
    )


board_auto_jobtype_table = db.Table('board_auto_jobtype', db.Model.metadata,
    db.Column('jobtype_id', None, db.ForeignKey('jobtype.id'), primary_key=True),
    db.Column('board_id', None, db.ForeignKey('board.id'), primary_key=True),
    db.Column('created_at', db.DateTime, nullable=False, default=db.func.utcnow())
    )


board_auto_jobcategory_table = db.Table('board_auto_jobcategory', db.Model.metadata,
    db.Column('jobcategory_id', None, db.ForeignKey('jobcategory.id'), primary_key=True),
    db.Column('board_id', None, db.ForeignKey('board.id'), primary_key=True),
    db.Column('created_at', db.DateTime, nullable=False, default=db.func.utcnow())
    )


def jobtype_choices(cls, board=None):
    if board:
        return [(ob.id, ob.title) for ob in board.types if not ob.private]
    else:
        return [(ob.id, ob.title) for ob in cls.query.filter_by(private=False, public=True).order_by('seq')]

JobType.choices = classmethod(jobtype_choices)


def jobcategory_choices(cls, board=None):
    if board:
        return [(ob.id, ob.title) for ob in board.categories if not ob.private]
    else:
        return [(ob.id, ob.title) for ob in cls.query.filter_by(private=False, public=True).order_by('seq')]

JobCategory.choices = classmethod(jobcategory_choices)


class BoardAutoDomain(TimestampMixin, db.Model):
    """
    Domain tag for boards
    """
    __tablename__ = 'board_auto_domain'
    #: Board we are referencing
    board_id = db.Column(None, db.ForeignKey('board.id'), primary_key=True, nullable=False)
    #: Domain for this board
    domain = db.Column(db.Unicode(80), primary_key=True, nullable=False, index=True)

    def __repr__(self):
        return '<BoardAutoDomain %s for board %s>' % (self.domain, self.board.name)


class BoardAutoLocation(TimestampMixin, db.Model):
    """
    Location tag for boards
    """
    __tablename__ = 'board_auto_location'
    #: Board we are referencing
    board_id = db.Column(None, db.ForeignKey('board.id'), primary_key=True, nullable=False)
    #: Geonameid for this board
    geonameid = db.Column(db.Integer, primary_key=True, nullable=False, index=True)

    def __repr__(self):
        return '<BoardAutoLocation %d for board %s>' % (self.geonameid, self.board.name)


class Board(BaseNameMixin, db.Model):
    """
    Boards show a filtered set of jobs at board-specific URLs.
    """
    __tablename__ = 'board'
    #: Reserved board names
    reserved_names = ['static', 'beta']
    #: Caption
    caption = db.Column(db.Unicode(250), nullable=True)
    #: Lastuser organization userid that owns this
    userid = db.Column(db.Unicode(22), nullable=False, index=True)
    #: Welcome text
    description = db.Column(db.UnicodeText, nullable=False, default=u'')
    #: Restrict displayed posts to 24 hours if not logged in?
    require_login = db.Column(db.Boolean, nullable=False, default=True)
    #: Restrict ability to list via this board?
    restrict_listing = db.Column(db.Boolean, nullable=False, default=True)
    #: Relax pay data requirement?
    require_pay = db.Column(db.Boolean, nullable=False, default=True)
    #: New job template headline
    newjob_headline = db.Column(db.Unicode(100), nullable=True)
    #: New job posting instructions
    newjob_blurb = db.Column(db.UnicodeText, nullable=True)
    #: Featured board
    featured = db.Column(db.Boolean, default=False, nullable=False, index=True)
    #: Posting users
    posting_users = db.relationship(User, secondary=board_users_table)
    #: Available job types
    types = db.relationship(JobType, secondary=board_jobtype_table, order_by=JobType.seq)
    #: Available job categories
    categories = db.relationship(JobCategory, secondary=board_jobcategory_table, order_by=JobCategory.seq)

    #: Automatic tagging domains
    domains = db.relationship(BoardAutoDomain, backref='board', cascade='all, delete-orphan',
        order_by=BoardAutoDomain.domain)
    auto_domains = association_proxy('domains', 'domain', creator=lambda d: BoardAutoDomain(domain=d))
    #: Automatic tagging locations
    auto_locations = db.relationship(BoardAutoLocation, backref='board', cascade='all, delete-orphan')
    auto_geonameids = association_proxy('auto_locations', 'geonameid', creator=lambda l: BoardAutoLocation(geonameid=l))
    #: Automatic tagging keywords
    auto_tags = db.relationship(Tag, secondary=board_auto_tag_table, order_by=Tag.name)
    auto_keywords = association_proxy('auto_tags', 'title', creator=lambda t: Tag.get(t, create=True))
    auto_types = db.relationship(JobType, secondary=board_auto_jobtype_table, order_by=JobType.seq)
    auto_categories = db.relationship(JobCategory, secondary=board_auto_jobcategory_table, order_by=JobCategory.seq)
    #: Must all criteria match for an auto-post?
    auto_all = db.Column(db.Boolean, default=False, nullable=False)
    #: Users active on this board
    users_active_at = db.relationship(UserActiveAt, lazy='dynamic', backref='board')

    def __repr__(self):
        return '<Board %s "%s">' % (self.name, self.title)

    @property
    def is_root(self):
        return self.name == u'www'

    @property
    def not_root(self):
        return self.name != u'www'

    @property
    def options(self):
        """Form helper method (see BoardOptionsForm)"""
        return self

    @property
    def autotag(self):
        """Form helper method (see BoardTaggingForm)"""
        return self

    @cached_property
    def tz(self):
        return timezone(self.timezone)

    @property
    def title_and_name(self):
        return Markup(u'{title} (<a href="{url}" target="_blank">{name}</a>)'.format(
            title=self.title, name=self.name, url=self.url_for()))

    def owner_is(self, user):
        if user is None:
            return False
        if self.userid == user.userid or self.userid in user.allowner_ids():
            return True
        return False

    def link_to_jobpost(self, jobpost):
        return BoardJobPost.query.get((self.id, jobpost.id))

    def add(self, jobpost):
        link = self.link_to_jobpost(jobpost)
        if not link:
            link = BoardJobPost(jobpost=jobpost, board=self)
            db.session.add(link)
        return link

    def permissions(self, user, inherited=None):
        perms = super(Board, self).permissions(user, inherited)
        perms.add('view')
        if not self.restrict_listing:
            perms.add('new-job')
        if user is not None and (user.userid == self.userid or self.userid in user.allowner_ids()):
            perms.add('edit')
            perms.add('delete')
            perms.add('add')
            perms.add('new-job')
            perms.add('edit-filterset')
        elif user in self.posting_users:
            perms.add('new-job')
        return perms

    def url_for(self, action='view', _external=False):
        if action == 'view':
            if self.is_root:
                # Specialcase 'www'. Don't use www.hasjob.co.
                return url_for('index', subdomain=None, _external=_external)
            else:
                return url_for('index', subdomain=self.name, _external=_external)
        elif action == 'edit':
            return url_for('board_edit', board=self.name, _external=_external)
        elif action == 'delete':
            return url_for('board_delete', board=self.name, _external=_external)
        elif action == 'oembed':
            if self.is_root:
                return url_for('index', subdomain=None, embed=1, _external=_external)
            else:
                return url_for('index', subdomain=self.name, embed=1, _external=_external)

    @classmethod
    def get(cls, name):
        return cls.query.filter_by(name=name).one_or_none()


def _user_boards(self):
    return Board.query.filter(
        Board.userid.in_(self.user_organizations_owned_ids())).options(
        db.load_only('id', 'name', 'title', 'userid')).all()

User.boards = _user_boards


class BoardJobPost(TimestampMixin, db.Model):
    """
    Link job posts to boards.
    """
    __tablename__ = 'board_jobpost'
    #: Linked Board
    board_id = db.Column(None, db.ForeignKey('board.id'), primary_key=True)
    board = db.relationship(Board, backref=db.backref('boardposts',
        lazy='dynamic', cascade='all, delete-orphan'))
    #: Linked JobPost
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), primary_key=True, index=True)
    jobpost = db.relationship(JobPost, backref=db.backref('postboards',
        lazy='dynamic', order_by='BoardJobPost.created_at', cascade='all, delete-orphan'))
    #: Is this post pinned on this board?
    pinned = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return '<BoardJobPost {board_id}: {jobpost_id}>'.format(board_id=self.board_id, jobpost_id=self.jobpost_id)


def _jobpost_link_to_board(self, board):
    return BoardJobPost.query.get((board.id, self.id))

JobPost.link_to_board = _jobpost_link_to_board


def _jobpost_add_to(self, board):
    with db.session.no_autoflush:
        if isinstance(board, basestring):
            board = Board.get(board)
        if not board:
            return

        link = self.link_to_board(board)
        if not link:
            link = BoardJobPost(jobpost=self, board=board)
            db.session.add(link)
        return link

JobPost.add_to = _jobpost_add_to
