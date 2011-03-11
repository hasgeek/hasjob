# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from pytz import utc, timezone
from flask import render_template, redirect, url_for, request, session, abort, flash

from app import app
from models import db, POSTSTATUS, JobPost, unique_hash
import forms
from utils import sanitize_html

@app.route('/')
def index():
    now = datetime.utcnow()
    newlimit = timedelta(days=3)
    posts = JobPost.query.filter(
        JobPost.status.in_([POSTSTATUS.CONFIRMED, POSTSTATUS.REVIEWED])).filter(
        JobPost.datetime > datetime.now() - timedelta(days=30)).order_by(db.desc(JobPost.datetime))
    return render_template('index.html', posts=posts, now=now, newlimit=newlimit)


@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))


@app.route('/detail/<hashid>')
def jobdetail(hashid):
    post = JobPost.query.filter_by(hashid=hashid).first()
    if post is None:
        abort(404)
    if post.status == POSTSTATUS.DRAFT:
        if 'userkey' not in session or session['userkey'] != post.email_verify_key:
            abort(403)
    if post.status == POSTSTATUS.REJECTED:
        abort(410)
    return render_template('detail.html', post=post)


@app.route('/detail/')
def detailroot():
    return redirect(url_for(index))


@app.route('/edit/<hashid>/<key>', methods=['GET', 'POST'])
def editjob(hashid, key, form=None, post=None):
    if form is None:
        form = forms.PostingForm(request.form)
    if post is None:
        post = JobPost.query.filter_by(hashid=hashid).first()
        if post is None:
            abort(404)
    if key != post.email_verify_key:
        abort(403)
    if request.method == 'POST' and form.validate():
        print isinstance(form.job_description.data, unicode)
        post.headline = form.job_headline.data
        post.category = form.job_category.data
        post.location = form.job_location.data
        post.relocation_assist = form.job_relocation_assist.data
        post.description = sanitize_html(form.job_description.data)
        print isinstance(post.description, unicode)
        post.perks = sanitize_html(form.job_perks_description.data) if form.job_perks.data else ''
        post.how_to_apply = sanitize_html(form.job_how_to_apply.data)
        post.company_name = form.company_name.data
        post.company_logo = form.company_logo.data # TODO: Resize logo
        post.company_url = form.company_url.data
        post.email = form.poster_email.data

        db.session.commit()
        session['userkey'] = post.email_verify_key
        return redirect(url_for('jobdetail', hashid=post.hashid), code=303)

    elif request.method == 'GET':
        # Populate form from model
        form.job_headline.data = post.headline
        form.job_category.data = post.category
        form.job_location.data = post.location
        form.job_relocation_assist.data = post.relocation_assist
        form.job_description.data = post.description
        form.job_perks.data = True if post.perks else False
        form.job_perks_description.data = post.perks
        form.job_how_to_apply.data = post.how_to_apply
        form.company_name.data = post.company_name
        form.company_url.data = post.company_url
        form.poster_email.data = post.email

    return render_template('postjob.html', form=form) # TODO: Make a separate form with appropriate instructions


@app.route('/edit/')
def editroot():
    return redirect(url_for('index'))


@app.route('/new', methods=['GET', 'POST'])
def newjob():
    form = forms.PostingForm(request.form)
    if request.method == 'POST' and request.form.get('form.id') != 'newheadline' and form.validate():
        # Make a model, set cookie for email id, and redirect to detail page
        # Since it's still a draft, cookie must match job post's email id
        post = JobPost(hashid = unique_hash(JobPost),
                       ipaddr = request.environ['REMOTE_ADDR'],
                       useragent = request.user_agent.string)
        db.session.add(post)
        flash("This is a preview. It is only visible to you. If everything is okay, you may confirm and publish.", category='info')
        return editjob(post.hashid, post.email_verify_key, form, post)
    return render_template('postjob.html', form=form)


@app.route('/search')
def search():
    return "Coming soon"

# --- Error handlers ----------------------------------------------------------

@app.errorhandler(403)
def page_not_found(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(410)
def page_not_found(e):
    return render_template('410.html'), 410

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500

# --- Template filters --------------------------------------------------------

@app.template_filter('shortdate')
def shortdate(date):
    tz = timezone(app.config['TIMEZONE'])
    return utc.localize(date).astimezone(tz).strftime('%b %e')

@app.template_filter('longdate')
def longdate(date):
    tz = timezone(app.config['TIMEZONE'])
    return utc.localize(date).astimezone(tz).strftime('%B %e, %Y')

@app.template_filter('cleanurl')
def cleanurl(url):
    if url.startswith('http://'):
        return url[7:]
    elif url.startswith('https://'):
        return url[8:]
    else:
        return url
