#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from app import app
import models, forms, views, assets, uploads, search
from models import db

app.config.from_object(__name__)
try:
    app.config.from_object('settings')
except ImportError:
    import sys
    print >> sys.stderr, "Please create a settings.py with the necessary settings. See settings-sample.py."
    print >> sys.stderr, "You may use the site without these settings, but some features may not work."

uploads.configure()
search.configure()
views.mail.init_app(app)

file_handler = logging.FileHandler(app.config['LOGFILE'])
file_handler.setLevel(logging.WARNING)
app.logger.addHandler(file_handler)
if app.config['ADMINS']:
    mail_handler = logging.handlers.SMTPHandler(app.config['MAIL_SERVER'],
        app.config['DEFAULT_MAIL_SENDER'][1],
        app.config['ADMINS'],
        'hasgeek-jobs failure',
        credentials = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']))
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)


if __name__ == '__main__':
    import sys
    # Create database table
    db.create_all()
    # Seed with sample data
    with app.test_request_context():
        if models.JobType.query.count() == 0:
            print >> sys.stderr, "Adding some job types"
            db.session.add(models.JobType(seq=10, slug='fulltime', title='Full-time employment'))
            db.session.add(models.JobType(seq=20, slug='contract', title='Short-term contract'))
            db.session.add(models.JobType(seq=30, slug='freelance', title='Freelance or consulting'))
            db.session.add(models.JobType(seq=40, slug='volunteer', title='Volunteer contributor'))
            db.session.add(models.JobType(seq=50, slug='partner', title='Partner for a venture'))
            db.session.commit()
        if models.JobCategory.query.count() == 0:
            print >> sys.stderr, "Adding some job categories"
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
        if models.ReportCode.query.count() == 0:
            print >> sys.stderr, "Adding some report codes"
            db.session.add(models.ReportCode(seq=10, slug='spam', title='Spam, not a job listing'))
            db.session.add(models.ReportCode(seq=20, slug='fake', title='Appears to be a fake listing'))
            db.session.add(models.ReportCode(seq=30, slug='anon', title='Organization is not clearly identified'))
            db.session.add(models.ReportCode(seq=40, slug='unclear', title='Job position is not properly described'))
            db.session.commit()
    app.run(debug=True)
