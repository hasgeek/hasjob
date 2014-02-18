# -*- coding: utf-8 -*-
# Admin views

from datetime import datetime, timedelta
from flask import abort, Response

from hasjob import app
from hasjob.search import delete_from_index
from hasjob.models import JobPost, agelimit


@app.route('/admin/update-search/<key>')
def delete_index(key):
    if key == app.config['PERIODIC_KEY']:
        now = datetime.utcnow()
        upper_age_limit = timedelta(days=agelimit.days * 2)  # Reasonably large window to clear backlog
        items = JobPost.query.filter(JobPost.datetime > now - upper_age_limit).filter(JobPost.datetime < now - agelimit).all()
        delete_from_index.delay(items)
        return Response("Removed %d items.\n" % len(items),
                        content_type='text/plain; charset=utf-8')
    else:
        abort(403)

# --- Admin views ------------------------------------------------------------
# Work pending
