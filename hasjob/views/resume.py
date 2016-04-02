# -*- coding: utf-8 -*-

from flask import g, abort
from coaster.views import render_with
from baseframe import csrf
from ..models import User, JobApplication
from .. import app, lastuser


@csrf.exempt
@app.route('/@<username>', subdomain='<subdomain>')
@app.route('/@<username>')
@render_with({'text/html': 'resume.html'}, json=True)
@lastuser.requires_login
def resume(username):
    user = User.get(username=username)
    if user is None:
        user = User.get(userid=username)
    if user is None:
        abort(404)

    # We have a user. Is the currently logged in user
    # authorised to see this?
    view_allowed = False
    # Is the user viewing their own profile?
    if g.user == user:
        view_allowed = True
    else:
        # No? Is the user a potential employer?
        for appl in user.job_applications.options(*JobApplication._defercols):
            if appl.jobpost.admin_is(g.user):
                view_allowed = True
                break
    if not view_allowed:
        abort(403)

    return {'user': user, 'resume': user.resume}
