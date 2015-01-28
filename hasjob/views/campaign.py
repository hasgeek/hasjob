# -*- coding: utf-8 -*-

from flask import flash, url_for, redirect, render_template
from coaster.views import load_model, load_models
from baseframe.forms import render_form, render_delete_sqla, render_redirect
from .. import app, lastuser
from ..models import db, Campaign, CampaignAction
from ..forms import CampaignForm, CampaignActionForm


@app.route('/campaign', methods=['GET'])
@lastuser.requires_permission('siteadmin')
def campaign_list():
    return render_template('campaign_list.html', campaigns=Campaign.all())


@app.route('/campaign/new', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
def campaign_new():
    form = CampaignForm()
    if form.validate_on_submit():
        campaign = Campaign()
        form.populate_obj(campaign)
        campaign.make_name()
        db.session.add(campaign)
        db.session.commit()
        flash(u"Created a campaign", 'success')
        return render_redirect(url_for('campaign_view', campaign=campaign.name), code=303)

    return render_form(form=form, title=u"Create a campaign…", submit="Next",
        message=u"Campaigns appaear around the job board and provide a call to action for users",
        formid="campaign_new", cancel_url=url_for('index'), ajax=False)


@app.route('/campaign/<campaign>')
@lastuser.requires_permission('siteadmin')
@load_model(Campaign, {'name': 'campaign'}, 'campaign')
def campaign_view(campaign):
    return render_template('campaign_info.html', campaign=campaign)


@app.route('/campaign/<campaign>/edit', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
@load_model(Campaign, {'name': 'campaign'}, 'campaign')
def campaign_edit(campaign):
    form = CampaignForm(obj=campaign)
    if form.validate_on_submit():
        form.populate_obj(campaign)
        campaign.make_name()
        db.session.commit()
        flash(u"Edited campaign settings", 'success')
        return render_redirect(url_for('campaign_view', campaign=campaign.name), code=303)

    return render_form(form=form, title=u"Edit campaign settings", submit="Save",
        formid="campaign_edit", cancel_url=url_for('campaign_list'), ajax=False)


@app.route('/campaign/<campaign>/delete', methods=['GET', 'POST'])
@lastuser.requires_login
@load_model(Campaign, {'name': 'campaign'}, 'campaign', permission='delete')
def campaign_delete(campaign):
    return render_delete_sqla(campaign, db, title=u"Confirm delete",
        message=u"Delete campaign '%s'?" % campaign.title,
        success=u"You have deleted campaign '%s'." % campaign.title,
        next=url_for('campaign_list'))


@app.route('/campaign/<campaign>/new', methods=['GET', 'POST'])
@lastuser.requires_login
@load_model(Campaign, {'name': 'campaign'}, 'campaign')
def campaign_action_new(campaign):
    form = CampaignActionForm()
    if form.validate_on_submit():
        action = CampaignAction(campaign=campaign)
        db.session.add(action)
        form.populate_obj(action)
        action.make_name()
        db.session.commit()
        flash(u"Added campaign action %s" % action.title, 'interactive')
        return redirect(url_for('campaign_view', campaign=campaign.name), code=303)

    return render_form(form=form, title=u"Edit campaign action", submit="Save",
        formid="campaign_action_edit", cancel_url=url_for('campaign_view', campaign=campaign.name), ajax=False)


@app.route('/campaign/<campaign>/<action>/edit', methods=['GET', 'POST'])
@lastuser.requires_login
@load_models(
    (Campaign, {'name': 'campaign'}, 'campaign'),
    (CampaignAction, {'hashid': 'hashid'}, 'action'))
def campaign_action_edit(campaign, action):
    form = CampaignActionForm(obj=action)
    if form.validate_on_submit():
        form.populate_obj(action)
        action.make_name()
        db.session.commit()
        flash(u"Edited campaign action %s" % action.title, 'interactive')
        return redirect(url_for('campaign_view', campaign=campaign.name), code=303)

    return render_form(form=form, title=u"Edit campaign action", submit="Save",
        formid="campaign_action_edit", cancel_url=url_for('campaign_view', campaign=campaign.name), ajax=False)


@app.route('/campaign/<campaign>/<action>/delete', methods=['GET', 'POST'])
@lastuser.requires_login
@load_models(
    (Campaign, {'name': 'campaign'}, 'campaign'),
    (CampaignAction, {'hashid': 'hashid'}, 'action'))
def campaign_action_delete(campaign, action):
    return render_delete_sqla(action, db, title=u"Confirm delete",
        message=u"Delete campaign action '%s'?" % campaign.title,
        success=u"You have deleted campaign action '%s'." % campaign.title,
        next=url_for('campaign_view', campaign=campaign.name))
