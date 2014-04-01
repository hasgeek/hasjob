# -*- coding: utf-8 -*-

from pytz import timezone
from werkzeug import cached_property
from . import db, BaseMixin, BaseNameMixin
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
        return '<Board %s %s "%s">' % (self.userid, self.name, self.title)

    @cached_property
    def tz(self):
        return timezone(self.timezone)

    def owner_is(self, user):
        if user is None:
            return False
        if user.userid == self.userid or self.userid in user.organizations_owned_ids():
            return True
        return False


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
