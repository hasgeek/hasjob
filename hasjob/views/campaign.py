# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import timedelta
from cStringIO import StringIO
from pytz import UTC
import unicodecsv
from flask import g, request, flash, url_for, redirect, render_template, Markup, abort
from coaster.utils import buid, make_name
from coaster.views import load_model, load_models
from baseframe.forms import render_form, render_delete_sqla, render_redirect
from .. import app, lastuser
from ..models import (db, Campaign, CampaignView, CampaignAction, CampaignUserAction, CampaignAnonUserAction,
    CAMPAIGN_ACTION)
from ..forms import CampaignForm, CampaignActionForm


def chart_interval_for(campaign, default='hour'):
    interval = default
    started_at = db.session.query(db.func.min(CampaignView.datetime)).filter(CampaignView.campaign == campaign).first()[0]
    if started_at:
        ended_at = db.session.query(db.func.max(CampaignView.datetime)).filter(CampaignView.campaign == campaign).first()[0]
        if ended_at - started_at > timedelta(days=7):
            # It's been a week. Show data per day
            interval = 'day'
        else:
            # Under a week? Per hour
            interval = 'hour'
    return interval


@app.route('/admin/campaign', methods=['GET'])
@lastuser.requires_permission('siteadmin')
def campaign_list():
    return render_template('campaign_list.html', campaigns=Campaign.all())


