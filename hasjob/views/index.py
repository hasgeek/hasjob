# -*- coding: utf-8 -*-

from datetime import datetime
from collections import OrderedDict

from sqlalchemy.exc import ProgrammingError
from flask import abort, redirect, render_template, request, Response, url_for, g, flash, Markup
from coaster.utils import getbool, parse_isoformat, for_tsquery
from baseframe import csrf, _

from .. import app, lastuser
from ..models import (db, JobCategory, JobPost, JobType, POSTSTATUS, newlimit, agelimit, JobLocation,
    Domain, Location, Tag, JobPostTag, Campaign, CAMPAIGN_POSITION, CURRENCY)
from ..views.helper import (getposts, getallposts, gettags, location_geodata, cache_viewcounts, session_jobpost_ab,
    bgroup, filter_locations)
from ..uploads import uploaded_logos
from ..utils import string_to_number


@csrf.exempt
@app.route('/', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/', methods=['GET', 'POST'])
def index(basequery=None, type=None, category=None, md5sum=None, domain=None,
        location=None, title=None, showall=True, statuses=None, tag=None, batched=True):

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
    for rl in r_locations:
        if rl.isdigit():
            f_locations.append(int(rl))
        elif rl:
            ld = location_geodata(rl)
            if ld:
                f_locations.append(ld['geonameid'])
    if f_locations:
        data_filters['locations'] = f_locations
        basequery = basequery.join(JobLocation).filter(JobLocation.geonameid.in_(f_locations))
    if getbool(request.args.get('anywhere')):
        data_filters['anywhere'] = True
        # Only works as a positive filter: you can't search for jobs that are NOT anywhere
        basequery = basequery.filter(JobPost.remote_location == True)  # NOQA
    if 'currency' in request.args and request.args['currency'] in CURRENCY.keys():
        data_filters['currency'] = request.args['currency']
        basequery = basequery.filter(JobPost.pay_currency == request.args['currency'])
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

    # getposts sets g.board_jobs, used below
    posts = getposts(basequery, pinned=True, showall=showall, statuses=statuses).all()

    # Cache viewcounts (admin view or not)
    cache_viewcounts(posts)

    if posts:
        employer_name = posts[0].company_name
    else:
        employer_name = u'a single employer'

    if g.user:
        g.starred_ids = set(g.user.starred_job_ids(agelimit))
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
                blink = board_jobs[post.id]
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
                    blink = board_jobs[post.id]
                    if blink is not None:
                        pinned = blink.pinned
                pinsandposts.append((pinned, post, bgroup(jobpost_ab, post)))
        else:
            pinsandposts = [(post.pinned, post, bgroup(jobpost_ab, post)) for post in posts]

    # Pick a header campaign (only if not kiosk or an XHR reload)
    if not g.kiosk and not request.is_xhr:
        if g.preview_campaign:
            header_campaign = g.preview_campaign
        else:
            if location:
                geonameids = g.user_geonameids + [location['geonameid']]
            else:
                geonameids = g.user_geonameids
            header_campaign = Campaign.for_context(CAMPAIGN_POSITION.HEADER, board=g.board, user=g.user,
                anon_user=g.anon_user, geonameids=geonameids)
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

        # Depending on the display mechanism (grouped or ungrouped), extract the batch
        if grouped:
            if not startdate:
                startindex = 0
            else:
                # Loop through group looking for start of next batch. See below to understand the
                # nesting structure of 'grouped'
                for startindex, row in enumerate(grouped.values()):
                    # Skip examination of pinned listings (having row[0][0] = True)
                    if (not row[0][0]) and row[0][1].datetime < startdate:
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
            else:
                for startindex, row in enumerate(pinsandposts):
                    # Skip pinned posts when looking for starting index
                    if (not row[0]) and row[1].datetime < startdate:
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

    # Test values for development:
    # if not g.user_geonameids:
    #     g.user_geonameids = [1277333, 1277331, 1269750]
    if not location and 'l' not in request.args and g.user_geonameids and (g.user or g.anon_user):
        # No location filters? Prompt the user
        ldata = location_geodata(g.user_geonameids)
        location_prompts = [ldata[geonameid] for geonameid in g.user_geonameids if geonameid in ldata]
    else:
        location_prompts = []

    return render_template('index.html', pinsandposts=pinsandposts, grouped=grouped, now=now,
                           newlimit=newlimit, jobtype=type, jobcategory=category, title=title,
                           md5sum=md5sum, domain=domain, employer_name=employer_name,
                           location=location, showall=showall, tag=tag, is_index=is_index,
                           header_campaign=header_campaign, loadmore=loadmore,
                           location_prompts=location_prompts, search_domains=search_domains,
                           is_siteadmin=lastuser.has_permission('siteadmin'),
                           job_locations=filter_locations(),
                           job_type_choices=JobType.name_title_pairs(g.board),
                           job_category_choices=JobCategory.name_title_pairs(g.board))


@csrf.exempt
@app.route('/drafts', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/drafts', methods=['GET', 'POST'])
@lastuser.requires_login
def browse_drafts():
    basequery = JobPost.query.filter_by(user=g.user)
    return index(basequery=basequery, statuses=[POSTSTATUS.DRAFT, POSTSTATUS.PENDING])


@csrf.exempt
@app.route('/type/<name>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/type/<name>', methods=['GET', 'POST'])
def browse_by_type(name):
    if name == 'all':
        return redirect(url_for('index'))
    ob = JobType.query.filter_by(name=name).first_or_404()
    basequery = JobPost.query.filter_by(type_id=ob.id)
    return index(basequery=basequery, type=ob, title=ob.title)


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
    ob = JobCategory.query.filter_by(name=name).first_or_404()
    basequery = JobPost.query.filter_by(category_id=ob.id)
    return index(basequery=basequery, category=ob, title=ob.title)


@csrf.exempt
@app.route('/by/<md5sum>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/by/<md5sum>', methods=['GET', 'POST'])
def browse_by_email(md5sum):
    if not md5sum:
        abort(404)
    basequery = JobPost.query.filter_by(md5sum=md5sum)
    return index(basequery=basequery, md5sum=md5sum, showall=True)


@csrf.exempt
@app.route('/in/<location>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/in/<location>', methods=['GET', 'POST'])
def browse_by_location(location):
    loc = Location.get(location)
    if loc:
        geodata = {'geonameid': loc.id, 'name': loc.name, 'use_title': loc.title, 'description': Markup(loc.description)}
    else:
        geodata = location_geodata(location)
    if not geodata:
        abort(404)
    if location != geodata['name']:
        return redirect(url_for('browse_by_location', location=geodata['name']))
    basequery = JobPost.query.filter(db.and_(
        JobLocation.jobpost_id == JobPost.id, JobLocation.geonameid == geodata['geonameid']))
    return index(basequery=basequery, location=geodata, title=geodata['use_title'])


@csrf.exempt
@app.route('/in/anywhere', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/in/anywhere', methods=['GET', 'POST'])
def browse_by_anywhere():
    basequery = JobPost.query.filter(JobPost.remote_location == True)  # NOQA
    return index(basequery=basequery)


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
    posts = list(getposts(basequery, showall=False))
    if posts:  # Can't do this unless posts is a list
        updated = posts[0].datetime.isoformat() + 'Z'
        if md5sum:
            title = posts[0].company_name
    else:
        updated = datetime.utcnow().isoformat() + 'Z'
    return Response(render_template('feed.xml', posts=posts, updated=updated, title=title),
        content_type='application/atom+xml; charset=utf-8')


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
    return feed(basequery=basequery, md5sum=md5sum)


@app.route('/at/<domain>/feed', subdomain='<subdomain>')
@app.route('/at/<domain>/feed')
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
