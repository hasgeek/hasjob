# -*- coding: utf-8 -*-

from flask_mail import Message
from flask import render_template
from flask_rq import job
from html2text import html2text
from premailer import transform as email_transform
from hasjob import mail
from hasjob.models import db, JobPost, JobPostSubscription, JobPostAlert, jobpost_alert_table
from hasjob.views.index import fetch_jobposts


def get_unseen_posts(subscription):
    posts = fetch_jobposts(filters=subscription.filterset.to_filters(), posts_only=True)
    seen_jobpostids = JobPost.query.join(jobpost_alert_table).join(JobPostAlert).filter(
        JobPostAlert.jobpost_subscription == subscription).options(db.load_only('id')).all()
    return [post for post in posts if post.id not in seen_jobpostids]


@job('hasjob')
def send_email_alerts():
    for subscription in JobPostSubscription.get_active_subscriptions():
        if subscription.has_recent_alert():
            # Alert was sent recently, break out of loop
            break

        if not subscription.is_right_time_to_send_alert():
            break

        unseen_posts = get_unseen_posts(subscription)
        if not unseen_posts:
            # Nothing new to see, break out of loop
            break

        jobpost_alert = JobPostAlert(jobpost_subscription=subscription)
        jobpost_alert.jobposts = unseen_posts

        msg = Message(subject=u"New jobs on Hasjob", recipients=[subscription.email])
        html = email_transform(render_template('job_alert_mailer.html.jinja2', posts=jobpost_alert.jobposts))
        msg.html = html
        msg.body = html2text(html)
        mail.send(msg)
        jobpost_alert.register_delivery()
        db.session.add(jobpost_alert)
        db.session.commit()
