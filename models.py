# -*- coding: utf-8 -*-

from datetime import datetime
from flaskext.sqlalchemy import SQLAlchemy

from app import app
from utils import random_long_key, random_hash_key, newid

db = SQLAlchemy(app)

class POSTSTATUS:
    DRAFT     = 0 # Being written
    PENDING   = 1 # Pending email verification and payment
    CONFIRMED = 2 # Post is now live on site
    REVIEWED  = 3 # Reviewed and cleared for push channels
    REJECTED  = 4 # Reviewed and rejected as inappropriate
    WITHDRAWN = 5 # Withdrawn by owner


class USERLEVEL:
    USER          = 0 # Just a user
    REVIEWER      = 1 # Reviewer. Allowed to edit
    ADMINISTRATOR = 2 # Admin. Allowed to change job types and categories


class JobType(db.Model):
    __tablename__ = 'jobtype'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(250), nullable=False, unique=True)
    title = db.Column(db.Unicode(250), nullable=False)
    seq = db.Column(db.Integer, nullable=False, default=0)
    public = db.Column(db.Boolean, nullable=False, default=True)

    def __call__(self):
        return self.title


class JobCategory(db.Model):
    __tablename__ = 'jobcategory'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(250), nullable=False, unique=True)
    title = db.Column(db.Unicode(250), nullable=False)
    seq = db.Column(db.Integer, nullable=False, default=0)
    public = db.Column(db.Boolean, nullable=False, default=True)

    def __call__(self):
        return self.title


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    #: userid should match the userid in lastuser
    userid = db.Column(db.String(22), nullable=False, unique=True, default=newid)
    email = db.Column(db.Unicode(250), nullable=False, unique=True)


class JobPost(db.Model):
    __tablename__ = 'jobpost'

    # Metadata
    id = db.Column(db.Integer, primary_key=True)
    hashid = db.Column(db.String(5), nullable=False, unique=True)
    datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Job description
    headline = db.Column(db.Unicode(100), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('jobtype.id'), nullable=False)
    type = db.relation(JobType, primaryjoin=type_id == JobType.id)
    category_id = db.Column(db.Integer, db.ForeignKey('jobcategory.id'), nullable=False)
    category = db.relation(JobCategory, primaryjoin=category_id == JobCategory.id)
    location = db.Column(db.Unicode(80), nullable=False)
    relocation_assist = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.UnicodeText, nullable=False)
    perks = db.Column(db.UnicodeText, nullable=False)
    how_to_apply = db.Column(db.UnicodeText, nullable=False)

    # Company details
    company_name = db.Column(db.Unicode(80), nullable=False)
    company_logo = db.Column(db.Unicode(255), nullable=True)
    company_url = db.Column(db.Unicode(255), nullable=False, default='')
    email = db.Column(db.Unicode(80), nullable=False)

    # Payment, audit and workflow fields
    promocode = db.Column(db.String(40), nullable=True)
    status = db.Column(db.Integer, nullable=False, default=POSTSTATUS.DRAFT)
    ipaddr = db.Column(db.String(45), nullable=False)
    useragent = db.Column(db.Unicode(250), nullable=True)
    edit_key = db.Column(db.String(40), nullable=False, default=random_long_key)
    email_verify_key = db.Column(db.String(40), nullable=False, default=random_long_key)
    email_sent = db.Column(db.Boolean, nullable=False, default=False)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    payment_value = db.Column(db.Integer, nullable=False, default=0)
    payment_received = db.Column(db.Boolean, nullable=False, default=False)
    reviewer = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    review_datetime = db.Column(db.DateTime, nullable=True)
    review_comments = db.Column(db.Unicode(250), nullable=True)

    def is_draft(self):
        return self.status == POSTSTATUS.DRAFT

def unique_hash(model=JobPost):
    """
    Returns a unique hash for a given model
    """
    while 1:
        hashid = random_hash_key()
        if model.query.filter_by(hashid=hashid).count() == 0:
            break
    return hashid
