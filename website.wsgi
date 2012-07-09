import sys
import os.path
sys.path.insert(0, os.path.dirname(__file__))

from coaster import logging
from hasjob import app as application
from hasjob.search import configure as search_configure
from hasjob.uploads import configure as uploads_configure
search_configure()
uploads_configure()
logging.configure(application)