@app.route('/admin/campaign/new', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
def campaign_new():
    form = CampaignForm()
    if request.method == 'GET' and g.board:
        form.boards.data = [g.board]
    if form.validate_on_submit():
        campaign = Campaign(user=g.user)
        form.populate_obj(campaign)
        campaign.name = buid()  # Use a random name since it's also used in user action submit forms
        db.session.add(campaign)
        db.session.commit()
        flash(u"Created a campaign", 'success')
        return render_redirect(url_for('campaign_view', campaign=campaign.name), code=303)

    return render_form(form=form, title=u"Create a campaign…", submit="Next",
        message=u"Campaigns appear around the job board and provide a call to action for users",
        formid="campaign_new", cancel_url=url_for('campaign_list'), ajax=False)


@app.route('/admin/campaign/<campaign>')
@lastuser.requires_permission('siteadmin')
@load_model(Campaign, {'name': 'campaign'}, 'campaign')
def campaign_view(campaign):
    return render_template('campaign_info.html', campaign=campaign, interval=chart_interval_for(campaign, default=None))


@app.route('/admin/campaign/<campaign>/edit', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
@load_model(Campaign, {'name': 'campaign'}, 'campaign')
def campaign_edit(campaign):
    form = CampaignForm(obj=campaign)
    if form.validate_on_submit():
        form.populate_obj(campaign)
        db.session.commit()
        flash(u"Edited campaign settings", 'success')
        return render_redirect(url_for('campaign_view', campaign=campaign.name), code=303)

    return render_form(form=form, title=u"Edit campaign settings", submit="Save",
        formid="campaign_edit", cancel_url=url_for('campaign_view', campaign=campaign.name), ajax=False)


@app.route('/admin/campaign/<campaign>/delete', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
@load_model(Campaign, {'name': 'campaign'}, 'campaign')
def campaign_delete(campaign):
    return render_delete_sqla(campaign, db, title=u"Confirm delete",
        message=u"Delete campaign '%s'?" % campaign.title,
        success=u"You have deleted campaign '%s'." % campaign.title,
        next=url_for('campaign_list'))


@app.route('/admin/campaign/<campaign>/new', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
@load_model(Campaign, {'name': 'campaign'}, 'campaign')
def campaign_action_new(campaign):
    form = CampaignActionForm()
    if request.method == 'GET':
        form.seq.data = max([a.seq for a in campaign.actions] or [0]) + 1
    if form.validate_on_submit():
        action = CampaignAction(campaign=campaign)
        db.session.add(action)
        form.populate_obj(action)
        action.make_name()
        db.session.commit()
        flash(u"Added campaign action ‘%s’" % action.title, 'interactive')
        return redirect(url_for('campaign_view', campaign=campaign.name), code=303)

    return render_form(form=form, title=u"Add a new campaign action…", submit="Save",
        formid="campaign_action_new", cancel_url=url_for('campaign_view', campaign=campaign.name), ajax=False)


@app.route('/admin/campaign/<campaign>/<action>/edit', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
@load_models(
    (Campaign, {'name': 'campaign'}, 'campaign'),
    (CampaignAction, {'name': 'action', 'campaign': 'campaign'}, 'action'))
def campaign_action_edit(campaign, action):
    form = CampaignActionForm(obj=action)
    if form.validate_on_submit():
        form.populate_obj(action)
        action.make_name()
        db.session.commit()
        flash(u"Edited campaign action ‘%s’" % action.title, 'interactive')
        return redirect(url_for('campaign_view', campaign=campaign.name), code=303)

    return render_form(form=form, title=u"Edit campaign action", submit="Save",
        formid="campaign_action_edit", cancel_url=url_for('campaign_view', campaign=campaign.name), ajax=False)


@app.route('/admin/campaign/<campaign>/<action>/delete', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
@load_models(
    (Campaign, {'name': 'campaign'}, 'campaign'),
    (CampaignAction, {'name': 'action', 'campaign': 'campaign'}, 'action'))
def campaign_action_delete(campaign, action):
    return render_delete_sqla(action, db, title=u"Confirm delete",
        message=u"Delete campaign action '%s'?" % campaign.title,
        success=u"You have deleted campaign action '%s'." % campaign.title,
        next=url_for('campaign_view', campaign=campaign.name))


@app.route('/admin/campaign/<campaign>/<action>/csv', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
@load_models(
    (Campaign, {'name': 'campaign'}, 'campaign'),
    (CampaignAction, {'name': 'action', 'campaign': 'campaign'}, 'action'))
def campaign_action_csv(campaign, action):
    if action.type not in ('Y', 'N', 'M', 'F'):
        abort(403)
    outfile = StringIO()
    out = unicodecsv.writer(outfile, 'excel')
    out.writerow(['fullname', 'username', 'email', 'phone'])
    for ua in action.useractions:
        out.writerow([ua.user.fullname, ua.user.username, ua.user.email, ua.user.phone])
    return outfile.getvalue(), 200, {'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename="%s-%s.csv"' % (
            make_name(campaign.title), make_name(action.title))}


# --- Campaign charts ---------------------------------------------------------

@app.route('/admin/campaign/<campaign>/views.csv')
@lastuser.requires_permission('siteadmin')
@load_model(Campaign, {'name': 'campaign'}, 'campaign')
def campaign_view_counts(campaign):
    timezone = g.user.timezone if g.user else 'UTC'
    viewdict = defaultdict(dict)

    interval = chart_interval_for(campaign)

    hourly_views = db.session.query('hour', 'count').from_statement(db.text(
        '''SELECT date_trunc(:interval, campaign_view.datetime AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM campaign_view WHERE campaign_id=:campaign_id GROUP BY hour ORDER BY hour;'''
    )).params(interval=interval, timezone=timezone, campaign_id=campaign.id)

    for hour, count in hourly_views:
        viewdict[hour]['_views'] = count

    hourly_views = db.session.query('hour', 'count').from_statement(db.text(
        '''SELECT date_trunc(:interval, campaign_anon_view.datetime AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM campaign_anon_view WHERE campaign_id=:campaign_id GROUP BY hour ORDER BY hour;'''
    )).params(interval=interval, timezone=timezone, campaign_id=campaign.id)

    for hour, count in hourly_views:
        viewdict[hour]['_views'] = viewdict[hour].setdefault('_views', 0) + count

    hourly_views = db.session.query('hour', 'count').from_statement(db.text(
        '''SELECT date_trunc(:interval, campaign_user_action.created_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(DISTINCT(user_id)) AS count FROM campaign_user_action WHERE action_id IN (SELECT id FROM campaign_action WHERE campaign_id = :campaign_id AND type != :dismiss_type) GROUP BY hour ORDER BY hour;'''
        )).params(interval=interval, timezone=timezone, campaign_id=campaign.id, dismiss_type=CAMPAIGN_ACTION.DISMISS)

    for hour, count in hourly_views:
        viewdict[hour]['_combined'] = count

    hourly_views = db.session.query('hour', 'count').from_statement(db.text(
        '''SELECT date_trunc(:interval, campaign_anon_user_action.created_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(DISTINCT(anon_user_id)) AS count FROM campaign_anon_user_action WHERE action_id IN (SELECT id FROM campaign_action WHERE campaign_id = :campaign_id AND type != :dismiss_type) GROUP BY hour ORDER BY hour;'''
        )).params(interval=interval, timezone=timezone, campaign_id=campaign.id, dismiss_type=CAMPAIGN_ACTION.DISMISS)

    for hour, count in hourly_views:
        viewdict[hour]['_combined'] = viewdict[hour].setdefault('_combined', 0) + count

    action_names = []

    for action in campaign.actions:
        action_names.append(action.name)
        hourly_views = db.session.query('hour', 'count').from_statement(db.text(
            '''SELECT date_trunc(:interval, campaign_user_action.created_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM campaign_user_action WHERE action_id=:action_id GROUP BY hour ORDER BY hour;'''
        )).params(interval=interval, timezone=timezone, action_id=action.id)
        for hour, count in hourly_views:
            viewdict[hour][action.name] = count

        hourly_views = db.session.query('hour', 'count').from_statement(db.text(
            '''SELECT date_trunc(:interval, campaign_anon_user_action.created_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM campaign_anon_user_action WHERE action_id=:action_id GROUP BY hour ORDER BY hour;'''
        )).params(interval=interval, timezone=timezone, action_id=action.id)
        for hour, count in hourly_views:
            viewdict[hour][action.name] = viewdict[hour].setdefault(action.name, 0) + count

    if viewdict:
        # Top-off with site-wide user presence (available since 31 Jan 2015 in user_active_at)
        minhour = g.user.tz.localize(min(viewdict.keys())).astimezone(UTC).replace(tzinfo=None)
        maxhour = g.user.tz.localize(max(viewdict.keys()) + timedelta(seconds=3599)).astimezone(UTC).replace(tzinfo=None)

        hourly_views = db.session.query('hour', 'count').from_statement(db.text(
            '''SELECT date_trunc(:interval, user_active_at.active_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(DISTINCT(user_active_at.user_id)) AS count FROM user_active_at WHERE user_active_at.active_at >= :min AND user_active_at.active_at <= :max GROUP BY hour ORDER BY hour;'''
            )).params(interval=interval, timezone=timezone, min=minhour, max=maxhour)

        for hour, count in hourly_views:
            viewdict[hour]['_site'] = count

        hourly_views = db.session.query('hour', 'count').from_statement(
            '''SELECT DATE_TRUNC(:interval, event_session.created_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(DISTINCT(anon_user_id)) AS count FROM event_session WHERE event_session.anon_user_id IS NOT NULL AND event_session.created_at >= :min AND event_session.created_at <= :max GROUP BY hour ORDER BY hour'''
            ).params(interval=interval, timezone=timezone, min=minhour, max=maxhour)

        for hour, count in hourly_views:
            viewdict[hour]['_site'] = viewdict[hour].setdefault('_site', 0) + count

    viewlist = []
    for slot in viewdict:
        row = [slot, viewdict[slot].get('_site', 0), viewdict[slot].get('_views', 0), viewdict[slot].get('_combined', 0)]
        for name in action_names:
            row.append(viewdict[slot].get(name, 0))
        viewlist.append(row)

    viewlist.sort()  # Sorts by first column, the hour slot (datetime)
    for row in viewlist:
        row[0] = row[0].isoformat()

    outfile = StringIO()
    out = unicodecsv.writer(outfile, 'excel')
    out.writerow(['_hour', '_site', '_views', '_combined'] + action_names)
    out.writerows(viewlist)

    return outfile.getvalue(), 200, {'Content-Type': 'text/plain'}


# --- Campaign actions --------------------------------------------------------

@app.route('/go/c/<campaign>/<action>', subdomain='<subdomain>')
@app.route('/go/c/<campaign>/<action>')
@load_models(
    (Campaign, {'name': 'campaign'}, 'campaign'),
    (CampaignAction, {'name': 'action', 'campaign': 'campaign'}, 'action')
    )
def campaign_action_redirect(campaign, action):
    if action.type != CAMPAIGN_ACTION.LINK:
        abort(405)
    if g.user:
        cua = CampaignUserAction.get(action, g.user)
        if not cua:
            cua = CampaignUserAction(action=action, user=g.user)
            db.session.add(cua)
            db.session.commit()
    elif g.anon_user:
        cua = CampaignAnonUserAction.get(action, g.anon_user)
        if not cua:
            cua = CampaignAnonUserAction(action=action, anon_user=g.anon_user)
            db.session.add(cua)
            db.session.commit()
    return redirect(action.link, code=302)


@app.route('/go/c/<campaign>', methods=['POST'], subdomain='<subdomain>')
@app.route('/go/c/<campaign>', methods=['POST'])
@load_model(Campaign, {'name': 'campaign'}, 'campaign')
def campaign_action(campaign):
    """
    First level submission.
    """
    form = campaign.form()
    if not form.validate():
        return render_template('campaign_action_response.html',
            campaign=campaign,
            message=Markup("<p>This form timed out. Please try again</p>"))

    dismissed = 'dismiss' in request.form
    if dismissed:
        if g.user:
            view = campaign.view_for(g.user)
            if view:
                view.dismissed = True
                db.session.commit()
        elif g.anon_user:
            view = campaign.view_for(anon_user=g.anon_user)
            if view:
                view.dismissed = True
                db.session.commit()
        return render_template('campaign_action_response.html',
            campaign=campaign, dismiss=True)

    action_name = request.form.get('action')
    action = CampaignAction.get(campaign, action_name)
    if not action:
        return render_template('campaign_action_response.html',
            campaign=campaign,
            message=Markup("<p>Unknown action selected</p>"))
    cua = None
    if g.user:
        cua = CampaignUserAction.get(action, g.user)
        if not cua:
            cua = CampaignUserAction(action=action, user=g.user)
            db.session.add(cua)
    else:
        if g.anon_user and action.type == CAMPAIGN_ACTION.DISMISS:
            cua = CampaignAnonUserAction.get(action, g.anon_user)
            if not cua:
                cua = CampaignAnonUserAction(action=action, anon_user=g.anon_user)
                db.session.add(cua)
        else:  # All of the other types require a user (not an anon user; will change when forms are introduced)
            return render_template('campaign_action_response.html', campaign=campaign,
                redirect=url_for('login', next=request.referrer, message=u"Please login so we can save your preferences"))

    if action.type in (CAMPAIGN_ACTION.RSVP_Y, CAMPAIGN_ACTION.RSVP_N, CAMPAIGN_ACTION.RSVP_M):
        for cua in campaign.useractions(g.user).values():
            if cua.action != action and cua.action.group == action.group and cua.action.type in (
                    CAMPAIGN_ACTION.RSVP_Y, CAMPAIGN_ACTION.RSVP_N, CAMPAIGN_ACTION.RSVP_M):
                db.session.delete(cua)  # If user changed their RSVP answer, delete old answer
        db.session.commit()
        return render_template('campaign_action_response.html', campaign=campaign,
            message=Markup(action.message))
    elif action.type == CAMPAIGN_ACTION.DISMISS:
        view = campaign.view_for(g.user, g.anon_user)
        if view:
            view.dismissed = True
            db.session.commit()
        return render_template('campaign_action_response.html',
            campaign=campaign, dismiss=True,
            message=Markup(action.message))
    elif action.type == CAMPAIGN_ACTION.FORM:
        # Render a form here
        db.session.commit()
        return render_template('campaign_action_response.html', campaign=campaign,
            message=Markup("To be implemented"))  # TODO
