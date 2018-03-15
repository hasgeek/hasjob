# -*- coding: utf-8 -*-
# flake8: noqa

from datetime import timedelta
from coaster.utils import LabeledEnum
from coaster.db import db
from coaster.sqlalchemy import (BaseMixin, BaseNameMixin, TimestampMixin, BaseScopedIdMixin,
    BaseScopedNameMixin, CoordinatesMixin, make_timestamp_columns)
from baseframe import __
from .. import app

agelimit = timedelta(days=30)
newlimit = timedelta(days=1)


class POSTSTATUS(LabeledEnum):
    DRAFT =        (0,  __("Draft"))         # Being written
    PENDING =      (1,  __("Pending"))       # Pending email verification
    CONFIRMED =    (2,  __("Confirmed"))     # Post is now live on site
    REVIEWED =     (3,  __("Reviewed"))      # Reviewed and cleared for push channels
    REJECTED =     (4,  __("Rejected"))      # Reviewed and rejected as inappropriate
    WITHDRAWN =    (5,  __("Withdrawn"))     # Withdrawn by owner
    FLAGGED =      (6,  __("Flagged"))       # Flagged by users for review
    SPAM =         (7,  __("Spam"))          # Marked as spam
    MODERATED =    (8,  __("Moderated"))     # Moderated, needs edit
    ANNOUNCEMENT = (9,  __("Announcement"))  # Special announcement
    CLOSED =       (10, __("Closed"))        # Not accepting applications, but publicly viewable

    UNPUBLISHED = {DRAFT, PENDING}
    GONE = {REJECTED, WITHDRAWN, SPAM}
    UNACCEPTABLE = {REJECTED, SPAM}
    LISTED = {CONFIRMED, REVIEWED, ANNOUNCEMENT}
    POSTPENDING = {CONFIRMED, REVIEWED, REJECTED, WITHDRAWN, FLAGGED, SPAM, MODERATED, ANNOUNCEMENT, CLOSED}
    MY = {DRAFT, PENDING, CONFIRMED, REVIEWED, MODERATED, ANNOUNCEMENT, CLOSED}
    ARCHIVED = {CONFIRMED, REVIEWED, ANNOUNCEMENT, CLOSED}


class CURRENCY(LabeledEnum):
    INR = ('INR', 'INR')
    USD = ('USD', 'USD')
    EUR = ('EUR', 'EUR')

    __order__ = (INR, USD, EUR)


class EMPLOYER_RESPONSE(LabeledEnum):
    NEW =      (0, __("New"))       # New application
    PENDING =  (1, __("Pending"))   # Employer viewed on website
    IGNORED =  (2, __("Ignored"))   # Dismissed as not worth responding to
    REPLIED =  (3, __("Replied"))   # Employer replied to candidate
    FLAGGED =  (4, __("Flagged"))   # Employer reported a spammer
    SPAM =     (5, __("Spam"))      # Admin marked this as spam
    REJECTED = (6, __("Rejected"))  # Employer rejected candidate with a message

    __order__ = (NEW, PENDING, IGNORED, REPLIED, FLAGGED, SPAM, REJECTED)


class PAY_TYPE(LabeledEnum):
    NOCASH    = (0, __("Nothing"))
    ONETIME   = (1, __("One-time"))
    RECURRING = (2, __("Recurring"))

    __order__ = (NOCASH, ONETIME, RECURRING)


class CANDIDATE_FEEDBACK(LabeledEnum):
    NORESPONSE =     (0, __("No response"))
    INPROCESS =      (1, __("In process"))
    DID_NOT_GET =    (2, __("Did not get the job"))
    DID_NOT_ACCEPT = (3, __("Got offer, did not accept"))
    GOT_JOB =        (4, __("Got the job"))

    __order__ = (NORESPONSE, INPROCESS, DID_NOT_GET, DID_NOT_ACCEPT, GOT_JOB)


from .user import *
from .jobcategory import *
from .jobpostreport import *
from .jobtype import *
from .location import *
from .tag import *
from .reportcode import *
from .jobpost import *
from .domain import *
from .board import *
from .flags import *
from .campaign import *
from .filtered_view import *
