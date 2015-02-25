# -*- coding: utf-8 -*-

from . import db, BaseNameMixin
from flask import url_for

__all__ = ['Location']


class Location(BaseNameMixin, db.Model):
    """
    A location where jobs are listed, using geonameid for primary key.
    """
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    geonameid = db.synonym('id')

    #: Landing page description
    description = db.Column(db.UnicodeText, nullable=True)

    def url_for(self, action='view', _external=False, **kwargs):
        if action == 'view':
            return url_for('browse_by_location', location=self.name, _external=_external, **kwargs)
        elif action == 'edit':
            return url_for('location_edit', name=self.name, _external=_external, **kwargs)

    @classmethod
    def get(cls, name):
        return cls.query.filter_by(name=name).one_or_none()
