# -*- coding: utf-8 -*-

from datetime import timedelta
from flask.ext.sqlalchemy import SQLAlchemy

from hasjob import app
from hasjob.utils import random_hash_key


db = SQLAlchemy(app)
agelimit = timedelta(days=30)


class POSTSTATUS:
    DRAFT = 0  # Being written
    PENDING = 1  # Pending email verification and payment
    CONFIRMED = 2  # Post is now live on site
    REVIEWED = 3  # Reviewed and cleared for push channels
    REJECTED = 4  # Reviewed and rejected as inappropriate
    WITHDRAWN = 5  # Withdrawn by owner
    FLAGGED = 6  # Flagged by users for review


class USERLEVEL:
    USER = 0  # Just a user
    REVIEWER = 1  # Reviewer. Allowed to edit
    ADMINISTRATOR = 2  # Admin. Allowed to change job types and categories


from hasjob.models.jobcategory import *
from hasjob.models.jobpostreport import *
from hasjob.models.jobtype import *
from hasjob.models.reportcode import *
from hasjob.models.jobpost import *
from hasjob.models.user import *


def unique_hash(model=JobPost):
    """
    Returns a unique hash for a given model
    """
    while 1:
        hashid = random_hash_key()
        if model.query.filter_by(hashid=hashid).count() == 0:
            break
    return hashid
