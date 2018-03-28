# -*- coding: utf-8 -*-

from flask import jsonify
from coaster.views import requestargs
from ..models import Tag, Domain
from .. import app, lastuser


@app.route('/api/1/tag/autocomplete')
@lastuser.requires_login
@requestargs('q')
def tag_autocomplete(q):
    return jsonify({'tags': [t.title for t in Tag.autocomplete(q)]})


@app.route('/api/1/domain/autocomplete')
@lastuser.requires_login
@requestargs('q')
def domain_autocomplete(q):
    return jsonify({'domains': [d.name for d in Domain.autocomplete(q)]})
