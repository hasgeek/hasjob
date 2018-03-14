from hasjob import *
from hasjob.models import *
import IPython

IPython.embed()

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)