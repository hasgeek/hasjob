#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
from flask.ext.rq import RQ
from flask.ext.mail import Mail
from flask.ext.lastuser import Lastuser
from flask.ext.lastuser.sqlalchemy import UserManager
from baseframe import baseframe, assets, Version, cache
import coaster.app
from ._version import __version__


# First, make an app and config it

app = Flask(__name__, instance_relative_config=True, static_folder=None)
app.static_folder = 'static'
mail = Mail()
lastuser = Lastuser()

# Second, setup assets
version = Version(__version__)
assets['hasjob.js'][version] = 'js/scripts.js'
assets['hasjob.css'][version] = 'css/screen.css'

# Third, after config, import the models and views

from . import models, views
from .models import db


# Configure the app
def init_for(env):
    coaster.app.init_app(app, env)
    RQ(app)
    if app.config.get('SERVER_NAME'):
        subdomain = app.config.get('STATIC_SUBDOMAIN', 'static')
    else:
        subdomain = None
    app.add_url_rule('/static/<path:filename>', endpoint='static',
        view_func=app.send_static_file, subdomain=subdomain)
    baseframe.init_app(app, requires=['hasjob'],
        ext_requires=[('jquery.textarea-expander', 'jquery.tinymce', 'jquery.form', 'jquery.cookie',
        'select2', 'jquery.sparkline','jquery.nouislider'), 'firasans', 'baseframe-networkbar'])
    app.assets.register('js_tinymce', assets.require('tiny_mce.js>=3.5.0,<4.0.0'))
    if subdomain:
        # The /_baseframe path has to be under the current domain because TinyMCE
        # doesn't like loading from a subdomain, but we also need access to /_baseframe
        # in the static subdomain for other assets (potentially obsoleted by ext_requires)
        app.add_url_rule(baseframe.static_url_path + '/<path:filename>',
            view_func=baseframe.send_static_file,
            endpoint='baseframe_static', subdomain=subdomain)

    from hasjob.uploads import configure as uploads_configure
    from hasjob.search import configure as search_configure
    uploads_configure()
    search_configure()
    mail.init_app(app)
    lastuser.init_app(app)
    lastuser.init_usermanager(UserManager(db, models.User))
