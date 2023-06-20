from __future__ import annotations

from . import BaseNameMixin, Model, sa

__all__ = ['JobCategory']


class JobCategory(BaseNameMixin, Model):
    __tablename__ = 'jobcategory'

    #: Sequence number for sorting in the display list (to be deprecated by boards)
    seq = sa.orm.mapped_column(sa.Integer, nullable=False, default=0)
    #: This job category is an option for jobs on Hasjob (to be deprecated by boards)
    public = sa.orm.mapped_column(sa.Boolean, nullable=False, default=True)
    #: This job category is private and not available as an option in boards
    private = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False)

    def __repr__(self):
        return '<JobCategory %d %s%s>' % (
            self.seq,
            self.title,
            ' (private)' if self.private else '',
        )
