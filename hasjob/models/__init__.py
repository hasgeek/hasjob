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


class POST_STATE(LabeledEnum):
    DRAFT =        (0, 'draft',  __("Draft"))         # Being written
    PENDING =      (1, 'pending',  __("Pending"))       # Pending email verification
    CONFIRMED =    (2, 'confirmed',  __("Confirmed"))     # Post is now live on site
    REVIEWED =     (3, 'reviewed',  __("Reviewed"))      # Reviewed and cleared for push channels
    REJECTED =     (4, 'rejected',  __("Rejected"))      # Reviewed and rejected as inappropriate
    WITHDRAWN =    (5, 'withdrawn',  __("Withdrawn"))     # Withdrawn by owner
    FLAGGED =      (6, 'flagged',  __("Flagged"))       # Flagged by users for review
    SPAM =         (7, 'spam',  __("Spam"))          # Marked as spam
    MODERATED =    (8, 'moderated',  __("Moderated"))     # Moderated, needs edit
    ANNOUNCEMENT = (9, 'announcement',  __("Announcement"))  # Special announcement
    CLOSED =       (10, 'closed', __("Closed"))        # Not accepting applications, but publicly viewable

    __order__ = (DRAFT, PENDING, CONFIRMED, REVIEWED, ANNOUNCEMENT, CLOSED,
                 FLAGGED, MODERATED, REJECTED, SPAM, WITHDRAWN)

    UNPUBLISHED = {DRAFT, PENDING}
    GONE = {REJECTED, WITHDRAWN, SPAM}
    UNACCEPTABLE = {REJECTED, SPAM}
    PUBLIC = {CONFIRMED, REVIEWED, ANNOUNCEMENT, CLOSED}
    MY = {DRAFT, PENDING, CONFIRMED, REVIEWED, MODERATED, ANNOUNCEMENT, CLOSED}
    ARCHIVED = {CONFIRMED, REVIEWED, ANNOUNCEMENT, CLOSED}


class CURRENCY(LabeledEnum):
    INR = ('INR', 'INR')
    USD = ('USD', 'USD')
    EUR = ('EUR', 'EUR')

    __order__ = (INR, USD, EUR)


class EMPLOYER_RESPONSE(LabeledEnum):
    NEW =      (0, 'new', __("New"))       # New application
    PENDING =  (1, 'pending', __("Pending"))   # Employer viewed on website
    IGNORED =  (2, 'ignored', __("Ignored"))   # Dismissed as not worth responding to
    REPLIED =  (3, 'replied', __("Replied"))   # Employer replied to candidate
    FLAGGED =  (4, 'flagged', __("Flagged"))   # Employer reported a spammer
    SPAM =     (5, 'spam', __("Spam"))      # Admin marked this as spam
    REJECTED = (6, 'rejected', __("Rejected"))  # Employer rejected candidate with a message

    __order__ = (NEW, PENDING, IGNORED, REPLIED, FLAGGED, SPAM, REJECTED)

    CAN_REPLY = {NEW, PENDING, IGNORED}
    CAN_REJECT = CAN_REPLY
    CAN_IGNORE = {NEW, PENDING}
    CAN_REPORT = {NEW, PENDING, IGNORED, REJECTED}


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
from .filterset import *
