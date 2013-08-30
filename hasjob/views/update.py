import bleach
from datetime import datetime, timedelta
from markdown import markdown
from difflib import SequenceMatcher

from sqlalchemy.exc import IntegrityError
from flask import (
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
    session,
    escape,
    Markup,
    )
from flask.ext.mail import Message
from baseframe import cache
from coaster import get_email_domain, md5sum
from hasjob import app, forms, mail, lastuser
from hasjob.models import (
    agelimit,
    db,
    JobCategory,
    JobType,
    JobPost,
    JobPostReport,
    POSTSTATUS,
    ReportCode,
    UserJobView,
    unique_hash,
    viewcounts_by_id,
    )
from hasjob.twitter import tweet
from hasjob.uploads import uploaded_logos
from hasjob.utils import get_word_bag, scrubemail
from hasjob.views import ALLOWED_TAGS
from hasjob.views.display import webmail_domains


@app.route('/view/<hashid>', methods=('GET', 'POST'))
def jobdetail(hashid):
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    if post.status in [POSTSTATUS.DRAFT, POSTSTATUS.PENDING]:
        if post.edit_key not in session.get('userkeys', []):
            abort(403)
    if post.status in [POSTSTATUS.REJECTED, POSTSTATUS.WITHDRAWN, POSTSTATUS.SPAM]:
        abort(410)
    if g.user:
        jobview = UserJobView.query.get((g.user.id, post.id))
        if jobview is None:
            jobview = UserJobView(user=g.user, jobpost=post)
            cache.delete_memoized(viewcounts_by_id, post.id)
            db.session.add(jobview)
            try:
                db.session.commit()
            except IntegrityError:
                pass  # User opened two tabs at once? We don't really know
    else:
        jobview = None
    reportform = forms.ReportForm()
    reportform.report_code.choices = [(ob.id, ob.title) for ob in ReportCode.query.filter_by(public=True).order_by('seq')]
    rejectform = forms.RejectForm()
    stickyform = forms.StickyForm(obj=post)
    if reportform.validate_on_submit():
        report = JobPostReport(post=post, reportcode_id=reportform.report_code.data)
        report.ipaddr = request.environ['REMOTE_ADDR']
        report.useragent = request.user_agent.string
        db.session.add(report)
        db.session.commit()
        if request.is_xhr:
            return "<p>Thanks! This job listing has been flagged for review.</p>"  # FIXME: Ugh!
        else:
            flash("Thanks! This job listing has been flagged for review.", "interactive")
    elif request.method == 'POST' and request.is_xhr:
        return render_template('inc/reportform.html', reportform=reportform, ajaxreg=True)
    return render_template('detail.html', post=post, reportform=reportform, rejectform=rejectform, siteadmin=lastuser.has_permission('siteadmin'), webmail_domains=webmail_domains, jobview=jobview, stickyform=stickyform)


@app.route('/reveal/<hashid>')
@lastuser.requires_login
def revealjob(hashid):
    """
    This view is a GET request and that is intentional.
    """
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    if post.status in [POSTSTATUS.REJECTED, POSTSTATUS.WITHDRAWN, POSTSTATUS.SPAM]:
        abort(410)
    jobview = UserJobView.query.get((g.user.id, post.id))
    if jobview is None:
        jobview = UserJobView(user=g.user, jobpost=post, applied=True)
        cache.delete_memoized(viewcounts_by_id, post.id)
        db.session.add(jobview)
        try:
            db.session.commit()
        except IntegrityError:
            pass  # User double-clicked. Ignore.
    elif not jobview.applied:
        jobview.applied = True
        cache.delete_memoized(viewcounts_by_id, post.id)
        db.session.commit()
    if request.is_xhr:
        return scrubemail(unicode(escape(post.how_to_apply)), ('z', 'y'))
    else:
        return redirect(url_for('jobdetail', hashid=post.hashid), 303)


@app.route('/sticky/<hashid>', methods=['POST'])
@lastuser.requires_permission('siteadmin')
def stickyjob(hashid):
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    stickyform = forms.StickyForm(obj=post)
    if stickyform.validate_on_submit():
        post.sticky = stickyform.sticky.data
        db.session.commit()
        if post.sticky:
            msg = "This listing has been made sticky."
        else:
            msg = "This listing is no longer sticky."
    else:
        msg = "Invalid submission"
    if request.is_xhr:
        return Markup('<p>' + msg + '</p>')
    else:
        flash(msg)
        return redirect(url_for('jobdetail', hashid=post.hashid), 303)


