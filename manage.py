#!/usr/bin/env python

from coaster.manage import init_manager

from hasjob.models import db
from hasjob import app, init_for


if __name__ == '__main__':
    db.init_app(app)
    manager = init_manager(app, db, init_for)
    manager.run()
