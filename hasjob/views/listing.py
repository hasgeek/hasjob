# -*- coding: utf-8 -*-

import bleach
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from html2text import html2text
from premailer import transform as email_transform

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError
from flask import abort, flash, g, redirect, render_template, request, url_for, session, Markup, jsonify
from flask.ext.mail import Message
from baseframe import cache
from baseframe.forms import Form
from coaster.utils import getbool, get_email_domain, md5sum, base_domain_matches
from coaster.views import load_model
from hasjob import app, forms, mail, lastuser, dogpile_cache
from hasjob.models import (
    agelimit,
    db,
    Domain,
    JobCategory,
    JobType,
    JobPost,
    JobPostReport,
    POSTSTATUS,
    EMPLOYER_RESPONSE,
    PAY_TYPE,
    ReportCode,
    UserJobView,
    AnonJobView,
    JobApplication,
    Campaign, CAMPAIGN_POSITION,
    unique_hash,
    viewstats_by_id_qhour,
    viewstats_by_id_hour,
    viewstats_by_id_day,
    )
from hasjob.twitter import tweet
from hasjob.tagging import tag_locations, add_to_boards, tag_jobpost
from hasjob.uploads import uploaded_logos
from hasjob.utils import get_word_bag, redactemail, random_long_key, common_legal_names
from hasjob.views import ALLOWED_TAGS
from hasjob.nlp import identify_language
from hasjob.views.helper import gif1x1, cache_viewcounts, session_jobpost_ab, bgroup


