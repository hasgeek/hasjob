# -*- coding: utf-8 -*-

from . import db, BaseScopedNameMixin
from flask import url_for
from .board import Board

__all__ = ['Location']


class Location(BaseScopedNameMixin, db.Model):
    """
    A location where jobs are listed, using geonameid for primary key. Scoped to a board
    """
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    geonameid = db.synonym('id')
    board_id = db.Column(None, db.ForeignKey('board.id'), nullable=False, primary_key=True, index=True)
    parent = db.synonym('board_id')
    board = db.relationship(Board, backref=db.backref('locations', lazy='dynamic', cascade='all, delete-orphan'))

    #: Landing page description
    description = db.Column(db.UnicodeText, nullable=True)

    __table_args__ = (db.UniqueConstraint('board_id', 'name'),)

    def url_for(self, action='view', **kwargs):
        subdomain = self.board.name if self.board.not_root else None
        if action == 'view':
            return url_for('browse_by_location', location=self.name, subdomain=subdomain, **kwargs)
        elif action == 'edit':
            return url_for('location_edit', name=self.name, subdomain=subdomain, **kwargs)

    @classmethod
    def get(cls, name, board):
        return cls.query.filter_by(name=name, board=board).one_or_none()
