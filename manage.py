#!/usr/bin/env python

from coaster.manage import init_manager, manager

import hasjob
import hasjob.models as models
import hasjob.forms as forms
import hasjob.views as views
from hasjob.models import db
from hasjob import app, init_for
from datetime import datetime, timedelta


@manager.option('-e', '--env', default='dev', help="runtime env [default 'dev']")
def sweep(env):
    """Sweep user sessions to close all inactive sessions"""
    manager.init_for(env)
    es = models.EventSession
    # Close all sessions that have been inactive for >= 30 minutes
    es.query.filter(es.ended_at == None,  # NOQA
        es.active_at < (datetime.utcnow() - timedelta(minutes=30))).update(
        {es.ended_at: es.active_at})
    db.session.commit()


if __name__ == '__main__':
    db.init_app(app)
    manager = init_manager(app, db, init_for, hasjob=hasjob, models=models, forms=forms, views=views)

    manager.run()
