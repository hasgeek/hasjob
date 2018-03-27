# -*- coding: utf-8 -*-

from coaster.sqlalchemy import Query, failsafe_add
from coaster.utils import make_name, LabeledEnum
from baseframe import __
from . import db, TimestampMixin, BaseNameMixin, POST_STATE
from ..utils import escape_for_sql_like
from .jobpost import JobPost

__all__ = ['TAG_TYPE', 'Tag', 'JobPostTag']


class TAG_TYPE(LabeledEnum):
    # The NLP parser added this tag
    AUTO = (0, 'auto', __("Automatic"))
    # A user confirmed an automatic tag
    CONFIRMED = (1, 'confirmed', __("Confirmed"))
    # A user manually added this tag
    MANUAL = (2, 'manual', __("Manual"))
    # A reviewer confirmed this tag
    REVIEWED = (3, 'reviewed', __("Reviewed"))
    # A user or reviewer deleted this automatic tag
    DELETED = (4, 'deleted', __("Deleted"))
    # A re-run of the parser found this auto-tag missing
    # in the latest results and so removed it
    REMOVED = (5, 'removed', __("Removed"))
    # Tag is currently present
    TAG_PRESENT = {AUTO, CONFIRMED, MANUAL, REVIEWED}


class Tag(BaseNameMixin, db.Model):
    """
    A tag extracted from text.
    """
    __tablename__ = 'tag'
    __name_length__ = __title_length__ = 80
    public = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return "<Tag %r>" % self.title

    def __unicode__(self):
        return self.title

    @classmethod
    def get(cls, tag, create=False):
        title = tag[:cls.__name_length__]
        name = make_name(title)
        ob = cls.query.filter_by(name=name).one_or_none()
        if create and not ob:
            ob = cls(name=name, title=title)
            ob = failsafe_add(db.session, ob, name=name)
        return ob

    @classmethod
    def autocomplete(cls, prefix):
        search = escape_for_sql_like(make_name(prefix))
        return cls.query.filter(cls.name.like(search), cls.public == True).all()  # NOQA


class JobPostTag(TimestampMixin, db.Model):
    """
    A tag in a tag set.
    """
    __tablename__ = 'jobpost_tag'
    query_class = Query
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), nullable=False, primary_key=True)
    jobpost = db.relationship(JobPost, backref=db.backref('taglinks', cascade='all, delete-orphan'))
    tag_id = db.Column(None, db.ForeignKey('tag.id'), nullable=False, primary_key=True, index=True)
    tag = db.relationship(Tag, lazy='joined', backref=db.backref('taglinks', cascade='all, delete-orphan'))
    status = db.Column(db.SmallInteger, nullable=False)

    def __repr__(self):
        return "<JobPostTag %r for %s>" % (self.tag.title, self.jobpost.hashid)

    @property
    def status_label(self):
        return TAG_TYPE[self.status]

    @classmethod
    def get(cls, jobpost, tag):
        return cls.query.filter_by(jobpost=jobpost, tag=tag).one_or_none()


def related_posts(self, limit=12):
    # TODO: One JobPostTag moves to statemanager, use sqlalchemy to get rid of this raw query
    return db.session.query(JobPost).options(*JobPost._defercols).from_statement(db.text(
        '''SELECT jobpost.id, jobpost.hashid, jobpost.datetime, jobpost.headline, jobpost.headlineb,
            jobpost.location, jobpost.company_name, jobpost.type_id, jobpost.category_id, jobpost.status,
            jobpost.pay_type, jobpost.pay_currency, jobpost.pay_cash_min, jobpost.pay_cash_max,
            jobpost.pay_equity_min, jobpost.pay_equity_max, jobpost.email_domain
            FROM (
                SELECT jobpost_tag.jobpost_id AS jobpost_id, COUNT(*) AS count FROM jobpost_tag, jobpost
                WHERE jobpost.id = jobpost_tag.jobpost_id AND tag_id IN (
                    SELECT tag_id FROM jobpost_tag WHERE jobpost_id=:id)
                AND jobpost_id != :id AND jobpost.status IN :listed
                AND jobpost.datetime >= NOW() AT TIME ZONE 'UTC' - INTERVAL '30 days'
                AND jobpost_tag.status IN :tag_present
                GROUP BY jobpost_tag.jobpost_id ORDER BY count DESC LIMIT :limit) AS matches, jobpost
            WHERE jobpost.id = matches.jobpost_id;'''
        )).params(id=self.id, listed=tuple(POST_STATE.PUBLIC), limit=limit, tag_present=tuple(TAG_TYPE.TAG_PRESENT))


JobPost.related_posts = related_posts
