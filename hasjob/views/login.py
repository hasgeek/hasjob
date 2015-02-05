# -*- coding: utf-8 -*-

from sqlalchemy.exc import IntegrityError
from flask import g, Response, redirect, flash, session, request
from flask.ext.lastuser import signal_user_session_refreshed, signal_user_looked_up
from coaster.views import get_next_url

from .. import app, lastuser
from ..signals import signal_login, signal_logout
from ..models import db, AnonUser, Organization, UserActiveAt


@app.route('/login')
@lastuser.login_handler
def login():
    return {'scope': 'id email/* phone/* organizations/* teams/* notice/*'}


@app.route('/logout')
@lastuser.logout_handler
def logout():
    flash(u"You are now logged out", category='info')
    signal_logout.send(app, user=g.user)
    return get_next_url()


@app.route('/login/redirect')
@lastuser.auth_handler
def lastuserauth():
    Organization.update_from_user(g.user, db.session, make_user_profiles=False, make_org_profiles=False)
    signal_login.send(app, user=g.user)
    db.session.commit()
    return redirect(get_next_url())


@app.route('/login/notify', methods=['POST'])
@lastuser.notification_handler
def lastusernotify(user):
    Organization.update_from_user(user, db.session, make_user_profiles=False, make_org_profiles=False)
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


@signal_user_session_refreshed.connect
def track_user(user):
    db.session.add(UserActiveAt(user=user, board=g.board))
    try:
        db.session.commit()
    except IntegrityError:  # Small but not impossible chance we got two parallel signals
        db.session.rollback()


@signal_user_looked_up.connect
def load_anon_user(user):
    """
    1. If there's g.user and session['anon_user'], it loads that anon_user and tags with user=g.user, then removes anon
    2. If there's no g.user and no session['anon_user'], sets session['anon_user'] = 'test'
    3. If there's no g.user and there is session['anon_user'] = 'test', creates a new anon user, then saves to cookie
    4. If there's no g.user and there is session['anon_user'] != 'test', loads g.anon_user
    """
    g.anon_user = None  # Could change below
    g.event_data = {}   # Views can add data to the current pageview event

    if request.endpoint in ('static', 'baseframe.static'):
        # Don't bother loading an anon user when rendering static resources
        return

    if user:
        if 'au' in session and session['au'] != 'test' and session['au'] is not None:
            anon_user = AnonUser.query.get(session['au'])
            if anon_user:
                anon_user.user = user
        session.pop('au', None)
    else:
        if not session.get('au'):
            session['au'] = 'test'
        elif session['au'] == 'test':  # This client sent us back our test cookie, so set a real value now
            g.anon_user = AnonUser()
            db.session.add(g.anon_user)
        else:
            anon_user = AnonUser.query.get(session['au'])
            if not anon_user:
                # XXX: We got a fake value? This shouldn't happen
                session['au'] = 'test'  # Try again
            else:
                g.anon_user = anon_user
    db.session.commit()
    if g.anon_user:
        session['au'] = g.anon_user.id
        session.permanent = True
