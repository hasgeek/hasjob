# -*- coding: utf-8 -*-

from flask import redirect, url_for
from hasjob import app


@app.route('/type/')
@app.route('/category/')
@app.route('/view/')
@app.route('/edit/')
@app.route('/confirm/')
@app.route('/withdraw/')
@app.route('/in/')
@app.route('/at/')
@app.route('/by/')
@app.route('/index.php')
def root_paths():
    return redirect(url_for('index'), code=302)


ALLOWED_TAGS = [
    'strong',
    'em',
    'p',
    'ol',
    'ul',
    'li',
    'br',
    'a',
]

from . import (index, error_handling, helper, listing, location, static, login, board, kiosk, campaign,  # NOQA
    admindash, domain, bid)
