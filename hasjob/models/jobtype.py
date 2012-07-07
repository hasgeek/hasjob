from hasjob.models import db

class JobType(db.Model):
    __tablename__ = 'jobtype'
    idref = 'type'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(250), nullable=False, unique=True)
    title = db.Column(db.Unicode(250), nullable=False)
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
