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
    NEW = (0, u"New")            # New application
    PENDING = (1, u"Pending")    # Employer viewed on website
    IGNORED = (2, u"Ignored")    # Dismissed as not worth responding to
    REPLIED = (3, u"Replied")    # Employer replied to candidate
    FLAGGED = (4, u"Flagged")    # Employer reported a spammer
    SPAM = (5, u"Spam")          # Admin marked this as spam
    REJECTED = (6, u"Rejected")  # Employer rejected candidate with a message


from hasjob.models.user import *
from hasjob.models.jobcategory import *
from hasjob.models.jobpostreport import *
from hasjob.models.jobtype import *
from hasjob.models.reportcode import *
from hasjob.models.jobpost import *
