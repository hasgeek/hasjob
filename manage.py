#!/usr/bin/env python

from coaster.manage import init_manager

from hasjob.models import db
from hasjob import app, init_for
from hasjob.search import configure_once as search_configure


def configure(env='dev'):
    """Configure Hasjob's search indexing"""
    init_for(env)
    search_configure()


if __name__ == '__main__':
    db.init_app(app)
    manager = init_manager(app, db, init_for)
    manager.command(configure)

    manager.run()
