# -*- coding: utf-8 -*-

from sqlalchemy import DDL, event
from coaster.sqlalchemy import Query
from coaster.utils import make_name, LabeledEnum
from baseframe import __
from . import db, TimestampMixin, BaseNameMixin
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


class Tag(BaseNameMixin, db.Model):
    """
    A tag extracted from text.
    """
    __tablename__ = 'tag'
    __name_length__ = __title_length__ = 80
    public = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return "<Tag %r>" % self.tag

    def __unicode__(self):
        return self.tag

    @classmethod
    def get(cls, tag, create=False):
        name = make_name(tag)
        ob = cls.query.filter_by(name=name).one_or_none()
        if create and not ob:
            ob = cls(title=tag[:cls.__name_length__])
            db.session.add(ob)
        return ob


class JobPostTag(TimestampMixin, db.Model):
    """
    A tag in a tag set.
    """
    __tablename__ = 'jobpost_tag'
    query_class = Query
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), nullable=False, primary_key=True)
    jobpost = db.relationship(JobPost, backref=db.backref('taglinks', cascade='all, delete-orphan'))
    tag_id = db.Column(None, db.ForeignKey('tag.id'), nullable=False, primary_key=True, index=True)
    tag = db.relationship(Tag, backref=db.backref('taglinks', cascade='all, delete-orphan'))
    status = db.Column(db.SmallInteger, nullable=False)

    def __repr__(self):
        return "<JobPostTag %r for %s>" % (self.tag.tag, self.jobpost.hashid)

    @property
    def status_label(self):
        return TAG_TYPE[self.status]

    @classmethod
    def get(cls, jobpost, tag):
        return cls.query.filter_by(jobpost=jobpost, tag=tag).one_or_none()
