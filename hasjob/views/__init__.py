# -*- coding: utf-8 -*-

import os.path
import re
import bleach
from collections import defaultdict
from datetime import date, datetime, timedelta
from urllib import quote, quote_plus
from pytz import utc, timezone
from difflib import SequenceMatcher
from flask import (render_template, redirect, url_for, request, session, abort,
    flash, g, Response, Markup, escape, jsonify)
from flask.ext.mail import Mail, Message
from markdown import markdown

from hasjob.twitter import tweet
from hasjob import app, forms
from hasjob.models import db, POSTSTATUS, JobPost, JobType, JobCategory, JobPostReport, ReportCode, unique_hash, agelimit
from hasjob.uploads import uploaded_logos, process_image
from hasjob.utils import scrubemail, md5sum, get_email_domain, get_word_bag
from hasjob.search import do_search

from hasjob.views.display import *
from hasjob.views.error_handling import *
from hasjob.views.search import *
from hasjob.views.stats import *
from hasjob.views.constants import *
from hasjob.views.helper import *
from hasjob.views.static import *
from hasjob.views.update import *

@app.route('/type/')
@app.route('/category/')
@app.route('/view/')
@app.route('/edit/')
@app.route('/confirm/')
@app.route('/withdraw/')
def root_paths():
    return redirect(url_for('index'), code=302)

