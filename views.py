# -*- coding: utf-8 -*-

import os.path
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from urllib import quote, quote_plus
from pytz import utc, timezone
from difflib import SequenceMatcher
from flask import (render_template, redirect, url_for, request, session, abort,
    flash, g, Response, Markup, escape, jsonify)
from flaskext.mail import Mail, Message
from markdown import markdown
from twitter import tweet

from app import app
from models import db, POSTSTATUS, JobPost, JobType, JobCategory, JobPostReport, ReportCode, unique_hash, agelimit
import forms
from uploads import uploaded_logos, process_image
from utils import sanitize_html, scrubemail, md5sum, get_email_domain, get_word_bag
from search import do_search

mail = Mail()

# --- Constants ---------------------------------------------------------------

newlimit = timedelta(days=1)

# --- Helper functions --------------------------------------------------------

def getposts(basequery=None, sticky=False):
    if basequery is None:
        basequery = JobPost.query
    query = basequery.filter(
            JobPost.status.in_([POSTSTATUS.CONFIRMED, POSTSTATUS.REVIEWED])).filter(
            JobPost.datetime > datetime.utcnow() - agelimit)
    if sticky:
        query = query.order_by(db.desc(JobPost.sticky))
    return query.order_by(db.desc(JobPost.datetime))


def getallposts(order_by=None, desc=False, start=None, limit=None):
    if order_by is None:
        order_by = JobPost.datetime
    filt = JobPost.query.filter(JobPost.status.in_([POSTSTATUS.CONFIRMED, POSTSTATUS.REVIEWED]))
    count = filt.count()
    if desc:
        filt = filt.order_by(db.desc(order_by))
    else:
        filt = filt.order_by(order_by)
    if start is not None:
        filt = filt.offset(start)
    if limit is not None:
        filt = filt.limit(limit)
    return count, filt


# --- Routes ------------------------------------------------------------------

@app.route('/')
def index(basequery=None, type=None, category=None, md5sum=None):
    now = datetime.utcnow()
    posts = list(getposts(basequery, sticky=True))
    if posts:
        employer_name = posts[0].company_name
    else:
        employer_name = u'a single employer'
    return render_template('index.html', posts=posts, now=now, newlimit=newlimit,
                           jobtype=type, jobcategory=category, md5sum=md5sum,
                           employer_name=employer_name)


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


@app.route('/by/<md5sum>')
def browse_by_email(md5sum):
    if not md5sum:
        abort(404)
    basequery = JobPost.query.filter_by(md5sum=md5sum)
    return index(basequery=basequery, md5sum=md5sum)


@app.route('/feed')
def feed(basequery=None, type=None, category=None, md5sum=None):
    title = "All jobs"
    if type:
        title = type.title
    elif category:
        title = category.title
    elif md5sum:
        title = u"Jobs at a single employer"
    posts = list(getposts(basequery))
    if posts: # Can't do this unless posts is a list
        updated = posts[0].datetime.isoformat()+'Z'
        if md5sum:
            title = posts[0].company_name
    else:
        updated = datetime.utcnow().isoformat()+'Z'
    return Response(render_template('feed.xml', posts=posts, updated=updated, title=title),
                           content_type = 'application/atom+xml; charset=utf-8')


@app.route('/type/<slug>/feed')
def feed_by_type(slug):
    if slug == 'all':
        return redirect(url_for('feed'))
    ob = JobType.query.filter_by(slug=slug).first()
    if not ob:
        abort(404)
    basequery = JobPost.query.filter_by(type_id=ob.id)
    return feed(basequery=basequery, type=ob)


@app.route('/category/<slug>/feed')
def feed_by_category(slug):
    if slug == 'all':
        return redirect(url_for('feed'))
    ob = JobCategory.query.filter_by(slug=slug).first()
    if not ob:
        abort(404)
    basequery = JobPost.query.filter_by(category_id=ob.id)
    return feed(basequery=basequery, category=ob)


@app.route('/by/<md5sum>/feed')
def feed_by_email(md5sum):
    if not md5sum:
        abort(404)
    basequery = JobPost.query.filter_by(md5sum=md5sum)
    return feed(basequery=basequery, md5sum=md5sum)


