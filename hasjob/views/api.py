# -*- coding: utf-8 -*-
from datetime import datetime
from flask import jsonify, g, session, request, Response
from flask_wtf import FlaskForm
from coaster.views import requestargs, render_with
from .helper import rq_save_impressions
from ..models import db, Tag, Domain, AnonUser, EventSession, UserEvent
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


@app.route('/api/1/anonsession', methods=['POST'])
@render_with(json=True)
def anon_session():
    """
    Load anon user:

    1. If client sends valid csrf token, create and set g.anon_user
    2. if g.anon_user exists, set session['au'] to anon_user.id
    """
    now = datetime.utcnow()

    csrf_form = FlaskForm()
    if not g.user and not g.anon_user and csrf_form.validate_on_submit():
        # This client sent us valid csrf token
        g.anon_user = AnonUser()
        db.session.add(g.anon_user)
        g.esession = EventSession.new_from_request(request)
        g.esession.anon_user = g.anon_user
        g.esession.load_from_cache(session['es'], UserEvent)
        db.session.add(g.esession)
        db.session.commit()

    if g.anon_user:
        session['au'] = g.anon_user.id
        if 'impression' in session:
            rq_save_impressions(g.esession.id, session.pop('impressions').values(), now, delay=False)

    return Response({'status': 'ok'})
