#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
from flask.ext.mail import Mail
from flask.ext.assets import Environment, Bundle
from flask.ext.lastuser import LastUser
from baseframe import baseframe, networkbar_js, networkbar_css
import coaster.app

# First, make an app and config it

app = Flask(__name__, instance_relative_config=True)
app.register_blueprint(baseframe)
mail = Mail()
lastuser = LastUser()

# Second, setup assets
assets = Environment(app)
js = Bundle('js/libs/jquery-1.5.1.min.js',
            'js/libs/jquery.textarea-expander.js',
            'js/libs/tiny_mce/jquery.tinymce.js',
            'js/libs/jquery.form.js',
            'js/libs/jquery.oembed.js',
            networkbar_js,
            'js/scripts.js',
            filters='jsmin', output='js/packed.js')

css = Bundle(networkbar_css,
             'css/screen.css',
             filters='cssmin', output='css/packed.css')


# Configure the app
def init_for(env):
    coaster.app.init_app(app, env)
    from hasjob.search import configure as search_configure
    from hasjob.uploads import configure as uploads_configure
    search_configure()
    uploads_configure()
    mail.init_app(app)
    lastuser.init_app(app)
    assets.register('js_all', js)
    assets.register('css_all', css)

# Third, after config, import the models and views

import hasjob.models
import hasjob.views
