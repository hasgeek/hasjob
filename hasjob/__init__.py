import os.path

import geoip2.database
from baseframe import Version, assets, baseframe
from flask import Flask
from flask_assets import Bundle
from flask_lastuser import Lastuser
from flask_lastuser.sqlalchemy import UserManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_redis import FlaskRedis
from flask_rq2 import RQ

import coaster.app
from coaster.assets import WebpackManifest

from ._version import __version__
from .uploads import configure as uploads_configure

# First, make an app and config it

app = Flask(__name__, instance_relative_config=True, subdomain_matching=True)
app.static_folder = 'static'
mail = Mail()
lastuser = Lastuser()
redis_store = FlaskRedis(decode_responses=True)
rq = RQ()
manifest = WebpackManifest(
    app, filepath='static/build/manifest.json', urlpath='/static/build/'
)

# Second, setup assets
version = Version(__version__)

# Third, after config, import the models and views

from . import cli, models, views  # noqa: F401  # isort:skip
from .models import db  # isort:skip

# Configure the app
coaster.app.init_app(app)
db.init_app(app)
db.app = app
migrate = Migrate(app, db)
app.geoip = None
if 'GEOIP_PATH' in app.config:
    if not os.path.exists(app.config['GEOIP_PATH']):
        app.logger.warning("GeoIP database missing at %s", app.config['GEOIP_PATH'])
    else:
        app.geoip = geoip2.database.Reader(app.config['GEOIP_PATH'])

rq.init_app(app)

baseframe.init_app(
    app,
    requires=[
        'baseframe-bs3',
        'jquery.autosize',
        'jquery.liblink',
        'jquery.wnumb',
        'jquery.nouislider',
        'baseframe-firasans',
        'fontawesome>=4.3.0',
        'bootstrap-multiselect',
        'nprogress',
        'ractive',
        'jquery.appear',
        'hammer',
    ],
)

# FIXME: Hack for external build system generating relative /static URLs.
# Fix this by generating absolute URLs to the static subdomain during build.
app.add_url_rule(
    '/static/<path:filename>',
    endpoint='static_root',
    view_func=app.send_static_file,
    subdomain=None,
)
app.add_url_rule(
    '/static/<path:filename>',
    endpoint='static_subdomain',
    view_func=app.send_static_file,
    subdomain='<subdomain>',
)

# TinyMCE has to be loaded by itself, unminified, or it won't be able to find its assets
app.assets.register(
    'js_tinymce',
    assets.require('!jquery.js', 'tinymce.js>=4.0.0', 'jquery.tinymce.js>=4.0.0'),
)
app.assets.register(
    'css_editor',
    Bundle(
        'css/editor.css',
        filters=['cssrewrite', 'cssmin'],
        output='css/editor.packed.css',
    ),
)

uploads_configure(app)
mail.init_app(app)
redis_store.init_app(app)
lastuser.init_app(app)
lastuser.init_usermanager(UserManager(db, models.User))
