# -*- coding: utf-8 -*-

from collections import namedtuple
from datetime import datetime
from sqlalchemy import distinct
from werkzeug import cached_property
from baseframe import __, cache
from . import db, agelimit, newlimit, POSTSTATUS, EMPLOYER_RESPONSE
from .user import User
from .jobpost import JobPost, JobApplication
from .board import Board

__all__ = ['UserFlags']


UserFlag = namedtuple('UserFlag', ['category', 'title', 'for_user', 'user_ids'])


class UserFlags(object):
    """
    A collection of bi-directional flags to (a) set on a user or (b) find matching users.
    This is a convenience class, meant only to be an easy way to look up contents.
    """

    # Is a new user (under a day, a month)

    is_new_since_day = UserFlag('user',
        __("Is a new user (joined <= a day ago)"),
        lambda user: user.created_at >= datetime.utcnow() - newlimit,
        lambda: db.session.query(User.id).filter(User.created_at >= datetime.utcnow() - newlimit)
        )

    is_new_since_month = UserFlag('user',
        __("Is a new user (joined <= a month ago)"),
        lambda user: user.created_at >= datetime.utcnow() - agelimit,
        lambda: db.session.query(User.id).filter(User.created_at >= datetime.utcnow() - agelimit)
        )

    is_not_new = UserFlag('user',
        __("Is not a new user (joined > a month ago)"),
        lambda user: user.created_at < datetime.utcnow() - agelimit,
        lambda: db.session.query(User.id).filter(User.created_at < datetime.utcnow() - agelimit)
        )

    # Is a candidate (all time, new, recent, past)

    is_candidate_alltime = UserFlag('candidate',
        __("Is a candidate (applied at any time)"),
        lambda user: JobApplication.query.filter(
            JobApplication.user == user
            ).notempty(),
        lambda: db.session.query(distinct(JobApplication.user_id).label('id'))
        )

    is_candidate_day = UserFlag('candidate',
        __("Is a candidate (applied <= a day ago)"),
        lambda user: JobApplication.query.filter(
            JobApplication.user == user,
            JobApplication.created_at >= datetime.utcnow() - newlimit
            ).notempty(),
        lambda: db.session.query(distinct(JobApplication.user_id).label('id')).filter(
            JobApplication.created_at >= datetime.utcnow() - newlimit
            )
        )

    is_candidate_month = UserFlag('candidate',
        __("Is a candidate (applied <= a month ago)"),
        lambda user: JobApplication.query.filter(
            JobApplication.user == user,
            JobApplication.created_at >= datetime.utcnow() - agelimit
            ).notempty(),
        lambda: db.session.query(distinct(JobApplication.user_id).label('id')).filter(
            JobApplication.created_at >= datetime.utcnow() - agelimit
            )
        )

    is_candidate_past = UserFlag('candidate',
        __("Is a candidate (applied > a month ago)"),
        lambda user: JobApplication.query.filter(
            JobApplication.user == user,
            JobApplication.created_at < datetime.utcnow() - agelimit
            ).notempty(),
        lambda: db.session.query(distinct(JobApplication.user_id).label('id')).filter(
            JobApplication.created_at < datetime.utcnow() - agelimit
            )
        )

    # Is a candidate who got a response from an employer

    has_jobapplication_response_alltime = UserFlag('candidate',
        __("Is a candidate who received a response (at any time)"),
        lambda user: JobApplication.query.filter(
            JobApplication.user == user,
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED
            ).notempty(),
        lambda: db.session.query(distinct(JobApplication.user_id).label('id')).filter(
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED
            )
        )

    has_jobapplication_response_day = UserFlag('candidate',
        __("Is a candidate who received a response (in <= a day)"),
        lambda user: JobApplication.query.filter(
            JobApplication.user == user,
            JobApplication.replied_at >= datetime.utcnow() - newlimit,
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED
            ).notempty(),
        lambda: db.session.query(distinct(JobApplication.user_id).label('id')).filter(
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED,
            JobApplication.replied_at >= datetime.utcnow() - newlimit
            )
        )

    has_jobapplication_response_month = UserFlag('candidate',
        __("Is a candidate who received a response (in <= a month)"),
        lambda user: JobApplication.query.filter(
            JobApplication.user == user,
            JobApplication.replied_at >= datetime.utcnow() - agelimit,
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED
            ).notempty(),
        lambda: db.session.query(distinct(JobApplication.user_id).label('id')).filter(
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED,
            JobApplication.replied_at >= datetime.utcnow() - agelimit
            )
        )

    has_jobapplication_response_past = UserFlag('candidate',
        __("Is a candidate who received a response (in > a month)"),
        lambda user: JobApplication.query.filter(
            JobApplication.user == user,
            JobApplication.replied_at < datetime.utcnow() - agelimit,
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED
            ).notempty(),
        lambda: db.session.query(distinct(JobApplication.user_id).label('id')).filter(
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED,
            JobApplication.replied_at < datetime.utcnow() - agelimit
            )
        )

    # Is an employer (not including collaborators) (all time, new, recent, past)

    is_employer_alltime = UserFlag('employer',
        __("Is an employer (posted at any time)"),
        lambda user: JobPost.query.filter(
            JobPost.user == user,
            JobPost.status.in_(POSTSTATUS.POSTPENDING)
            ).notempty(),
        lambda: db.session.query(db.distinct(JobPost.user_id).label('id')).filter(
            JobPost.status.in_(POSTSTATUS.POSTPENDING)
            )
        )

    is_employer_day = UserFlag('employer',
        __("Is an employer (posted <= a day ago)"),
        lambda user: JobPost.query.filter(
            JobPost.user == user,
            JobPost.datetime >= datetime.utcnow() - newlimit,
            JobPost.status.in_(POSTSTATUS.POSTPENDING)
            ).notempty(),
        lambda: db.session.query(db.distinct(JobPost.user_id).label('id')).filter(
            JobPost.datetime >= datetime.utcnow() - newlimit,
            JobPost.status.in_(POSTSTATUS.POSTPENDING)
            )
        )

    is_employer_month = UserFlag('employer',
        __("Is an employer (posted <= a month ago)"),
        lambda user: JobPost.query.filter(
            JobPost.user == user,
            JobPost.datetime >= datetime.utcnow() - agelimit,
            JobPost.status.in_(POSTSTATUS.POSTPENDING)
            ).notempty(),
        lambda: db.session.query(db.distinct(JobPost.user_id).label('id')).filter(
            JobPost.datetime >= datetime.utcnow() - agelimit,
            JobPost.status.in_(POSTSTATUS.POSTPENDING)
            )
        )

    is_employer_past = UserFlag('employer',
        __("Is an employer (posted > a month ago)"),
        lambda user: JobPost.query.filter(
            JobPost.user == user,
            JobPost.datetime < datetime.utcnow() - agelimit,
            JobPost.status.in_(POSTSTATUS.POSTPENDING)
            ).notempty(),
        lambda: db.session.query(db.distinct(JobPost.user_id).label('id')).filter(
            JobPost.datetime < datetime.utcnow() - agelimit,
            JobPost.status.in_(POSTSTATUS.POSTPENDING)
            )
        )

    # Employer who didn't confirm a listing

    has_jobpost_unconfirmed_alltime = UserFlag('employer',
        __("Is an employer who did not confirm a post (at any time)"),
        lambda user: JobPost.query.filter(
            JobPost.user == user,
            JobPost.status.in_(POSTSTATUS.UNPUBLISHED)
            ).notempty(),
        lambda: db.session.query(db.distinct(JobPost.user_id).label('id')).filter(
            JobPost.status.in_(POSTSTATUS.POSTPENDING)
            )
        )

    has_jobpost_unconfirmed_day = UserFlag('employer',
        __("Is an employer who did not confirm a post (posted <= a day ago)"),
        lambda user: JobPost.query.filter(
            JobPost.user == user,
            JobPost.datetime >= datetime.utcnow() - newlimit,
            JobPost.status.in_(POSTSTATUS.UNPUBLISHED)
            ).notempty(),
        lambda: db.session.query(db.distinct(JobPost.user_id).label('id')).filter(
            JobPost.datetime >= datetime.utcnow() - newlimit,
            JobPost.status.in_(POSTSTATUS.POSTPENDING)
            )
        )

    has_jobpost_unconfirmed_month = UserFlag('employer',
        __("Is an employer who did not confirm a post (posted <= a month ago)"),
        lambda user: JobPost.query.filter(
            JobPost.user == user,
            JobPost.datetime >= datetime.utcnow() - agelimit,
            JobPost.status.in_(POSTSTATUS.UNPUBLISHED)
            ).notempty(),
        lambda: db.session.query(db.distinct(JobPost.user_id).label('id')).filter(
            JobPost.datetime >= datetime.utcnow() - agelimit,
            JobPost.status.in_(POSTSTATUS.POSTPENDING)
            )
        )

    # Employer who responded to a candidate

    has_responded_candidate_alltime = UserFlag('candidate',
        __("Is an employer who responded to a candidate (at any time)"),
        lambda user: JobApplication.query.filter(
            JobApplication.replied_by == user,
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED
            ).notempty(),
        lambda: db.session.query(distinct(JobApplication.replied_by_id).label('id')).filter(
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED
            )
        )

    has_responded_candidate_day = UserFlag('candidate',
        __("Is an employer who responded to a candidate (in <= a day)"),
        lambda user: JobApplication.query.filter(
            JobApplication.replied_by == user,
            JobApplication.replied_at >= datetime.utcnow() - newlimit,
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED
            ).notempty(),
        lambda: db.session.query(distinct(JobApplication.replied_by_id).label('id')).filter(
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED,
            JobApplication.replied_at >= datetime.utcnow() - newlimit
            )
        )

    has_responded_candidate_month = UserFlag('candidate',
        __("Is an employer who responded to a candidate (in <= a month)"),
        lambda user: JobApplication.query.filter(
            JobApplication.replied_by == user,
            JobApplication.replied_at >= datetime.utcnow() - agelimit,
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED
            ).notempty(),
        lambda: db.session.query(distinct(JobApplication.replied_by_id).label('id')).filter(
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED,
            JobApplication.replied_at >= datetime.utcnow() - agelimit
            )
        )

    has_responded_candidate_past = UserFlag('candidate',
        __("Is an employer who responded to a candidate (in > a month)"),
        lambda user: JobApplication.query.filter(
            JobApplication.replied_by == user,
            JobApplication.replied_at < datetime.utcnow() - agelimit,
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED
            ).notempty(),
        lambda: db.session.query(distinct(JobApplication.replied_by_id).label('id')).filter(
            JobApplication.response == EMPLOYER_RESPONSE.REPLIED,
            JobApplication.replied_at < datetime.utcnow() - agelimit
            )
        )

    # Account created in <= a day
    is_new_lurker_within_day = UserFlag('lurker',
        __("Is a lurker (joined <= a day ago)"),
        lambda user: user.created_at >= datetime.utcnow() - newlimit and (
            not JobPost.query.filter(JobPost.user == user).notempty()) or (
            not JobApplication.query.filter(JobApplication.user == user).notempty()) or (
            not JobApplication.query.filter(JobApplication.replied_by == user).notempty()),
        lambda: db.session.query(User.id).filter(
            User.created_at >= datetime.utcnow() - newlimit,
            ~User.id.in_(db.session.query(JobApplication.user_id).filter(JobApplication.user_id != None)),
            ~User.id.in_(db.session.query(JobApplication.replied_by_id).filter(JobApplication.replied_by_id != None)),
            ~User.id.in_(db.session.query(JobPost.user_id).filter(JobPost.user_id != None))
            )  # NOQA
        )

    # Account created in <= a month
    is_new_lurker_within_month = UserFlag('lurker',
        __("Is a lurker (joined <= a month ago)"),
        lambda user: user.created_at >= datetime.utcnow() - agelimit and (
            not JobPost.query.filter(JobPost.user == user).notempty()) or (
            not JobApplication.query.filter(JobApplication.user == user).notempty()) or (
            not JobApplication.query.filter(JobApplication.replied_by == user).notempty()),
        lambda: db.session.query(User.id).filter(
            User.created_at >= datetime.utcnow() - agelimit,
            ~User.id.in_(db.session.query(JobApplication.user_id).filter(JobApplication.user_id != None)),
            ~User.id.in_(db.session.query(JobApplication.replied_by_id).filter(JobApplication.replied_by_id != None)),
            ~User.id.in_(db.session.query(JobPost.user_id).filter(JobPost.user_id != None))
            )  # NOQA
        )

    # Account created > a month ago
    is_lurker_since_past = UserFlag('lurker',
        __("Is a lurker (joined > a month ago)"),
        lambda user: user.created_at < datetime.utcnow() - agelimit and (
            not JobPost.query.filter(JobPost.user == user).notempty()) or (
            not JobApplication.query.filter(JobApplication.user == user).notempty()) or (
            not JobApplication.query.filter(JobApplication.replied_by == user).notempty()),
        lambda: db.session.query(User.id).filter(
            User.created_at < datetime.utcnow() - agelimit,
            ~User.id.in_(db.session.query(JobApplication.user_id).filter(JobApplication.user_id != None)),
            ~User.id.in_(db.session.query(JobApplication.replied_by_id).filter(JobApplication.replied_by_id != None)),
            ~User.id.in_(db.session.query(JobPost.user_id).filter(JobPost.user_id != None))
            )  # NOQA
        )

    # Has always been a lurker
    is_lurker_since_alltime = UserFlag('lurker',
        __("Is a lurker"),
        lambda user: (
            not JobPost.query.filter(JobPost.user == user).notempty()) or (
            not JobApplication.query.filter(JobApplication.user == user).notempty()) or (
            not JobApplication.query.filter(JobApplication.replied_by == user).notempty()),
        lambda: db.session.query(User.id).filter(
            ~User.id.in_(db.session.query(JobApplication.user_id).filter(JobApplication.user_id != None)),
            ~User.id.in_(db.session.query(JobApplication.replied_by_id).filter(JobApplication.replied_by_id != None)),
            ~User.id.in_(db.session.query(JobPost.user_id).filter(JobPost.user_id != None))
            )  # NOQA
        )

    # Has been lurking for a day+
    is_inactive_since_day = UserFlag('lurker',
        __("Is inactive (for a day+)"),
        lambda user: (
            not JobPost.query.filter(
                JobPost.user == user, JobPost.created_at >= datetime.utcnow() - newlimit
                ).notempty()) or (
            not JobApplication.query.filter(
                JobApplication.user == user, JobApplication.created_at >= datetime.utcnow() - newlimit
                ).notempty()) or (
            not JobApplication.query.filter(
                JobApplication.replied_by == user, JobApplication.replied_at >= datetime.utcnow() - newlimit
                ).notempty()),
        lambda: db.session.query(User.id).filter(
            ~User.id.in_(db.session.query(JobApplication.user_id).filter(
                JobApplication.user_id != None, JobApplication.created_at >= datetime.utcnow() - newlimit)),
            ~User.id.in_(db.session.query(JobApplication.replied_by_id).filter(
                JobApplication.replied_by_id != None, JobApplication.replied_at >= datetime.utcnow() - newlimit)),
            ~User.id.in_(db.session.query(JobPost.user_id).filter(
                JobPost.user_id != None, JobPost.created_at >= datetime.utcnow() - newlimit))
            )  # NOQA
        )

    # Has been lurking for a month+
    is_inactive_since_month = UserFlag('lurker',
        __("Is inactive (for a month+)"),
        lambda user: (
            not JobPost.query.filter(
                JobPost.user == user, JobPost.created_at >= datetime.utcnow() - agelimit
                ).notempty()) or (
            not JobApplication.query.filter(
                JobApplication.user == user, JobApplication.created_at >= datetime.utcnow() - agelimit
                ).notempty()) or (
            not JobApplication.query.filter(
                JobApplication.replied_by == user, JobApplication.replied_at >= datetime.utcnow() - agelimit
                ).notempty()),
        lambda: db.session.query(User.id).filter(
            ~User.id.in_(db.session.query(JobApplication.user_id).filter(
                JobApplication.user_id != None, JobApplication.created_at >= datetime.utcnow() - agelimit)),
            ~User.id.in_(db.session.query(JobApplication.replied_by_id).filter(
                JobApplication.replied_by_id != None, JobApplication.replied_at >= datetime.utcnow() - agelimit)),
            ~User.id.in_(db.session.query(JobPost.user_id).filter(
                JobPost.user_id != None, JobPost.created_at >= datetime.utcnow() - newlimit))
            )  # NOQA
        )

    # One-way flags (no elegant way to do a reverse query)

    has_boards = UserFlag('admin',
        __("Has a sub-board"),
        lambda user: Board.query.filter(
            Board.userid.in_(user.allowner_ids())
            ).notempty(),
        None
        )


def _user_flags(self):
    cache_key = 'user/flags/' + str(self.id)
    flags = cache.get(cache_key)
    if not flags:
        flags = {}
        for key, func in UserFlags.__dict__.items():
            if isinstance(func, UserFlag):
                flags[key] = func.for_user(self)
        cache.set(cache_key, flags, timeout=3600)  # Cache for one hour
    return flags

User.flags = cached_property(_user_flags)
