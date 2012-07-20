#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
from flask.ext.mail import Mail
from flask.ext.assets import Environment, Bundle
import coaster.app

# First, make an app and config it

app = Flask(__name__, instance_relative_config=True)
mail = Mail()

# Second, setup assets
assets = Environment(app)
js = Bundle('js/libs/jquery-1.5.1.min.js',
            'js/libs/jquery.textarea-expander.js',
            'js/libs/tiny_mce/jquery.tinymce.js',
            'js/libs/jquery.form.js',
            'js/scripts.js',
            filters='jsmin', output='js/packed.js')

# Configure the app
def init_for(env):
    coaster.app.init_app(app, env)
    from hasjob.search import configure as search_configure
    from hasjob.uploads import configure as uploads_configure
    search_configure()
    uploads_configure()
    mail.init_app(app)
    assets.register('js_all', js)

# Third, after config, import the models and views

import hasjob.models
import hasjob.views
