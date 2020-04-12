# -*- coding: utf-8 -*-

from flask import redirect, url_for

from .. import app
from . import (  # NOQA: F401
    admin_filterset,
    admindash,
    api,
    board,
    campaign,
    domain,
    error_handling,
    helper,
    index,
    kiosk,
    listing,
    location,
    login,
    static,
)


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
