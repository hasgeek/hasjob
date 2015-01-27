# -*- coding: utf-8 -*-

from flask.ext.lastuser.sqlalchemy import UserBase2, TeamBase2
from . import db

__all__ = ['User', 'Team']


class User(UserBase2, db.Model):
    __tablename__ = 'user'

    blocked = db.Column(db.Boolean, nullable=False, default=False)


class Team(TeamBase2, db.Model):
    __tablename__ = 'team'
