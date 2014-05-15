# -*- coding: utf-8 -*-

from flask import g, session, request, redirect, url_for, flash, Response, abort
from coaster.utils import getbool
from .. import app
from ..models import JobType, JobCategory
from .helper import getposts


@app.before_request
def kiosk_mode_flag():
    if session.get('kiosk'):
        g.kiosk = True
    else:
        g.kiosk = False
    g.peopleflow_url = session.get('peopleflow')


@app.route('/admin/kiosk')
def kiosk_mode():
    if getbool(request.args.get('enable')):
        session['kiosk'] = True
        session['peopleflow'] = request.args.get('url')
        session.permanent = True
        flash("Kiosk mode has been enabled", 'success')
    else:
        session.pop('kiosk', None)
        session.pop('peopleflow', None)
        session.permanent = False
        flash("Kiosk mode has been disabled", 'success')
    return redirect(url_for('index'))


@app.route('/kiosk.appcache', subdomain='<subdomain>')
@app.route('/kiosk.appcache')
def kiosk_manifest():

    if g.kiosk:
        lines = []
        lines.append('CACHE MANIFEST')

        lines.append('CACHE:')
        # Home page
        lines.append('/')

        # Type/category pages
        for item in JobType.query.all():
            lines.append(url_for('browse_by_type', name=item.name))

        for item in JobCategory.query.all():
            lines.append(url_for('browse_by_category', name=item.name))

        # Posts
        for post in getposts(None, showall=True):
            lines.append(url_for('jobdetail', hashid=post.hashid))

        # Static resources
        lines.append(url_for('static', filename='favicon.ico'))
        lines.append(url_for('static', filename='img/favicon.ico'))
        lines.append(url_for('static', filename='img/logo-star.png'))
        lines.append(url_for('static', filename='opensearch.xml'))
        lines.append(url_for('static', filename='css/editor.css'))

        lines.append(url_for('baseframe.static', filename='js/modernizr.min.js'))

        # Assets
        lines.extend(app.assets['js_all'].urls())
        lines.extend(app.assets['css_all'].urls())

        # External resources
        lines.append('//fonts.googleapis.com/css?family=Walter+Turncoat|McLaren|Source+Sans+Pro:400,600')
        if app.config.get('TYPEKIT_CODE'):
            lines.append('//use.typekit.com/' + app.config['TYPEKIT_CODE'] + '.js')

        # Exclude everything else
        lines.append('NETWORK:')
        lines.append('*')

        return Response(u'\r\n'.join(lines),
            content_type='text/cache-manifest')
    else:
        abort(410)
