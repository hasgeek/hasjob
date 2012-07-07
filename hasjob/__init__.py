#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import environ
from flask import Flask
from flask.ext.mail import Mail
from flask.ext.assets import Environment, Bundle
from coaster import configureapp
import uploads, search

# First, make an app and config it

app = Flask(__name__, instance_relative_config=True)
configureapp(app, 'HASJOB_ENV')
mail = Mail()
mail.init_app(app)
assets = Environment(app)
uploads.configure()
search.configure()

# Second, setup assets

assets = Environment(app)

js = Bundle('js/libs/jquery-1.5.1.min.js',
            'js/libs/jquery.textarea-expander.js',
            'js/libs/tiny_mce/jquery.tinymce.js',
            'js/libs/jquery.form.js',
            'js/scripts.js',
            filters='jsmin', output='js/packed.js')

assets.register('js_all', js)

# Third, after config, import the models and views

import hasjob.models
import hasjob.views
if environ.get('HASJOB_ENV') == 'prod':
    import hasjob.loghandler
