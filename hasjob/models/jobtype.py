from __future__ import annotations

from . import BaseNameMixin, Model, sa

__all__ = ['JobType']


class JobType(BaseNameMixin, Model):
    __tablename__ = 'jobtype'

    #: Sequence number for sorting in the display list (to be deprecated by boards)
    seq = sa.orm.mapped_column(sa.Integer, nullable=False, default=0)
    #: This job type is an option for jobs on Hasjob (to be deprecated by boards)
    public = sa.orm.mapped_column(sa.Boolean, nullable=False, default=True)
    #: This job type is private and not available as an option in boards
    private = sa.orm.mapped_column(sa.Boolean, nullable=False, default=False)
    #: Jobs with this type may offer to pay nothing
    nopay_allowed = sa.orm.mapped_column(sa.Boolean, nullable=False, default=True)
    #: Jobs with this type may be listed from a webmail domain
    webmail_allowed = sa.orm.mapped_column(sa.Boolean, nullable=False, default=True)

    def __repr__(self):
        return '<JobType %d %s%s>' % (
            self.seq,
            self.title,
            ' (private)' if self.private else '',
        )
