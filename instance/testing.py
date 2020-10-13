import os

#: The title of this site
SITE_TITLE = 'Job Board'
#: Database backend
SQLALCHEMY_DATABASE_URI = 'postgresql:///hasjob_testing'
SERVER_NAME = 'hasjob.travis.local:5000'
#: LastUser server
LASTUSER_SERVER = 'https://hasgeek.com/'
#: LastUser client id
LASTUSER_CLIENT_ID = os.environ.get('LASTUSER_CLIENT_ID', '')
#: LastUser client secret
LASTUSER_CLIENT_SECRET = os.environ.get('LASTUSER_CLIENT_SECRET', '')

STATIC_SUBDOMAIN = 'static'

ASSET_SERVER = 'https://static.hasgeek.co.in/'
ASSET_MANIFEST_PATH = "static/build/manifest.json"
# no trailing slash
ASSET_BASE_PATH = '/static/build'
