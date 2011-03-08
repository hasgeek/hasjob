# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, session, abort

from app import app
from models import db, POSTSTATUS, JobPost, unique_hash
import forms

@app.route('/')
def index():
    posts = JobPost.query.filter(
        JobPost.status.in_([POSTSTATUS.CONFIRMED, POSTSTATUS.REVIEWED])).filter(
        JobPost.datetime > datetime.now() - timedelta(days=30)).order_by(db.desc(JobPost.datetime))
    return render_template('index.html', posts=posts)


@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))


@app.route('/detail/<hashid>')
def jobdetail(hashid):
    post = JobPost.query.filter_by(hashid=hashid).first()
    if post is None:
        abort(404)
    if post.status == POSTSTATUS.DRAFT:
        if 'userid' not in session or session['userid'] != post.email:
            abort(403)
    if post.status == POSTSTATUS.REJECTED:
        abort(403) # TODO: Present an error message
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
        post.headline = form.job_headline.data
        post.category = form.job_category.data
        post.location = form.job_location.data
        post.relocation_assist = form.job_relocation_assist.data
        post.description = form.job_description.data # FIXME: Sanitize input
        post.perks = form.job_perks_description.data if form.job_perks.data else ''
        post.how_to_apply = form.job_how_to_apply.data
        post.company_name = form.company_name.data
        post.company_logo = form.company_logo.data # TODO: Resize logo
        post.company_url = form.company_url.data
        post.email = form.poster_email.data

        db.session.commit()
        session['userid'] = post.email
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
    print request.method
    if request.method == 'POST' and form.validate():
        # Make a model, set cookie for email id, and redirect to detail page
        # Since it's still a draft, cookie must match job post's email id
        post = JobPost(hashid = unique_hash(JobPost),
                       ipaddr = request.environ['REMOTE_ADDR'],
                       useragent = request.user_agent.string)
        db.session.add(post)
        return editjob(post.hashid, post.email_verify_key, form, post)
    return render_template('postjob.html', form=form)


@app.route('/search')
def search():
    return "Coming soon"
