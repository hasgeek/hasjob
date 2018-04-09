# -*- coding: utf-8 -*-


from flask import abort, redirect, render_template, request, url_for, g
from flask_mail import Message
from flask_rq import job
from premailer import transform as email_transform
from html2text import html2text
from .. import app, mail
from ..models import (db, User, AnonUser, JobPostSubscription, Filterset)


@app.route('/confirm_subscription_to_job_alerts', subdomain='<subdomain>')
@app.route('/confirm_subscription_to_job_alerts')
def confirm_subscription_to_job_alerts():
    sub = JobPostSubscription.query.filter_by(email_verify_key=request.args.get('token')).one_or_none()
    if not sub:
        abort(404)
    if sub.email_verified_at:
        abort(400)
    sub.verify_email()
    db.session.commit()
    return redirect(url_for('index'), code=302)


@job('hasjob')
def send_email_confirmation_for_job_alerts(to_address, token):
    msg = Message(subject=u"Job alerts", recipients=[to_address])
    html = email_transform(render_template('job_alert_email_confirmation.html.jinja2', token=token))
    msg.html = html
    msg.body = html2text(html)
    mail.send(msg)


@app.route('/subscribe_to_job_alerts', subdomain='<subdomain>', methods=['POST'])
@app.route('/subscribe_to_job_alerts', methods=['POST'])
def subscribe_to_job_alerts():
    if not request.json or not request.json.get('filters'):
        abort(400)

    if g.user and g.user.email:
        email = g.user.email
    # elif request.json.get('email') and valid_email(request.json.get('email')):
    elif request.json.get('email'):
        email = request.json.get('email')
    else:
        abort(400)

    user_type = User.__name__
    if g.user:
        user = g.user
        if not g.user.email:
            # TODO Should we update email on g.user?
            pass
    else:
        user = User.query.filter_by(email=email).one_or_none()
        if not user:
            user = g.anon_user
            user_type = AnonUser.__name__

    filterset = Filterset.from_filters(g.board, request.json.get('filters'))
    if not filterset:
        filterset = Filterset.init_from_filters(g.board, request.json.get('filters'))
        db.session.add(filterset)

    sub = JobPostSubscription(user=user, user_type=user_type, filterset=filterset)
    db.session.add(sub)
    db.session.commit()

    send_email_confirmation_for_job_alerts.delay(to_address=email, token=sub.email_verify_key)
    return redirect(url_for('index'), code=302)
