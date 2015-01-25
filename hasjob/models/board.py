# -*- coding: utf-8 -*-

from pytz import timezone
from werkzeug import cached_property
from flask import url_for
from sqlalchemy.orm import defer
from sqlalchemy.ext.associationproxy import association_proxy
from coaster.sqlalchemy import make_timestamp_columns
from baseframe import cache
from . import db, TimestampMixin, BaseNameMixin
from .user import User
from .jobpost import JobPost
from .jobtype import JobType
from .jobcategory import JobCategory

__all__ = ['Board', 'BoardJobPost', 'BoardDomain', 'BoardLocation']


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


class BoardDomain(TimestampMixin, db.Model):
    """
    Domain tag for boards
    """
    __tablename__ = 'board_domain'
    #: Board we are referencing
    board_id = db.Column(None, db.ForeignKey('board.id'), primary_key=True, nullable=False)
    #: Domain for this board
    domain = db.Column(db.Unicode(80), primary_key=True, nullable=False, index=True)

    def __repr__(self):
        return '<BoardDomain %s for board %s>' % (self.domain, self.board.name)


class BoardLocation(TimestampMixin, db.Model):
    """
    Location tag for boards
    """
    __tablename__ = 'board_location'
    #: Board we are referencing
    board_id = db.Column(None, db.ForeignKey('board.id'), primary_key=True, nullable=False)
    #: Geonameid for this board
    geonameid = db.Column(db.Integer, primary_key=True, nullable=False, index=True)

    def __repr__(self):
        return '<BoardLocation %d for board %s>' % (self.geonameid, self.board.name)


class Board(BaseNameMixin, db.Model):
    """
    Boards show a filtered set of jobs at board-specific URLs.
    """
    __tablename__ = 'board'
    #: Reserved board names
    reserved_names = ['www', 'static', 'beta']
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
    #: Posting users
    posting_users = db.relationship(User, secondary=board_users_table)
    #: Available job types
    types = db.relationship(JobType, secondary=board_jobtype_table, order_by=JobType.seq)
    #: Available job categories
    categories = db.relationship(JobCategory, secondary=board_jobcategory_table, order_by=JobCategory.seq)

    #: Automatic tagging domains
    domains = db.relationship(BoardDomain, backref='board', cascade='all, delete-orphan')
    tag_domains = association_proxy('domains', 'domain', creator=lambda d: BoardDomain(domain=d))
    #: Automatic tagging locations
    locations = db.relationship(BoardLocation, backref='board', cascade='all, delete-orphan')
    tag_locations = association_proxy('locations', 'geonameid', creator=lambda l: BoardLocation(geonameid=l))

    def __repr__(self):
        return '<Board %s "%s">' % (self.name, self.title)

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

    def owner_is(self, user):
        if user is None:
            return False
        if user.userid == self.userid or self.userid in user.organizations_owned_ids():
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
        if user is not None and (user.userid == self.userid or self.userid in user.organizations_owned_ids()):
            perms.add('edit')
            perms.add('delete')
            perms.add('add')
            perms.add('new-job')
        elif user in self.posting_users:
            perms.add('new-job')
        return perms

    def url_for(self, action='view', _external=False):
        if action == 'view':
            if self.name == u'www':
                # Specialcase 'www'. Don't use www.hasjob.co.
                return url_for('index', subdomain=None, _external=_external)
            else:
                return url_for('index', subdomain=self.name, _external=_external)
        elif action == 'edit':
            return url_for('board_edit', board=self.name, _external=_external)
        elif action == 'delete':
            return url_for('board_delete', board=self.name, _external=_external)

    @classmethod
    def get(cls, name):
        return cls.query.filter_by(name=name).one_or_none()


def _user_boards(self):
    return Board.query.filter(
        Board.userid.in_(self.user_organizations_owned_ids())).options(
        defer(Board.description)).all()

User.boards = _user_boards


def _user_has_boards(self):
    # Cached version of User.boards()
    key = 'user/board/count/' + str(self.id)
    count = cache.get(key)
    if not count:
        count = Board.query.filter(
            Board.userid.in_(self.user_organizations_owned_ids())).options(
            defer(Board.description)).count()
        cache.set(key, count, timeout=300)
    return bool(count)

User.has_boards = property(_user_has_boards)


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
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), primary_key=True)
    jobpost = db.relationship(JobPost, backref=db.backref('postboards',
        lazy='dynamic', order_by='BoardJobPost.created_at', cascade='all, delete-orphan'))
    #: Is this post pinned on this board?
    pinned = db.Column(db.Boolean, default=False, nullable=False)


def _jobpost_link_to_board(self, board):
    return BoardJobPost.query.get((board.id, self.id))

JobPost.link_to_board = _jobpost_link_to_board


def _jobpost_add_to(self, board):
    with db.session.no_autoflush:
        link = self.link_to_board(board)
        if not link:
            link = BoardJobPost(jobpost=self, board=board)
            db.session.add(link)
        return link

JobPost.add_to = _jobpost_add_to
