# -*- coding: utf-8 -*-

from collections import OrderedDict
from flask import g, redirect, abort, url_for
from baseframe import _
from baseframe.forms import render_form, render_delete_sqla
from ..models import db, Location, JobLocation, JobPost
from ..forms import NewLocationForm, EditLocationForm
from .. import app, lastuser
from ..extapi import location_geodata


@app.route('/in/new', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/in/new', methods=['GET', 'POST'])
def location_new():
    if not (lastuser.has_permission('siteadmin') or (g.board and g.board.owner_is(g.user))):
        abort(403)
    geonames = OrderedDict([(r.geonameid, None) for r in
        db.session.query(
            JobLocation.geonameid, db.func.count(JobLocation.geonameid).label('count')
            ).join(JobPost).filter(
                JobPost.state.LISTED,
                ~JobLocation.geonameid.in_(db.session.query(Location.id).filter(Location.board == g.board))
            ).group_by(JobLocation.geonameid).order_by(db.text('count DESC')).limit(100)])
    data = location_geodata(list(geonames.keys()))
    for row in list(data.values()):
        geonames[row['geonameid']] = row
    choices = [('%s/%s' % (row['geonameid'], row['name']), row['picker_title']) for row in list(geonames.values())]
    form = NewLocationForm()
    form.geoname.choices = choices

    if form.validate_on_submit():
        geonameid, name = form.geoname.data.split('/', 1)
        geonameid = int(geonameid)
        title = geonames[geonameid]['use_title']
        location = Location(id=geonameid, board=g.board, name=name, title=title)
        db.session.add(location)
        db.session.commit()
        return redirect(location.url_for('edit'), code=303)

    return render_form(form=form, title=_("Add a location"), submit=_("Next"))


# This view does not use load_model because of the dependency on g.board, which
# load_model does not currently support
@app.route('/in/<name>/edit', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/in/<name>/edit', methods=['GET', 'POST'])
def location_edit(name):
    if not (lastuser.has_permission('siteadmin') or (g.board and g.board.owner_is(g.user))):
        abort(403)
    location = Location.get(name, g.board)
    if not location:
        abort(404)

    form = EditLocationForm(obj=location)
    if form.validate_on_submit():
        form.populate_obj(location)
        db.session.commit()
        return redirect(location.url_for(), code=303)
    return render_form(form=form, title=_("Edit location"))


# This view does not use load_model because of the dependency on g.board, which
# load_model does not currently support
@app.route('/in/<name>/delete', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/in/<name>/delete', methods=['GET', 'POST'])
def location_delete(name):
    if not (lastuser.has_permission('siteadmin') or (g.board and g.board.owner_is(g.user))):
        abort(403)
    location = Location.get(name, g.board)
    if not location:
        abort(404)

    return render_delete_sqla(location, db, title=_("Confirm delete"),
        message=_("Delete location ‘{title}’?").format(title=location.title),
        success=_("You have deleted location ‘{title}’.").format(title=location.title),
        next=url_for('index'), cancel_url=location.url_for())
