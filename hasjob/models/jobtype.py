# -*- coding: utf-8 -*-

from . import db, BaseNameMixin

__all__ = ['JobType']


class JobType(BaseNameMixin, db.Model):
    __tablename__ = 'jobtype'

    #: Sequence number for sorting in the display list (to be deprecated by boards)
    seq = db.Column(db.Integer, nullable=False, default=0)
    #: This job type is an option for jobs on Hasjob (to be deprecated by boards)
    public = db.Column(db.Boolean, nullable=False, default=True)
    #: This job type is private and not available as an option in boards
    private = db.Column(db.Boolean, nullable=False, default=False)
    #: Jobs with this type may offer to pay nothing
    nopay_allowed = db.Column(db.Boolean, nullable=False, default=True)
    #: Jobs with this type may be listed from a webmail domain
    webmail_allowed = db.Column(db.Boolean, nullable=False, default=True)

    def __str__(self):
        return '<JobType %d %s%s>' % (self.seq, self.title, ' (private)' if self.private else '')
