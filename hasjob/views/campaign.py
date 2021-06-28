from collections import defaultdict
from datetime import timedelta
from functools import wraps
from io import StringIO
import csv

from flask import Markup, abort, flash, g, redirect, render_template, request, url_for

from pytz import UTC

from baseframe import __
from baseframe.forms import render_delete_sqla, render_form, render_redirect
from coaster.utils import classmethodproperty, make_name, uuid_b58
from coaster.views import (
    InstanceLoader,
    ModelView,
    UrlForView,
    load_model,
    load_models,
    route,
    viewdata,
)

from .. import app, lastuser
from ..forms import CampaignActionForm, CampaignForm
from ..models import (
    CAMPAIGN_ACTION,
    Campaign,
    CampaignAction,
    CampaignAnonUserAction,
    CampaignUserAction,
    CampaignView,
    db,
)
from .admin import AdminView


@route('/admin/campaign')
class AdminCampaignList(AdminView):
    __decorators__ = [lastuser.requires_permission('siteadmin')]

    @property
    def listquery(self):
        return Campaign.query.order_by(
            Campaign.start_at.desc(), Campaign.priority.desc()
        ).options(db.load_only('title', 'start_at', 'end_at', 'public'))

    @route('')
    @viewdata(tab=True, index=0, title=__("Current"))
    def list_current(self):
        return render_template(
            'campaign_list.html.jinja2',
            title="Current campaigns",
            campaigns=self.listquery.filter(Campaign.state.is_current).all(),
        )

    @route('longterm', methods=['GET'])
    @viewdata(tab=True, index=1, title=__("Long term"))
    def list_longterm(self):
        return render_template(
            'campaign_list.html.jinja2',
            title="Long term campaigns",
            campaigns=self.listquery.filter(Campaign.state.is_longterm).all(),
        )

    @route('offline', methods=['GET'])
    @viewdata(tab=True, index=2, title=__("Offline"))
    def list_offline(self):
        return render_template(
            'campaign_list.html.jinja2',
            title="Offline campaigns",
            campaigns=self.listquery.filter(Campaign.state.is_offline).all(),
        )

    @route('disabled', methods=['GET'])
    @viewdata(tab=True, index=3, title=__("Disabled"))
    def list_disabled(self):
        return render_template(
            'campaign_list.html.jinja2',
            title="Disabled campaigns",
            campaigns=self.listquery.filter(Campaign.state.is_disabled).all(),
        )

    @route('new', methods=['GET', 'POST'])
    @viewdata(tab=True, index=4, title=__("New"))
    def new(self):
        self.message = "Campaigns appear around the job board and provide a call to action for users"
        form = CampaignForm()
        if request.method == 'GET' and g.board:
            form.boards.data = [g.board]
        if form.validate_on_submit():
            campaign = Campaign(user=g.user)
            form.populate_obj(campaign)
            # Use a random name since it's also used in user action submit forms
            campaign.name = uuid_b58()
            db.session.add(campaign)
            db.session.commit()
            flash("Created a campaign", 'success')
            return render_redirect(campaign.url_for(), code=303)

        return render_form(
            form=form,
            title="Create a campaign…",
            submit="Next",
            formid="campaign_new",
            cancel_url=url_for(self.list_current.endpoint),
            ajax=False,
        )


AdminCampaignList.init_app(app)


def chart_interval_for(campaign, default='hour'):
    interval = default
    started_at = (
        db.session.query(db.func.min(CampaignView.datetime))
        .filter(CampaignView.campaign == campaign)
        .first()[0]
    )
    if started_at:
        ended_at = (
            db.session.query(db.func.max(CampaignView.datetime))
            .filter(CampaignView.campaign == campaign)
            .first()[0]
        )
        if ended_at - started_at > timedelta(days=7):
            # It's been a week. Show data per day
            interval = 'day'
        else:
            # Under a week? Per hour
            interval = 'hour'
    return interval


