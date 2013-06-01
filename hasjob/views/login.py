# -*- coding: utf-8 -*-

from flask import Response, redirect, flash
from flask.ext.lastuser.sqlalchemy import UserManager
from coaster.views import get_next_url

from hasjob import app, lastuser
from hasjob.models import db, User


lastuser.init_usermanager(UserManager(db, User))


@app.route('/login')
@lastuser.login_handler
def login():
    return {'scope': 'id email organizations'}


@app.route('/logout')
@lastuser.logout_handler
def logout():
    flash(u"You are now logged out", category='info')
    return get_next_url()


@app.route('/login/redirect')
@lastuser.auth_handler
def lastuserauth():
    # Save the user object
    db.session.commit()
    return redirect(get_next_url())


@app.route('/login/notify')
@lastuser.notification_handler
def lastusernotify(user):
    # Save the user object
    db.session.commit()


@lastuser.auth_error_handler
def lastuser_error(error, error_description=None, error_uri=None):
    if error == 'access_denied':
        flash("You denied the request to login", category='error')
        return redirect(get_next_url())
    return Response(u"Error: %s\n"
                    u"Description: %s\n"
                    u"URI: %s" % (error, error_description, error_uri),
                    mimetype="text/plain")