@app.route('/reject/<hashid>', methods=('GET', 'POST'))
@lastuser.requires_permission('siteadmin')
def rejectjob(hashid):
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    if post.status in [POSTSTATUS.DRAFT, POSTSTATUS.PENDING]:
        if post.edit_key not in session.get('userkeys', []):
            abort(403)
    if post.status in [POSTSTATUS.REJECTED, POSTSTATUS.WITHDRAWN, POSTSTATUS.SPAM]:
        abort(410)
    rejectform = forms.RejectForm()
    if rejectform.validate_on_submit():
        post.closed_datetime = datetime.utcnow()
        post.review_comments = rejectform.reason.data
        post.review_datetime = datetime.utcnow()
        post.reviewer = g.user

        if request.form.get('submit') == 'spam':
            flashmsg = "This job listing has been marked as spam."
            post.status = POSTSTATUS.SPAM
        else:
            flashmsg = "This job listing has been rejected."
            post.status = POSTSTATUS.REJECTED
            msg = Message(subject="About your job listing on the HasGeek Job Board",
                recipients=[post.email])
            msg.body = render_template("reject_email.md", post=post)
            msg.html = markdown(msg.body)
            mail.send(msg)
        db.session.commit()
        if request.is_xhr:

            return "<p>%s</p>" % flashmsg
        else:
            flash(flashmsg, "interactive")
    elif request.method == 'POST' and request.is_xhr:
        return render_template('inc/rejectform.html', post=post, rejectform=rejectform, ajaxreg=True)
    return redirect(url_for('jobdetail', hashid=post.hashid))


@app.route('/confirm/<hashid>', methods=('GET', 'POST'))
def confirm(hashid):
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    form = forms.ConfirmForm()
    if post.status in [POSTSTATUS.REJECTED, POSTSTATUS.SPAM]:
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
        session.modified = True  # Since it won't detect changes to lists
        session.permanent = True
        return render_template('mailsent.html', post=post)
    return render_template('confirm.html', post=post, form=form)


@app.route('/confirm/<hashid>/<key>')
def confirm_email(hashid, key):
    # If post is in pending state and email key is correct, convert to published
    # and update post.datetime to utcnow() so it'll show on top of the stack
    # This function expects key to be email_verify_key, not edit_key like the others
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    if post.status in [POSTSTATUS.REJECTED, POSTSTATUS.SPAM]:
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
            if app.config.get('THROTTLE_LIMIT', 0) > 0:
                post_count = JobPost.query.filter(JobPost.email_domain == post.email_domain).filter(
                    JobPost.status > POSTSTATUS.PENDING).filter(
                        JobPost.datetime > datetime.utcnow() - timedelta(days=1)).count()
                if post_count > app.config['THROTTLE_LIMIT']:
                    flash(u"We've received too many listings from %s in the last 24 hours. Please try again in a few hours."
                        % post.email_domain, category='info')
                    return redirect(url_for('index'))
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
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    form = forms.WithdrawForm()
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
        form_description = bleach.linkify(bleach.clean(form.job_description.data, tags=ALLOWED_TAGS))
        form_perks = bleach.linkify(bleach.clean(form.job_perks_description.data, tags=ALLOWED_TAGS)) if form.job_perks.data else ''
        form_how_to_apply = form.job_how_to_apply.data
        form_email_domain = get_email_domain(form.poster_email.data)
        form_words = get_word_bag(u' '.join((form_description, form_perks, form_how_to_apply)))

        similar = False
        for oldpost in JobPost.query.filter(db.or_(
            db.and_(
                JobPost.email_domain == form_email_domain,
                JobPost.status.in_([POSTSTATUS.CONFIRMED, POSTSTATUS.REVIEWED,
                    POSTSTATUS.WITHDRAWN, POSTSTATUS.REJECTED])),
            JobPost.status == POSTSTATUS.SPAM)).filter(
                JobPost.datetime > datetime.utcnow() - agelimit).all():
            if oldpost.id != post.id:
                if oldpost.words:
                    s = SequenceMatcher(None, form_words, oldpost.words)
                    if s.ratio() > 0.6:
                        similar = True
                        break

        if similar:
            flash("This listing is very similar to an earlier listing. You may not relist the same job "
                "in less than %d days." % agelimit.days, category='interactive')
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
            post.fullname = form.poster_name.data
            post.email = form.poster_email.data
            post.email_domain = form_email_domain
            post.md5sum = md5sum(post.email)
            post.hr_contact = form.hr_contact.data
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
        form.poster_name.data = post.fullname
        form.poster_email.data = post.email
        form.hr_contact.data = int(post.hr_contact or False)

    return render_template('postjob.html', form=form, no_email=post.status > POSTSTATUS.DRAFT)


@app.route('/new', methods=('GET', 'POST'))
def newjob():
    form = forms.ListingForm()
    form.job_type.choices = [(ob.id, ob.title) for ob in JobType.query.filter_by(public=True).order_by('seq')]
    form.job_category.choices = [(ob.id, ob.title) for ob in JobCategory.query.filter_by(public=True).order_by('seq')]
    if request.method == 'GET' or (request.method == 'POST' and request.form.get('form.id') == 'newheadline'):
        if g.user:
            form.poster_name.data = g.user.fullname
            form.poster_email.data = g.user.email
    if request.method == 'POST' and request.form.get('form.id') != 'newheadline' and form.validate():
        # POST request from new job page, with successful validation
        # Move it to the editjob page for handling here forward
        post = JobPost(hashid=unique_hash(JobPost),
                       ipaddr=request.environ['REMOTE_ADDR'],
                       useragent=request.user_agent.string)
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
