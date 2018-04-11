# -*- coding: utf-8 -*-


from flask import abort, redirect, render_template, request, url_for, g, flash
from flask_mail import Message
from flask_rq import job
from premailer import transform as email_transform
from pyisemail import is_email
from html2text import html2text
from baseframe import _
from .. import app, mail
from ..models import (db, JobPostSubscription, Filterset)


@job('hasjob')
def send_confirmation_email_for_job_alerts(to_address, token):
    msg = Message(subject=u"Please confirm your email to receive alerts on new jobs", recipients=[to_address])
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
        message = _(u"Thank you for signing up to receive job alerts from us! We'll keep you posted.")
        verified_user = True
    elif request.json.get('email') and is_email(request.json.get('email')):
        email = request.json.get('email')
        message = _(u"Thank you for signing up to receive job alerts from us! We've sent you a confirmation email, please do confirm it so we can keep you posted.")
        verified_user = False
    else:
        flash(_(u"Oops! Sorry, we need an email address to send you alerts."), 'danger')
        return redirect(url_for('index'), code=302)

    filterset = Filterset.from_filters(g.board, request.json.get('filters'))
    if not filterset:
        filterset = Filterset(board=g.board, filters=request.json.get('filters'))
        db.session.add(filterset)

    subscription = JobPostSubscription(filterset=filterset, email=email, user=g.user, anon_user=g.anon_user)
    if verified_user:
        subscription.verify_email()
    db.session.add(subscription)
    db.session.commit()
    if not verified_user:
        send_confirmation_email_for_job_alerts.delay(to_address=subscription.email, token=subscription.email_verify_key)

    flash(message, 'success')
    return redirect(url_for('index'), code=302)


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
    flash(_(u"You've just subscribed to receive alerts from us! We'll keep you posted."), 'success')
    return redirect(url_for('index'), code=302)


@app.route('/unsubscribe_from_job_alerts', subdomain='<subdomain>')
@app.route('/unsubscribe_from_job_alerts')
def unsubscribe_from_job_alerts():
    sub = JobPostSubscription.query.filter_by(unsubscribe_key=request.args.get('token')).one_or_none()
    if not sub:
        abort(404)
    if not sub.email_verified_at:
        abort(400)
    sub.unsubscribe()
    db.session.commit()
    flash(_(u"You've just unsubscribed from receiving alerts! Hope they were useful."), 'success')
    return redirect(url_for('index'), code=302)
