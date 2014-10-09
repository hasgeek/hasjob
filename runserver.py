#!/usr/bin/env python
# -*- coding: utf-8 -*-
from hasjob import app, init_for, models
from hasjob.models import db

if __name__ == '__main__':

    import sys
    init_for('dev')
    # Seed with sample data
    with app.test_request_context():
        if not models.JobType.query.notempty():
            print >> sys.stderr, "Adding some job types"
            db.session.add(models.JobType(seq=10, name=u'fulltime', title=u'Full-time employment'))
            db.session.add(models.JobType(seq=20, name=u'contract', title=u'Short-term contract'))
            db.session.add(models.JobType(seq=30, name=u'freelance', title=u'Freelance or consulting'))
            db.session.add(models.JobType(seq=40, name=u'volunteer', title=u'Volunteer contributor'))
            db.session.add(models.JobType(seq=50, name=u'partner', title=u'Partner for a venture'))
            db.session.commit()
        if not models.JobCategory.query.notempty():
            print >> sys.stderr, "Adding some job categories"
            db.session.add(models.JobCategory(seq=10, name=u'programming', title=u'Programming'))
            db.session.add(models.JobCategory(seq=20, name=u'ux', title=u'Interaction Design'))
            db.session.add(models.JobCategory(seq=30, name=u'design', title=u'Graphic Design'))
            db.session.add(models.JobCategory(seq=40, name=u'testing', title=u'Testing'))
            db.session.add(models.JobCategory(seq=50, name=u'sysadmin', title=u'Systems Administration'))
            db.session.add(models.JobCategory(seq=60, name=u'business', title=u'Business/Management'))
            db.session.add(models.JobCategory(seq=70, name=u'edit', title=u'Writer/Editor'))
            db.session.add(models.JobCategory(seq=80, name=u'support', title=u'Customer Support'))
            db.session.add(models.JobCategory(seq=90, name=u'mobile', title=u'Mobile (iPhone, Android, other)'))
            db.session.commit()
        if not models.ReportCode.query.notempty():
            print >> sys.stderr, "Adding some report codes"
            db.session.add(models.ReportCode(seq=10, name=u'spam', title=u'Spam, not a job listing'))
            db.session.add(models.ReportCode(seq=20, name=u'fake', title=u'Appears to be a fake listing'))
            db.session.add(models.ReportCode(seq=30, name=u'anon', title=u'Organization is not clearly identified'))
            db.session.add(models.ReportCode(seq=40, name=u'unclear', title=u'Job position is not properly described'))
            db.session.commit()
    app.run('0.0.0.0', debug=True)
