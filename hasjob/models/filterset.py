from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.associationproxy import association_proxy

from ..extapi import location_geodata
from . import BaseScopedNameMixin, Model, db, relationship, sa
from .board import Board
from .domain import Domain
from .jobcategory import JobCategory
from .jobtype import JobType
from .tag import Tag

__all__ = ['Filterset']


filterset_jobtype_table = sa.Table(
    'filterset_jobtype',
    Model.metadata,
    sa.Column('filterset_id', None, sa.ForeignKey('filterset.id'), primary_key=True),
    sa.Column(
        'jobtype_id', None, sa.ForeignKey('jobtype.id'), primary_key=True, index=True
    ),
    sa.Column(
        'created_at',
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        default=sa.func.utcnow(),
    ),
)


filterset_jobcategory_table = sa.Table(
    'filterset_jobcategory',
    Model.metadata,
    sa.Column('filterset_id', None, sa.ForeignKey('filterset.id'), primary_key=True),
    sa.Column(
        'jobcategory_id',
        None,
        sa.ForeignKey('jobcategory.id'),
        primary_key=True,
        index=True,
    ),
    sa.Column(
        'created_at',
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        default=sa.func.utcnow(),
    ),
)


filterset_tag_table = sa.Table(
    'filterset_tag',
    Model.metadata,
    sa.Column('filterset_id', None, sa.ForeignKey('filterset.id'), primary_key=True),
    sa.Column('tag_id', None, sa.ForeignKey('tag.id'), primary_key=True, index=True),
    sa.Column(
        'created_at',
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        default=sa.func.utcnow(),
    ),
)

filterset_domain_table = sa.Table(
    'filterset_domain',
    Model.metadata,
    sa.Column('filterset_id', None, sa.ForeignKey('filterset.id'), primary_key=True),
    sa.Column(
        'domain_id', None, sa.ForeignKey('domain.id'), primary_key=True, index=True
    ),
    sa.Column(
        'created_at',
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        default=sa.func.utcnow(),
    ),
)


