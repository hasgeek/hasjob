# -*- coding: utf-8 -*-

from flask import jsonify
from coaster.views import requestargs
from ..models import Tag
from .. import app, lastuser


@app.route('/api/1/tag/autocomplete')
@lastuser.requires_login
@requestargs('q')
def tag_autocomplete(q):
    return jsonify({'tags': [t.title for t in Tag.autocomplete(q)]})
