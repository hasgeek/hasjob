from datetime import datetime

from hasjob.models import agelimit, db, JobPost, POSTSTATUS

def getposts(basequery=None, sticky=False):
    if basequery is None:
        basequery = JobPost.query
    query = basequery.filter(
            JobPost.status.in_([POSTSTATUS.CONFIRMED, POSTSTATUS.REVIEWED])).filter(
            JobPost.datetime > datetime.utcnow() - agelimit)
    if sticky:
        query = query.order_by(db.desc(JobPost.sticky))
    return query.order_by(db.desc(JobPost.datetime))


def getallposts(order_by=None, desc=False, start=None, limit=None):
    if order_by is None:
        order_by = JobPost.datetime
    filt = JobPost.query.filter(JobPost.status.in_([POSTSTATUS.CONFIRMED, POSTSTATUS.REVIEWED]))
    count = filt.count()
    if desc:
        filt = filt.order_by(db.desc(order_by))
    else:
        filt = filt.order_by(order_by)
    if start is not None:
        filt = filt.offset(start)
    if limit is not None:
        filt = filt.limit(limit)
    return count, filt
