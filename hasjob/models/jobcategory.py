# -*- coding: utf-8 -*-

from hasjob.models import BaseNameMixin, db

__all__ = ['JobCategory']


class JobCategory(BaseNameMixin, db.Model):
    __tablename__ = 'jobcategory'
    idref = 'category'

    #: Sequence number for sorting in the display list (to be deprecated by boards)
    seq = db.Column(db.Integer, nullable=False, default=0)
    #: This job category is an option for jobs on Hasjob (to be deprecated by boards)
    public = db.Column(db.Boolean, nullable=False, default=True)
    #: This job category is private and not available as an option in boards
    private = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return '<JobCategory %d %s%s>' % (self.seq, self.title, ' (private)' if self.private else '')

    def search_mapping(self):
        """
        Returns a dictionary suitable for search indexing.
        """
        return {'title': self.title,
                'content': self.title,
                'public': self.public,
                'datetime': self.updated_at,
                'idref': u'%s/%s' % (self.idref, self.id),
                }
