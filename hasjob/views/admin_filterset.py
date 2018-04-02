# -*- coding: utf-8 -*-

from flask import flash, g, abort
from coaster.views import route, viewdata, UrlForView, ModelView
from coaster.auth import current_auth
from baseframe import __
from baseframe.forms import render_form, render_redirect
from .. import app
from ..models import db, Filterset
from ..forms import FiltersetForm


@route('/f')
class AdminFiltersetView(UrlForView, ModelView):
    model = Filterset

    def loader(self, kwargs):
        if 'name' in kwargs:
            return Filterset.get(g.board, kwargs.get('name'))

    @route('new', methods=['GET', 'POST'])
    @viewdata(title=__("New"))
    def new(self):
        if 'edit-filterset' not in g.board.current_permissions:
            abort(403)

        form = FiltersetForm(parent=g.board)
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
                flash(u"There already exists a filterset with the selected criteria", 'interactive')
        return render_form(form=form, title=u"Create a filterset…", submit="Create",
            formid="filterset_new", ajax=False)

    @route('<name>/edit', methods=['GET', 'POST'])
    @viewdata(title=__("Edit"))
    def edit(self, **kwargs):
        if 'edit-filterset' not in g.board.current_permissions:
            abort(403)

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
