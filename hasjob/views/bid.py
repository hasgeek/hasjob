# -*- coding: utf-8 -*-

"""
Views for pinning jobposts.
"""
from flask import g, abort, request, render_template
from baseframe import _, csrf
from baseframe.forms import render_form
from .. import app, lastuser
from ..models import JobPost, CreditTransaction
from ..forms import PinBidForm
from .helper import location_geodata


@app.route('/account/credits')
@lastuser.requires_login
def credit_balance():
    transactions = CreditTransaction.get_all(g.user)
    return render_template('credit_balance.html',
        title="Credit balance", transactions=transactions, balance=g.user.credit_balance)


@app.route('/<domain>/<hashid>/promote', methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/promote', methods=('GET', 'POST'))
@lastuser.requires_login
def promotejob(domain, hashid):
    """
    Promote a job
    """
    post = JobPost.get(hashid)
    if not post:
        abort(404)

    return render_template('promote.html', post=post)


@csrf.exempt
@app.route('/<domain>/<hashid>/promote/bid', methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/promote/bid', methods=('GET', 'POST'))
@lastuser.requires_login
def makebid(domain, hashid):
    """
    Place a bid for promoting a job
    """
    post = JobPost.get(hashid)
    if not post:
        abort(404)

    form = PinBidForm()
    form.post = post

    if request.method == 'GET':
        location_data = location_geodata(g.user_geonameids)
        location_list = [location_data[geonameid] for geonameid in g.user_geonameids if geonameid in location_data]
        if location_list:
            location = location_list[0]['name']
        else:
            location = _("unknown")

        print location

        form.start_at.description = form.start_at.description.format(timezone=form.start_at.timezone)
        form.load.description = form.load.description.format(count=g.user.credit_balance)
        form.geonameids.description = form.geonameids.description.format(location=location)

        form.start_at.data = post.datetime
        form.end_at.data = post.expiry_date

    if form.validate_on_submit():
        # Do stuff
        pass

    return render_form(form=form, title=_("Bid to pin a job post"), submit=_("Bid"),
        cancel_url=post.url_for('promote'), ajax=False,
        message=_("Hasjob offers three pinned positions on the first row of the home page. Jobs are pinned on "
            "the basis of the three highest bids and each is charged at the rate offered by the next highest bidder "
            "(a generalized second-price auction). You only pay once per user. You can cancel or pause a bid at any "
            "time"))


@csrf.exempt
@app.route('/<domain>/<hashid>/promote', methods=('GET', 'POST'), subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/promote', methods=('GET', 'POST'))
@lastuser.requires_login
def editbid(domain, hashid):
    """
    Edit bid parameters
    """
    post = JobPost.get(hashid)
    if not post:
        abort(404)

    return render_template('newbid.html', post=post)
