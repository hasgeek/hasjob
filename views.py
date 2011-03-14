# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from urllib import quote, quote_plus
from pytz import utc, timezone
from flask import render_template, redirect, url_for, request, session, abort, flash, g
from flaskext.mail import Mail, Message
from markdown import markdown

from app import app
from models import db, POSTSTATUS, JobPost, JobType, JobCategory, unique_hash
import forms
from uploads import uploaded_logos, process_image
from utils import sanitize_html

mail = Mail()

@app.route('/')
def index(basequery=None, type=None, category=None):
    now = datetime.utcnow()
    newlimit = timedelta(days=3)
    if basequery is None:
        basequery = JobPost.query
    posts = basequery.filter(
        JobPost.status.in_([POSTSTATUS.CONFIRMED, POSTSTATUS.REVIEWED])).filter(
        JobPost.datetime > datetime.now() - timedelta(days=30)).order_by(db.desc(JobPost.datetime))
    return render_template('index.html', posts=posts, now=now, newlimit=newlimit,
                           jobtype=type, jobcategory=category)


@app.route('/type/<slug>')
def browse_by_type(slug):
    if slug == 'all':
        return redirect(url_for('index'))
    ob = JobType.query.filter_by(slug=slug).first()
    if not ob:
        abort(404)
    basequery = JobPost.query.filter_by(type_id=ob.id)
    return index(basequery=basequery, type=ob)


@app.route('/category/<slug>')
def browse_by_category(slug):
    if slug == 'all':
        return redirect(url_for('index'))
    ob = JobCategory.query.filter_by(slug=slug).first()
    if not ob:
        abort(404)
    basequery = JobPost.query.filter_by(category_id=ob.id)
    return index(basequery=basequery, category=ob)



@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))


@app.route('/logo/<hashid>')
def logoimage(hashid):
    post = JobPost.query.filter_by(hashid=hashid).first()
    if post is None:
        abort(404)
    if post.status == POSTSTATUS.REJECTED:
        # Don't show logo if post has been rejected. Could be spam
        abort(410)
    return redirect(uploaded_logos.url(post.company_logo))


@app.route('/view/<hashid>')
def jobdetail(hashid):
    post = JobPost.query.filter_by(hashid=hashid).first()
    if post is None:
        abort(404)
    if post.status == POSTSTATUS.DRAFT:
        if post.edit_key not in session.get('userkeys', []):
            abort(403)
    if post.status == POSTSTATUS.REJECTED:
        abort(410)
    return render_template('detail.html', post=post)


@app.route('/confirm/<hashid>', methods=('GET', 'POST'))
def confirm(hashid):
    post = JobPost.query.filter_by(hashid=hashid).first()
    form = forms.ConfirmForm()
    if post is None:
        abort(404)
    elif post.status == POSTSTATUS.REJECTED:
        abort(410)
    elif post.status == POSTSTATUS.DRAFT:
        if post.edit_key not in session.get('userkeys', []):
            abort(403)
    else:
        # Any other status: no confirmation required (via this handler)
        return redirect(url_for('jobdetail', hashid=post.hashid), code=302)
    if 'form.id' in request.form and form.validate_on_submit():
        # User has accepted terms of service. Now send email and/or wait for payment
        if not post.email_sent:
            msg = Message(subject="Confirmation of your job listing at the HasGeek Job Board",
                recipients=[post.email])
            msg.body = render_template("confirm_email.md", post=post)
            msg.html = markdown(msg.body)
            mail.send(msg)
            post.email_sent = True
            post.status = POSTSTATUS.PENDING
            db.session.commit()
        session.get('userkeys', []).remove(post.edit_key)
        session.modified = True # Since it won't detect changes to lists
        return render_template('mailsent.html', post=post)
    return render_template('confirm.html', post=post, form=form)


@app.route('/confirm/<hashid>/<key>')
def confirm_email(hashid, key):
    # If post is in pending state and email key is correct, convert to published
    # and update post.datetime to utcnow() so it'll show on top of the stack
    # This function expects key to be email_verify_key, not edit_key like the others
    post = JobPost.query.filter_by(hashid=hashid).first()
    if post is None:
        abort(404)
    elif post.status == POSTSTATUS.REJECTED:
        abort(410)
    elif post.status in [POSTSTATUS.CONFIRMED, POSTSTATUS.REVIEWED]:
        flash("This job listing has already been confirmed and published", "interactive")
        return redirect(url_for('jobdetail', hashid=post.hashid), code=302)
    elif post.status == POSTSTATUS.DRAFT:
        # This should not happen. The user doesn't have this URL until they
        # pass the confirm form
        return redirect(url_for('confirm', hashid=post.hashid), code=302)
    elif post.status == POSTSTATUS.PENDING:
        if key != post.email_verify_key:
            abort(403)
        else:
            post.email_verified = True
            post.status = POSTSTATUS.CONFIRMED
            post.datetime = datetime.utcnow()
            db.session.commit()
            flash("Congratulations! Your job listing has been published", "interactive")
    return redirect(url_for('jobdetail', hashid=post.hashid), code=302)


@app.route('/withdraw/<hashid>/<key>', methods=('GET', 'POST'))
def withdraw(hashid, key):
    # TODO: Support for withdrawing job posts
    abort(404)