@app.route('/archive')
def archive():
    def sortarchive(order_by):
        current_order_by = request.args.get('order_by')
        reverse = request.args.get('reverse')
        if order_by == current_order_by:
            if reverse is None:
                reverse = False
            try:
                reverse = bool(int(reverse))
            except ValueError:
                reverse = False
            reverse = int(not reverse)
        return url_for('archive', order_by=order_by,
            reverse=reverse,
            start=request.args.get('start'),
            limit=request.args.get('limit'))

    order_by = {
        'date': JobPost.datetime,
        'headline': JobPost.headline,
        'company': JobPost.company_name,
        'location': JobPost.location,
        }.get(request.args.get('order_by'))
    reverse = request.args.get('reverse')
    start = request.args.get('start', 0)
    limit = request.args.get('limit', 100)
    if order_by is None and reverse is None:
        order_by = JobPost.datetime
        reverse = True
    try:
        if reverse is not None:
            reverse = bool(int(reverse))
    except ValueError:
        reverse = None
    try:
        if start is not None:
            start = int(start)
    except ValueError:
        start = 0
    try:
        if limit is not None:
            limit = int(limit)
    except ValueError:
        limit = 100
    count, posts = getallposts(order_by=order_by, desc=reverse, start=start, limit=limit)

    if request.is_xhr:
        tmpl = 'archive_inner.html'
    else:
        tmpl = 'archive.html'
    return render_template(tmpl, order_by=request.args.get('order_by'),
        posts=posts, start=start, limit=limit, count=count,
        # Pass some functions
        min=min, max=max, sortarchive=sortarchive)


@app.route('/robots.txt')
def robots():
    return Response("Disallow: /edit/*\n"
                    "Disallow: /confirm/*\n"
                    "Disallow: /withdraw/*\n"
                    "Disallow: /admin/*\n"
                    "",
                    content_type = 'text/plain; charset=utf-8')


@app.route('/sitemap.xml')
def sitemap():
    sitemapxml = '<?xml version="1.0" encoding="UTF-8"?>\n'\
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    # Add job type pages to sitemap
    for item in JobType.query.all():
        sitemapxml += '  <url>\n'\
                      '    <loc>%s</loc>\n' % url_for('browse_by_type', slug=item.slug, _external=True) + \
                      '  </url>\n'
    # Add job category pages to sitemap
    for item in JobCategory.query.all():
      sitemapxml += '  <url>\n'\
                    '    <loc>%s</loc>\n' % url_for('browse_by_category', slug=item.slug, _external=True) + \
                    '  </url>\n'
    # Add live posts to sitemap
    for post in getposts():
        sitemapxml += '  <url>\n'\
                      '    <loc>%s</loc>\n' % url_for('jobdetail', hashid=post.hashid, _external=True) + \
                      '    <lastmod>%s</lastmod>\n' % (post.datetime.isoformat()+'Z') + \
                      '    <changefreq>monthly</changefreq>\n'\
                      '  </url>\n'
    sitemapxml += '</urlset>'
    return Response(sitemapxml, content_type = 'text/xml; charset=utf-8')


@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='img/favicon.ico'))


@app.route('/logo/<hashid>')
def logoimage(hashid):
    post = JobPost.query.filter_by(hashid=hashid).first()
    if post is None:
        abort(404)
    if not post.company_logo:
        # If there's no logo (perhaps it was deleted), don't try to show one
        abort(404)
    if post.status == POSTSTATUS.REJECTED:
        # Don't show logo if post has been rejected. Could be spam
        abort(410)
    return redirect(uploaded_logos.url(post.company_logo))


@app.route('/view/<hashid>', methods=('GET', 'POST'))
def jobdetail(hashid):
    post = JobPost.query.filter_by(hashid=hashid).first()
    if post is None:
        abort(404)
    if post.status in [POSTSTATUS.DRAFT, POSTSTATUS.PENDING]:
        if post.edit_key not in session.get('userkeys', []):
            abort(403)
    if post.status in [POSTSTATUS.REJECTED, POSTSTATUS.WITHDRAWN]:
        abort(410)
    reportform = forms.ReportForm()
    reportform.report_code.choices = [(ob.id, ob.title) for ob in ReportCode.query.filter_by(public=True).order_by('seq')]
    if reportform.validate_on_submit():
        report = JobPostReport(post=post, reportcode_id = reportform.report_code.data)
        report.ipaddr = request.environ['REMOTE_ADDR']
        report.useragent = request.user_agent.string
        db.session.add(report)
        db.session.commit()
        if request.is_xhr:
            return "<p>Thanks! This job listing has been flagged for review.</p>" #FIXME: Ugh!
        else:
            flash("Thanks! This job listing has been flagged for review.", "interactive")
    elif request.method == 'POST' and request.is_xhr:
        return render_template('inc/reportform.html', reportform=reportform, ajaxreg=True)
    return render_template('detail.html', post=post, reportform=reportform)


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
        session.permanent = True
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
            if app.config['TWITTER_ENABLED']:
                try:
                    tweet(post.headline, url_for('jobdetail', hashid=post.hashid,
                        _external=True), post.location)
                    flash("Congratulations! Your job listing has been published and tweeted",
                          "interactive")
                except:  # FIXME: Catch-all
                    flash("Congratulations! Your job listing has been published "
                          "(Twitter was not reachable for tweeting)", "interactive")
            else:
                flash("Congratulations! Your job listing has been published", "interactive")
    return redirect(url_for('jobdetail', hashid=post.hashid), code=302)


