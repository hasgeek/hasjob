# -*- coding: utf-8 -*-

from collections import OrderedDict
from datetime import datetime
from flask import redirect, abort
from baseframe.forms import render_form
from ..models import db, agelimit, Location, JobLocation, JobPost, POSTSTATUS
from ..forms import NewLocationForm, EditLocationForm
from .. import app, lastuser
from .helper import location_geodata


@app.route('/in/new', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
def location_new():
    now = datetime.utcnow()
    geonames = OrderedDict([(r.geonameid, None) for r in
        db.session.query(JobLocation.geonameid, db.func.count(JobLocation.geonameid).label('count')).join(
            JobPost).filter(JobPost.status.in_(POSTSTATUS.LISTED), JobPost.datetime > now - agelimit,
            ~JobLocation.geonameid.in_(db.session.query(Location.id))
            ).group_by(JobLocation.geonameid).order_by('count DESC').limit(100)])
    data = location_geodata(geonames.keys())
    for row in data:
        geonames[row['geonameid']] = row
    choices = [('%s/%s' % (row['geonameid'], row['name']), row['picker_title']) for row in data]
    form = NewLocationForm()
    form.geoname.choices = choices

    if form.validate_on_submit():
        geonameid, name = form.geoname.data.split('/', 1)
        geonameid = int(geonameid)
        title = geonames[geonameid]['short_title']
        location = Location(id=geonameid, name=name, title=title)
        db.session.add(location)
        db.session.commit()
        return redirect(location.url_for('edit'), code=303)

    return render_form(form=form, title="Add a location")


@app.route('/in/<name>/edit', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
def location_edit(name):
    location = Location.get(name)
    if not location:
        abort(404)

    form = EditLocationForm(obj=location)
    if form.validate_on_submit():
        form.populate_obj(location)
        db.session.commit()
        return redirect(location.url_for(), code=303)
    return render_form(form=form, title="Edit location")
