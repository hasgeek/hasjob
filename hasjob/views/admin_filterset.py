from flask import abort, flash, g

from baseframe import __
from baseframe.forms import render_form, render_redirect
from coaster.views import ModelView, UrlForView, route, viewdata

from .. import app
from ..forms import FiltersetForm
from ..models import Filterset, db


@route('/f')
class AdminFiltersetView(UrlForView, ModelView[Filterset]):

    route_model_map = {'name': 'name'}

    def loader(self, name=None):
        if name:
            return Filterset.get(g.board, name)

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
                flash("Created a filterset", 'success')
                return render_redirect(filterset.url_for(), code=303)
            except ValueError:
                db.session.rollback()
                flash(
                    "There already exists a filterset with the selected criteria",
                    'interactive',
                )
        return render_form(
            form=form,
            title="Create a filterset…",
            submit="Create",
            formid="filterset_new",
            ajax=False,
        )

    @route('<name>/edit', methods=['GET', 'POST'])
    @viewdata(title=__("Edit"))
    def edit(self):
        if 'edit-filterset' not in g.board.current_permissions:
            abort(403)

        form = FiltersetForm(obj=self.obj)
        if form.validate_on_submit():
            form.populate_obj(self.obj)
            try:
                db.session.commit()
                flash("Updated filterset", 'success')
                return render_redirect(self.obj.url_for(), code=303)
            except ValueError:
                db.session.rollback()
                flash(
                    "There already exists a filterset with the selected criteria",
                    'interactive',
                )
        return render_form(
            form=form,
            title="Edit filterset…",
            submit="Update",
            formid="filterset_edit",
            ajax=False,
        )


AdminFiltersetView.init_app(app)
