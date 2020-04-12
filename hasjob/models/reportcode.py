# -*- coding: utf-8 -*-

from . import BaseNameMixin, db

__all__ = ['ReportCode']


class ReportCode(BaseNameMixin, db.Model):
    __tablename__ = 'reportcode'

    seq = db.Column(db.Integer, nullable=False, default=0)
    public = db.Column(db.Boolean, nullable=False, default=True)
