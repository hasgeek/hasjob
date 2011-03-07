# -*- coding: utf-8 -*-

from datetime import datetime
from flaskext.sqlalchemy import SQLAlchemy
from app import app

db = SQLAlchemy(app)

class JobPost(db.Model):
    __tablename__ = 'jobpost'
    # Metadata
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(6), nullable=False, unique=True)
    datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Job description
    headline = db.Column(db.Unicode(100), nullable=False)
    category = db.Column(db.Unicode(50), nullable=False)
    location = db.Column(db.Unicode(80), nullable=False)
    relocation_assist = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.Unicode, nullable=False)
    perks = db.Column(db.Unicode, nullable=True)
    how_to_apply = db.Column(db.Unicode, nullable=False)

    # Company details
    company_name = db.Column(db.Unicode(80), nullable=True)
    company_logo = db.Column(db.LargeBinary, nullable=True) # FIXME: Images in the db?
    company_url = db.Column(db.Unicode(255), nullable=True)
    email = db.Column(db.Unicode(80), nullable=False)

    # Audit fields
    ipaddr = db.Column(db.Text(45), nullable=False)
    promocode = db.Column(db.Text(40), nullable=True)
