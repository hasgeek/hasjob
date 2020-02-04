# -*- coding: utf-8 -*-
import os

#: The title of this site
SITE_TITLE = 'Job Board'
#: Database backend
SQLALCHEMY_DATABASE_URI = 'postgres://127.0.0.1/hasjob'
SERVER_NAME = 'hasjob.travis.local:5000'
#: LastUser server
LASTUSER_SERVER = 'https://auth.hasgeek.com/'
#: LastUser client id
LASTUSER_CLIENT_ID = os.environ.get('LASTUSER_CLIENT_ID', '')
#: LastUser client secret
LASTUSER_CLIENT_SECRET = os.environ.get('LASTUSER_CLIENT_SECRET', '')

STATIC_SUBDOMAIN = 'static'

ASSET_SERVER = 'https://static.hasgeek.co.in/'
#: Server host name (and port if not 80/443)
ASSET_MANIFEST_PATH = "static/build/manifest.json"
# no trailing slash
ASSET_BASE_PATH = '/static/build'