class Filterset(BaseScopedNameMixin, Model):
    """
    Store filters to display a filtered set of jobs scoped by a board on SEO friendly URLs

    Eg: `https://hasjob.co/f/machine-learning-jobs-in-bangalore`
    """

    __tablename__ = 'filterset'

    board_id = sa.orm.mapped_column(
        None, sa.ForeignKey('board.id'), nullable=False, index=True
    )
    board = relationship(Board)
    parent = sa.orm.synonym('board')

    #: Welcome text
    description = sa.orm.mapped_column(sa.UnicodeText, nullable=False, default='')

    #: Associated job types
    types = relationship(JobType, secondary=filterset_jobtype_table)
    #: Associated job categories
    categories = relationship(JobCategory, secondary=filterset_jobcategory_table)
    tags = relationship(Tag, secondary=filterset_tag_table)
    auto_tags = association_proxy(
        'tags', 'title', creator=lambda t: Tag.get(t, create=True)
    )
    domains = relationship(Domain, secondary=filterset_domain_table)
    auto_domains = association_proxy('domains', 'name', creator=lambda d: Domain.get(d))
    geonameids = sa.orm.mapped_column(
        postgresql.ARRAY(sa.Integer(), dimensions=1), default=[], nullable=False
    )
    remote_location = sa.orm.mapped_column(
        sa.Boolean, default=False, nullable=False, index=True
    )
    pay_currency = sa.orm.mapped_column(sa.CHAR(3), nullable=True, index=True)
    pay_cash = sa.orm.mapped_column(sa.Integer, nullable=True, index=True)
    equity = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False, index=True)
    keywords = sa.orm.mapped_column(
        sa.Unicode(250), nullable=False, default='', index=True
    )

    def __repr__(self):
        return f'<Filterset {self.board.title} {self.title!r}>'

    @classmethod
    def get(cls, board, name):
        return cls.query.filter(cls.board == board, cls.name == name).one_or_none()

    def url_for(self, action='view', _external=True, **kwargs):
        kwargs.setdefault('subdomain', self.board.name if self.board.not_root else None)
        return super().url_for(action, name=self.name, _external=_external, **kwargs)

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
            'q': self.keywords,
        }

    @classmethod
    def from_filters(cls, board, filters):
        basequery = cls.query.filter(cls.board == board)

        if filters.get('t'):
            basequery = (
                basequery.join(filterset_jobtype_table)
                .join(JobType)
                .filter(JobType.name.in_(filters['t']))
                .group_by(Filterset.id)
                .having(
                    sa.func.count(filterset_jobtype_table.c.filterset_id)
                    == len(filters['t'])
                )
            )
        else:
            basequery = basequery.filter(
                ~(
                    sa.exists(
                        sa.select(1).where(
                            Filterset.id == filterset_jobtype_table.c.filterset_id
                        )
                    )
                )
            )

        if filters.get('c'):
            basequery = (
                basequery.join(filterset_jobcategory_table)
                .join(JobCategory)
                .filter(JobCategory.name.in_(filters['c']))
                .group_by(Filterset.id)
                .having(
                    sa.func.count(filterset_jobcategory_table.c.filterset_id)
                    == len(filters['c'])
                )
            )
        else:
            basequery = basequery.filter(
                ~(
                    sa.exists(
                        sa.select(1).where(
                            Filterset.id == filterset_jobcategory_table.c.filterset_id
                        )
                    )
                )
            )

        if filters.get('k'):
            basequery = (
                basequery.join(filterset_tag_table)
                .join(Tag)
                .filter(Tag.name.in_(filters['k']))
                .group_by(Filterset.id)
                .having(
                    sa.func.count(filterset_tag_table.c.filterset_id)
                    == len(filters['k'])
                )
            )
        else:
            basequery = basequery.filter(
                ~(
                    sa.exists(
                        sa.select(1).where(
                            Filterset.id == filterset_tag_table.c.filterset_id
                        )
                    )
                )
            )

        if filters.get('d'):
            basequery = (
                basequery.join(filterset_domain_table)
                .join(Domain)
                .filter(Domain.name.in_(filters['d']))
                .group_by(Filterset.id)
                .having(
                    sa.func.count(filterset_domain_table.c.filterset_id)
                    == len(filters['d'])
                )
            )
        else:
            basequery = basequery.filter(
                ~(
                    sa.exists(
                        sa.select(1).where(
                            Filterset.id == filterset_domain_table.c.filterset_id
                        )
                    )
                )
            )

        if filters.get('l'):
            basequery = basequery.filter(cls.geonameids == sorted(filters['l']))
        else:
            basequery = basequery.filter(cls.geonameids == [])

        if filters.get('equity'):
            basequery = basequery.filter(cls.equity.is_(True))
        else:
            basequery = basequery.filter(cls.equity.is_(False))

        if filters.get('pay') and filters.get('currency'):
            basequery = basequery.filter(
                cls.pay_cash == filters['pay'], cls.pay_currency == filters['currency']
            )
        else:
            basequery = basequery.filter(
                cls.pay_cash.is_(None), cls.pay_currency.is_(None)
            )

        if filters.get('q'):
            basequery = basequery.filter(cls.keywords == filters['q'])
        else:
            basequery = basequery.filter(cls.keywords == '')

        if filters.get('anywhere'):
            basequery = basequery.filter(cls.remote_location.is_(True))
        else:
            basequery = basequery.filter(cls.remote_location.is_(False))

        return basequery.one_or_none()


@event.listens_for(Filterset, 'before_update')
@event.listens_for(Filterset, 'before_insert')
def _format_and_validate(mapper, connection, target):
    with db.session.no_autoflush:
        if target.geonameids:
            target.geonameids = sorted(target.geonameids)

        filterset = Filterset.from_filters(target.board, target.to_filters())
        if filterset and filterset.id != target.id:
            raise ValueError(
                "There already exists a filter set with this filter criteria"
            )


create_geonameids_trigger = sa.DDL(
    '''
    CREATE INDEX ix_filterset_geonameids on filterset USING gin (geonameids);
'''
)

event.listen(
    Filterset.__table__,
    'after_create',
    create_geonameids_trigger.execute_if(dialect='postgresql'),
)
