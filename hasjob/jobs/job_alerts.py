# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from flask_mail import Message
from flask import render_template
from flask_rq import job
from html2text import html2text
from premailer import transform as email_transform
from hasjob import mail
from hasjob.models import db, JobPost, JobPostSubscription, JobPostAlert, jobpost_alert_table
from hasjob.views.index import fetch_jobposts


@job('hasjob')
def send_email_alerts():
    subscriptions = JobPostSubscription.query.filter(JobPostSubscription.active == True,
        JobPostSubscription.email_verified_at != None).all()
    for sub in subscriptions:
        if JobPostAlert.query.filter(
            JobPostAlert.jobpost_subscription == sub,
            JobPostAlert.sent_at >= datetime.utcnow() - timedelta(days=sub.email_frequency.value)
            ).order_by('created_at desc').notempty():
            print 'alert was recently sent so skipping'
            break

        posts = fetch_jobposts(filters=sub.filterset.to_filters(), posts_only=True)
        sent_jobpostids = JobPost.query.join(jobpost_alert_table).join(JobPostAlert).filter(JobPostAlert.jobpost_subscription == sub).options(db.load_only('id')).all()
        unseen_posts = [post for post in posts if post.id not in sent_jobpostids]
        if not unseen_posts:
            print "no unseen posts"
            break

        jobpost_alert = JobPostAlert(jobpost_subscription=sub)
        jobpost_alert.jobposts = unseen_posts
        db.session.commit()

        msg = Message(subject=u"Job alerts", recipients=[sub.user.email])
        html = email_transform(render_template('job_alert_mailer.html.jinja2', posts=jobpost_alert.jobposts))
        msg.html = html
        msg.body = html2text(html)
        mail.send(msg)
