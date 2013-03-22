#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
from flask.ext.mail import Mail
from flask.ext.lastuser import LastUser
from flask.ext.assets import Environment
from baseframe import baseframe, Version
from baseframe import assets as assets_registry
import coaster.app
from ._version import __version__


# First, make an app and config it

app = Flask(__name__, instance_relative_config=True)
app.register_blueprint(baseframe)
mail = Mail()
lastuser = LastUser()

# Second, setup assets
version = Version(__version__)
assets = Environment(app)
assets_registry['jquery-ui.js'][version] = 'js/libs/jquery-ui-1.10.0.custom.js'
assets_registry['jQRangeSlider.js'][version] = 'js/libs/jQRangeSlider-min.js'
assets_registry['jquery.textarea.expander.js'][version] = 'js/libs/jquery.textarea-expander.js'
assets_registry['jquery.oembed.js'][version] = 'js/libs/jquery.oembed.js'
assets_registry['hasjob.js'][version] = 'js/scripts.js'
assets_registry['hasjob.css'][version] = 'css/screen.css'
assets_registry['jquery-ui.css'][version] = 'css/jquery-ui.css'
assets_registry['range-slider.css'][version] = 'css/range-slider.css'

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
    assets.register('js_all', assets_registry.require('jquery.js', 'jquery-ui.js', 'jQRangeSlider.js',
        'jquery.textarea.expander.js', 'jquery.tinymce.js', 'jquery.form.js',
        'jquery.oembed.js', 'baseframe-networkbar.js', 'range-slider.js', 'hasjob.js'))
    assets.register('css_all', assets_registry.require('baseframe-networkbar.css',
                    'range-slider.css', 'jquery-ui.css','hasjob.css'))