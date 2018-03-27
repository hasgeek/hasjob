# -*- coding: utf-8 -*-

from sqlalchemy.dialects import postgresql
from sqlalchemy import event, DDL
from sqlalchemy.ext.associationproxy import association_proxy
from . import db, BaseScopedNameMixin, JobType, JobCategory, Tag, Domain, Board
from ..extapi import location_geodata


__all__ = ['Filterset']


filterset_jobtype_table = db.Table('filterset_jobtype', db.Model.metadata,
    db.Column('filterset_id', None, db.ForeignKey('filterset.id'), primary_key=True),
    db.Column('jobtype_id', None, db.ForeignKey('jobtype.id'), primary_key=True, index=True),
    db.Column('created_at', db.DateTime, nullable=False, default=db.func.utcnow())
)


filterset_jobcategory_table = db.Table('filterset_jobcategory', db.Model.metadata,
    db.Column('filterset_id', None, db.ForeignKey('filterset.id'), primary_key=True),
    db.Column('jobcategory_id', None, db.ForeignKey('jobcategory.id'), primary_key=True, index=True),
    db.Column('created_at', db.DateTime, nullable=False, default=db.func.utcnow())
)


filterset_tag_table = db.Table('filterset_tag', db.Model.metadata,
    db.Column('filterset_id', None, db.ForeignKey('filterset.id'), primary_key=True),
    db.Column('tag_id', None, db.ForeignKey('tag.id'), primary_key=True, index=True),
    db.Column('created_at', db.DateTime, nullable=False, default=db.func.utcnow())
)

filterset_domain_table = db.Table('filterset_domain', db.Model.metadata,
    db.Column('filterset_id', None, db.ForeignKey('filterset.id'), primary_key=True),
    db.Column('domain_id', None, db.ForeignKey('domain.id'), primary_key=True, index=True),
    db.Column('created_at', db.DateTime, nullable=False, default=db.func.utcnow())
)


