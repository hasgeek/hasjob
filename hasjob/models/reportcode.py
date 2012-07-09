from hasjob.models import db


class ReportCode(db.Model):
    __tablename__ = 'reportcode'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(250), nullable=False, unique=True)
    title = db.Column(db.Unicode(250), nullable=False)
    seq = db.Column(db.Integer, nullable=False, default=0)
    public = db.Column(db.Boolean, nullable=False, default=True)
