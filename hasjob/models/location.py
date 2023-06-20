from __future__ import annotations

from flask import url_for

from . import BaseScopedNameMixin, Model, backref, relationship, sa
from .board import Board

__all__ = ['Location']


class Location(BaseScopedNameMixin, Model):
    """
    A location where jobs are listed, using geonameid for primary key. Scoped to a board
    """

    __tablename__ = 'location'
    id = sa.orm.mapped_column(  # noqa: A003  # type: ignore[assignment]
        sa.Integer, primary_key=True, autoincrement=False
    )
    geonameid = sa.orm.synonym('id')
    board_id = sa.orm.mapped_column(
        None, sa.ForeignKey('board.id'), nullable=False, primary_key=True, index=True
    )
    board = relationship(
        Board,
        backref=backref('locations', lazy='dynamic', cascade='all, delete-orphan'),
    )
    parent = sa.orm.synonym('board')

    #: Landing page description
    description = sa.orm.mapped_column(sa.UnicodeText, nullable=True)

    __table_args__ = (sa.UniqueConstraint('board_id', 'name'),)

    def url_for(self, action='view', **kwargs):
        subdomain = self.board.name if self.board.not_root else None
        if action == 'view':
            return url_for(
                'browse_by_location', location=self.name, subdomain=subdomain, **kwargs
            )
        elif action == 'edit':
            return url_for(
                'location_edit', name=self.name, subdomain=subdomain, **kwargs
            )

    @classmethod
    def get(cls, name, board):
        return cls.query.filter_by(name=name, board=board).one_or_none()
