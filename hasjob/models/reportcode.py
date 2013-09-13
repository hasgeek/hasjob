from hasjob.models import db, BaseNameMixin


class ReportCode(BaseNameMixin, db.Model):
    __tablename__ = 'reportcode'

    seq = db.Column(db.Integer, nullable=False, default=0)
    public = db.Column(db.Boolean, nullable=False, default=True)
