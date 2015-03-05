# -*- coding: utf-8 -*-

from sqlalchemy import event, DDL
from sqlalchemy.dialects.postgresql import TSVECTOR
from flask import url_for
from baseframe.staticdata import webmail_domains
from . import db, BaseMixin
from .user import User
from .jobpost import JobPost

__all__ = ['Domain']


class Domain(BaseMixin, db.Model):
    """
    A DNS domain affiliated with a job post.
    """
    __tablename__ = 'domain'
    #: DNS name of this domain
    name = db.Column(db.Unicode(80), nullable=False, unique=True)
    #: Title of the employer at this domain
    title = db.Column(db.Unicode(250), nullable=True)
    #: Legal title
    legal_title = db.Column(db.Unicode(250), nullable=True)
    #: Description
    description = db.Column(db.UnicodeText, nullable=True)
    #: Logo URL
    logo_url = db.Column(db.Unicode(250), nullable=True)
    #: Is this a known webmail domain?
    is_webmail = db.Column(db.Boolean, default=False, nullable=False)
    #: Is this domain banned from listing on Hasjob? (Recruiter, etc)
    is_banned = db.Column(db.Boolean, default=False, nullable=False)
    #: Who banned it?
    banned_by_id = db.Column(None, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    banned_by = db.relationship(User)
    #: Reason for banning
    banned_reason = db.Column(db.Unicode(250), nullable=True)
    #: Search vector
    search_vector = db.Column(TSVECTOR, nullable=True)

    def __repr__(self):
        flags = [' webmail' if self.is_webmail else '', ' banned' if self.is_banned else '']
        return '<Domain %s%s>' % (self.name, ''.join(flags))

    @property
    def use_title(self):
        return self.title or self.name

    @property
    def has_profile(self):
        return bool(self.title and self.description)

    def editor_is(self, user):
        """
        Is this user authorized to edit this domain?
        """
        if not user:
            return False
        if JobPost.query.filter_by(domain=self, user=user).notempty():
            return True
        return False

    def url_for(self, action='view', _external=False, **kwargs):
        if action == 'view':
            return url_for('browse_by_domain', domain=self.name, _external=_external, **kwargs)
        elif action == 'edit':
            return url_for('domain_edit', domain=self.name, _external=_external, **kwargs)

    @classmethod
    def get(cls, name, create=False):
        name = name.lower()
        result = cls.query.filter_by(name=name).one_or_none()
        if not result and create:
            result = cls(name=name, is_webmail=name in webmail_domains)
            db.session.add(result)
        return result


create_domain_search_trigger = DDL(
    '''
    CREATE FUNCTION domain_search_vector_update() RETURNS TRIGGER AS $$
    BEGIN
        NEW.search_vector = to_tsvector('english', COALESCE(NEW.name, '') || ' ' || COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.legal_title, '') || ' ' || COALESCE(NEW.description, ''));
        RETURN NEW;
    END
    $$ LANGUAGE 'plpgsql';

    CREATE TRIGGER domain_search_vector_trigger BEFORE INSERT OR UPDATE ON domain
    FOR EACH ROW EXECUTE PROCEDURE domain_search_vector_update();

    CREATE INDEX ix_domain_search_vector ON domain USING gin(search_vector);
    ''')

event.listen(Domain.__table__, 'after_create',
    create_domain_search_trigger.execute_if(dialect='postgresql'))
