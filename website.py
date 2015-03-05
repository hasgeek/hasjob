import sys
import os.path
sys.path.insert(0, os.path.dirname(__file__))

from hasjob import init_for
init_for('prod')
