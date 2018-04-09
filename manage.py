#!/usr/bin/env python

from coaster.manage import init_manager, Manager

import hasjob
import hasjob.models as models
import hasjob.forms as forms
import hasjob.views as views
from hasjob.models import db
from hasjob import app
from hasjob.jobs.job_alerts import send_email_alerts
from datetime import datetime, timedelta

periodic = Manager(usage="Periodic tasks from cron (with recommended intervals)")


@periodic.command
def sessions():
    """Sweep user sessions to close all inactive sessions (10m)"""
    es = models.EventSession
    # Close all sessions that have been inactive for >= 30 minutes
    es.query.filter(es.ended_at == None,  # NOQA
        es.active_at < (datetime.utcnow() - timedelta(minutes=30))).update(
        {es.ended_at: es.active_at})
    db.session.commit()


@periodic.command
def impressions():
    """Recount impressions for jobposts in the dirty list (5m)"""
    views.helper.update_dirty_impression_counts()


@periodic.command
def campaignviews():
    """Reset campaign views after more than 30 days since last view (1d)"""
    views.helper.reset_campaign_views()


@periodic.command
def send_job_alerts():
    """Run email alerts very morning at 8 AM"""
    send_email_alerts.delay()


if __name__ == '__main__':
    db.init_app(app)
    manager = init_manager(app, db, hasjob=hasjob, models=models, forms=forms, views=views)
    manager.add_command('periodic', periodic)
    manager.run()