def campaign_current_tab(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self.obj:
            if self.obj.state.is_current:
                self.current_tab = 'list_current'
            elif self.obj.state.is_longterm:
                self.current_tab = 'list_longterm'
            elif self.obj.state.is_offline:
                self.current_tab = 'list_offline'
            elif self.obj.state.is_disabled:
                self.current_tab = 'list_disabled'
        return f(self, *args, **kwargs)

    return wrapper


def campaign_action_current_tab(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self.obj:
            if self.obj.parent.state.is_current:
                self.current_tab = 'list_current'
            elif self.obj.parent.state.is_longterm:
                self.current_tab = 'list_longterm'
            elif self.obj.parent.state.is_offline:
                self.current_tab = 'list_offline'
            elif self.obj.parent.state.is_disabled:
                self.current_tab = 'list_disabled'
        return f(self, *args, **kwargs)

    return wrapper


@route('/admin/campaign/<campaign>')
class AdminCampaignView(UrlForView, InstanceLoader, ModelView):
    __decorators__ = [lastuser.requires_permission('siteadmin'), campaign_current_tab]
    model = Campaign
    route_model_map = {'campaign': 'name'}

    @classmethodproperty
    def tabs(cls):  # noqa: N805
        return AdminCampaignList.tabs

    @route('')
    def view(self):
        return render_template(
            'campaign_info.html.jinja2',
            campaign=self.obj,
            interval=chart_interval_for(self.obj, default=None),
        )

    @route('edit', methods=['GET', 'POST'])
    def edit(self):
        form = CampaignForm(obj=self.obj)
        if form.validate_on_submit():
            form.populate_obj(self.obj)
            db.session.commit()
            flash("Edited campaign settings", 'success')
            return render_redirect(self.obj.url_for(), code=303)

        return render_form(
            form=form,
            title="Edit campaign settings",
            submit="Save",
            formid="campaign_edit",
            cancel_url=self.obj.url_for(),
            ajax=False,
        )

    @route('delete', methods=['GET', 'POST'])
    def delete(self):
        return render_delete_sqla(
            self.obj,
            db,
            title="Confirm delete",
            message="Delete campaign '%s'?" % self.obj.title,
            success="You have deleted campaign '%s'." % self.obj.title,
            next=url_for(getattr(self, self.current_tab).endpoint),
            cancel_url=self.obj.url_for(),
        )

    @route('new', methods=['GET', 'POST'])
    def action_new(self):
        self.form_header = Markup(
            render_template(
                'campaign_action_edit_header.html.jinja2', campaign=self.obj
            )
        )
        form = CampaignActionForm()
        if request.method == 'GET':
            form.seq.data = max([a.seq for a in self.obj.actions] or [0]) + 1
        if form.validate_on_submit():
            action = CampaignAction(campaign=self.obj)
            db.session.add(action)
            form.populate_obj(action)
            action.name = uuid_b58()  # Use a random name since it needs to be permanent
            db.session.commit()
            flash("Added campaign action ‘%s’" % action.title, 'interactive')
            return redirect(self.obj.url_for(), code=303)

        return render_form(
            form=form,
            title="Add a new campaign action…",
            submit="Save",
            formid="campaign_action_new",
            cancel_url=self.obj.url_for(),
            ajax=False,
        )

    @route('views.csv')
    def view_counts(self):
        campaign = self.obj
        timezone = g.user.timezone if g.user else 'UTC'
        viewdict = defaultdict(dict)

        interval = chart_interval_for(campaign)

        hourly_views = (
            db.session.query('hour', 'count')
            .from_statement(
                db.text(
                    '''SELECT date_trunc(:interval, campaign_view.datetime AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM campaign_view WHERE campaign_id=:campaign_id GROUP BY hour ORDER BY hour;'''
                )
            )
            .params(interval=interval, timezone=timezone, campaign_id=campaign.id)
        )

        for hour, count in hourly_views:
            viewdict[hour]['_views'] = count

        hourly_views = (
            db.session.query('hour', 'count')
            .from_statement(
                db.text(
                    '''SELECT date_trunc(:interval, campaign_anon_view.datetime AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM campaign_anon_view WHERE campaign_id=:campaign_id GROUP BY hour ORDER BY hour;'''
                )
            )
            .params(interval=interval, timezone=timezone, campaign_id=campaign.id)
        )

        for hour, count in hourly_views:
            viewdict[hour]['_views'] = viewdict[hour].setdefault('_views', 0) + count

        hourly_views = (
            db.session.query('hour', 'count')
            .from_statement(
                db.text(
                    '''SELECT date_trunc(:interval, campaign_user_action.created_at AT TIME ZONE :timezone) AS hour, COUNT(DISTINCT(user_id)) AS count FROM campaign_user_action WHERE action_id IN (SELECT id FROM campaign_action WHERE campaign_id = :campaign_id AND type != :dismiss_type) GROUP BY hour ORDER BY hour;'''
                )
            )
            .params(
                interval=interval,
                timezone=timezone,
                campaign_id=campaign.id,
                dismiss_type=CAMPAIGN_ACTION.DISMISS,
            )
        )

        for hour, count in hourly_views:
            viewdict[hour]['_combined'] = count

        hourly_views = (
            db.session.query('hour', 'count')
            .from_statement(
                db.text(
                    '''SELECT date_trunc(:interval, campaign_anon_user_action.created_at AT TIME ZONE :timezone) AS hour, COUNT(DISTINCT(anon_user_id)) AS count FROM campaign_anon_user_action WHERE action_id IN (SELECT id FROM campaign_action WHERE campaign_id = :campaign_id AND type != :dismiss_type) GROUP BY hour ORDER BY hour;'''
                )
            )
            .params(
                interval=interval,
                timezone=timezone,
                campaign_id=campaign.id,
                dismiss_type=CAMPAIGN_ACTION.DISMISS,
            )
        )

        for hour, count in hourly_views:
            viewdict[hour]['_combined'] = (
                viewdict[hour].setdefault('_combined', 0) + count
            )

        action_names = []

        for action in campaign.actions:
            action_names.append(action.name)
            hourly_views = (
                db.session.query('hour', 'count')
                .from_statement(
                    db.text(
                        '''SELECT date_trunc(:interval, campaign_user_action.created_at AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM campaign_user_action WHERE action_id=:action_id GROUP BY hour ORDER BY hour;'''
                    )
                )
                .params(interval=interval, timezone=timezone, action_id=action.id)
            )
            for hour, count in hourly_views:
                viewdict[hour][action.name] = count

            hourly_views = (
                db.session.query('hour', 'count')
                .from_statement(
                    db.text(
                        '''SELECT date_trunc(:interval, campaign_anon_user_action.created_at AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM campaign_anon_user_action WHERE action_id=:action_id GROUP BY hour ORDER BY hour;'''
                    )
                )
                .params(interval=interval, timezone=timezone, action_id=action.id)
            )
            for hour, count in hourly_views:
                viewdict[hour][action.name] = (
                    viewdict[hour].setdefault(action.name, 0) + count
                )

        if viewdict:
            # Top-off with site-wide user presence (available since 31 Jan 2015 in user_active_at)
            minhour = g.user.tz.localize(min(viewdict.keys())).astimezone(UTC)
            maxhour = g.user.tz.localize(
                max(viewdict.keys()) + timedelta(seconds=3599)
            ).astimezone(UTC)

            hourly_views = (
                db.session.query('hour', 'count')
                .from_statement(
                    db.text(
                        '''SELECT date_trunc(:interval, user_active_at.active_at AT TIME ZONE :timezone) AS hour, COUNT(DISTINCT(user_active_at.user_id)) AS count FROM user_active_at WHERE user_active_at.active_at >= :min AND user_active_at.active_at <= :max GROUP BY hour ORDER BY hour;'''
                    )
                )
                .params(interval=interval, timezone=timezone, min=minhour, max=maxhour)
            )

            for hour, count in hourly_views:
                viewdict[hour]['_site'] = count

            hourly_views = (
                db.session.query('hour', 'count')
                .from_statement(
                    db.text(
                        '''SELECT DATE_TRUNC(:interval, event_session.created_at AT TIME ZONE :timezone) AS hour, COUNT(DISTINCT(anon_user_id)) AS count FROM event_session WHERE event_session.anon_user_id IS NOT NULL AND event_session.created_at >= :min AND event_session.created_at <= :max GROUP BY hour ORDER BY hour'''
                    )
                )
                .params(interval=interval, timezone=timezone, min=minhour, max=maxhour)
            )

            for hour, count in hourly_views:
                viewdict[hour]['_site'] = viewdict[hour].setdefault('_site', 0) + count

        viewlist = []
        for slot in viewdict:
            row = [
                slot,
                viewdict[slot].get('_site', 0),
                viewdict[slot].get('_views', 0),
                viewdict[slot].get('_combined', 0),
            ]
            for name in action_names:
                row.append(viewdict[slot].get(name, 0))
            viewlist.append(row)

        viewlist.sort()  # Sorts by first column, the hour slot (datetime)
        for row in viewlist:
            row[0] = row[0].isoformat()

        outfile = StringIO()
        out = csv.writer(outfile, 'excel')
        out.writerow(['_hour', '_site', '_views', '_combined'] + action_names)
        out.writerows(viewlist)

        return outfile.getvalue(), 200, {'Content-Type': 'text/plain'}


AdminCampaignView.init_app(app)


@route('/admin/campaign/<campaign>/<action>')
class AdminCampaignActionView(UrlForView, InstanceLoader, ModelView):
    __decorators__ = [
        lastuser.requires_permission('siteadmin'),
        campaign_action_current_tab,
    ]
    model = CampaignAction
    route_model_map = {'action': 'name', 'campaign': 'parent.name'}

    @classmethodproperty
    def tabs(cls):  # noqa: N805
        return AdminCampaignList.tabs

    @property
    def form_header(self):
        return Markup(
            render_template(
                'campaign_action_edit_header.html.jinja2', campaign=self.obj.parent
            )
        )

    @route('edit', methods=['GET', 'POST'])
    def edit(self):
        form = CampaignActionForm(obj=self.obj)
        if form.validate_on_submit():
            form.populate_obj(self.obj)
            db.session.commit()
            flash("Edited campaign action ‘%s’" % self.obj.title, 'interactive')
            return redirect(self.obj.parent.url_for(), code=303)

        return render_form(
            form=form,
            title="Edit campaign action",
            submit="Save",
            formid="campaign_action_edit",
            cancel_url=self.obj.parent.url_for(),
            ajax=False,
        )

    @route('delete', methods=['GET', 'POST'])
    def delete(self):
        return render_delete_sqla(
            self.obj,
            db,
            title="Confirm delete",
            message="Delete campaign action '%s'?" % self.obj.title,
            success="You have deleted campaign action '%s'." % self.obj.title,
            next=self.obj.parent.url_for(),
        )

    @route('csv', methods=['GET', 'POST'])
    def csv(self):
        if self.obj.type not in ('Y', 'N', 'M', 'F'):
            abort(403)
        outfile = StringIO()
        out = csv.writer(outfile, 'excel')
        out.writerow(['fullname', 'username', 'email', 'phone'])
        for ua in self.obj.useractions:
            out.writerow(
                [ua.user.fullname, ua.user.username, ua.user.email, ua.user.phone]
            )
        return (
            outfile.getvalue(),
            200,
            {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename="%s-%s.csv"'
                % (make_name(self.obj.parent.title), make_name(self.obj.title)),
            },
        )


AdminCampaignActionView.init_app(app)


# --- Campaign actions --------------------------------------------------------


@app.route('/go/c/<campaign>/<action>', subdomain='<subdomain>')
@app.route('/go/c/<campaign>/<action>')
@load_models(
    (Campaign, {'name': 'campaign'}, 'campaign'),
    (CampaignAction, {'name': 'action', 'campaign': 'campaign'}, 'action'),
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
        return render_template(
            'campaign_action_response.html.jinja2',
            campaign=campaign,
            message=Markup("<p>This form timed out. Please try again</p>"),
        )

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
        return render_template(
            'campaign_action_response.html.jinja2', campaign=campaign, dismiss=True
        )

    action_name = request.form.get('action')
    action = CampaignAction.get(campaign, action_name)
    if not action:
        return render_template(
            'campaign_action_response.html.jinja2',
            campaign=campaign,
            message=Markup("<p>Unknown action selected</p>"),
        )
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
            return render_template(
                'campaign_action_response.html.jinja2',
                campaign=campaign,
                redirect=url_for(
                    'login',
                    next=request.referrer,
                    message="Please login so we can save your preferences",
                ),
            )

    if action.is_rsvp_type:
        for cua in campaign.useractions(g.user).values():
            if (
                cua.action != action
                and cua.action.group == action.group
                and cua.action.is_rsvp_type
            ):
                # If user changed their RSVP answer, delete old answer
                db.session.delete(cua)
        db.session.commit()
        return render_template(
            'campaign_action_response.html.jinja2',
            campaign=campaign,
            message=Markup(action.message),
        )
    elif action.type == CAMPAIGN_ACTION.DISMISS:
        view = campaign.view_for(g.user, g.anon_user)
        if view:
            view.dismissed = True
            db.session.commit()
        return render_template(
            'campaign_action_response.html.jinja2',
            campaign=campaign,
            dismiss=True,
            message=Markup(action.message),
        )
    elif action.type == CAMPAIGN_ACTION.FORM:
        # Render a form here
        db.session.commit()
        # TODO
        return render_template(
            'campaign_action_response.html.jinja2',
            campaign=campaign,
            message=Markup("To be implemented"),
        )
