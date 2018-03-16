# -*- coding: utf-8 -*-

from flask import url_for
from sqlalchemy.dialects import postgresql
from sqlalchemy import event, DDL
from . import db, BaseScopedNameMixin, JobType, JobCategory, Tag, Domain, Board

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


class FilteredView(BaseScopedNameMixin, db.Model):
    """
    Store filters to display a filtered set of jobs scoped by a board on SEO friendly URLs

    Eg: `https://hasjob.co/f/machine-learning-jobs-in-bangalore`
    """

    __tablename__ = 'filtered_view'

    board_id = db.Column(None, db.ForeignKey('board.id'), nullable=False, index=True)
    board = db.relationship(Board)
    parent = db.synonym('board')

    #: Welcome text
    description = db.Column(db.UnicodeText, nullable=False, default=u'')

    #: Associated job types
    types = db.relationship(JobType, secondary=filteredview_jobtype_table)
    #: Associated job categories
    categories = db.relationship(JobCategory, secondary=filteredview_jobcategory_table)
    tags = db.relationship(Tag, secondary=filteredview_tag_table)
    domains = db.relationship(Domain, secondary=filteredview_domain_table)
    location_geonameids = db.Column(postgresql.ARRAY(db.Integer(), dimensions=1), nullable=True, index=True)
    remote_location = db.Column(db.Boolean, default=False, nullable=False, index=True)
    pay_currency = db.Column(db.CHAR(3), nullable=True, index=True)
    pay_cash_min = db.Column(db.Integer, nullable=True, index=True)
    equity = db.Column(db.Boolean, nullable=False, default=False, index=True)
    keywords = db.Column(db.Unicode(250), nullable=False, default=u'', index=True)

    def __repr__(self):
        return '<Filtered view %s "%s">' % (self.board.title, self.title)

    @classmethod
    def get(cls, board, name):
        return cls.query.filter(cls.board == board, cls.name == name).first_or_404()

    def url_for(self, action='view', _external=False, **kwargs):
        if action == 'view':
            subdomain = self.board.name if self.board.not_root else None
            return url_for('filtered_view', subdomain=subdomain, name=self.name, _external=_external)

    def to_filters(self, translate_geonameids=True):
        from hasjob.views.helper import location_geodata

        location_names = []
        if translate_geonameids and self.location_geonameids:
            location_dict = location_geodata(self.location_geonameids)
            for geonameid in self.location_geonameids:
                location_names.append(location_dict[geonameid]['name'])

        return {
            't': [jobtype.name for jobtype in self.types],
            'c': [jobcategory.name for jobcategory in self.categories],
            'l': location_names if translate_geonameids else self.location_geonameids,
            'currency': self.pay_currency,
            'pay': self.pay_cash_min,
            'equity': self.equity,
            'anywhere': self.remote_location
        }

    @classmethod
    def from_filters(cls, board, filters):
        # TODO sort location_geonameids for querying?
        basequery = cls.query.filter(cls.board == board)

        if filters.get('t'):
            basequery = basequery.join(
                filteredview_jobtype_table).join(
                JobType).filter(JobType.name.in_(filters['t']))
        else:
            basequery = basequery.filter(~cls.id.in_(db.select([filteredview_jobtype_table.c.filtered_view_id])))

        if filters.get('c'):
            basequery = basequery.join(
                filteredview_jobcategory_table).join(
                JobCategory).filter(JobCategory.name.in_(filters['c']))
        else:
            basequery = basequery.filter(~cls.id.in_(db.select([filteredview_jobcategory_table.c.filtered_view_id])))

        if filters.get('l'):
            basequery = basequery.filter(cls.location_geonameids == sorted(filters['l']))
        else:
            basequery = basequery.filter(cls.location_geonameids == None)

        if filters.get('equity'):
            basequery = basequery.filter(cls.equity == True)
        else:
            basequery = basequery.filter(cls.equity == False)

        if filters.get('pay') and filters.get('currency'):
            basequery = basequery.filter(cls.pay_cash_min == filters['pay'],
                cls.pay_currency == filters['currency'])
        else:
            basequery = basequery.filter(cls.pay_cash_min == None, cls.pay_currency == None)

        if filters.get('keywords'):
            basequery = basequery.filter(cls.keywords == filters['keywords'])
        else:
            basequery = basequery.filter(cls.keywords == '')

        if filters.get('anywhere'):
            basequery = basequery.filter(cls.remote_location == True)
        else:
            basequery = basequery.filter(cls.remote_location == False)

        return basequery.one_or_none()


@event.listens_for(FilteredView, 'before_update')
@event.listens_for(FilteredView, 'before_insert')
def _format_and_validate(mapper, connection, target):
    if target.location_geonameids:
        target.location_geonameids = sorted(target.location_geonameids)

    if FilteredView.from_filters(target.board, target.to_filters(translate_geonameids=False)):
        raise ValueError("There already exists a filtered view with this filter criteria")

create_location_geonameids_trigger = DDL('''
    CREATE INDEX idx_filtered_view_location_geonameids on filtered_view USING gin (location_geonameids);
''')

event.listen(FilteredView.__table__, 'after_create',
    create_location_geonameids_trigger.execute_if(dialect='postgresql'))
