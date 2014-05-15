# -*- coding: utf-8 -*-

from pytz import timezone
from werkzeug import cached_property
from flask import url_for
from sqlalchemy.orm import defer
from . import db, BaseMixin, BaseNameMixin
from .user import User
from .jobpost import JobPost

__all__ = ['Board', 'BoardJobPost']


class Board(BaseNameMixin, db.Model):
    """
    Boards show a filtered set of jobs at board-specific URLs.
    """
    __tablename__ = 'board'
    #: Lastuser organization userid that owns this
    userid = db.Column(db.Unicode(22), nullable=False, index=True)
    #: Welcome text
    description = db.Column(db.UnicodeText, nullable=False, default=u'')

    def __repr__(self):
        return '<Board %s "%s">' % (self.name, self.title)

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
        return BoardJobPost.query.filter_by(board=self, jobpost=jobpost).one_or_none()

    def add(self, jobpost):
        link = self.link_to_jobpost(jobpost)
        if not link:
            link = BoardJobPost(board=self, jobpost=jobpost)
            db.session.add(link)
        return link

    def permissions(self, user, inherited=None):
        perms = super(Board, self).permissions(user, inherited)
        perms.add('view')
        if user is not None and user.userid == self.userid or self.userid in user.organizations_owned_ids():
            perms.add('edit')
            perms.add('delete')
            perms.add('add')
        return perms

    def url_for(self, action='view', _external=False):
        if action == 'view':
            return url_for('board_view', board=self.name, _external=_external)
        elif action == 'edit':
            return url_for('board_edit', board=self.name, _external=_external)
        elif action == 'delete':
            return url_for('board_delete', board=self.name, _external=_external)


def _user_boards(self):
    return Board.query.filter(
        Board.userid.in_(self.user_organizations_owned_ids())).options(
        defer(Board.description)).all()

User.boards = _user_boards


class BoardJobPost(BaseMixin, db.Model):
    """
    Link job posts to boards.
    """
    __tablename__ = 'board_jobpost'
    #: Linked JobPost
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), nullable=False)
    jobpost = db.relationship(JobPost, backref=db.backref('postboards',
        lazy='dynamic', cascade='all, delete-orphan'))
    #: Linked Board
    board_id = db.Column(None, db.ForeignKey('board.id'), nullable=False)
    board = db.relationship(Board, backref=db.backref('boardposts',
        lazy='dynamic', cascade='all, delete-orphan'))
    #: Is this listing pinned on this board?
    pinned = db.Column(db.Boolean, default=False, nullable=False)

    # TODO: Make proxies to link Board and JobPost directly to each other


def _jobpost_link_to_board(self, board):
    return BoardJobPost.query.filter_by(jobpost=self, board=board).one_or_none()

JobPost.link_to_board = _jobpost_link_to_board


def _jobpost_add_to(self, board):
    link = self.link_to_board(board)
    if not link:
        link = BoardJobPost(board=board, jobpost=self)
        db.session.add(link)
    return link

JobPost.add_to = _jobpost_add_to
