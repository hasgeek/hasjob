#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
from flask.ext.mail import Mail
from flask.ext.lastuser import Lastuser
from baseframe import baseframe, assets, Version
import coaster.app
from ._version import __version__


# First, make an app and config it

app = Flask(__name__, instance_relative_config=True)
mail = Mail()
lastuser = Lastuser()

# Second, setup assets
version = Version(__version__)
assets['hasjob.js'][version] = 'js/scripts.js'
assets['hasjob.css'][version] = 'css/screen.css'

# Third, after config, import the models and views

import hasjob.models
import hasjob.views
from hasjob.models import db


# Configure the app
def init_for(env):
    coaster.app.init_app(app, env)
    baseframe.init_app(app, requires=['jquery.textarea-expander', 
        'jquery.tinymce', 'jquery.form', 'jquery.cookie', 'jquery.sparkline', 'baseframe-networkbar', 'hasjob'
        ])
    app.assets.register('js_tinymce', assets.require('tiny_mce.js>=3.5.0,<4.0.0'))
    from hasjob.search import configure as search_configure
    from hasjob.uploads import configure as uploads_configure
    search_configure()
    uploads_configure()
    mail.init_app(app)
    lastuser.init_app(app)
