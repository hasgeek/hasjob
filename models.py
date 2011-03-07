# -*- coding: utf-8 -*-

from flaskext.sqlalchemy import SQLAlchemy
from app import app

db = SQLAlchemy(app)
