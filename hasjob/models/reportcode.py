from __future__ import annotations

from . import BaseNameMixin, Model, sa

__all__ = ['ReportCode']


class ReportCode(BaseNameMixin, Model):
    __tablename__ = 'reportcode'

    seq = sa.orm.mapped_column(sa.Integer, nullable=False, default=0)
    public = sa.orm.mapped_column(sa.Boolean, nullable=False, default=True)
