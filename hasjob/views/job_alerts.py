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
from ..forms import JobPostSubscriptionForm


@job('hasjob')
def send_confirmation_email_for_job_alerts(to_address, token):
    msg = Message(subject=u"Please confirm your email to receive alerts on new jobs", recipients=[to_address])
    html = email_transform(render_template('job_alert_email_confirmation.html.jinja2', token=token))
    msg.html = html
    msg.body = html2text(html)
    mail.send(msg)


@app.route('/api/1/subscribe_to_job_alerts', subdomain='<subdomain>', methods=['POST'])
@app.route('/api/1/subscribe_to_job_alerts', methods=['POST'])
def subscribe_to_job_alerts():
    form = JobPostSubscriptionForm()
    if not form.validate_on_submit():
        flash(_(u"Oops! Sorry, we need an valid email address to send you alerts."), 'danger')
        return redirect(url_for('index'), code=302)

    if g.user and g.user.email:
        email = g.user.email
        message = _(u"Thank you for signing up to receive job alerts from us! We'll keep you posted.")
        verified_user = True
    elif form.email.data:
        email = form.email.data
        message = _(u"Thank you for signing up to receive job alerts from us! We've sent you a confirmation email, please do confirm it so we can keep you posted.")
        verified_user = False

    filters = {
        'l': request.args.getlist('l'),
        't': request.args.getlist('t'),
        'c': request.args.getlist('c'),
        'currency': request.args.get('currency'),
        'pay': request.args.get('pay'),
        'equity': request.args.get('equity'),
        'q': request.args.get('q')
    }
    filterset = Filterset.from_filters(g.board, filters)
    if filterset:
        existing_subscription = JobPostSubscription.get(filterset, email)
        if existing_subscription:
            flash(_(u"You've already subscribed to receive alerts for jobs that match this filtering criteria."), 'danger')
            return redirect(url_for('index'), code=302)
    else:
        filterset = Filterset(board=g.board, filters=filters)
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


@app.route('/api/1/confirm_subscription_to_job_alerts', subdomain='<subdomain>')
@app.route('/api/1/confirm_subscription_to_job_alerts')
def confirm_subscription_to_job_alerts():
    subscription = JobPostSubscription.query.filter_by(email_verify_key=request.args.get('token')).one_or_none()
    if not subscription:
        abort(404)
    if subscription.email_verified_at:
        abort(400)
    subscription.verify_email()
    db.session.commit()
    flash(_(u"You've just subscribed to receive alerts from us! We'll keep you posted."), 'success')
    return redirect(url_for('index'), code=302)


@app.route('/api/1/unsubscribe_from_job_alerts', subdomain='<subdomain>')
@app.route('/api/1/unsubscribe_from_job_alerts')
def unsubscribe_from_job_alerts():
    subscription = JobPostSubscription.query.filter_by(unsubscribe_key=request.args.get('token')).one_or_none()
    if not subscription:
        abort(404)
    if not subscription.email_verified_at:
        abort(400)
    subscription.unsubscribe()
    db.session.commit()
    flash(_(u"You've just unsubscribed from receiving alerts! Hope they were useful."), 'success')
    return redirect(url_for('index'), code=302)
