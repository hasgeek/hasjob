# -*- coding: utf-8 -*-

from datetime import datetime
from flask.ext.lastuser.sqlalchemy import UserBase2, TeamBase2
from . import db

__all__ = ['User', 'Team', 'UserActiveAt']


class User(UserBase2, db.Model):
    __tablename__ = 'user'

    blocked = db.Column(db.Boolean, nullable=False, default=False)


class Team(TeamBase2, db.Model):
    __tablename__ = 'team'


class UserActiveAt(db.Model):
    active_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, primary_key=True)
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=False, primary_key=True, index=True)
    user = db.relationship(User)
