#!/usr/bin/env python

from coaster.manage import init_manager, database

import hasjob
import hasjob.models as models
import hasjob.forms as forms
import hasjob.views as views
from hasjob.models import db
from hasjob import app, init_for
from datetime import datetime, timedelta

@database.option('-e', '--env', default='dev', help="runtime env [default 'dev']")
def sweep(env):
    """Sweep the user database to close all the inactive sessions"""
    manager.init_for(env)
    print "Sweeping all the inactive sessions"
    es = models.EventSession
    # Inactive sessions are only kept for 30mins
    es.query.filter((es.ended_at==None) & (es.active_at<(datetime.utcnow() - \
        timedelta(minutes=30)))).update({es.ended_at: es.active_at})


if __name__ == '__main__':
    db.init_app(app)
    manager = init_manager(app, db, init_for, hasjob=hasjob, models=models, forms=forms, views=views)

    manager.run()
