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

def configure():
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
    configure()

    import sys
    # Create database table
    db.create_all()
    # Seed with sample data
    with app.test_request_context():
        if models.ReportCode.query.count() == 0:
            print >> sys.stderr, "Adding some report codes"
            db.session.add(models.ReportCode(seq=10, slug='spam', title=u'Spam, not a job listing'))
            db.session.add(models.ReportCode(seq=20, slug='fake', title=u'Appears to be a fake listing'))
            db.session.add(models.ReportCode(seq=30, slug='anon', title=u'Organization is not clearly identified'))
            db.session.add(models.ReportCode(seq=40, slug='unclear', title=u'Job position is not properly described'))
            db.session.commit()
    app.run(debug=True)
