# -*- coding: utf-8 -*-

from flask import flash, g
from coaster.views import route, viewdata, UrlForView, InstanceLoader, ModelView
from baseframe import __
from baseframe.forms import render_form, render_redirect
from .. import app, lastuser
from ..models import db, Filterset
from ..forms import FiltersetForm
from .admin import AdminView


@route('/f')
class AdminFilterset(AdminView):
    __decorators__ = [lastuser.requires_permission('siteadmin')]

    @route('new', methods=['GET', 'POST'])
    @viewdata(tab=True, index=4, title=__("New"))
    def new(self):
        form = FiltersetForm(board=g.board)
        if form.validate_on_submit():
            filterset = Filterset(board=g.board, title=form.title.data)
            form.populate_obj(filterset)
            try:
                db.session.add(filterset)
                db.session.commit()
                flash(u"Created a filterset", 'success')
                return render_redirect(filterset.url_for(), code=303)
            except ValueError:
                db.session.rollback()
                flash(u"There already exists a filterset with the selected criteria", 'failure')
        return render_form(form=form, title=u"Create a filterset…", submit="Create",
            formid="filterset_new", ajax=False)

AdminFilterset.init_app(app)


@route('/f/<name>')
class AdminFiltersetView(UrlForView, InstanceLoader, ModelView):
    __decorators__ = [lastuser.requires_permission('siteadmin')]
    model = Filterset

    def loader(self, kwargs):
        return Filterset.get(g.board, kwargs.get('name'))

    @route('edit', methods=['GET', 'POST'])
    @viewdata(tab=True, index=4, title=__("Edit"))
    def edit(self, **kwargs):
        form = FiltersetForm(obj=self.obj)
        if form.validate_on_submit():
            form.populate_obj(self.obj)
            try:
                db.session.commit()
                flash(u"Updated filterset", 'success')
                return render_redirect(self.obj.url_for(), code=303)
            except ValueError:
                db.session.rollback()
                flash(u"There already exists a filterset with the selected criteria", 'interactive')
        return render_form(form=form, title=u"Edit filterset…", submit="Update",
            formid="filterset_edit", ajax=False)


AdminFiltersetView.init_app(app)
