# -*- coding: utf-8 -*-

from sqlalchemy.exc import IntegrityError
from flask import g, Response, redirect, flash
from flask_lastuser import signal_user_session_refreshed
from coaster.views import get_next_url

from .. import app, lastuser
from ..signals import signal_login, signal_logout
from ..models import db, UserActiveAt


@app.route('/500')
def error500():
    raise Exception("Something b0rked")


@app.route('/login')
@lastuser.login_handler
def login():
    return {'scope': 'id email/* phone/* organizations/*'}


@app.route('/logout')
@lastuser.logout_handler
def logout():
    flash("You are now logged out", category='info')
    signal_logout.send(app, user=g.user)
    return get_next_url()


@app.route('/login/redirect')
@lastuser.auth_handler
def lastuserauth():
    signal_login.send(app, user=g.user)
    db.session.commit()
    return redirect(get_next_url())


@app.route('/login/notify', methods=['POST'])
@lastuser.notification_handler
def lastusernotify(user):
    db.session.commit()


@lastuser.auth_error_handler
def lastuser_error(error, error_description=None, error_uri=None):
    if error == 'access_denied':
        flash("You denied the request to login", category='error')
        return redirect(get_next_url())
    return Response("Error: %s\n"
                    "Description: %s\n"
                    "URI: %s" % (error, error_description, error_uri),
                    mimetype="text/plain")


@signal_user_session_refreshed.connect
def track_user(user):
    db.session.add(UserActiveAt(user=user, board=g.board))
    try:
        db.session.commit()
    except IntegrityError:  # Small but not impossible chance we got two parallel signals
        db.session.rollback()
