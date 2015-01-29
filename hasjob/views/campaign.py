# -*- coding: utf-8 -*-

from cStringIO import StringIO
import unicodecsv
from flask import g, request, flash, url_for, redirect, render_template, Markup, abort
from coaster.utils import buid
from coaster.views import load_model, load_models
from baseframe.forms import render_form, render_delete_sqla, render_redirect
from .. import app, lastuser
from ..models import db, Campaign, CampaignAction, CampaignUserAction, CAMPAIGN_ACTION
from ..forms import CampaignForm, CampaignActionForm


@app.route('/admin/campaign', methods=['GET'])
@lastuser.requires_permission('siteadmin')
def campaign_list():
    return render_template('campaign_list.html', campaigns=Campaign.all())


@app.route('/admin/campaign/new', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
def campaign_new():
    form = CampaignForm()
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
    return render_template('campaign_info.html', campaign=campaign)


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


# --- Campaign charts ---------------------------------------------------------

@app.route('/admin/campaign/<campaign>/views.csv')
@lastuser.requires_permission('siteadmin')
@load_model(Campaign, {'name': 'campaign'}, 'campaign')
def campaign_view_counts(campaign):
    timezone = g.user.timezone if g.user else 'UTC'

    viewdict = {}
    hourly_views = db.session.query('hour', 'count').from_statement(db.text(
        '''SELECT date_trunc('hour', campaign_view.created_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM campaign_view WHERE campaign_id=:campaign_id GROUP BY hour ORDER BY hour;'''
    )).params(timezone=timezone, campaign_id=campaign.id)

    for hour, count in hourly_views:
        viewdict[hour] = {'_views': count}

    hourly_views = db.session.query('hour', 'count').from_statement(db.text(
        '''SELECT date_trunc('hour', campaign_user_action.created_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(DISTINCT(user_id)) AS count FROM campaign_user_action WHERE action_id IN (SELECT id FROM campaign_action WHERE campaign_id = :campaign_id) GROUP BY hour ORDER BY hour;'''
        )).params(timezone=timezone, campaign_id=campaign.id)

    for hour, count in hourly_views:
        viewdict.setdefault(hour, {})['_combined'] = count

    action_names = []

    for action in campaign.actions:
        action_names.append(action.name)
        hourly_views = db.session.query('hour', 'count').from_statement(db.text(
            '''SELECT date_trunc('hour', campaign_user_action.created_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM campaign_user_action WHERE action_id=:action_id GROUP BY hour ORDER BY hour;'''
        )).params(timezone=timezone, action_id=action.id)
        for hour, count in hourly_views:
            viewdict.setdefault(hour, {})[action.name] = count

    viewlist = []
    for slot in viewdict:
        row = [slot, viewdict[slot].get('_views', 0), viewdict[slot].get('_combined', 0)]
        for name in action_names:
            row.append(viewdict[slot].get(name, 0))
        viewlist.append(row)

    viewlist.sort()  # Sorts by first column, the hour slot (datetime)
    for row in viewlist:
        row[0] = row[0].isoformat()

    outfile = StringIO()
    out = unicodecsv.writer(outfile, 'excel')
    out.writerow(['_hour', '_views', '_combined'] + action_names)
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
    return redirect(action.link, code=302)


@app.route('/go/c/<campaign>', methods=['POST'], subdomain='<subdomain>')
@app.route('/go/c/<campaign>', methods=['POST'])
@load_model(Campaign, {'name': 'campaign'}, 'campaign')
def campaign_action(campaign):
    """
    First level submission.
    """
    action_name = request.form.get('action')
    action = CampaignAction.get(campaign, action_name)
    if not action:
        return render_template('campaign_action_response.html',
            campaign=campaign,
            message=Markup("p>Unknown action selected</p>"))
    cua = None
    if g.user:
        cua = CampaignUserAction.get(action, g.user)
        if not cua:
            cua = CampaignUserAction(action=action, user=g.user)
            db.session.add(cua)
    if action.type == CAMPAIGN_ACTION.LINK:
        db.session.commit()
        return render_template('campaign_action_response.html', campaign=campaign, redirect=action.link)
    elif not g.user:  # All of the other types require a user
        return render_template('campaign_action_response.html', campaign=campaign,
            redirect=url_for('login', next=request.referrer, message=u"Please login so we can save your preferences"))

    if action.type in (CAMPAIGN_ACTION.RSVP_Y, CAMPAIGN_ACTION.RSVP_N, CAMPAIGN_ACTION.RSVP_M):
        for cua in campaign.useractions(g.user).values():
            if cua.action != action and cua.action.type in (
                    CAMPAIGN_ACTION.RSVP_Y, CAMPAIGN_ACTION.RSVP_N, CAMPAIGN_ACTION.RSVP_M):
                db.session.delete(cua)  # If user changed their RSVP answer, delete old answer
        db.session.commit()
        return render_template('campaign_action_response.html', campaign=campaign,
            message=Markup(action.message))
    elif action.type == CAMPAIGN_ACTION.DISMISS:
        view = campaign.view_for(g.user)
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
