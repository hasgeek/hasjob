# -*- coding: utf-8 -*-
# Admin views

from datetime import datetime, timedelta
from flask import abort, Response

from hasjob import app
from hasjob.search import delete_from_index
from hasjob.models import db, JobPost, agelimit
from hasjob.utils import md5sum


@app.route('/admin/update-search/<key>')
def delete_index(key):
    if key == app.config['PERIODIC_KEY']:
        now = datetime.utcnow()
        upper_age_limit = timedelta(days=agelimit.days*2) # Reasonably large window to clear backlog
        items = JobPost.query.filter(JobPost.datetime > now - upper_age_limit).filter(JobPost.datetime < now - agelimit).all()
        delete_from_index(items)
        return Response("Removed %d items.\n" % len(items),
                        content_type='text/plain; charset=utf-8')
    else:
        abort(403)


@app.route('/admin/update-md5sum/<key>')
def update_md5sum(key):
    # This view is a hack. We need proper SQL migrations instead of this
    if key == app.config['PERIODIC_KEY']:
        for post in JobPost.query.all():
            if not post.md5sum:
                post.md5sum = md5sum(post.email)
        db.session.commit()
        return Response("Updated md5sum for all posts.\n",
                        content_type='text/plain; charset=utf-8')
    else:
        abort(403)

# --- Admin views ------------------------------------------------------------
# LastUser integration pending
