# -*- coding: utf-8 -*-

from flask import g, session, request, redirect, url_for, flash, Response, abort
from coaster.utils import getbool
from .. import app
from ..models import JobType, JobCategory
from .helper import getposts


@app.route('/admin/kiosk', subdomain='<subdomain>')
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
        for item in JobType.query.filter_by(public=True).all():
            lines.append(url_for('browse_by_type', name=item.name))

        for item in JobCategory.query.filter_by(public=True).all():
            lines.append(url_for('browse_by_category', name=item.name))

        # Posts
        for post in getposts(None, showall=True):
            lines.append(post.url_for())

        # Static resources
        lines.append(url_for('static', filename='img/logo-star.png'))
        lines.append(url_for('opensearch'))
        lines.append(url_for('static', filename='css/editor.css'))

        lines.append(url_for('baseframe.static', filename='js/modernizr.min.js'))

        # Assets
        lines.extend(app.assets['js_all'].urls())
        lines.extend(app.assets['css_all'].urls())

        # External resources
        lines.append('//fonts.googleapis.com/css?family=McLaren|Source+Sans+Pro:400,600')
        if app.config.get('TYPEKIT_CODE'):
            lines.append('//use.typekit.com/' + app.config['TYPEKIT_CODE'] + '.js')

        # Exclude everything else
        lines.append('NETWORK:')
        lines.append('*')

        return Response('\r\n'.join(lines),
            content_type='text/cache-manifest')
    else:
        abort(410)
