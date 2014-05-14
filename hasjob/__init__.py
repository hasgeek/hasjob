#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
from flask.ext.rq import RQ
from flask.ext.mail import Mail
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

# Second, setup assets
version = Version(__version__)
assets['hasjob.js'][version] = 'js/app.js'
assets['hasjob.css'][version] = 'css/app.css'

# Third, after config, import the models and views

from . import models, views
from .models import db


# Configure the app
def init_for(env):
    coaster.app.init_app(app, env)
    RQ(app)

    baseframe.init_app(app, requires=['hasjob'],
        ext_requires=['baseframe-bs3', ('jquery.textarea-expander', 'jquery.cookie',
        'jquery.sparkline','jquery.nouislider'), ('firasans', 'baseframe-firasans'), 'fontawesome>=4.0.0'])
    app.assets.register('js_tinymce', assets.require('tinymce.js>=4.0.0'))

    from hasjob.uploads import configure as uploads_configure
    from hasjob.search import configure as search_configure
    uploads_configure()
    search_configure()
    mail.init_app(app)
    lastuser.init_app(app)
    lastuser.init_usermanager(UserManager(db, models.User))
