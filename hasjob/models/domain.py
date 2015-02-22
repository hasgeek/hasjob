# -*- coding: utf-8 -*-

from baseframe.staticdata import webmail_domains
from . import db, BaseMixin
from .user import User

__all__ = ['Domain']


class Domain(BaseMixin, db.Model):
    """
    A DNS domain affiliated with a job post.
    """
    __tablename__ = 'domain'
    #: DNS name of this domain
    name = db.Column(db.Unicode(80), nullable=False, unique=True)
    #: Is this a known webmail domain?
    is_webmail = db.Column(db.Boolean, default=False, nullable=False)
    #: Is this domain banned from listing on Hasjob? (Recruiter, etc)
    is_banned = db.Column(db.Boolean, default=False, nullable=False)
    #: Who banned it?
    banned_by_id = db.Column(None, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    banned_by = db.relationship(User)
    #: Reason for banning
    banned_reason = db.Column(db.Unicode(250), nullable=True)

    def __repr__(self):
        flags = [' webmail' if self.is_webmail else '', ' banned' if self.is_banned else '']
        return '<Domain %s%s>' % (self.name, ''.join(flags))

    @classmethod
    def get(cls, name, create=False):
        name = name.lower()
        result = cls.query.filter_by(name=name).one_or_none()
        if not result and create:
            result = cls(name=name, is_webmail=name in webmail_domains)
            db.session.add(result)
        return result
