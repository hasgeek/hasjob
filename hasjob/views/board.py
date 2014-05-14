# -*- coding: utf-8 -*-

from flask import g, abort, Markup, flash, url_for, redirect
from coaster.views import load_model
from baseframe.forms import render_form, render_delete_sqla, render_redirect
from .. import app, lastuser
from ..models import db, Board
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

    g.board = Board.query.filter_by(name=subdomain or u'www').first()
    if subdomain and g.board is None:
        abort(404)


@app.url_defaults
def add_subdomain_parameter(endpoint, values):
    if app.url_map.is_endpoint_expecting(endpoint, 'subdomain'):
        if 'subdomain' not in values:
            values['subdomain'] = g.board.name if g.board else None


@app.route('/board', methods=['GET', 'POST'])
@lastuser.requires_login
def board_new():
    form = BoardForm()
    form.userid.choices = [(g.user.userid, g.user.fullname)] + [(o['userid'], o['title']) for o in g.user.organizations_owned()]
    if form.validate_on_submit():
        board = Board()
        form.populate_obj(board)
        if not board.name:
            board.make_name()
        db.session.add(board)
        db.session.commit()
        flash(u"Created a board for %s" % board.title, 'success')
        return render_redirect(url_for('board_edit', board=board.name), code=303)
    return render_form(form=form, title=u"Create a board…", submit="Next",
        formid="board_new", cancel_url=url_for('index'), ajax=False)


@app.route('/board/<board>/edit', methods=['GET', 'POST'])
@lastuser.requires_login
@load_model(Board, {'name': 'board'}, 'board', permission='edit')
def board_edit(board):
    form = BoardForm(obj=board)
    form.userid.choices = [(g.user.userid, g.user.fullname)] + [(o['userid'], o['title']) for o in g.user.organizations_owned()]
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
