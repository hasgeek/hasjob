#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
from flask.ext.mail import Mail
from flask.ext.lastuser import LastUser
from baseframe import baseframe, Version
from baseframe import assets as assets
import coaster.app
from ._version import __version__


# First, make an app and config it

app = Flask(__name__, instance_relative_config=True)
mail = Mail()
lastuser = LastUser()

# Second, setup assets
version = Version(__version__)
assets['jquery-ui.js'][version] = 'js/libs/jquery-ui-1.10.0.custom.js'
assets['jQRangeSlider.js'][version] = 'js/libs/jQRangeSlider-min.js'
assets['jquery.textarea.expander.js'][version] = 'js/libs/jquery.textarea-expander.js'
assets['jquery.oembed.js'][version] = 'js/libs/jquery.oembed.js'
assets['hasjob.js'][version] = 'js/scripts.js'
assets['hasjob.css'][version] = 'css/screen.css'
assets['jquery-ui.css'][version] = 'css/jquery-ui.css'
assets['range-slider.css'][version] = 'css/range-slider.css'

# Third, after config, import the models and views

import hasjob.models
import hasjob.views
from hasjob.models import db


# Configure the app
def init_for(env):
    coaster.app.init_app(app, env)
    from hasjob.search import configure as search_configure
    from hasjob.uploads import configure as uploads_configure
    search_configure()
    uploads_configure()
    mail.init_app(app)
    lastuser.init_app(app)
    baseframe.init_app(app, requires=[
        'jquery-ui', 'jQRangeSlider',
        'jquery.textarea.expander', 'jquery.tinymce', 'jquery.form',
        'jquery.oembed', 'baseframe-networkbar', 'range-slider', 'hasjob',
        ])