@app.route('/withdraw/<hashid>/<key>', methods=('GET', 'POST'))
def withdraw(hashid, key):
    # TODO: Support for withdrawing job posts
    post = JobPost.query.filter_by(hashid=hashid).first()
    form = forms.WithdrawForm()
    if post is None:
        abort(404)
    if key != post.edit_key:
        abort(403)
    if post.status == POSTSTATUS.WITHDRAWN:
        flash("Your job listing has already been withdrawn", "info")
        return redirect(url_for('index'), code=303)
    if post.status not in [POSTSTATUS.CONFIRMED, POSTSTATUS.REVIEWED]:
        flash("Your post cannot be withdrawn because it is not public", "info")
        return redirect(url_for('index'), code=303)
    if form.validate_on_submit():
        post.status = POSTSTATUS.WITHDRAWN
        post.closed_datetime = datetime.utcnow()
        db.session.commit()
        flash("Your job listing has been withdrawn and is no longer available", "info")
        return redirect(url_for('index'), code=303)
    return render_template("withdraw.html", post=post, form=form)


@app.route('/edit/<hashid>/<key>', methods=('GET', 'POST'))
def editjob(hashid, key, form=None, post=None, validated=False):
    if form is None:
        form = forms.ListingForm(request.form)
        form.job_type.choices = [(ob.id, ob.title) for ob in JobType.query.filter_by(public=True).order_by('seq')]
        form.job_category.choices = [(ob.id, ob.title) for ob in JobCategory.query.filter_by(public=True).order_by('seq')]
    if post is None:
        post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    if key != post.edit_key:
        abort(403)
    # Don't allow email address to be changed once its confirmed
    if request.method == 'POST' and post.status >= POSTSTATUS.PENDING:
        form.poster_email.data = post.email
    if request.method == 'POST' and (validated or form.validate()):
        form_description = sanitize_html(form.job_description.data)
        form_perks = sanitize_html(form.job_perks_description.data) if form.job_perks.data else ''
        form_how_to_apply = form.job_how_to_apply.data
        form_email_domain = get_email_domain(form.poster_email.data)
        form_words = get_word_bag(u' '.join((form_description, form_perks, form_how_to_apply)))

        similar = False
        for oldpost in JobPost.query.filter(JobPost.email_domain == form_email_domain).filter(
                                            JobPost.status > POSTSTATUS.PENDING).filter(
                                            JobPost.datetime > datetime.utcnow() - agelimit).all():
            if oldpost.id != post.id:
                if oldpost.words:
                    s = SequenceMatcher(None, form_words, oldpost.words)
                    if s.ratio() > 0.6:
                        similar = True
                        break

        if similar:
            flash("This listing is very similar to an earlier listing. You may not relist the same job "
                "in less than %d days. If you believe this to be an error, please email us at %s." % (agelimit.days,
                app.config['ADMINS'][0]), category='interactive')
        else:
            post.headline = form.job_headline.data
            post.type_id = form.job_type.data
            post.category_id = form.job_category.data
            post.location = form.job_location.data
            post.relocation_assist = form.job_relocation_assist.data
            post.description = form_description
            post.perks = form_perks
            post.how_to_apply = form_how_to_apply
            post.company_name = form.company_name.data
            post.company_url = form.company_url.data
            post.email = form.poster_email.data
            post.email_domain = form_email_domain
            post.md5sum = md5sum(post.email)
            # To protect from gaming, don't allow words to be removed in edited listings once the post
            # has been confirmed. Just add the new words.
            if post.status >= POSTSTATUS.CONFIRMED:
                prev_words = post.words or ''
            else:
                prev_words = u''
            post.words = get_word_bag(u' '.join((prev_words, form_description, form_perks, form_how_to_apply)))

            if request.files['company_logo']:
                # The form's validator saved the processed logo in g.company_logo.
                thumbnail = g.company_logo
                logofilename = uploaded_logos.save(thumbnail, name='%s.' % post.hashid)
                post.company_logo = logofilename
            else:
                if form.company_logo_remove.data:
                    post.company_logo = None

            db.session.commit()
            userkeys = session.get('userkeys', [])
            userkeys.append(post.edit_key)
            session['userkeys'] = userkeys
            session.permanent = True
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

    return render_template('postjob.html', form=form, no_email=post.status > POSTSTATUS.DRAFT)


