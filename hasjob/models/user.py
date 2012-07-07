from hasjob.models import db
from hasjob.utils import newid

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    #: userid should match the userid in lastuser
    userid = db.Column(db.String(22), nullable=False, unique=True, default=newid)
    email = db.Column(db.Unicode(250), nullable=False, unique=True)
