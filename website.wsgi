import sys
import os.path
sys.path.insert(0, os.path.dirname(__file__))

from coaster import logging
from hasjob import init_for, app
init_for('prod')
