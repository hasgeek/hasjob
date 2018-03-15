# -*- coding: utf-8 -*-

from flask import url_for
from sqlalchemy.dialects import postgresql
from . import db, BaseNameMixin, JobType, JobCategory, JobLocation, Tag, Domain, User

__all__ = ['FilteredView']


filteredview_jobtype_table = db.Table('filteredview_jobtype_table', db.Model.metadata,
    db.Column('filtered_view_id', None, db.ForeignKey('filtered_view.id'), primary_key=True),
    db.Column('jobtype_id', None, db.ForeignKey('jobtype.id'), primary_key=True),
    db.Column('created_at', db.DateTime, nullable=False, default=db.func.utcnow())
)


filteredview_jobcategory_table = db.Table('filteredview_jobcategory_table', db.Model.metadata,
    db.Column('filtered_view_id', None, db.ForeignKey('filtered_view.id'), primary_key=True),
    db.Column('jobcategory_id', None, db.ForeignKey('jobcategory.id'), primary_key=True),
    db.Column('created_at', db.DateTime, nullable=False, default=db.func.utcnow())
)


filteredview_tag_table = db.Table('filteredview_tag_table', db.Model.metadata,
    db.Column('filtered_view_id', None, db.ForeignKey('filtered_view.id'), primary_key=True),
    db.Column('tag_id', None, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('created_at', db.DateTime, nullable=False, default=db.func.utcnow())
)

filteredview_domain_table = db.Table('filteredview_domain_table', db.Model.metadata,
    db.Column('filtered_view_id', None, db.ForeignKey('filtered_view.id'), primary_key=True),
    db.Column('domain_id', None, db.ForeignKey('domain.id'), primary_key=True),
    db.Column('created_at', db.DateTime, nullable=False, default=db.func.utcnow())
)


class FilteredView(BaseNameMixin, db.Model):
    """
    Filtered views show a filtered set of jobs at SEO friendly URLs configured by an audience manager.
    """

    __tablename__ = 'filtered_view'

    user_id = db.Column(None, db.ForeignKey('user.id'), primary_key=True, index=True)
    user = db.relationship(User)

    #: Welcome text
    description = db.Column(db.UnicodeText, nullable=False, default=u'')

    #: Associated job types
    types = db.relationship(JobType, secondary=filteredview_jobtype_table)
    #: Associated job categories
    categories = db.relationship(JobCategory, secondary=filteredview_jobcategory_table)
    tags = db.relationship(Tag, secondary=filteredview_tag_table)
    domains = db.relationship(Domain, secondary=filteredview_domain_table)
    location_names = db.Column(postgresql.ARRAY(db.Unicode(), dimensions=1), nullable=True)
    remote_location = db.Column(db.Boolean, default=False, nullable=False)

    pay_currency = db.Column(db.CHAR(3), nullable=True)
    pay_cash_min = db.Column(db.Integer, nullable=True)
    equity = db.Column(db.Boolean, nullable=False, default=False)
    keywords = db.Column(db.UnicodeText, nullable=False, default=u'')

    def __repr__(self):
        return '<Filtered view %s "%s">' % (self.name, self.title)

    def url_for(self, action='view', **kwargs):
        if action == 'view':
            return url_for('filtered_view', name=self.name, **kwargs)
