import sys
import os.path
sys.path.insert(0, os.path.dirname(__file__))

from coaster import logging
from hasjob import app as application
logging.configure(application)
