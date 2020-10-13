from datetime import timedelta

from baseframe import __
from coaster.db import db  # NOQA: F401
from coaster.sqlalchemy import (  # NOQA: F401
    BaseMixin,
    BaseNameMixin,
    BaseScopedIdMixin,
    BaseScopedNameMixin,
    CoordinatesMixin,
    TimestampMixin,
    make_timestamp_columns,
)
from coaster.utils import LabeledEnum

TimestampMixin.__with_timezone__ = True

agelimit = timedelta(days=30)
newlimit = timedelta(days=1)


class POST_STATE(LabeledEnum):  # NOQA: N801
    #: Being written
    DRAFT = (0, 'draft', __("Draft"))
    #: Pending email verification
    PENDING = (1, 'pending', __("Pending"))
    #: Post is now live on site
    CONFIRMED = (2, 'confirmed', __("Confirmed"))
    #: Reviewed and cleared for push channels
    REVIEWED = (3, 'reviewed', __("Reviewed"))
    #: Reviewed and rejected as inappropriate
    REJECTED = (4, 'rejected', __("Rejected"))
    #: Withdrawn by owner
    WITHDRAWN = (5, 'withdrawn', __("Withdrawn"))
    #: Flagged by users for review
    FLAGGED = (6, 'flagged', __("Flagged"))
    #: Marked as spam
    SPAM = (7, 'spam', __("Spam"))
    #: Moderated, needs edit
    MODERATED = (8, 'moderated', __("Moderated"))
    #: Special announcement
    ANNOUNCEMENT = (9, 'announcement', __("Announcement"))
    #: Not accepting applications, but publicly viewable
    CLOSED = (10, 'closed', __("Closed"))

    __order__ = (
        DRAFT,
        PENDING,
        CONFIRMED,
        REVIEWED,
        ANNOUNCEMENT,
        CLOSED,
        FLAGGED,
        MODERATED,
        REJECTED,
        SPAM,
        WITHDRAWN,
    )

    UNPUBLISHED = {DRAFT, PENDING}
    UNPUBLISHED_OR_MODERATED = {DRAFT, PENDING, MODERATED}
    GONE = {REJECTED, WITHDRAWN, SPAM}
    UNACCEPTABLE = {REJECTED, SPAM}
    PUBLIC = {CONFIRMED, REVIEWED, ANNOUNCEMENT, CLOSED}
    MY = {DRAFT, PENDING, CONFIRMED, REVIEWED, MODERATED, ANNOUNCEMENT, CLOSED}
    ARCHIVED = {CONFIRMED, REVIEWED, ANNOUNCEMENT, CLOSED}


class CURRENCY(LabeledEnum):  # NOQA: N801
    INR = ('INR', 'INR')
    USD = ('USD', 'USD')
    EUR = ('EUR', 'EUR')

    __order__ = (INR, USD, EUR)


class EMPLOYER_RESPONSE(LabeledEnum):  # NOQA: N801
    #: New application
    NEW = (0, 'new', __("New"))
    #: Employer viewed on website
    PENDING = (1, 'pending', __("Pending"))
    #: Dismissed as not worth responding to
    IGNORED = (2, 'ignored', __("Ignored"))
    #: Employer replied to candidate
    REPLIED = (3, 'replied', __("Replied"))
    #: Employer reported a spammer
    FLAGGED = (4, 'flagged', __("Flagged"))
    #: Admin marked this as spam
    SPAM = (5, 'spam', __("Spam"))
    #: Employer rejected candidate with a message
    REJECTED = (6, 'rejected', __("Rejected"))

    __order__ = (NEW, PENDING, IGNORED, REPLIED, FLAGGED, SPAM, REJECTED)

    CAN_REPLY = {NEW, PENDING, IGNORED}
    CAN_REJECT = CAN_REPLY
    CAN_IGNORE = {NEW, PENDING}
    CAN_REPORT = {NEW, PENDING, IGNORED, REJECTED}


class PAY_TYPE(LabeledEnum):  # NOQA: N801
    NOCASH = (0, __("Nothing"))
    ONETIME = (1, __("One-time"))
    RECURRING = (2, __("Recurring"))

    __order__ = (NOCASH, ONETIME, RECURRING)


class CANDIDATE_FEEDBACK(LabeledEnum):  # NOQA: N801
    NORESPONSE = (0, __("No response"))
    INPROCESS = (1, __("In process"))
    DID_NOT_GET = (2, __("Did not get the job"))
    DID_NOT_ACCEPT = (3, __("Got offer, did not accept"))
    GOT_JOB = (4, __("Got the job"))

    __order__ = (NORESPONSE, INPROCESS, DID_NOT_GET, DID_NOT_ACCEPT, GOT_JOB)


from .board import *  # NOQA # isort:skip
from .campaign import *  # NOQA # isort:skip
from .domain import *  # NOQA # isort:skip
from .filterset import *  # NOQA # isort:skip
from .flags import *  # NOQA # isort:skip
from .jobcategory import *  # NOQA # isort:skip
from .jobpost import *  # NOQA # isort:skip
from .jobpostreport import *  # NOQA # isort:skip
from .jobtype import *  # NOQA # isort:skip
from .location import *  # NOQA # isort:skip
from .reportcode import *  # NOQA # isort:skip
from .tag import *  # NOQA # isort:skip
from .user import *  # NOQA # isort:skip
