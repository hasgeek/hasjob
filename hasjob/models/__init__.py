# -*- coding: utf-8 -*-

from datetime import timedelta
from flask.ext.sqlalchemy import SQLAlchemy
from coaster import LabeledEnum
from coaster.sqlalchemy import BaseMixin, BaseNameMixin, TimestampMixin
from hasjob import app


db = SQLAlchemy(app)
agelimit = timedelta(days=30)
newlimit = timedelta(days=1)


class POSTSTATUS:
    DRAFT = 0      # Being written
    PENDING = 1    # Pending email verification and payment
    CONFIRMED = 2  # Post is now live on site
    REVIEWED = 3   # Reviewed and cleared for push channels
    REJECTED = 4   # Reviewed and rejected as inappropriate
    WITHDRAWN = 5  # Withdrawn by owner
    FLAGGED = 6    # Flagged by users for review
    SPAM = 7       # Marked as spam


class EMPLOYER_RESPONSE(LabeledEnum):
    PENDING = (0, u"Pending")      # No response yet
    OPENED = (1, u"Opened")        # Response was undone (currently only un-flagged)
    IGNORED = (2, u"Ignored")      # Dismissed as not interesting
    CONNECTED = (3, u"Connected")  # Make a connection between both
    FLAGGED = (4, u"Flagged")      # Employer reported a spammer


from hasjob.models.jobcategory import *
from hasjob.models.jobpostreport import *
from hasjob.models.jobtype import *
from hasjob.models.reportcode import *
from hasjob.models.jobpost import *
from hasjob.models.user import *