@app.route('/<domain>/<hashid>', methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/<domain>/<hashid>', methods=('GET', 'POST'))
@app.route('/view/<hashid>', defaults={'domain': None}, methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/view/<hashid>', defaults={'domain': None}, methods=('GET', 'POST'))
def jobdetail(domain, hashid):
    is_siteadmin = lastuser.has_permission('siteadmin')
    query = JobPost.fetch(hashid).options(
        db.subqueryload('locations'), db.subqueryload('taglinks'))
    post = query.first_or_404()

    # If we're on a board (that's not 'www') and this post isn't on this board,
    # redirect to (a) the first board it is on, or (b) on the root domain (which may
    # be the 'www' board, which is why we don't bother to redirect if we're currently
    # in the 'www' board)
    if g.board and g.board.not_root and post.link_to_board(g.board) is None:
        blink = post.postboards.first()
        if blink:
            return redirect(post.url_for(subdomain=blink.board.name, _external=True))
        else:
            return redirect(post.url_for(subdomain=None, _external=True))

    # If this post is past pending state and the domain doesn't match, redirect there
    if post.status not in POSTSTATUS.UNPUBLISHED and post.email_domain != domain:
        return redirect(post.url_for(), code=301)

    if post.status in POSTSTATUS.UNPUBLISHED:
        if not ((g.user and post.admin_is(g.user))):
            abort(403)
    if post.status in POSTSTATUS.GONE:
        abort(410)
    if g.user:
        jobview = UserJobView.get(post, g.user)
        if jobview is None:
            jobview = UserJobView(user=g.user, jobpost=post)
            post.uncache_viewcounts('viewed')
            cache.delete_memoized(viewstats_by_id_qhour, post.id)
            cache.delete_memoized(viewstats_by_id_hour, post.id)
            cache.delete_memoized(viewstats_by_id_day, post.id)
            db.session.add(jobview)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
            post.viewcounts  # Re-populate cache
    else:
        jobview = None

    if g.anon_user:
        anonview = AnonJobView.get(post, g.anon_user)
        if not anonview:
            anonview = AnonJobView(jobpost=post, anon_user=g.anon_user)
            db.session.add(anonview)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    if g.user:
        report = JobPostReport.query.filter_by(post=post, user=g.user).first()
    else:
        report = None

    g.jobpost_viewed = (post.id, getbool(request.args.get('b')))

    reportform = forms.ReportForm(obj=report)
    reportform.report_code.choices = [(ob.id, ob.title) for ob in ReportCode.query.filter_by(public=True).order_by('seq')]
    rejectform = forms.RejectForm()
    moderateform = forms.ModerateForm()
    if request.method == 'GET':
        moderateform.reason.data = post.review_comments
    if g.board:
        pinnedform = forms.PinnedForm(obj=post.link_to_board(g.board))
    else:
        pinnedform = forms.PinnedForm(obj=post)

    if reportform.validate_on_submit():
        if g.user:
            if report is None:
                report = JobPostReport(post=post, user=g.user)
            report.reportcode_id = reportform.report_code.data
            report.ipaddr = request.environ['REMOTE_ADDR']
            report.useragent = request.user_agent.string
            db.session.add(report)
            db.session.commit()
            if request.is_xhr:
                return "<p>Thanks! This post has been flagged for review</p>"  # FIXME: Ugh!
            else:
                flash("Thanks! This post has been flagged for review", "interactive")
        else:
            if request.is_xhr:
                return "<p>You need to be logged in to report a post</p>"  # FIXME: Ugh!
            else:
                flash("You need to be logged in to report a post", "interactive")
    elif request.method == 'POST' and request.is_xhr:
        return render_template('inc/reportform.html', reportform=reportform)

    if post.company_url and post.status != POSTSTATUS.ANNOUNCEMENT:
        domain_mismatch = not base_domain_matches(post.company_url.lower(), post.email_domain.lower())
    else:
        domain_mismatch = False

    if not g.kiosk:
        if g.preview_campaign:
            header_campaign = g.preview_campaign
        else:
            header_campaign = Campaign.for_context(CAMPAIGN_POSITION.HEADER, board=g.board, user=g.user,
                anon_user=g.anon_user, geonameids=g.user_geonameids + post.geonameids)
    else:
        header_campaign = None

    if g.user and not g.kiosk:
        g.starred_ids = set(g.user.starred_job_ids(agelimit))
    else:
        g.starred_ids = set()

    is_bgroup = getbool(request.args.get('b'))
    headline = post.headlineb if is_bgroup and post.headlineb else post.headline

    return render_template('detail.html', post=post, headline=headline, reportform=reportform, rejectform=rejectform,
        pinnedform=pinnedform,
        jobview=jobview, report=report, moderateform=moderateform,
        domain_mismatch=domain_mismatch, header_campaign=header_campaign,
        is_bgroup=is_bgroup, is_siteadmin=is_siteadmin
        )


@app.route('/<domain>/<hashid>/related', subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/related')
@app.route('/view/<hashid>/related', defaults={'domain': None}, subdomain='<subdomain>')
@app.route('/view/<hashid>/related', defaults={'domain': None})
def job_related_posts(domain, hashid):
    is_siteadmin = lastuser.has_permission('siteadmin')
    post = JobPost.query.filter_by(hashid=hashid).options(*JobPost._defercols).first_or_404()

    jobpost_ab = session_jobpost_ab()
    related_posts = post.related_posts().all()
    if is_siteadmin or (g.user and g.user.flags.get('is_employer_month')):
        cache_viewcounts(related_posts)
    g.impressions = {rp.id: (False, rp.id, bgroup(jobpost_ab, rp)) for rp in related_posts}

    return render_template('related_posts.html', post=post,
        related_posts=related_posts, is_siteadmin=is_siteadmin)


@app.route('/<domain>/<hashid>/star', defaults={'domain': None}, methods=['POST'], subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/star', defaults={'domain': None}, methods=['POST'])
@app.route('/star/<hashid>', defaults={'domain': None}, methods=['POST'], subdomain='<subdomain>')
@app.route('/star/<hashid>', defaults={'domain': None}, methods=['POST'])
@lastuser.requires_login
def starjob(domain, hashid):
    """
    Star/unstar a job
    """
    is_starred = None
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    # Handle IntegrityError/StaleDataError caused by users double clicking
    passed = False
    while not passed:
        if g.user.has_starred_post(post):
            g.user.starred_jobs.remove(post)
            is_starred = False
        else:
            g.user.starred_jobs.append(post)
            is_starred = True
        try:
            db.session.commit()
            passed = True
        except (IntegrityError, StaleDataError):
            pass

    response = jsonify(is_starred=is_starred)
    if is_starred:
        response.status_code = 201
    return response


@app.route('/<domain>/<hashid>/reveal', methods=['POST'], subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/reveal', methods=['POST'])
@app.route('/reveal/<hashid>', methods=['POST'], defaults={'domain': None}, subdomain='<subdomain>')
@app.route('/reveal/<hashid>', methods=['POST'], defaults={'domain': None})
@lastuser.requires_login
def revealjob(domain, hashid):
    """
    Reveal job application form
    """
    post = JobPost.query.filter_by(hashid=hashid).options(db.load_only('id', 'status', 'how_to_apply')).first_or_404()
    if post.status in POSTSTATUS.GONE:
        abort(410)
    jobview = UserJobView.query.get((post.id, g.user.id))
    if jobview is None:
        jobview = UserJobView(user=g.user, jobpost=post, applied=True)
        db.session.add(jobview)
        try:
            db.session.commit()
            post.uncache_viewcounts('opened')
            cache.delete_memoized(viewstats_by_id_qhour, post.id)
            cache.delete_memoized(viewstats_by_id_hour, post.id)
            cache.delete_memoized(viewstats_by_id_day, post.id)
            post.viewcounts  # Re-populate cache
        except IntegrityError:
            db.session.rollback()
            pass  # User double-clicked. Ignore.
    elif not jobview.applied:
        jobview.applied = True
        db.session.commit()
        post.uncache_viewcounts('opened')
        cache.delete_memoized(viewstats_by_id_qhour, post.id)
        cache.delete_memoized(viewstats_by_id_hour, post.id)
        cache.delete_memoized(viewstats_by_id_day, post.id)
        post.viewcounts  # Re-populate cache

    applyform = None
    job_application = JobApplication.query.filter_by(user=g.user, jobpost=post).first()
    if not job_application:
        applyform = forms.ApplicationForm()
        applyform.apply_phone.data = g.user.phone

    return render_template('jobpost_reveal.html',
        post=post,
        instructions=redactemail(post.how_to_apply),
        applyform=applyform,
        job_application=job_application)


@app.route('/<domain>/<hashid>/apply', methods=['POST'], subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/apply', methods=['POST'])
@app.route('/apply/<hashid>', defaults={'domain': None}, methods=['POST'], subdomain='<subdomain>')
@app.route('/apply/<hashid>', defaults={'domain': None}, methods=['POST'])
def applyjob(domain, hashid):
    """
    Apply to a job (including in kiosk mode)
    """
    post = JobPost.query.filter_by(hashid=hashid).options(db.load_only('id', 'email', 'email_domain')).first_or_404()
    # If the domain doesn't match, redirect to correct URL
    if post.email_domain != domain:
        return redirect(post.url_for('apply'), code=301)

    if g.user:
        job_application = JobApplication.query.filter_by(user=g.user, jobpost=post).first()
    else:
        job_application = None
    if job_application:
        flashmsg = "You have already applied to this job. You may not apply again"
        if request.is_xhr:
            return u'<p><strong>{}</strong></p>'.format(flashmsg)
        else:
            flash(flashmsg, 'interactive')
            return redirect(post.url_for(), 303)
    else:
        if g.kiosk:
            applyform = forms.KioskApplicationForm()
        else:
            applyform = forms.ApplicationForm()
        applyform.post = post
        if applyform.validate_on_submit():
            if g.user and g.user.blocked:
                flashmsg = "Your account has been blocked from applying to jobs"
            else:
                if g.kiosk:
                    job_application = JobApplication(user=None, jobpost=post,
                        fullname=applyform.apply_fullname.data,
                        email=applyform.apply_email.data,
                        phone=applyform.apply_phone.data,
                        message=applyform.apply_message.data,
                        words=None)
                else:
                    job_application = JobApplication(user=g.user, jobpost=post,
                        fullname=g.user.fullname,
                        email=applyform.apply_email.data,
                        phone=applyform.apply_phone.data,
                        message=applyform.apply_message.data,
                        optin=applyform.apply_optin.data,
                        words=applyform.words)
                db.session.add(job_application)
                db.session.commit()
                post.uncache_viewcounts('applied')
                email_html = email_transform(
                    render_template('apply_email.html',
                        post=post, job_application=job_application,
                        archive_url=job_application.url_for(_external=True)),
                    base_url=request.url_root)
                email_text = html2text(email_html)
                flashmsg = "Your application has been sent to the employer"

                msg = Message(subject=u"Job application: {fullname}".format(fullname=job_application.fullname),
                    recipients=[post.email])
                if not job_application.user:
                    # Also BCC the candidate (for kiosk mode)
                    # FIXME: This should be a separate copy of the email as the tracking gif is now shared
                    # between both employer and candidate
                    msg.bcc = [job_application.email]
                msg.body = email_text
                msg.html = email_html
                mail.send(msg)

            if request.is_xhr:
                return u'<p><strong>{}</strong></p>'.format(flashmsg)
            else:
                flash(flashmsg, 'interactive')
                return redirect(post.url_for(), 303)

        if request.is_xhr:
            return render_template('inc/applyform.html', post=post, applyform=applyform)
        else:
            return redirect(post.url_for(), 303)


@app.route('/<domain>/<hashid>/manage', methods=('GET', 'POST'), defaults={'key': None}, subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/manage', methods=('GET', 'POST'), defaults={'key': None})
@app.route('/manage/<hashid>', methods=('GET', 'POST'), defaults={'key': None, 'domain': None}, subdomain='<subdomain>')
@app.route('/manage/<hashid>', methods=('GET', 'POST'), defaults={'key': None, 'domain': None})
@load_model(JobPost, {'hashid': 'hashid'}, 'post', permission=('manage', 'siteadmin'), addlperms=lastuser.permissions,
    kwargs=True)
def managejob(post, kwargs):
    # If the domain doesn't match, redirect to correct URL
    if post.email_domain != kwargs.get('domain'):
        return redirect(post.url_for('manage'), code=301)

    first_application = post.applications.options(db.load_only('hashid')).first()
    if first_application:
        return redirect(first_application.url_for(), code=303)
    else:
        return redirect(post.url_for(), code=303)


@app.route('/<domain>/<hashid>/appl/<application>/track.gif', subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/appl/<application>/track.gif')
@app.route('/view/<hashid>/<application>/track.gif', defaults={'domain': None}, subdomain='<subdomain>')
@app.route('/view/<hashid>/<application>/track.gif', defaults={'domain': None})
def view_application_email_gif(domain, hashid, application):
    post = JobPost.query.filter_by(hashid=hashid).one_or_none()
    if post:
        # FIXME: Can't use one_or_none() until we ensure jobpost_id+user_id is unique
        job_application = JobApplication.query.filter_by(hashid=application, jobpost=post).first()
    else:
        job_application = None

    if job_application is not None:
        if job_application.response == EMPLOYER_RESPONSE.NEW:
            job_application.response = EMPLOYER_RESPONSE.PENDING
            db.session.commit()
        return gif1x1, 200, {
            'Content-Type': 'image/gif',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
            }
    else:
        return gif1x1, 404, {
            'Content-Type': 'image/gif',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
            }


@app.route('/<domain>/<hashid>/appl/<application>', subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/appl/<application>')
@app.route('/view/<hashid>/<application>', defaults={'domain': None}, subdomain='<subdomain>')
@app.route('/view/<hashid>/<application>', defaults={'domain': None})
def view_application(domain, hashid, application):
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    # Transition code until we force all employers to login before posting
    if post.user and not (post.admin_is(g.user) or lastuser.has_permission('siteadmin')):
        if not g.user:
            return redirect(url_for('login', message=u"You need to be logged in to view candidate applications on Hasjob."))
        else:
            abort(403)
    job_application = JobApplication.query.filter_by(hashid=application, jobpost=post).first_or_404()

    # If this domain doesn't match, redirect to correct URL
    if post.email_domain != domain:
        return redirect(job_application.url_for(), code=301)

    if job_application.response == EMPLOYER_RESPONSE.NEW:
        # If the application is pending, mark it as opened.
        # However, don't do this if the user is a siteadmin, unless they also own the post.
        if post.admin_is(g.user) or not lastuser.has_permission('siteadmin'):
            job_application.response = EMPLOYER_RESPONSE.PENDING
            db.session.commit()
    response_form = forms.ApplicationResponseForm()

    statuses = set([app.status for app in post.applications])

    if not g.kiosk:
        if g.preview_campaign:
            header_campaign = g.preview_campaign
        else:
            header_campaign = Campaign.for_context(CAMPAIGN_POSITION.HEADER, board=g.board, user=g.user,
                anon_user=g.anon_user, geonameids=g.user_geonameids + post.geonameids)
    else:
        header_campaign = None

    return render_template('application.html', post=post, job_application=job_application,
        header_campaign=header_campaign,
        response_form=response_form, statuses=statuses, is_siteadmin=lastuser.has_permission('siteadmin'))


@app.route('/<domain>/<hashid>/appl/<application>/process', methods=['POST'], subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/appl/<application>/process', methods=['POST'])
@app.route('/apply/<hashid>/<application>', defaults={'domain': None}, methods=['POST'], subdomain='<subdomain>')
@app.route('/apply/<hashid>/<application>', defaults={'domain': None}, methods=['POST'])
def process_application(domain, hashid, application):
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    if post.user and not post.admin_is(g.user):
        if not g.user:
            return redirect(url_for('login'))
        else:
            abort(403)
    job_application = JobApplication.query.filter_by(hashid=application, jobpost=post).first_or_404()
    response_form = forms.ApplicationResponseForm()
    flashmsg = ''

    if response_form.validate_on_submit():
        if (request.form.get('action') == 'reply' and job_application.can_reply()) or (
                request.form.get('action') == 'reject' and job_application.can_reject()):
            if not response_form.response_message.data:
                flashmsg = "You need to write a message to the candidate."
            else:
                if request.form.get('action') == 'reply':
                    job_application.response = EMPLOYER_RESPONSE.REPLIED
                else:
                    job_application.response = EMPLOYER_RESPONSE.REJECTED
                job_application.response_message = response_form.response_message.data
                job_application.replied_by = g.user
                job_application.replied_at = datetime.utcnow()

                email_html = email_transform(
                    render_template('respond_email.html',
                        post=post, job_application=job_application,
                        archive_url=job_application.url_for(_external=True)),
                    base_url=request.url_root)
                email_text = html2text(email_html)

                sender_name = g.user.fullname if post.admin_is(g.user) else post.fullname or post.company_name
                sender_formatted = u'{sender} (via {site})'.format(
                    sender=sender_name,
                    site=app.config['SITE_TITLE'])

                if job_application.is_replied():
                    msg = Message(
                        subject=u"{candidate}: {headline}".format(
                            candidate=job_application.user.fullname, headline=post.headline),
                        sender=(sender_formatted, app.config['MAIL_SENDER']),
                        reply_to=(sender_name, post.email),
                        recipients=[job_application.email],
                        bcc=[post.email])
                    flashmsg = "We sent your message to the candidate and copied you. Their email and phone number are below"
                else:
                    msg = Message(subject=u"Job declined: {headline}".format(headline=post.headline),
                        sender=(sender_formatted, app.config['MAIL_SENDER']),
                        bcc=[job_application.email, post.email])
                    flashmsg = "We sent your message to the candidate and copied you"
                msg.body = email_text
                msg.html = email_html
                mail.send(msg)
                db.session.commit()
        elif request.form.get('action') == 'ignore' and job_application.can_ignore():
            job_application.response = EMPLOYER_RESPONSE.IGNORED
            db.session.commit()
        elif request.form.get('action') == 'flag' and job_application.can_report():
            job_application.response = EMPLOYER_RESPONSE.FLAGGED
            db.session.commit()
        elif request.form.get('action') == 'unflag' and job_application.is_flagged():
            job_application.response = EMPLOYER_RESPONSE.NEW
            db.session.commit()

    if flashmsg:
        if request.is_xhr:
            return u'<p><strong>{}</strong></p>'.format(flashmsg)
        else:
            flash(flashmsg, 'interactive')

    return redirect(job_application.url_for(), 303)


@app.route('/<domain>/<hashid>/pin', methods=['POST'], subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/pin', methods=['POST'])
@app.route('/pinned/<hashid>', defaults={'domain': None}, methods=['POST'], subdomain='<subdomain>')
@app.route('/pinned/<hashid>', defaults={'domain': None}, methods=['POST'])
@lastuser.requires_permission('siteadmin')
def pinnedjob(domain, hashid):
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    if g.board:
        obj = post.link_to_board(g.board)
        if obj is None:
            abort(404)
    else:
        obj = post
    pinnedform = forms.PinnedForm(obj=obj)
    if pinnedform.validate_on_submit():
        obj.pinned = pinnedform.pinned.data
        db.session.commit()
        if obj.pinned:
            msg = "This post has been pinned."
        else:
            msg = "This post is no longer pinned."
        # cache bust
        dogpile_cache.invalidate_region('hour')
    else:
        msg = "Invalid submission"
    if request.is_xhr:
        return Markup('<p>' + msg + '</p>')
    else:
        flash(msg)
        return redirect(post.url_for(), 303)


@app.route('/<domain>/<hashid>/reject', methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/reject', methods=('GET', 'POST'))
@app.route('/reject/<hashid>', defaults={'domain': None}, methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/reject/<hashid>', defaults={'domain': None}, methods=('GET', 'POST'))
@lastuser.requires_permission('siteadmin')
def rejectjob(domain, hashid):
    def send_reject_mail(reject_type, post, banned_posts=[]):
        if reject_type not in ['reject', 'ban']:
            return
        mail_meta = {
            'reject': {
                'subject': "About your job post on Hasjob",
                'template': "reject_email.html"
            },
            'ban': {
                'subject': "About your account and job posts on Hasjob",
                'template': "reject_domain_email.html"
            }
        }
        msg = Message(subject=mail_meta[reject_type]['subject'], recipients=[post.email])
        msg.html = email_transform(render_template(mail_meta[reject_type]['template'], post=post, banned_posts=banned_posts), base_url=request.url_root)
        msg.body = html2text(msg.html)
        mail.send(msg)

    def reject_post(post, reason, spam=False):
        post.status = POSTSTATUS.SPAM if spam else POSTSTATUS.REJECTED
        post.closed_datetime = db.func.utcnow()
        post.review_comments = reason
        post.review_datetime = db.func.utcnow()
        post.reviewer = g.user

    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    if post.status in POSTSTATUS.UNPUBLISHED and not post.admin_is(g.user):
        abort(403)
    if post.status in POSTSTATUS.GONE:
        abort(410)
    rejectform = forms.RejectForm()

    if rejectform.validate_on_submit():
        banned_posts = []
        if request.form.get('submit') == 'reject':
            flashmsg = "This job post has been rejected"
            reject_post(post, rejectform.reason.data)
        elif request.form.get('submit') == 'spam':
            flashmsg = "This job post has been marked as spam"
            reject_post(post, rejectform.reason.data, True)
        elif request.form.get('submit') == 'ban':
            # Moderator asked for a ban, so ban the user and reject
            # all posts from the domain if it's not a webmail domain
            if post.user:
                post.user.blocked = True
            if post.domain.is_webmail:
                flashmsg = "This job post has been rejected and the user banned"
                reject_post(post, rejectform.reason.data)
                banned_posts = [post]
            else:
                flashmsg = "This job post has been rejected and the user and domain banned"
                post.domain.is_banned = True
                post.domain.banned_by = g.user
                post.domain.banned_at = db.func.utcnow()
                post.domain.banned_reason = rejectform.reason.data

                for jobpost in post.domain.jobposts:
                    if jobpost.status in POSTSTATUS.LISTED:
                        reject_post(jobpost, rejectform.reason.data)
                        banned_posts.append(jobpost)
        else:
            # We're not sure what button the moderator hit
            abort(400)

        db.session.commit()
        send_reject_mail(request.form.get('submit'), post, banned_posts)
        # cache bust
        dogpile_cache.invalidate_region('hour')
        if request.is_xhr:
            return "<p>%s</p>" % flashmsg
        else:
            flash(flashmsg, "interactive")
    elif request.method == 'POST' and request.is_xhr:
        return render_template('inc/rejectform.html', post=post, rejectform=rejectform)
    return redirect(post.url_for(), code=303)


@app.route('/<domain>/<hashid>/moderate', methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/moderate', methods=('GET', 'POST'))
@app.route('/moderate/<hashid>', defaults={'domain': None}, methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/moderate/<hashid>', defaults={'domain': None}, methods=('GET', 'POST'))
@lastuser.requires_permission('siteadmin')
def moderatejob(domain, hashid):
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    if post.status in [POSTSTATUS.DRAFT, POSTSTATUS.PENDING]:
        abort(403)
    if post.status in [POSTSTATUS.REJECTED, POSTSTATUS.WITHDRAWN, POSTSTATUS.SPAM]:
        abort(410)
    moderateform = forms.ModerateForm()
    if moderateform.validate_on_submit():
        post.closed_datetime = datetime.utcnow()
        post.review_comments = moderateform.reason.data
        post.review_datetime = datetime.utcnow()
        post.reviewer = g.user
        flashmsg = "This job post has been moderated."
        post.status = POSTSTATUS.MODERATED
        msg = Message(subject="About your job post on Hasjob",
            recipients=[post.email])
        msg.html = email_transform(render_template('moderate_email.html', post=post), base_url=request.url_root)
        msg.body = html2text(msg.html)
        mail.send(msg)
        db.session.commit()
        # cache bust
        dogpile_cache.invalidate_region('hour')
        if request.is_xhr:
            return "<p>%s</p>" % flashmsg
    elif request.method == 'POST' and request.is_xhr:
        return render_template('inc/moderateform.html', post=post, moderateform=moderateform)
    return redirect(post.url_for(), code=303)


@app.route('/<domain>/<hashid>/confirm', methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/confirm', methods=('GET', 'POST'))
@app.route('/confirm/<hashid>', defaults={'domain': None}, methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/confirm/<hashid>', defaults={'domain': None}, methods=('GET', 'POST'))
def confirm(domain, hashid):
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    form = forms.ConfirmForm()
    if post.status in POSTSTATUS.GONE:
        abort(410)
    elif post.status in POSTSTATUS.UNPUBLISHED and not post.admin_is(g.user):
            abort(403)
    elif post.status not in POSTSTATUS.UNPUBLISHED:
        # Any other status: no confirmation required (via this handler)
        return redirect(post.url_for(), code=302)

    # We get here if it's (a) POSTSTATUS.UNPUBLISHED and (b) the user is confirmed authorised
    if 'form.id' in request.form and form.validate_on_submit():
        # User has accepted terms of service. Now send email and/or wait for payment
        msg = Message(subject="Confirmation of your job post at Hasjob",
            recipients=[post.email])
        msg.html = email_transform(render_template('confirm_email.html', post=post), base_url=request.url_root)
        msg.body = html2text(msg.html)
        mail.send(msg)
        post.email_sent = True
        post.status = POSTSTATUS.PENDING
        db.session.commit()

        footer_campaign = Campaign.for_context(CAMPAIGN_POSITION.AFTERPOST, board=g.board, user=g.user,
                    anon_user=g.anon_user, geonameids=g.user_geonameids)

        return render_template('mailsent.html', footer_campaign=footer_campaign)
    return render_template('confirm.html', post=post, form=form)


@app.route('/confirm/demo', defaults={'domain': None}, methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/confirm/demo', defaults={'domain': None}, methods=('GET', 'POST'))
def confirm_demo(domain):
    footer_campaign = Campaign.for_context(CAMPAIGN_POSITION.AFTERPOST, board=g.board, user=g.user,
                anon_user=g.anon_user, geonameids=g.user_geonameids)

    return render_template('mailsent.html', footer_campaign=footer_campaign)


@app.route('/<domain>/<hashid>/confirm/<key>', subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/confirm/<key>')
@app.route('/confirm/<hashid>/<key>', defaults={'domain': None}, subdomain='<subdomain>')
@app.route('/confirm/<hashid>/<key>', defaults={'domain': None})
def confirm_email(domain, hashid, key):
    # If post is in pending state and email key is correct, convert to published
    # and update post.datetime to utcnow() so it'll show on top of the stack
    # This function expects key to be email_verify_key, not edit_key like the others
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    if post.status in POSTSTATUS.GONE:
        abort(410)
    elif post.status in POSTSTATUS.LISTED:
        flash("This job post has already been confirmed and published", "interactive")
        return redirect(post.url_for(), code=302)
    elif post.status == POSTSTATUS.DRAFT:
        # This should not happen. The user doesn't have this URL until they
        # pass the confirm form
        return redirect(post.url_for('confirm'), code=302)
    elif post.status == POSTSTATUS.PENDING:
        if key != post.email_verify_key:
            return render_template('403.html', description=u"This link has expired or is malformed. Check if you have received a newer email from us.")
        else:
            if app.config.get('THROTTLE_LIMIT', 0) > 0:
                post_count = JobPost.query.filter(JobPost.email_domain == post.email_domain).filter(
                    JobPost.status.in_(POSTSTATUS.POSTPENDING)).filter(
                        JobPost.datetime > datetime.utcnow() - timedelta(days=1)).count()
                if post_count > app.config['THROTTLE_LIMIT']:
                    flash(u"We have received too many posts with %s addresses in the last 24 hours. "
                        u"Posts are rate-limited per domain, so yours was not confirmed for now. "
                        u"Please try confirming again in a few hours."
                        % post.email_domain, category='info')
                    return redirect(url_for('index'))
            post.email_verified = True
            post.status = POSTSTATUS.CONFIRMED
            post.datetime = datetime.utcnow()
            db.session.commit()
            if app.config['TWITTER_ENABLED']:
                if post.headlineb:
                    tweet.delay(post.headline, post.url_for(b=0, _external=True),
                        post.location, dict(post.parsed_location or {}), username=post.twitter)
                    tweet.delay(post.headlineb, post.url_for(b=1, _external=True),
                        post.location, dict(post.parsed_location or {}), username=post.twitter)
                else:
                    tweet.delay(post.headline, post.url_for(_external=True),
                        post.location, dict(post.parsed_location or {}), username=post.twitter)
            add_to_boards.delay(post.id)
            flash("Congratulations! Your job post has been published. As a bonus for being an employer on Hasjob, "
                "you can now see how your post is performing relative to others. Look in the sidebar of any post.",
                "interactive")
    # cache bust
    dogpile_cache.invalidate_region('hour')
    return redirect(post.url_for(), code=302)


@app.route('/<domain>/<hashid>/withdraw', methods=('GET', 'POST'), defaults={'key': None}, subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/withdraw', methods=('GET', 'POST'), defaults={'key': None})
@app.route('/withdraw/<hashid>', methods=('GET', 'POST'), defaults={'key': None, 'domain': None}, subdomain='<subdomain>')
@app.route('/withdraw/<hashid>/<key>', defaults={'domain': None}, methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/withdraw/<hashid>', methods=('GET', 'POST'), defaults={'key': None, 'domain': None})
@app.route('/withdraw/<hashid>/<key>', defaults={'domain': None}, methods=('GET', 'POST'))
def withdraw(domain, hashid, key):
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    form = forms.WithdrawForm()
    if not ((key is None and g.user is not None and post.admin_is(g.user)) or (key == post.edit_key)):
        abort(403)
    if post.status == POSTSTATUS.WITHDRAWN:
        flash("Your job post has already been withdrawn", "info")
        return redirect(url_for('index'), code=303)
    if post.status not in POSTSTATUS.LISTED:
        flash("Your post cannot be withdrawn because it is not public", "info")
        return redirect(url_for('index'), code=303)
    if form.validate_on_submit():
        post.status = POSTSTATUS.WITHDRAWN
        post.closed_datetime = datetime.utcnow()
        db.session.commit()
        flash("Your job post has been withdrawn and is no longer available", "info")
        # cache bust
        dogpile_cache.invalidate_region('hour')
        return redirect(url_for('index'), code=303)
    return render_template("withdraw.html", post=post, form=form)


@app.route('/<domain>/<hashid>/edit', methods=('GET', 'POST'), defaults={'key': None}, subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/edit', methods=('GET', 'POST'), defaults={'key': None})
@app.route('/edit/<hashid>', methods=('GET', 'POST'), defaults={'key': None, 'domain': None}, subdomain='<subdomain>')
@app.route('/edit/<hashid>/<key>', defaults={'domain': None}, methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/edit/<hashid>', methods=('GET', 'POST'), defaults={'key': None, 'domain': None})
@app.route('/edit/<hashid>/<key>', defaults={'domain': None}, methods=('GET', 'POST'))
def editjob(hashid, key, domain=None, form=None, validated=False, newpost=None):
    if form is None:
        form = forms.ListingForm(request.form)
        form.job_type.choices = JobType.choices(g.board)
        form.job_category.choices = JobCategory.choices(g.board)
        if g.board and not g.board.require_pay:
            form.job_pay_type.choices = [(-1, u'Confidential')] + PAY_TYPE.items()

    post = None
    no_email = False

    if not newpost:
        post = JobPost.query.filter_by(hashid=hashid).first_or_404()
        if not ((key is None and g.user is not None and post.admin_is(g.user)) or (key == post.edit_key)):
            abort(403)

        # Once this post is published, require editing at /domain/<hashid>/edit
        if not key and post.status not in POSTSTATUS.UNPUBLISHED and post.email_domain != domain:
            return redirect(post.url_for('edit'), code=301)

        # Don't allow editing jobs that aren't on this board as that may be a loophole when
        # the board allows no pay (except in the 'www' root board, where editing is always allowed)
        with db.session.no_autoflush:
            if g.board and g.board.not_root and post.link_to_board(g.board) is None and request.method == 'GET':
                blink = post.postboards.first()
                if blink:
                    return redirect(post.url_for('edit', subdomain=blink.board.name, _external=True))
                else:
                    return redirect(post.url_for('edit', subdomain=None, _external=True))

        # Don't allow email address to be changed once it's confirmed
        if post.status in POSTSTATUS.POSTPENDING:
            no_email = True

    if request.method == 'POST' and post and post.status in POSTSTATUS.POSTPENDING:
        # del form.poster_name  # Deprecated 2013-11-20
        form.poster_email.data = post.email
    if request.method == 'POST' and (validated or form.validate()):
        form_description = bleach.linkify(bleach.clean(form.job_description.data, tags=ALLOWED_TAGS))
        form_perks = bleach.linkify(bleach.clean(form.job_perks_description.data, tags=ALLOWED_TAGS)) if form.job_perks.data else ''
        form_how_to_apply = form.job_how_to_apply.data
        form_email_domain = get_email_domain(form.poster_email.data)
        form_words = get_word_bag(u' '.join((form_description, form_perks, form_how_to_apply)))

        similar = False
        with db.session.no_autoflush:
            for oldpost in JobPost.query.filter(db.or_(
                db.and_(
                    JobPost.email_domain == form_email_domain,
                    JobPost.status.in_(POSTSTATUS.POSTPENDING)),
                JobPost.status == POSTSTATUS.SPAM)).filter(
                    JobPost.datetime > datetime.utcnow() - agelimit).all():
                if not post or (oldpost.id != post.id):
                    if oldpost.words:
                        s = SequenceMatcher(None, form_words, oldpost.words)
                        if s.ratio() > 0.6:
                            similar = True
                            break

        if similar:
            flash("This post is very similar to an earlier post. You may not repost the same job "
                "in less than %d days." % agelimit.days, category='interactive')
        else:
            if newpost:
                post = JobPost(**newpost)
                db.session.add(post)
                if g.board:
                    post.add_to(g.board)
                    if g.board.not_root:
                        post.add_to('www')

            post.headline = form.job_headline.data
            post.headlineb = form.job_headlineb.data
            post.type_id = form.job_type.data
            post.category_id = form.job_category.data
            post.location = form.job_location.data
            post.relocation_assist = form.job_relocation_assist.data
            post.description = form_description
            post.perks = form_perks
            post.how_to_apply = form_how_to_apply
            post.company_name = form.company_name.data
            post.company_url = form.company_url.data
            post.hr_contact = form.hr_contact.data
            post.twitter = form.twitter.data

            post.pay_type = form.job_pay_type.data
            if post.pay_type == -1:
                post.pay_type = None

            if post.pay_type is not None and post.pay_type != PAY_TYPE.NOCASH:
                post.pay_currency = form.job_pay_currency.data
                post.pay_cash_min = form.job_pay_cash_min.data
                post.pay_cash_max = form.job_pay_cash_max.data
            else:
                post.pay_currency = None
                post.pay_cash_min = None
                post.pay_cash_max = None
            if form.job_pay_equity.data:
                post.pay_equity_min = form.job_pay_equity_min.data
                post.pay_equity_max = form.job_pay_equity_max.data
            else:
                post.pay_equity_min = None
                post.pay_equity_max = None

            post.admins = form.collaborators.data

            # Allow name and email to be set only on non-confirmed posts
            if not no_email:
                # post.fullname = form.poster_name.data  # Deprecated 2013-11-20
                if post.email != form.poster_email.data:
                    # Change the email_verify_key if the email changes
                    post.email_verify_key = random_long_key()
                post.email = form.poster_email.data
                post.email_domain = form_email_domain
                post.md5sum = md5sum(post.email)
                with db.session.no_autoflush:
                    # This is dependent on the domain's DNS validity already being confirmed
                    # by the form's email validator
                    post.domain = Domain.get(post.email_domain, create=True)
                    if not post.domain.is_webmail and not post.domain.title:
                        post.domain.title, post.domain.legal_title = common_legal_names(post.company_name)
            # To protect from gaming, don't allow words to be removed in edited posts once the post
            # has been confirmed. Just add the new words.
            if post.status in POSTSTATUS.POSTPENDING:
                prev_words = post.words or u''
            else:
                prev_words = u''
            post.words = get_word_bag(u' '.join((prev_words, form_description, form_perks, form_how_to_apply)))

            post.language, post.language_confidence = identify_language(post)

            if post.status == POSTSTATUS.MODERATED:
                post.status = POSTSTATUS.CONFIRMED

            if request.files['company_logo']:
                # The form's validator saved the processed logo in g.company_logo.
                thumbnail = g.company_logo
                logofilename = uploaded_logos.save(thumbnail, name='%s.' % post.hashid)
                post.company_logo = logofilename
            else:
                if form.company_logo_remove.data:
                    post.company_logo = None

            db.session.commit()
            tag_jobpost.delay(post.id)    # Keywords
            tag_locations.delay(post.id)  # Locations
            post.uncache_viewcounts('pay_label')
            session.pop('userkeys', None)  # Remove legacy userkeys dict
            session.permanent = True
            # cache bust
            dogpile_cache.invalidate_region('hour')
            return redirect(post.url_for(), code=303)
    elif request.method == 'POST':
        flash("Please review the indicated issues", category='interactive')
    elif request.method == 'GET':
        form.populate_from(post)
    return render_template('postjob.html', form=form, no_email=no_email)


@app.route('/new', methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/new', methods=('GET', 'POST'))
def newjob():
    form = forms.ListingForm()
    archived_post = None
    if not g.user:
        return redirect(url_for('login', next=url_for('newjob'),
            message=u"Hasjob now requires you to login before posting a job. Please login as yourself."
                u" We'll add details about your company later"))
    else:
        if g.user.blocked:
            flash("Your account has been blocked from posting jobs", category='info')
            return redirect(url_for('index'), code=303)

    if g.board:
        if 'new-job' not in g.board.permissions(g.user):
            abort(403)

    if g.board and not g.board.require_pay:
        form.job_pay_type.choices = [(-1, u'Confidential')] + PAY_TYPE.items()
    form.job_type.choices = JobType.choices(g.board)
    form.job_category.choices = JobCategory.choices(g.board)

    if request.method == 'GET':
        header_campaign = Campaign.for_context(CAMPAIGN_POSITION.BEFOREPOST, board=g.board, user=g.user,
                anon_user=g.anon_user, geonameids=g.user_geonameids)
        if g.user:
            # form.poster_name.data = g.user.fullname  # Deprecated 2013-11-20
            form.poster_email.data = g.user.email
    else:
        header_campaign = None

    # Job Reposting
    if request.method == 'GET' and request.args.get('template'):
        archived_post = JobPost.get(request.args['template'])
        if not archived_post:
            abort(404)
        if not archived_post.admin_is(g.user):
            abort(403)
        if not archived_post.is_old():
            flash("This post is currently active and cannot be posted again.")
            return redirect(archived_post.url_for(), code=303)
        form.populate_from(archived_post)
        header_campaign = None

    if form.validate_on_submit():
        # POST request from new job page, with successful validation
        # Move it to the editjob page for handling here forward
        newpost = {
            'hashid': unique_hash(JobPost),
            'ipaddr': request.environ['REMOTE_ADDR'],
            'useragent': request.user_agent.string,
            'user': g.user
            }
        return editjob(hashid=None, key=None, form=form, validated=True, newpost=newpost)
    elif form.errors:
        # POST request from new job page, with errors
        flash("Please review the indicated issues", category='interactive')

    # Render page. Execution reaches here under three conditions:
    # 1. GET request, page loaded for the first time
    # 2. POST request from this page, with errors
    return render_template('postjob.html', form=form, no_removelogo=True, archived_post=archived_post,
        header_campaign=header_campaign)


@app.route('/<domain>/<hashid>/close', methods=('GET', 'POST'), defaults={'key': None}, subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/close', methods=('GET', 'POST'), defaults={'key': None})
def close(domain, hashid, key):
    post = JobPost.get(hashid)
    if not post:
        abort(404)
    if not post.admin_is(g.user):
        abort(403)
    if request.method == 'GET' and post.is_closed():
        return redirect(post.url_for('reopen'), code=303)
    if not post.is_public():
        flash("Your job post can't be closed.", "info")
        return redirect(post.url_for(), code=303)
    form = Form()
    if form.validate_on_submit():
        post.close()
        post.closed_datetime = datetime.utcnow()
        db.session.commit()
        # cache bust
        dogpile_cache.invalidate_region('hour')
        return redirect(post.url_for(), code=303)
    return render_template("close.html", post=post, form=form)


@app.route('/<domain>/<hashid>/reopen', methods=('GET', 'POST'), defaults={'key': None}, subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/reopen', methods=('GET', 'POST'), defaults={'key': None})
def reopen(domain, hashid, key):
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    if not post:
        abort(404)
    if not post.admin_is(g.user):
        abort(403)
    # Only closed posts can be reopened
    if not post.is_closed():
        flash("Your job post can't be reopened.", "info")
        return redirect(post.url_for(), code=303)
    form = Form()
    if form.validate_on_submit():
        post.confirm()
        post.closed_datetime = datetime.utcnow()
        db.session.commit()
        # cache bust
        dogpile_cache.invalidate_region('hour')
        return redirect(post.url_for(), code=303)
    return render_template("reopen.html", post=post, form=form)
