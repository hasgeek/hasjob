#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from app import app
import models, forms, views, admin, assets, uploads, search
from models import db
import loghandler

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

log_formatter = loghandler.LocalVarFormatter()
file_handler = logging.FileHandler(app.config['LOGFILE'])
file_handler.setFormatter(log_formatter)
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
            db.session.add(models.JobType(seq=10, slug='fulltime', title=u'Full-time employment'))
            db.session.add(models.JobType(seq=20, slug='contract', title=u'Short-term contract'))
            db.session.add(models.JobType(seq=30, slug='freelance', title=u'Freelance or consulting'))
            db.session.add(models.JobType(seq=40, slug='volunteer', title=u'Volunteer contributor'))
            db.session.add(models.JobType(seq=50, slug='partner', title=u'Partner for a venture'))
            db.session.commit()
        if models.JobCategory.query.count() == 0:
            print >> sys.stderr, "Adding some job categories"
            db.session.add(models.JobCategory(seq=10, slug='programming', title=u'Programming'))
            db.session.add(models.JobCategory(seq=20, slug='ux', title=u'Interaction Design'))
            db.session.add(models.JobCategory(seq=30, slug='design', title=u'Graphic Design'))
            db.session.add(models.JobCategory(seq=40, slug='testing', title=u'Testing'))
            db.session.add(models.JobCategory(seq=50, slug='sysadmin', title=u'Systems Administration'))
            db.session.add(models.JobCategory(seq=60, slug='business', title=u'Business/Management'))
            db.session.add(models.JobCategory(seq=70, slug='edit', title=u'Writer/Editor'))
            db.session.add(models.JobCategory(seq=80, slug='support', title=u'Customer Support'))
            db.session.add(models.JobCategory(seq=90, slug='mobile', title=u'Mobile (iPhone, Android, other)'))
            db.session.commit()
        if models.ReportCode.query.count() == 0:
            print >> sys.stderr, "Adding some report codes"
            db.session.add(models.ReportCode(seq=10, slug='spam', title=u'Spam, not a job listing'))
            db.session.add(models.ReportCode(seq=20, slug='fake', title=u'Appears to be a fake listing'))
            db.session.add(models.ReportCode(seq=30, slug='anon', title=u'Organization is not clearly identified'))
            db.session.add(models.ReportCode(seq=40, slug='unclear', title=u'Job position is not properly described'))
            db.session.commit()
    app.run(debug=True)
