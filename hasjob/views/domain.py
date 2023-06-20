from flask import abort, flash, g

from baseframe import _
from baseframe.forms import render_form, render_redirect

from .. import app, lastuser
from ..forms import DomainForm
from ..models import Domain, db


@app.route('/<domain>/edit', methods=['GET', 'POST'])
def domain_edit(domain):
    obj = Domain.get(domain)
    if not obj:
        abort(404)
    if not (lastuser.has_permission('siteadmin') or obj.editor_is(g.user)):
        abort(403)
    form = DomainForm(obj=obj)
    if form.validate_on_submit():
        form.populate_obj(obj)
        db.session.commit()
        flash(_("Your changes have been saved"), 'success')
        return render_redirect(obj.url_for(), code=303)
    return render_form(
        form=form, title="Edit organization profile", cancel_url=obj.url_for()
    )