@app.route('/edit/<hashid>/<key>', methods=('GET', 'POST'))
def editjob(hashid, key, form=None, post=None):
    if form is None:
        form = forms.ListingForm(request.form)
        form.job_type.choices = [(ob.id, ob.title) for ob in JobType.query.filter_by(public=True).order_by('seq')]
        form.job_category.choices = [(ob.id, ob.title) for ob in JobCategory.query.filter_by(public=True).order_by('seq')]
    if post is None:
        post = JobPost.query.filter_by(hashid=hashid).first()
        if post is None:
            abort(404)
    if key != post.edit_key:
        abort(403)
    if request.method == 'POST' and form.validate():
        post.headline = form.job_headline.data
        post.type_id = form.job_type.data
        post.category_id = form.job_category.data
        post.location = form.job_location.data
        post.relocation_assist = form.job_relocation_assist.data
        print form.job_description.data
        post.description = sanitize_html(form.job_description.data)
        print "-----"
        print post.description
        post.perks = sanitize_html(form.job_perks_description.data) if form.job_perks.data else ''
        post.how_to_apply = form.job_how_to_apply.data
        post.company_name = form.company_name.data
        post.company_url = form.company_url.data
        post.email = form.poster_email.data

        # TODO: Provide option of replacing logo or leaving it alone
        if request.files['company_logo']:
            thumbnail = g.company_logo
            #if 'company_logo' in g:
            #    # The validator saved a copy of the processed logo
            #    thumbnail = g['company_logo']
            #else:
            #    thumbnail = process_image(request.files['company_logo'])
            logofilename = uploaded_logos.save(thumbnail, name='%s.' % post.hashid)
            post.company_logo = logofilename
        else:
            post.company_logo = None

        db.session.commit()
        userkeys = session.get('userkeys', [])
        userkeys.append(post.edit_key)
        session['userkeys'] = userkeys
        return redirect(url_for('jobdetail', hashid=post.hashid), code=303)
    elif request.method == 'POST':
        flash("Please correct the indicated errors", category='interactive')
    elif request.method == 'GET':
        # Populate form from model
        form.job_headline.data = post.headline
        form.job_type.data = post.type_id
        form.job_category.data = post.category_id
        form.job_location.data = post.location
        form.job_relocation_assist.data = post.relocation_assist
        form.job_description.data = post.description
        form.job_perks.data = True if post.perks else False
        form.job_perks_description.data = post.perks
        form.job_how_to_apply.data = post.how_to_apply
        form.company_name.data = post.company_name
        form.company_url.data = post.company_url
        form.poster_email.data = post.email

    return render_template('postjob.html', form=form)


@app.route('/new', methods=('GET', 'POST'))
def newjob():
    form = forms.ListingForm()
    form.job_type.choices = [(ob.id, ob.title) for ob in JobType.query.filter_by(public=True).order_by('seq')]
    form.job_category.choices = [(ob.id, ob.title) for ob in JobCategory.query.filter_by(public=True).order_by('seq')]
    if request.method == 'POST' and request.form.get('form.id') == 'newheadline':
        form.csrf.data = form.reset_csrf()
    if request.method == 'POST' and request.form.get('form.id') != 'newheadline' and form.validate():
        # Make a model, set cookie for email id, and redirect to detail page
        # Since it's still a draft, cookie must match job post's email id
        post = JobPost(hashid = unique_hash(JobPost),
                       ipaddr = request.environ['REMOTE_ADDR'],
                       useragent = request.user_agent.string)
        db.session.add(post)
        return editjob(post.hashid, post.edit_key, form, post)
    elif request.method == 'POST' and request.form.get('form.id') != 'newheadline':
        flash("Please correct the indicated errors", category='interactive')

    return render_template('postjob.html', form=form)


@app.route('/search')
def search():
    abort(404)


@app.route('/feed')
def feed():
    abort(404)


@app.route('/type/')
@app.route('/category/')
@app.route('/view/')
@app.route('/edit/')
@app.route('/confirm/')
@app.route('/withdraw/')
def root_paths():
    return redirect(url_for('index'), code=302)


# --- Error handlers ----------------------------------------------------------

@app.errorhandler(403)
def error_403(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def error_404(e):
    return render_template('404.html'), 404

@app.errorhandler(410)
def error_410(e):
    return render_template('410.html'), 410

@app.errorhandler(500)
def error_500(e):
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
        url = url[7:]
    elif url.startswith('https://'):
        url = url[8:]
    if url.endswith('/') and url.count('/') == 1:
        # Remove trailing slash if applied to end of domain name
        # but leave it in if it's a path
        url = url[:-1]
    return url

@app.template_filter('urlquote')
def urlquote(data):
    if isinstance(data, unicode):
        return quote(data.encode('utf-8'))
    else:
        return quote(data)

@app.template_filter('urlquoteplus')
def urlquote(data):
    if isinstance(data, unicode):
        return quote_plus(data.encode('utf-8'))
    else:
        return quote_plus(data)

@app.template_filter('scrubemail')
def scrubemail(data):
    # TODO: return Markup() with email scrubbed
    return data
