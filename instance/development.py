# -*- coding: utf-8 -*-
import os
CACHE_TYPE = 'redis'
CACHE_REDIS_HOST = 'redis'
#: Database backend
SQLALCHEMY_DATABASE_URI = 'postgres://postgres:postgres@pg/postgres'
REDIS_URL = 'redis://redis:6379/0'
SERVER_NAME = (os.environ.get('SERVER_NAME') + ':5000') or 'hasjob.docker.dev:5000'
#: LastUser server
LASTUSER_SERVER = os.environ.get('LASTUSER_SERVER') or 'https://auth.hasgeek.com'
#: LastUser client id
LASTUSER_CLIENT_ID = os.environ.get('LASTUSER_CLIENT_ID') or ''
#: LastUser client secret
LASTUSER_CLIENT_SECRET = os.environ.get('LASTUSER_CLIENT_SECRET') or ''
