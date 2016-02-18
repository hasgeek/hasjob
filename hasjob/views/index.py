# -*- coding: utf-8 -*-

from datetime import datetime
from collections import OrderedDict

from sqlalchemy.exc import ProgrammingError
from flask import abort, redirect, render_template, request, Response, url_for, g, flash, jsonify
from coaster.utils import getbool, parse_isoformat, for_tsquery
from coaster.views import render_with
from baseframe import csrf, _

from .. import app, lastuser
from ..models import (db, JobCategory, JobPost, JobType, POSTSTATUS, newlimit, agelimit, JobLocation,
    Domain, Location, Tag, JobPostTag, Campaign, CAMPAIGN_POSITION, CURRENCY, JobApplication, starred_job_table)
from ..views.helper import (getposts, getallposts, gettags, location_geodata, cache_viewcounts, session_jobpost_ab,
    bgroup, make_pay_graph)
from ..uploads import uploaded_logos
from ..utils import string_to_number


def stickie_dict(post, url, pinned=False, show_viewcounts=False, show_pay=False,
        starred=False, is_bgroup=None):
    result = {
        'headline': post.headlineb if is_bgroup else post.headline,
        'url': url,
        'pinned': pinned,
        'starred': starred,
        'date': post.datetime.isoformat() + 'Z',
        'location': post.location,
        'parsed_location': post.parsed_location,
        'company_name': post.company_name,
        'company_logo': post.url_for('logo'),
        }
    if show_viewcounts:
        result['viewcounts'] = {
            'listed': post.viewcounts['impressions'],
            'viewed': post.viewcounts['viewed'],
            'opened': post.viewcounts['opened'],
            'applied': post.viewcounts['applied']
            }
    if show_pay:
        result['pay'] = post.viewcounts['pay_label']
    return result


def json_index(data):
    pinsandposts = data['pinsandposts']
    grouped = data['grouped']
    is_siteadmin = data['is_siteadmin']
    loadmore = data['loadmore']

    result = {
        'grouped': [],
        'posts': [],
        'loadmore': loadmore.isoformat() + 'Z' if loadmore else None
        }
    if grouped:
        for grouping, group in grouped.items():
            rgroup = {
                'url': None,
                'posts': []
                }

            # First, process the first item to get a URL for the entire group
            pinned, post, is_bgroup = group[0]
            if len(group) == 1:
                rgroup['url'] = post.url_for(b=is_bgroup)
            elif grouping[0] in ('sd', 'nd'):  # Grouped by domain
                rgroup['url'] = url_for('browse_by_domain', domain=grouping[1])
            elif grouping[0] in ('se', 'ne'):  # Grouped by email (webmail user)
                rgroup['url'] = url_for('browse_by_email', md5sum=grouping[1])

            for pinned, post, is_bgroup in group:
                rgroup['posts'].append(stickie_dict(
                    post=post, url=post.url_for(b=is_bgroup), pinned=pinned, is_bgroup=is_bgroup,
                    show_viewcounts=is_siteadmin or g.user and g.user.flags.is_employer_month,
                    show_pay=is_siteadmin, starred=g.user and post.id in g.starred_ids
                    ))
            result['grouped'].append(rgroup)
    if pinsandposts:
        for pinned, post, is_bgroup in pinsandposts:
            result['posts'].append(stickie_dict(
                post=post, url=post.url_for(b=is_bgroup), pinned=pinned, is_bgroup=is_bgroup,
                show_viewcounts=is_siteadmin or g.user and g.user.flags.is_employer_month,
                show_pay=is_siteadmin, starred=g.user and post.id in g.starred_ids
                ))

    return jsonify(result)


