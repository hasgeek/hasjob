# -*- coding: utf-8 -*-

from flask import g, session, request, redirect, url_for, flash
from coaster.utils import getbool
from .. import app


@app.before_request
def kiosk_mode_flag():
    if session.get('kiosk'):
        g.kiosk = True
    else:
        g.kiosk = False


@app.route('/admin/kiosk')
def kiosk_mode():
    if getbool(request.args.get('enable')):
        session['kiosk'] = True
        session.permanent = True
        flash("Kiosk mode has been enabled", 'success')
    else:
        session.pop('kiosk', None)
        session.permanent = False
        flash("Kiosk mode has been disabled", 'success')
    return redirect(url_for('index'))
