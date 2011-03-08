# -*- coding: utf-8 -*-

from datetime import datetime
from flaskext.sqlalchemy import SQLAlchemy

from app import app
from utils import random_long_key, random_hash_key

db = SQLAlchemy(app)

class POSTSTATUS:
    DRAFT     = 0 # Being written
    PENDING   = 1 # Pending email verification and payment
    CONFIRMED = 2 # Post is now live on site
    REVIEWED  = 3 # Reviewed and cleared for push channels
    REJECTED  = 4 # Reviewed and rejected as inappropriate
    WITHDRAWN = 5 # Withdrawn by owner


class JobPost(db.Model):
    __tablename__ = 'jobpost'

    # Metadata
    id = db.Column(db.Integer, primary_key=True)
    hashid = db.Column(db.Text(5), nullable=False, unique=True)
    datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Job description
    headline = db.Column(db.Unicode(100), nullable=False)
    category = db.Column(db.Unicode(50), nullable=False)
    location = db.Column(db.Unicode(80), nullable=False)
    relocation_assist = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.Unicode, nullable=False)
    perks = db.Column(db.Unicode, nullable=False)
    how_to_apply = db.Column(db.Unicode, nullable=False)

    # Company details
    company_name = db.Column(db.Unicode(80), nullable=False)
    company_logo = db.Column(db.LargeBinary, nullable=True) # TODO: Images in the db?
    company_url = db.Column(db.Unicode(255), nullable=False)
    email = db.Column(db.Unicode(80), nullable=False)

    # Payment, audit and workflow fields
    promocode = db.Column(db.Text(40), nullable=True)
    terms_accepted = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.Integer, nullable=False, default=POSTSTATUS.DRAFT)
    ipaddr = db.Column(db.Text(45), nullable=False)
    useragent = db.Column(db.Unicode(250), nullable=True)
    email_verify_key = db.Column(db.String(40), nullable=False, default=random_long_key)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    payment_value = db.Column(db.Integer, nullable=False, default=0)
    payment_received = db.Column(db.Boolean, nullable=False, default=False)
    reviewer = db.Column(db.Integer, nullable=True)
    review_datetime = db.Column(db.DateTime, nullable=True)


def unique_hash(model=JobPost):
    """
    Returns a unique hash for a given model
    """
    while 1:
        hashid = random_hash_key()
        if model.query.filter_by(hashid=hashid).count() == 0:
            break
    return hashid