@csrf.exempt
@app.route('/', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/', methods=['GET', 'POST'])
@render_with({'text/html': 'index.html', 'application/json': json_index}, json=False)
def index(basequery=None, md5sum=None, tag=None, domain=None, title=None, showall=True, statuses=None, batched=True, ageless=False, template_vars={}):

    if basequery is None:
        is_index = True
    else:
        is_index = False
    now = datetime.utcnow()
    if basequery is None and not (g.user or g.kiosk or (g.board and not g.board.require_login)):
        showall = False
        batched = False

    if basequery is None:
        basequery = JobPost.query

    # Apply request.args filters
    data_filters = {}
    f_types = request.args.getlist('t')
    while '' in f_types:
        f_types.remove('')
    if f_types:
        data_filters['types'] = f_types
        basequery = basequery.join(JobType).filter(JobType.name.in_(f_types))
    f_categories = request.args.getlist('c')
    while '' in f_categories:
        f_categories.remove('')
    if f_categories:
        data_filters['categories'] = f_categories
        basequery = basequery.join(JobCategory).filter(JobCategory.name.in_(f_categories))
    r_locations = request.args.getlist('l')
    f_locations = []
    remote_location = getbool(request.args.get('anywhere')) or False
    for rl in r_locations:
        if rl == 'anywhere':
            remote_location = True
        elif rl.isdigit():
            f_locations.append(int(rl))
        elif rl:
            ld = location_geodata(rl)
            if ld:
                f_locations.append(ld['geonameid'])
    remote_location_query = basequery.filter(JobPost.remote_location == True)  # NOQA
    locations_query = basequery.join(JobLocation).filter(JobLocation.geonameid.in_(f_locations))
    if f_locations and remote_location:
        data_filters['locations'] = f_locations
        data_filters['anywhere'] = True
        recency = JobPost.datetime > datetime.utcnow() - agelimit
        basequery = locations_query.filter(recency).union(remote_location_query.filter(recency))
    elif f_locations:
        data_filters['locations'] = f_locations
        basequery = locations_query
    elif remote_location:
        data_filters['anywhere'] = True
        # Only works as a positive filter: you can't search for jobs that are NOT anywhere
        basequery = remote_location_query
    if 'currency' in request.args and request.args['currency'] in CURRENCY.keys():
        currency = request.args['currency']
        data_filters['currency'] = currency
        basequery = basequery.filter(JobPost.pay_currency == currency)
        pay_graph = currency
    else:
        pay_graph = False
    if getbool(request.args.get('equity')):
        # Only works as a positive filter: you can't search for jobs that DON'T pay in equity
        data_filters['equity'] = True
        basequery = basequery.filter(JobPost.pay_equity_min != None)  # NOQA
    if 'pmin' in request.args and 'pmax' in request.args:
        f_min = string_to_number(request.args['pmin'])
        f_max = string_to_number(request.args['pmax'])
        if f_min is not None and f_max is not None:
            data_filters['pay_min'] = f_min
            data_filters['pay_max'] = f_max
            basequery = basequery.filter(JobPost.pay_cash_min < f_max, JobPost.pay_cash_max >= f_min)
    else:
        f_min = None
        f_max = None

    if getbool(request.args.get('archive')):
        ageless = True
        data_filters['archive'] = True
        statuses = POSTSTATUS.ARCHIVED

    search_domains = None
    if request.args.get('q'):
        q = for_tsquery(request.args['q'])
        try:
            # TODO: Can we do syntax validation without a database roundtrip?
            db.session.query(db.func.to_tsquery(q)).all()
        except ProgrammingError:
            db.session.rollback()
            g.event_data['search_syntax_error'] = (request.args['q'], q)
            if not request.is_xhr:
                flash(_(u"Search terms ignored because this didn’t parse: {query}").format(query=q), 'danger')
        else:
            # Query's good? Use it.
            data_filters['query'] = q
            search_domains = Domain.query.filter(
                Domain.search_vector.match(q, postgresql_regconfig='english'), Domain.is_banned == False).options(
                db.load_only('name', 'title', 'logo_url')).all()  # NOQA
            basequery = basequery.filter(JobPost.search_vector.match(q, postgresql_regconfig='english'))

    if data_filters:
        g.event_data['filters'] = data_filters
        showall = True
        batched = True

    # getposts sets g.board_jobs, used below
    posts = getposts(basequery, pinned=True, showall=showall, statuses=statuses, ageless=ageless).all()

    # Cache viewcounts (admin view or not)
    cache_viewcounts(posts)

    if posts:
        employer_name = posts[0].company_name
    else:
        employer_name = u'a single employer'

    if g.user:
        g.starred_ids = set(g.user.starred_job_ids(agelimit if not ageless else None))
    else:
        g.starred_ids = set()

    jobpost_ab = session_jobpost_ab()

    # Make lookup slightly faster in the loop below since 'g' is a proxy
    board = g.board
    if board:
        board_jobs = g.board_jobs
    else:
        board_jobs = {}

    if is_index and posts and not g.kiosk:
        # Group posts by email_domain on index page only, when not in kiosk mode
        grouped = OrderedDict()
        for post in posts:
            pinned = post.pinned
            if board is not None:
                blink = board_jobs.get(post.id)  # board_jobs only contains the last 30 days, no archive
                if blink is not None:
                    pinned = blink.pinned
            if pinned:
                # Make pinned posts appear in a group of one
                grouped.setdefault(('s', post.hashid), []).append(
                    (pinned, post, bgroup(jobpost_ab, post)))
            elif post.status == POSTSTATUS.ANNOUNCEMENT:
                # Make announcements also appear in a group of one
                grouped.setdefault(('a', post.hashid), []).append(
                    (pinned, post, bgroup(jobpost_ab, post)))
            elif post.domain.is_webmail:
                grouped.setdefault(('ne', post.md5sum), []).append(
                    (pinned, post, bgroup(jobpost_ab, post)))
            else:
                grouped.setdefault(('nd', post.email_domain), []).append(
                    (pinned, post, bgroup(jobpost_ab, post)))
        pinsandposts = None
    else:
        grouped = None
        if g.board:
            pinsandposts = []
            for post in posts:
                pinned = post.pinned
                if board is not None:
                    blink = board_jobs.get(post.id)  # board_jobs only contains the last 30 days, no archive
                    if blink is not None:
                        pinned = blink.pinned
                pinsandposts.append((pinned, post, bgroup(jobpost_ab, post)))
        else:
            pinsandposts = [(post.pinned, post, bgroup(jobpost_ab, post)) for post in posts]

    # Pick a header campaign (only if not kiosk or an XHR reload)
    pay_graph_data = None
    if not g.kiosk:
        if g.preview_campaign:
            header_campaign = g.preview_campaign
        else:
            geonameids = g.user_geonameids + f_locations
            header_campaign = Campaign.for_context(CAMPAIGN_POSITION.HEADER, board=g.board, user=g.user,
                anon_user=g.anon_user, geonameids=geonameids)
        if pay_graph:
            pay_graph_data = make_pay_graph(pay_graph, posts, rmin=f_min, rmax=f_max)
    else:
        header_campaign = None

    loadmore = False
    if batched:
        # Figure out where the batch should start from
        startdate = None
        if 'startdate' in request.values:
            try:
                startdate = parse_isoformat(request.values['startdate'])
            except ValueError:
                pass

        if request.method == 'GET':
            batchsize = 31  # Skipping one for the special stickie that's on all pages
        else:
            batchsize = 32

        # list of posts that were pinned at the time of first load
        pinned_hashids = request.args.getlist('ph')
        # Depending on the display mechanism (grouped or ungrouped), extract the batch
        if grouped:
            if not startdate:
                startindex = 0
                for row in grouped.values():
                    # break when a non-pinned post is encountered
                    if (not row[0][0]):
                        break
                    else:
                        pinned_hashids.append(row[0][1].hashid)
            else:
                # Loop through group looking for start of next batch. See below to understand the
                # nesting structure of 'grouped'
                for startindex, row in enumerate(grouped.values()):
                    # Skip pinned posts when looking for starting index
                    if (row[0][1].hashid not in pinned_hashids and row[0][1].datetime < startdate):
                        break

            batch = grouped.items()[startindex:startindex + batchsize]
            if startindex + batchsize < len(grouped):
                # Get the datetime of the last group's first item
                # batch = [((type, domain), [(pinned, post, bgroup), ...])]
                # batch[-1] = ((type, domain), [(pinned, post, bgroup), ...])
                # batch[-1][1] = [(pinned, post, bgroup), ...]
                # batch[-1][1][0] = (pinned, post, bgroup)
                # batch[-1][1][0][1] = post
                loadmore = batch[-1][1][0][1].datetime
            grouped = OrderedDict(batch)
        elif pinsandposts:
            if not startdate:
                startindex = 0
                for row in pinsandposts:
                    # break when a non-pinned post is encountered
                    if not row[0]:
                        break
                    else:
                        pinned_hashids.append(row[1].hashid)
            else:
                for startindex, row in enumerate(pinsandposts):
                    # Skip pinned posts when looking for starting index
                    if (row[1].hashid not in pinned_hashids and row[1].datetime < startdate):
                        break

            batch = pinsandposts[startindex:startindex + batchsize]
            if startindex + batchsize < len(pinsandposts):
                # batch = [(pinned, post), ...]
                loadmore = batch[-1][1].datetime
            pinsandposts = batch
    if grouped:
        g.impressions = {post.id: (pinflag, post.id, is_bgroup)
            for group in grouped.itervalues()
            for pinflag, post, is_bgroup in group}
    elif pinsandposts:
        g.impressions = {post.id: (pinflag, post.id, is_bgroup) for pinflag, post, is_bgroup in pinsandposts}

    query_params = request.args.to_dict(flat=False)
    if loadmore:
        query_params.update({'startdate': loadmore.isoformat() + 'Z', 'ph': pinned_hashids})
    return dict(
        pinsandposts=pinsandposts, grouped=grouped, now=now,
        newlimit=newlimit, title=title,
        md5sum=md5sum, domain=domain, employer_name=employer_name,
        showall=showall, is_index=is_index,
        header_campaign=header_campaign, loadmore=loadmore,
        search_domains=search_domains, query_params=query_params,
        is_siteadmin=lastuser.has_permission('siteadmin'),
        pay_graph_data=pay_graph_data, paginated=JobPost.is_paginated(request), template_vars=template_vars)


@csrf.exempt
@app.route('/drafts', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/drafts', methods=['GET', 'POST'])
@lastuser.requires_login
def browse_drafts():
    basequery = JobPost.query.filter_by(user=g.user)
    return index(basequery=basequery, ageless=True, statuses=[POSTSTATUS.DRAFT, POSTSTATUS.PENDING])


@csrf.exempt
@app.route('/my', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/my', methods=['GET', 'POST'])
@lastuser.requires_login
def my_posts():
    basequery = JobPost.query.filter_by(user=g.user)
    return index(basequery=basequery, ageless=True, statuses=POSTSTATUS.MY)


@csrf.exempt
@app.route('/bookmarks', subdomain='<subdomain>')
@app.route('/bookmarks')
@lastuser.requires_login
def bookmarks():
    basequery = JobPost.query.join(starred_job_table).filter(starred_job_table.c.user_id == g.user.id)
    return index(basequery=basequery, ageless=True, statuses=POSTSTATUS.ARCHIVED)


@csrf.exempt
@app.route('/applied', subdomain='<subdomain>')
@app.route('/applied')
@lastuser.requires_login
def applied():
    basequery = JobPost.query.join(JobApplication).filter(JobApplication.user == g.user)
    return index(basequery=basequery, ageless=True, statuses=POSTSTATUS.ARCHIVED)


@csrf.exempt
@app.route('/type/<name>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/type/<name>', methods=['GET', 'POST'])
def browse_by_type(name):
    if name == 'all':
        return redirect(url_for('index'))
    return redirect(url_for('index', t=name), code=301)


@csrf.exempt
@app.route('/<domain>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/<domain>', methods=['GET', 'POST'])
def browse_by_domain(domain):
    if not domain or '.' not in domain:
        abort(404)
    obj = Domain.get(domain)
    if not obj:
        abort(404)
    if obj.is_banned:
        abort(410)
    basequery = JobPost.query.join(Domain).filter(JobPost.domain == obj)
    return index(basequery=basequery, domain=obj, title=obj.use_title, showall=True)


@app.route('/at/<domain>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/at/<domain>', methods=['GET', 'POST'])
def browse_by_domain_legacy(domain):
    return redirect(url_for('browse_by_domain', domain=domain), code=301)


@csrf.exempt
@app.route('/category/<name>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/category/<name>', methods=['GET', 'POST'])
def browse_by_category(name):
    if name == 'all':
        return redirect(url_for('index'))
    return redirect(url_for('index', c=name), code=301)


@csrf.exempt
@app.route('/by/<md5sum>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/by/<md5sum>', methods=['GET', 'POST'])
def browse_by_email(md5sum):
    if not md5sum:
        abort(404)
    basequery = JobPost.query.filter_by(md5sum=md5sum)
    if basequery.isempty():
        abort(404)
    jobpost_user = basequery.first().user
    return index(basequery=basequery, md5sum=md5sum, showall=True, template_vars={'jobpost_user': jobpost_user})


@csrf.exempt
@app.route('/in/<location>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/in/<location>', methods=['GET', 'POST'])
def browse_by_location(location):
    return redirect(url_for('index', l=location), code=301)


@csrf.exempt
@app.route('/in/anywhere', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/in/anywhere', methods=['GET', 'POST'])
def browse_by_anywhere():
    return redirect(url_for('index', l='anywhere'), code=301)


@csrf.exempt
@app.route('/tag/<tag>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/tag/<tag>', methods=['GET', 'POST'])
def browse_by_tag(tag):
    tag = Tag.query.filter_by(name=tag).first_or_404()
    basequery = JobPost.query.filter(db.and_(
        JobPostTag.jobpost_id == JobPost.id, JobPostTag.tag == tag))
    return index(basequery=basequery, tag=tag, title=tag.title)


@app.route('/tag', subdomain='<subdomain>')
@app.route('/tag')
def browse_tags():
    return render_template('tags.html', tags=gettags(alltime=getbool(request.args.get('all'))))


@app.route('/feed', subdomain='<subdomain>')
@app.route('/feed')
def feed(basequery=None, type=None, category=None, md5sum=None, domain=None, location=None, tag=None, title=None):
    title = "All jobs"
    if type:
        title = type.title
    elif category:
        title = category.title
    elif md5sum or domain:
        title = u"Jobs at a single employer"
    elif location:
        title = u"Jobs in {location}".format(location=location['use_title'])
    elif tag:
        title = u"Jobs tagged {tag}".format(tag=title)
    posts = list(getposts(basequery, showall=True, limit=100))
    if posts:  # Can't do this unless posts is a list
        updated = posts[0].datetime.isoformat() + 'Z'
        if md5sum:
            title = posts[0].company_name
    else:
        updated = datetime.utcnow().isoformat() + 'Z'
    return Response(render_template('feed-atom.xml', posts=posts, updated=updated, title=title),
        content_type='application/atom+xml; charset=utf-8')


@app.route('/feed/indeed', subdomain='<subdomain>')
@app.route('/feed/indeed')
def feed_indeed():
    title = "All jobs"
    posts = list(getposts(None, showall=True))
    if posts:  # Can't do this unless posts is a list
        updated = posts[0].datetime.isoformat() + 'Z'
    else:
        updated = datetime.utcnow().isoformat() + 'Z'
    return Response(render_template('feed-indeed.xml', posts=posts, updated=updated, title=title),
        content_type='textxml; charset=utf-8')


@app.route('/type/<name>/feed', subdomain='<subdomain>')
@app.route('/type/<name>/feed')
def feed_by_type(name):
    if name == 'all':
        return redirect(url_for('feed'))
    ob = JobType.query.filter_by(name=name).first_or_404()
    basequery = JobPost.query.filter_by(type_id=ob.id)
    return feed(basequery=basequery, type=ob)


@app.route('/category/<name>/feed', subdomain='<subdomain>')
@app.route('/category/<name>/feed')
def feed_by_category(name):
    if name == 'all':
        return redirect(url_for('feed'))
    ob = JobCategory.query.filter_by(name=name).first_or_404()
    basequery = JobPost.query.filter_by(category_id=ob.id)
    return feed(basequery=basequery, category=ob)


@app.route('/by/<md5sum>/feed', subdomain='<subdomain>')
@app.route('/by/<md5sum>/feed')
def feed_by_email(md5sum):
    if not md5sum:
        abort(404)
    basequery = JobPost.query.filter_by(md5sum=md5sum)
    if basequery.isempty():
        abort(404)
    return feed(basequery=basequery, md5sum=md5sum)


@app.route('/at/<domain>/feed', subdomain='<subdomain>')
@app.route('/at/<domain>/feed')
def feed_by_domain_legacy(domain):
    return redirect(url_for('feed_by_domain', domain=domain), code=301)


@app.route('/<domain>/feed', subdomain='<subdomain>')
@app.route('/<domain>/feed')
def feed_by_domain(domain):
    if not domain:
        abort(404)
    basequery = JobPost.query.filter_by(email_domain=domain)
    return feed(basequery=basequery, domain=domain)


@app.route('/in/<location>/feed', subdomain='<subdomain>')
@app.route('/in/<location>/feed')
def feed_by_location(location):
    geodata = location_geodata(location)
    if not geodata:
        abort(404)
    basequery = JobPost.query.filter(db.and_(
        JobLocation.jobpost_id == JobPost.id, JobLocation.geonameid == geodata['geonameid']))
    return feed(basequery=basequery, location=geodata)


@app.route('/in/anywhere/feed', subdomain='<subdomain>')
@app.route('/in/anywhere/feed')
def feed_by_anywhere():
    basequery = JobPost.query.filter(JobPost.remote_location == True)  # NOQA
    return feed(basequery=basequery)


@app.route('/tag/<tag>/feed', subdomain='<subdomain>')
@app.route('/tag/<tag>/feed')
def feed_by_tag(tag):
    tag = Tag.query.filter_by(name=tag).first_or_404()
    basequery = JobPost.query.filter(db.and_(
        JobPostTag.jobpost_id == JobPost.id, JobPostTag.tag == tag))
    return feed(basequery=basequery, tag=tag, title=tag.title)


@app.route('/archive')
def archive():
    def sortarchive(order_by):
        current_order_by = request.args.get('order_by')
        reverse = request.args.get('reverse')
        if order_by == current_order_by:
            if reverse is None:
                reverse = False
            try:
                reverse = bool(int(reverse))
            except ValueError:
                reverse = False
            reverse = int(not reverse)
        return url_for('archive', order_by=order_by,
            reverse=reverse,
            start=request.args.get('start'),
            limit=request.args.get('limit'))

    order_by = {
        'date': JobPost.datetime,
        'headline': JobPost.headline,
        'company': JobPost.company_name,
        'location': JobPost.location,
        }.get(request.args.get('order_by'))
    reverse = request.args.get('reverse')
    start = request.args.get('start', 0)
    limit = request.args.get('limit', 100)
    if order_by is None and reverse is None:
        order_by = JobPost.datetime
        reverse = True
    try:
        if reverse is not None:
            reverse = bool(int(reverse))
    except ValueError:
        reverse = None
    try:
        if start is not None:
            start = int(start)
    except ValueError:
        start = 0
    try:
        if limit is not None:
            limit = int(limit)
    except ValueError:
        limit = 100
    count, posts = getallposts(order_by=order_by, desc=reverse, start=start, limit=limit)

    if request.is_xhr:
        tmpl = 'archive_inner.html'
    else:
        tmpl = 'archive.html'
    return render_template(tmpl, order_by=request.args.get('order_by'),
        posts=posts, start=start, limit=limit, count=count,
        # Pass some functions
        min=min, max=max, sortarchive=sortarchive)


@app.route('/sitemap.xml', subdomain='<subdomain>')
@app.route('/sitemap.xml')
def sitemap():
    sitemapxml = '<?xml version="1.0" encoding="UTF-8"?>\n'\
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    # Add locations to sitemap
    for item in Location.query.all():
        sitemapxml += '  <url>\n'\
                      '    <loc>%s</loc>\n' % item.url_for(_external=True) + \
                      '    <lastmod>%s</lastmod>\n' % (item.updated_at.isoformat() + 'Z') + \
                      '    <changefreq>monthly</changefreq>\n'\
                      '  </url>\n'
    # Add live posts to sitemap
    for post in getposts(showall=True):
        sitemapxml += '  <url>\n'\
                      '    <loc>%s</loc>\n' % post.url_for(_external=True) + \
                      '    <lastmod>%s</lastmod>\n' % (post.datetime.isoformat() + 'Z') + \
                      '    <changefreq>monthly</changefreq>\n'\
                      '  </url>\n'
    sitemapxml += '</urlset>'
    return Response(sitemapxml, content_type='text/xml; charset=utf-8')


@app.route('/<domain>/<hashid>/logo', subdomain='<subdomain>')
@app.route('/<domain>/<hashid>/logo')
@app.route('/logo/<hashid>', defaults={'domain': None}, subdomain='<subdomain>')
@app.route('/logo/<hashid>', defaults={'domain': None})
def logoimage(domain, hashid):
    post = JobPost.query.filter_by(hashid=hashid).first_or_404()
    if not post.company_logo:
        # If there's no logo (perhaps it was deleted), don't try to show one
        abort(404)
    if post.status in [POSTSTATUS.REJECTED, POSTSTATUS.SPAM]:
        # Don't show logo if post has been rejected. Could be spam
        abort(410)
    return redirect(uploaded_logos.url(post.company_logo))


@app.route('/search', subdomain='<subdomain>')
@app.route('/search')
def search():
    return redirect(url_for('index', **request.args))
