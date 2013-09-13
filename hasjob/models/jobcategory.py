from hasjob.models import BaseNameMixin, db


class JobCategory(BaseNameMixin, db.Model):
    __tablename__ = 'jobcategory'
    idref = 'category'

    seq = db.Column(db.Integer, nullable=False, default=0)
    public = db.Column(db.Boolean, nullable=False, default=True)

    def __call__(self):
        return self.title

    def search_mapping(self):
        """
        Returns a dictionary suitable for search indexing.
        """
        return {'title': self.title,
                'content': self.title,
                'public': self.public,
                'idref': u'%s/%s' % (self.idref, self.id),
                }
