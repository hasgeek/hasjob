#!/usr/bin/env python

from coaster.manage import init_manager

import hasjob
import hasjob.models as models
import hasjob.forms as forms
import hasjob.views as views
from hasjob.models import db
from hasjob import app, init_for


if __name__ == '__main__':
    db.init_app(app)
    manager = init_manager(app, db, init_for, hasjob=hasjob, models=models, forms=forms, views=views)

    manager.run()
