# -*- coding: utf-8 -*-
import os
CACHE_TYPE = 'redis'
CACHE_REDIS_HOST = os.environ.get('CACHE_REDIS_HOST')
#: Database backend
SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
REDIS_URL = os.environ.get('REDIS_URL')
SERVER_NAME = (os.environ.get('SERVER_NAME') or 'hasjob.docker.dev') + ':5000'
#: LastUser server
LASTUSER_SERVER = os.environ.get('LASTUSER_SERVER') or 'https://auth.hasgeek.com'
#: LastUser client id
LASTUSER_CLIENT_ID = os.environ.get('LASTUSER_CLIENT_ID') or ''
#: LastUser client secret
LASTUSER_CLIENT_SECRET = os.environ.get('LASTUSER_CLIENT_SECRET') or ''
