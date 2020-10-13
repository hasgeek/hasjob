#!/usr/bin/env python

from datetime import timedelta

from coaster.manage import Manager, init_manager
from coaster.utils import utcnow
from hasjob import app
from hasjob.models import db
import hasjob
import hasjob.forms as forms
import hasjob.models as models
import hasjob.views as views

periodic = Manager(usage="Periodic tasks from cron (with recommended intervals)")


@periodic.command
def sessions():
    """Sweep user sessions to close all inactive sessions (10m)"""
    es = models.EventSession
    # Close all sessions that have been inactive for >= 30 minutes
    es.query.filter(
        es.ended_at.is_(None), es.active_at < (utcnow() - timedelta(minutes=30))
    ).update({es.ended_at: es.active_at})
    db.session.commit()


@periodic.command
def impressions():
    """Recount impressions for jobposts in the dirty list (5m)"""
    views.helper.update_dirty_impression_counts()


@periodic.command
def campaignviews():
    """Reset campaign views after more than 30 days since last view (1d)"""
    views.helper.reset_campaign_views()


if __name__ == '__main__':
    db.init_app(app)
    manager = init_manager(
        app, db, hasjob=hasjob, models=models, forms=forms, views=views
    )
    manager.add_command('periodic', periodic)
    manager.run()
