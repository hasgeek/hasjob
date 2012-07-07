# -*- coding: utf-8 -*-

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

