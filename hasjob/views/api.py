from flask import jsonify

from coaster.views import requestargs

from .. import app, lastuser
from ..models import Domain, Tag


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