@app.route('/new', methods=('GET', 'POST'))
def newjob():
    form = forms.ListingForm()
    form.job_type.choices = [(ob.id, ob.title) for ob in JobType.query.filter_by(public=True).order_by('seq')]
    form.job_category.choices = [(ob.id, ob.title) for ob in JobCategory.query.filter_by(public=True).order_by('seq')]
    if request.method == 'POST' and request.form.get('form.id') == 'newheadline':
        # POST request from the main page's Post a Job box.
        form.csrf_token.data = form.generate_csrf_token(session)
    if request.method == 'POST' and request.form.get('form.id') != 'newheadline' and form.validate():
        # POST request from new job page, with successful validation
        # Move it to the editjob page for handling here forward
        post = JobPost(hashid = unique_hash(JobPost),
                       ipaddr = request.environ['REMOTE_ADDR'],
                       useragent = request.user_agent.string)
        db.session.add(post)
        return editjob(post.hashid, post.edit_key, form, post, validated=True)
    elif request.method == 'POST' and request.form.get('form.id') != 'newheadline':
        # POST request from new job page, with errors
        flash("Please correct the indicated errors", category='interactive')

    # Render page. Execution reaches here under three conditions:
    # 1. GET request, page loaded for the first time
    # 2. POST request from main page's Post a Job box
    # 3. POST request from this page, with errors
    return render_template('postjob.html', form=form, no_removelogo=True)


@app.route('/search')
def search():
    now = datetime.utcnow()
    results = sorted(do_search(request.args.get('q', u''), expand=True),
        key=lambda r: getattr(r, 'datetime', now))
    results.reverse()
    return render_template('search.html', results=results, now=now, newlimit=newlimit)


@app.route('/tos')
def terms_of_service():
    return render_template('tos.html')


@app.route('/stats')
def stats():
    return render_template('stats.html')


@app.route('/stats/listings_by_date.json')
def stats_listings_by_date():
    now = datetime.utcnow()
    jobs = getposts()
    # Why is this code so complicated? How hard is it to get a count by date?
    # Just because we store datetime instead of date?
    listings_by_date = {}
    looper = now - agelimit
    for x in range(agelimit.days):
        listings_by_date[date(year=looper.year, month=looper.month, day=looper.day)] = 0
        looper += timedelta(days=1)
    for job in jobs:
        listings_by_date[date(year=job.datetime.year, month=job.datetime.month, day=job.datetime.day)] += 1
    listings_by_date = listings_by_date.items() # Convert from dict to list
    listings_by_date.sort()                     # and sort by date
    return jsonify(data=[[(x, listings_by_date[x][1]) for x in range(len(listings_by_date))]],
                   options={
                            'series': {'bars': {'show': True}},
                            'xaxis': {'show': True, 'min': 0, 'max': len(listings_by_date),
                                      'ticks': [(x, listings_by_date[x][0].strftime('%b %d')) for x in range(len(listings_by_date))]
                                     },
                            'yaxis': {'min': 0, 'tickSize': 1, 'tickDecimals': 0},
                            }
                   )


@app.route('/stats/listings_by_type.json')
def stats_listings_by_type():
    jobs = getposts()
    typecount = defaultdict(int)
    for job in jobs:
        typecount[job.type_id] += 1
    all_types = list(JobType.query.filter_by(public=True).order_by(JobType.seq).all())
    all_types.reverse() # Charts are drawn bottom to top
    data = []
    labels = []
    for x in range(len(all_types)):
        data.append([x, typecount[all_types[x].id]])
        labels.append([x, all_types[x].title])
    return jsonify(data=[{'data': data}],
                   options={
                            'series': {'bars': {'show': True, 'horizontal': True}},
                            'yaxis': {'show': True, 'min': 0, 'max': len(all_types), 'ticks': labels},
                            'xaxis': {'min': 0, 'tickSize': 1, 'tickDecimals': 0},
                            }
                   )


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

@app.template_filter('urlfor')
def url_from_ob(ob):
    if isinstance(ob, JobPost):
        return url_for('jobdetail', hashid=ob.hashid)
    elif isinstance(ob, JobType):
        return url_for('browse_by_type', slug=ob.slug)
    elif isinstance(ob, JobCategory):
        return url_for('browse_by_category', slug=ob.slug)


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
def scrubemail_filter(data, css_junk=''):
    return Markup(scrubemail(unicode(escape(data)), rot13=True, css_junk=css_junk))


@app.template_filter('usessl')
def usessl(url):
    """
    Convert a URL to https:// if SSL is enabled in site config
    """
    if not app.config.get('USE_SSL'):
        return url
    if url.startswith('//'): # //www.example.com/path
        return 'https:' + url
    if url.startswith('/'): # /path
        url = os.path.join(request.url_root, url[1:])
    if url.startswith('http:'): # http://www.example.com
        url = 'https:' + url[5:]
    return url
