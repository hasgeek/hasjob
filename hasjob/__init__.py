#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
from flask.ext.assets import Bundle
from flask.ext.rq import RQ
from flask.ext.mail import Mail
from flask.ext.redis import Redis
from flask.ext.lastuser import Lastuser
from flask.ext.lastuser.sqlalchemy import UserManager
from baseframe import baseframe, assets, Version
import coaster.app
from ._version import __version__


# First, make an app and config it

app = Flask(__name__, instance_relative_config=True, static_folder=None)
app.static_folder = 'static'
mail = Mail()
lastuser = Lastuser()
redis_store = Redis()

# Second, setup assets
version = Version(__version__)
assets['hasjob.js'][version] = 'js/app.js'
assets['hasjob.css'][version] = 'css/app.css'

# Third, after config, import the models and views

from . import models, views  # NOQA
from .models import db


# Configure the app
def init_for(env):
    coaster.app.init_app(app, env)
    RQ(app)

    baseframe.init_app(app, requires=['hasjob'],
        ext_requires=['baseframe-bs3',
            ('jquery.autosize', 'jquery.sparkline', 'jquery.liblink', 'jquery.wnumb', 'jquery.nouislider', 'jquery.appear'),
            'baseframe-firasans',
            'fontawesome>=4.3.0'],
        enable_csrf=True)
    # TinyMCE has to be loaded by itself, unminified, or it won't be able to find its assets
    app.assets.register('js_tinymce', assets.require('!jquery.js', 'tinymce.js>=4.0.0', 'jquery.tinymce.js>=4.0.0'))
    app.assets.register('css_editor', Bundle('css/editor.css',
        filters=['cssrewrite', 'cssmin'], output='css/editor.packed.css'))

    from hasjob.uploads import configure as uploads_configure
    from hasjob.search import configure as search_configure
    uploads_configure()
    search_configure()
    mail.init_app(app)
    redis_store.init_app(app)
    lastuser.init_app(app)
    lastuser.init_usermanager(UserManager(db, models.User, models.Team))
