#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app import app
import models, forms, views, assets, uploads
from models import db
from flaskext.assets import Environment, Bundle

app.config.from_object(__name__)
try:
    app.config.from_object('settings')
except ImportError:
    import sys
    print >> sys.stderr, "Please create a settings.py with the necessary settings. See settings-sample.py."
    print >> sys.stderr, "You may use the site without these settings, but some features may not work."

uploads.configure()
views.mail.init_app(app)

if __name__ == '__main__':
    #import logging
    #file_handler = logging.FileHandler('error.log')
    #file_handler.setLevel(logging.WARNING)
    #app.logger.addHandler(file_handler)
    # Create database table
    db.create_all()
    # Seed with sample data
    with app.test_request_context():
        if models.JobType.query.count() == 0:
            db.session.add(models.JobType(seq=10, slug='fulltime', title='Full-time employment'))
            db.session.add(models.JobType(seq=20, slug='contract', title='Short-term contract'))
            db.session.add(models.JobType(seq=30, slug='freelance', title='Freelance or consulting'))
            db.session.add(models.JobType(seq=40, slug='volunteer', title='Volunteer contributor'))
            db.session.add(models.JobType(seq=50, slug='partner', title='Partner for a venture'))
            db.session.commit()
        if models.JobCategory.query.count() == 0:
            db.session.add(models.JobCategory(seq=10, slug='programming', title='Programming'))
            db.session.add(models.JobCategory(seq=20, slug='ux', title='Interaction Design'))
            db.session.add(models.JobCategory(seq=30, slug='design', title='Graphic Design'))
            db.session.add(models.JobCategory(seq=40, slug='testing', title='Testing'))
            db.session.add(models.JobCategory(seq=50, slug='sysadmin', title='Systems Administration'))
            db.session.add(models.JobCategory(seq=60, slug='business', title='Business/Management'))
            db.session.add(models.JobCategory(seq=70, slug='edit', title='Writer/Editor'))
            db.session.add(models.JobCategory(seq=80, slug='support', title='Customer Support'))
            db.session.add(models.JobCategory(seq=90, slug='mobile', title='Mobile (iPhone, Android, other)'))
            db.session.commit()
    app.run(debug=True)
