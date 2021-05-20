#!/usr/bin/env python

from datetime import timedelta

from flask.cli import AppGroup

from coaster.utils import utcnow

from . import app, models, views
from .models import db


@app.shell_context_processor
def shell_context():
    return {'db': db, 'models': models}


periodic = AppGroup(
    'periodic', help="Periodic tasks from cron (with recommended intervals)"
)


@periodic.command('sessions')
def sessions():
    """Sweep user sessions to close all inactive sessions (10m)"""
    es = models.EventSession
    # Close all sessions that have been inactive for >= 30 minutes
    es.query.filter(
        es.ended_at.is_(None), es.active_at < (utcnow() - timedelta(minutes=30))
    ).update({es.ended_at: es.active_at})
    db.session.commit()


@periodic.command('impressions')
def impressions():
    """Recount impressions for jobposts in the dirty list (5m)"""
    views.helper.update_dirty_impression_counts()


@periodic.command('campaignviews')
def campaignviews():
    """Reset campaign views after more than 30 days since last view (1d)"""
    views.helper.reset_campaign_views()


app.cli.add_command(periodic)
