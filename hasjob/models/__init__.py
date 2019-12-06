# -*- coding: utf-8 -*-
# flake8: noqa

from datetime import timedelta
from coaster.utils import LabeledEnum
from coaster.db import db
from coaster.sqlalchemy import (BaseMixin, BaseNameMixin, TimestampMixin, BaseScopedIdMixin,
    BaseScopedNameMixin, CoordinatesMixin, make_timestamp_columns)
from baseframe import _
from .. import app

TimestampMixin.__with_timezone__ = True

agelimit = timedelta(days=30)
newlimit = timedelta(days=1)


class POST_STATE(LabeledEnum):
    DRAFT =        (0, 'draft',  _("Draft"))         # Being written
    PENDING =      (1, 'pending',  _("Pending"))       # Pending email verification
    CONFIRMED =    (2, 'confirmed',  _("Confirmed"))     # Post is now live on site
    REVIEWED =     (3, 'reviewed',  _("Reviewed"))      # Reviewed and cleared for push channels
    REJECTED =     (4, 'rejected',  _("Rejected"))      # Reviewed and rejected as inappropriate
    WITHDRAWN =    (5, 'withdrawn',  _("Withdrawn"))     # Withdrawn by owner
    FLAGGED =      (6, 'flagged',  _("Flagged"))       # Flagged by users for review
    SPAM =         (7, 'spam',  _("Spam"))          # Marked as spam
    MODERATED =    (8, 'moderated',  _("Moderated"))     # Moderated, needs edit
    ANNOUNCEMENT = (9, 'announcement',  _("Announcement"))  # Special announcement
    CLOSED =       (10, 'closed', _("Closed"))        # Not accepting applications, but publicly viewable

    __order__ = (DRAFT, PENDING, CONFIRMED, REVIEWED, ANNOUNCEMENT, CLOSED,
                 FLAGGED, MODERATED, REJECTED, SPAM, WITHDRAWN)

    UNPUBLISHED = {DRAFT, PENDING}
    UNPUBLISHED_OR_MODERATED = {DRAFT, PENDING, MODERATED}
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
    NEW =      (0, 'new', _("New"))       # New application
    PENDING =  (1, 'pending', _("Pending"))   # Employer viewed on website
    IGNORED =  (2, 'ignored', _("Ignored"))   # Dismissed as not worth responding to
    REPLIED =  (3, 'replied', _("Replied"))   # Employer replied to candidate
    FLAGGED =  (4, 'flagged', _("Flagged"))   # Employer reported a spammer
    SPAM =     (5, 'spam', _("Spam"))      # Admin marked this as spam
    REJECTED = (6, 'rejected', _("Rejected"))  # Employer rejected candidate with a message

    __order__ = (NEW, PENDING, IGNORED, REPLIED, FLAGGED, SPAM, REJECTED)

    CAN_REPLY = {NEW, PENDING, IGNORED}
    CAN_REJECT = CAN_REPLY
    CAN_IGNORE = {NEW, PENDING}
    CAN_REPORT = {NEW, PENDING, IGNORED, REJECTED}


class PAY_TYPE(LabeledEnum):
    NOCASH    = (0, _("Nothing"))
    ONETIME   = (1, _("One-time"))
    RECURRING = (2, _("Recurring"))

    __order__ = (NOCASH, ONETIME, RECURRING)


class CANDIDATE_FEEDBACK(LabeledEnum):
    NORESPONSE =     (0, _("No response"))
    INPROCESS =      (1, _("In process"))
    DID_NOT_GET =    (2, _("Did not get the job"))
    DID_NOT_ACCEPT = (3, _("Got offer, did not accept"))
    GOT_JOB =        (4, _("Got the job"))

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
