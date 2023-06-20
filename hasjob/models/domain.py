from __future__ import annotations

from flask import url_for
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import TSVECTOR
from werkzeug.utils import cached_property

from baseframe.utils import is_public_email_domain

from ..utils import escape_for_sql_like
from . import BaseMixin, Model, backref, db, relationship, sa
from .jobpost import JobPost
from .user import User

__all__ = ['Domain']


class Domain(BaseMixin, Model):
    """
    A DNS domain affiliated with a job post.
    """

    __tablename__ = 'domain'
    #: DNS name of this domain (domain.tld)
    name = sa.orm.mapped_column(sa.Unicode(80), nullable=False, unique=True)
    #: Title of the employer at this domain
    title = sa.orm.mapped_column(sa.Unicode(250), nullable=True)
    #: Legal title
    legal_title = sa.orm.mapped_column(sa.Unicode(250), nullable=True)
    #: Description
    description = sa.orm.mapped_column(sa.UnicodeText, nullable=True)
    #: Logo URL
    logo_url = sa.orm.mapped_column(sa.Unicode(250), nullable=True)
    #: Is this a known webmail domain?
    is_webmail = sa.orm.mapped_column(sa.Boolean, default=False, nullable=False)
    #: Is this domain banned from listing on Hasjob? (Recruiter, etc)
    is_banned = sa.orm.mapped_column(sa.Boolean, default=False, nullable=False)
    #: Who banned it?
    banned_by_id = sa.orm.mapped_column(
        None, sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True
    )
    banned_by = relationship(User)
    #: Banned when?
    banned_at = sa.orm.mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    #: Reason for banning
    banned_reason = sa.orm.mapped_column(sa.Unicode(250), nullable=True)
    #: Jobposts using this domain
    jobposts = relationship(JobPost, lazy='dynamic', backref=backref('domain'))
    #: Search vector
    search_vector = sa.orm.mapped_column(TSVECTOR, nullable=True, deferred=True)

    def __repr__(self):
        flags = [
            ' webmail' if self.is_webmail else '',
            ' banned' if self.is_banned else '',
        ]
        return '<Domain {}{}>'.format(self.name, ''.join(flags))

    @property
    def use_title(self):
        if self.title:
            return self.title
        if self.is_webmail:
            return self.name
        post = (
            self.jobposts.filter(JobPost.state.ARCHIVED)
            .order_by(JobPost.datetime.desc())
            .first()
        )
        if post:
            return post.company_name
        return self.name

    @property
    def has_profile(self):
        return bool(self.title and self.description)

    @cached_property
    def effective_logo_url(self):
        """
        Returns logo_url if present,
        else returns the logo from its most recent job post
        """
        if self.logo_url:
            return self.logo_url
        else:
            if self.is_webmail:
                return None
            post = (
                self.jobposts.filter(
                    JobPost.company_logo.isnot(None), JobPost.state.ARCHIVED
                )
                .order_by(JobPost.datetime.desc())
                .first()
            )
            return post.url_for('logo', _external=True) if post else None

    def editor_is(self, user):
        """
        Is this user authorized to edit this domain?
        """
        if not user:
            return False
        if (
            JobPost.query.filter_by(domain=self, user=user)
            .filter(~(JobPost.state.UNPUBLISHED))
            .notempty()
        ):
            return True
        return False

    def url_for(self, action='view', _external=False, **kwargs):
        if action == 'view':
            return url_for(
                'browse_by_domain', domain=self.name, _external=_external, **kwargs
            )
        elif action == 'edit':
            return url_for(
                'domain_edit', domain=self.name, _external=_external, **kwargs
            )

    @classmethod
    def get(cls, name, create=False):
        name = name.lower()
        result = cls.query.filter_by(name=name).one_or_none()
        if not result and create:
            result = cls(
                name=name, is_webmail=is_public_email_domain(name, default=False)
            )
            db.session.add(result)
        return result

    @classmethod
    def autocomplete(cls, prefix):
        return cls.query.filter(
            cls.name.ilike(escape_for_sql_like(prefix)), cls.is_banned.is_(False)
        ).all()


create_domain_search_trigger = sa.DDL(
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
    '''
)

event.listen(
    Domain.__table__,
    'after_create',
    create_domain_search_trigger.execute_if(dialect='postgresql'),
)
