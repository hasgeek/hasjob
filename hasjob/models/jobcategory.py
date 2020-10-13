from . import BaseNameMixin, db

__all__ = ['JobCategory']


class JobCategory(BaseNameMixin, db.Model):
    __tablename__ = 'jobcategory'

    #: Sequence number for sorting in the display list (to be deprecated by boards)
    seq = db.Column(db.Integer, nullable=False, default=0)
    #: This job category is an option for jobs on Hasjob (to be deprecated by boards)
    public = db.Column(db.Boolean, nullable=False, default=True)
    #: This job category is private and not available as an option in boards
    private = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return '<JobCategory %d %s%s>' % (
            self.seq,
            self.title,
            ' (private)' if self.private else '',
        )
