# -*- coding: utf-8 -*-

import os.path
import geoip2.database
from flask import Flask
from flask_migrate import Migrate
from flask_assets import Bundle
from flask_rq import RQ
from flask_mail import Mail
from flask_redis import FlaskRedis
from flask_lastuser import Lastuser
from flask_lastuser.sqlalchemy import UserManager
from baseframe import baseframe, assets, Version
import coaster.app
from ._version import __version__


# First, make an app and config it

app = Flask(__name__, instance_relative_config=True)
app.static_folder = 'static'
mail = Mail()
lastuser = Lastuser()
redis_store = FlaskRedis()

# Second, setup assets
version = Version(__version__)

# Third, after config, import the models and views

from . import models, views, jobs  # NOQA
from .models import db  # NOQA

# Configure the app
coaster.app.init_app(app)
db.init_app(app)
db.app = app
migrate = Migrate(app, db)
app.geoip = None
if 'GEOIP_PATH' in app.config:
    if not os.path.exists(app.config['GEOIP_PATH']):
        app.logger.warn("GeoIP database missing at " + app.config['GEOIP_PATH'])
    else:
        app.geoip = geoip2.database.Reader(app.config['GEOIP_PATH'])

RQ(app)

baseframe.init_app(app, requires=['baseframe-bs3', 'jquery.autosize', 'jquery.liblink',
    'jquery.wnumb', 'jquery.nouislider', 'baseframe-firasans', 'fontawesome>=4.3.0',
    'bootstrap-multiselect', 'nprogress', 'ractive', 'jquery.appear', 'hammer'])
# TinyMCE has to be loaded by itself, unminified, or it won't be able to find its assets
app.assets.register('js_tinymce', assets.require('!jquery.js', 'tinymce.js>=4.0.0', 'jquery.tinymce.js>=4.0.0'))
app.assets.register('css_editor', Bundle('css/editor.css',
    filters=['cssrewrite', 'cssmin'], output='css/editor.packed.css'))

from hasjob.uploads import configure as uploads_configure
uploads_configure()
mail.init_app(app)
redis_store.init_app(app)
lastuser.init_app(app)
lastuser.init_usermanager(UserManager(db, models.User))