class Filterset(BaseScopedNameMixin, db.Model):
    """
    Store filters to display a filtered set of jobs scoped by a board on SEO friendly URLs

    Eg: `https://hasjob.co/f/machine-learning-jobs-in-bangalore`
    """

    __tablename__ = 'filterset'

    board_id = db.Column(None, db.ForeignKey('board.id'), nullable=False, index=True)
    board = db.relationship(Board)
    parent = db.synonym('board')

    #: Welcome text
    description = db.Column(db.UnicodeText, nullable=False, default=u'')

    #: Associated job types
    types = db.relationship(JobType, secondary=filterset_jobtype_table)
    #: Associated job categories
    categories = db.relationship(JobCategory, secondary=filterset_jobcategory_table)
    tags = db.relationship(Tag, secondary=filterset_tag_table)
    auto_tags = association_proxy('tags', 'title', creator=lambda t: Tag.get(t, create=True))
    domains = db.relationship(Domain, secondary=filterset_domain_table)
    auto_domains = association_proxy('domains', 'name', creator=lambda d: Domain.get(d))
    geonameids = db.Column(postgresql.ARRAY(db.Integer(), dimensions=1), default=[], nullable=False)
    remote_location = db.Column(db.Boolean, default=False, nullable=False, index=True)
    pay_currency = db.Column(db.CHAR(3), nullable=True, index=True)
    pay_cash = db.Column(db.Integer, nullable=True, index=True)
    equity = db.Column(db.Boolean, nullable=False, default=False, index=True)
    keywords = db.Column(db.Unicode(250), nullable=False, default=u'', index=True)

    def __repr__(self):
        return '<Filterset %s "%s">' % (self.board.title, self.title)

    @classmethod
    def get(cls, board, name):
        return cls.query.filter(cls.board == board, cls.name == name).one_or_none()

    def url_for(self, action='view', _external=True, **kwargs):
        kwargs.setdefault('subdomain', self.board.name if self.board.not_root else None)
        return super(Filterset, self).url_for(action, name=self.name, _external=_external, **kwargs)

    def to_filters(self, translate_geonameids=False):
        location_names = []
        if translate_geonameids and self.geonameids:
            location_dict = location_geodata(self.geonameids)
            for geonameid in self.geonameids:
                # location_geodata returns related geonames as well
                # so we prune it down to our original list
                location_names.append(location_dict[geonameid]['name'])

        return {
            't': [jobtype.name for jobtype in self.types],
            'c': [jobcategory.name for jobcategory in self.categories],
            'k': [tag.name for tag in self.tags],
            'd': [domain.name for domain in self.domains],
            'l': location_names if translate_geonameids else self.geonameids,
            'currency': self.pay_currency,
            'pay': self.pay_cash,
            'equity': self.equity,
            'anywhere': self.remote_location,
            'q': self.keywords
        }

    @classmethod
    def from_filters(cls, board, filters):
        basequery = cls.query.filter(cls.board == board)

        if filters.get('t'):
            basequery = basequery.join(
                filterset_jobtype_table).join(
                JobType).filter(JobType.name.in_(filters['t'])).group_by(Filterset.id).having(
                db.func.count(filterset_jobtype_table.c.filterset_id) == len(filters['t']))
        else:
            basequery = basequery.filter(
                ~db.exists(
                    db.select([1]).where(
                        Filterset.id == filterset_jobtype_table.c.filterset_id
                    )
                )
            )

        if filters.get('c'):
            basequery = basequery.join(
                filterset_jobcategory_table).join(
                JobCategory).filter(JobCategory.name.in_(filters['c'])).group_by(Filterset.id).having(
                db.func.count(filterset_jobcategory_table.c.filterset_id) == len(filters['c']))
        else:
            basequery = basequery.filter(
                ~db.exists(
                    db.select([1]).where(
                        Filterset.id == filterset_jobcategory_table.c.filterset_id
                    )
                )
            )

        if filters.get('k'):
            basequery = basequery.join(
                filterset_tag_table).join(
                Tag).filter(Tag.name.in_(filters['k'])).group_by(Filterset.id).having(
                db.func.count(filterset_tag_table.c.filterset_id) == len(filters['k']))
        else:
            basequery = basequery.filter(
                ~db.exists(
                    db.select([1]).where(
                        Filterset.id == filterset_tag_table.c.filterset_id
                    )
                )
            )

        if filters.get('d'):
            basequery = basequery.join(
                filterset_domain_table).join(
                Domain).filter(Domain.name.in_(filters['d'])).group_by(Filterset.id).having(
                db.func.count(filterset_domain_table.c.filterset_id) == len(filters['d']))
        else:
            basequery = basequery.filter(
                ~db.exists(
                    db.select([1]).where(
                        Filterset.id == filterset_domain_table.c.filterset_id
                    )
                )
            )

        if filters.get('l'):
            basequery = basequery.filter(cls.geonameids == sorted(filters['l']))
        else:
            basequery = basequery.filter(cls.geonameids == [])

        if filters.get('equity'):
            basequery = basequery.filter(cls.equity == True)
        else:
            basequery = basequery.filter(cls.equity == False)

        if filters.get('pay') and filters.get('currency'):
            basequery = basequery.filter(cls.pay_cash == filters['pay'],
                cls.pay_currency == filters['currency'])
        else:
            basequery = basequery.filter(cls.pay_cash == None, cls.pay_currency == None)

        if filters.get('q'):
            basequery = basequery.filter(cls.keywords == filters['q'])
        else:
            basequery = basequery.filter(cls.keywords == '')

        if filters.get('anywhere'):
            basequery = basequery.filter(cls.remote_location == True)
        else:
            basequery = basequery.filter(cls.remote_location == False)

        return basequery.one_or_none()


@event.listens_for(Filterset, 'before_update')
@event.listens_for(Filterset, 'before_insert')
def _format_and_validate(mapper, connection, target):
    with db.session.no_autoflush:
        if target.geonameids:
            target.geonameids = sorted(target.geonameids)

        filterset = Filterset.from_filters(target.board, target.to_filters())
        if filterset and filterset.id != target.id:
            raise ValueError("There already exists a filter set with this filter criteria")

create_geonameids_trigger = DDL('''
    CREATE INDEX ix_filterset_geonameids on filterset USING gin (geonameids);
''')

event.listen(Filterset.__table__, 'after_create',
    create_geonameids_trigger.execute_if(dialect='postgresql'))
