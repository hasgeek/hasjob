# -*- coding: utf-8 -*-

from flask import g, abort, flash, url_for, redirect, request
from coaster.views import load_model, load_models
# from baseframe import dogpile
from baseframe.forms import render_form, render_delete_sqla, render_redirect
from .. import app, lastuser
from ..models import db, Board, JobPost
from ..forms import BoardForm


@app.url_value_preprocessor
def remove_subdomain_parameter(endpoint, values):
    if values:
        subdomain = values.pop('subdomain', None)
    else:
        subdomain = None

    if subdomain and subdomain == app.config.get('STATIC_SUBDOMAIN', 'static'):
        g.board = None
        return  # Don't bother processing for static domain

    if request.endpoint in ('static', 'baseframe.static'):
        g.board = None
        return  # Don't bother processing for static endpoints either (only applies in dev)

    g.board = Board.query.filter_by(name=subdomain or u'www').first()
    if subdomain and g.board is None:
        abort(404)


@app.url_defaults
def add_subdomain_parameter(endpoint, values):
    if app.url_map.is_endpoint_expecting(endpoint, 'subdomain'):
        if 'subdomain' not in values:
            values['subdomain'] = g.board.name if 'board' in g and g.board.not_root else None


@app.route('/board', methods=['GET', 'POST'])
@lastuser.requires_login
def board_new():
    form = BoardForm()
    if 'siteadmin' not in lastuser.permissions():
        # Allow only siteadmins to set this field
        del form.options.form.require_pay
    form.userid.choices = g.user.allowner_choices()
    if form.validate_on_submit():
        board = Board()
        form.populate_obj(board)
        if not board.name:
            board.make_name()
        db.session.add(board)
        if 'add' in request.args:
            post = JobPost.get(request.args['add'])
            if post:
                board.add(post)
        db.session.commit()
        flash(u"Created a job board named %s" % board.title, 'success')
        return render_redirect(url_for('board_view', board=board.name), code=303)
    return render_form(form=form, title=u"Create a job board…", submit="Next",
        message=u"Make your own job board with just the jobs you want to showcase. "
            "Your board will appear as a subdomain",
        formid="board_new", cancel_url=url_for('index'), ajax=False)


@app.route('/edit', subdomain='<subdomain>')
def board_edit_subdomain():
    return redirect(url_for('board_edit', board=g.board.name))


@app.route('/board/<board>/edit', methods=['GET', 'POST'])
@lastuser.requires_login
@load_model(Board, {'name': 'board'}, 'board', permission=('edit', 'siteadmin'), addlperms=lastuser.permissions)
def board_edit(board):
    form = BoardForm(obj=board)
    if 'siteadmin' not in lastuser.permissions():
        # Allow only siteadmins to set this field
        del form.options.form.require_pay
    form.userid.choices = g.user.allowner_choices()
    if board.userid not in g.user.allowner_ids():
        # We could get here if we are a siteadmin editing someone's board
        form.userid.choices.insert(0, (board.userid, u"(Preserve existing owner)"))
    if form.validate_on_submit():
        form.populate_obj(board)
        if not board.name:
            board.make_name()
        db.session.commit()
        flash(u"Edited board settings.", 'success')
        return render_redirect(url_for('index', subdomain=board.name), code=303)

    return render_form(form=form, title=u"Edit board settings", submit="Save",
        formid="board_edit", cancel_url=url_for('index', subdomain=board.name), ajax=False)


@app.route('/board/<board>/delete', methods=['GET', 'POST'])
@lastuser.requires_login
@load_model(Board, {'name': 'board'}, 'board', permission='delete')
def board_delete(board):
    return render_delete_sqla(board, db, title=u"Confirm delete",
        message=u"Delete board '%s'?" % board.title,
        success=u"You have deleted board '%s'." % board.title,
        next=url_for('index'))


@app.route('/board/<board>')
def board_view(board):
    return redirect(url_for('index', subdomain=board))


@app.route('/board/<board>/add/<hashid>')
@lastuser.requires_login
@load_models(
    (Board, {'name': 'board'}, 'board'),
    (JobPost, {'hashid': 'hashid'}, 'jobpost'),
    permission='add')
# FIXME: Should be a POST request
def board_add(board, jobpost):
    board.add(jobpost)
    db.session.commit()
    # cache bust
    # dogpile.invalidate_region('hasjob_index')
    flash(u"You’ve added this job to %s" % board.title, 'interactive')
    return redirect(jobpost.url_for(subdomain=board.name))
