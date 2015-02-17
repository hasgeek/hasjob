# -*- coding: utf-8 -*-

from datetime import datetime
from collections import OrderedDict
from flask import (
    abort,
    redirect,
    render_template,
    request,
    Response,
    url_for,
    g
    )
from coaster.utils import getbool, parse_isoformat
from baseframe import csrf
from baseframe.staticdata import webmail_domains

from .. import app, lastuser, redis_store
from ..models import (db, JobCategory, JobPost, JobType, POSTSTATUS, newlimit, agelimit, JobLocation,
    Tag, JobPostTag, Campaign, CAMPAIGN_POSITION)
from ..search import do_search
from ..views.helper import getposts, getallposts, gettags, location_geodata
from ..uploads import uploaded_logos


@csrf.exempt
@app.route('/', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/', methods=['GET', 'POST'])
def index(basequery=None, type=None, category=None, md5sum=None, domain=None,
        location=None, title=None, showall=True, statuses=None, tag=None, batched=True):
    now = datetime.utcnow()
    if basequery is None and not (g.user or g.kiosk or (g.board and not g.board.require_login)):
        showall = False
        batched = False
    posts = list(getposts(basequery, pinned=True, showall=showall, statuses=statuses))

    # Cache viewcounts (admin view or not)
    redis_pipe = redis_store.connection.pipeline()
    viewcounts_keys = [p.viewcounts_key for p in posts]
    for key in viewcounts_keys:
        redis_pipe.hgetall(key)
    viewcounts_values = redis_pipe.execute()
    g.viewcounts = dict(zip(viewcounts_keys, viewcounts_values))

    if posts:
        employer_name = posts[0].company_name
    else:
        employer_name = u'a single employer'

    if g.user:
        g.starred_ids = set(g.user.starred_job_ids(agelimit))
    else:
        g.starred_ids = set()

    # Make lookup slightly faster in the loop below since 'g' is a proxy
    board = g.board

    if basequery is None and posts and not g.kiosk:
        # Group posts by email_domain on index page only, when not in kiosk mode
        grouped = OrderedDict()
        for post in posts:
            pinned = post.pinned
            if board is not None:
                blink = post.link_to_board(board)
                if blink is not None:
                    pinned = blink.pinned
            if pinned:
                # Make pinned posts appear in a group of one
                grouped.setdefault(('s', post.hashid), []).append((pinned, post))
            elif post.status == POSTSTATUS.ANNOUNCEMENT:
                # Make announcements also appear in a group of one
                grouped.setdefault(('a', post.hashid), []).append((pinned, post))
            elif post.email_domain in webmail_domains:
                grouped.setdefault(('ne', post.md5sum), []).append((pinned, post))
            else:
                grouped.setdefault(('nd', post.email_domain), []).append((pinned, post))
        pinsandposts = None
    else:
        grouped = None
        if g.board:
            pinsandposts = []
            for post in posts:
                pinned = post.pinned
                if board is not None:
                    blink = post.link_to_board(board)
                    if blink is not None:
                        pinned = blink.pinned
                pinsandposts.append((pinned, post))
        else:
            pinsandposts = [(post.pinned, post) for post in posts]

    # Pick a header campaign
    if not g.kiosk:
        if g.preview_campaign:
            header_campaign = g.preview_campaign
        else:
            if location:
                geonameids = g.user_geonameids + [location['geonameid']]
            else:
                geonameids = g.user_geonameids
            header_campaign = Campaign.for_context(CAMPAIGN_POSITION.HEADER, board=g.board, user=g.user,
                geonameids=geonameids)
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
                # batch = [((type, domain), [(pinned, post), ...])]
                # batch[-1] = ((type, domain), [(pinned, post), ...])
                # batch[-1][1] = [(pinned, post), ...]
                # batch[-1][1][0] = (pinned, post)
                # batch[-1][1][0][1] = post
                loadmore = batch[-1][1][0][1].datetime
            grouped = OrderedDict(batch)
            g.impressions = [(pinflag, post.id)
                for grouping, group in batch
                for pinflag, post in group]
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
            g.impressions = [(pinflag, post.id) for pinflag, post in batch]

    return render_template('index.html', pinsandposts=pinsandposts, grouped=grouped, now=now,
                           newlimit=newlimit, jobtype=type, jobcategory=category, title=title,
                           md5sum=md5sum, domain=domain, employer_name=employer_name,
                           location=location, showall=showall, tag=tag,
                           header_campaign=header_campaign, loadmore=loadmore,
                           is_siteadmin=lastuser.has_permission('siteadmin'))


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
    basequery = JobPost.query.filter_by(email_domain=domain)
    return index(basequery=basequery, domain=domain, title=domain, showall=True)


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
    geodata = location_geodata(location)
    if not geodata:
        abort(404)
    basequery = JobPost.query.filter(db.and_(
        JobLocation.jobpost_id == JobPost.id, JobLocation.geonameid == geodata['geonameid']))
    return index(basequery=basequery, location=geodata, title=geodata['short_title'])


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
        title = u"Jobs in {location}".format(location=location['short_title'])
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
    # Add job type pages to sitemap
    for item in JobType.query.filter_by(public=True).all():
        sitemapxml += '  <url>\n'\
                      '    <loc>%s</loc>\n' % url_for('browse_by_type', name=item.name, _external=True) + \
                      '  </url>\n'
    # Add job category pages to sitemap
    for item in JobCategory.query.filter_by(public=True).all():
        sitemapxml += '  <url>\n'\
                      '    <loc>%s</loc>\n' % url_for('browse_by_category', name=item.name, _external=True) + \
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
    now = datetime.utcnow()
    results = sorted(do_search(request.args.get('q', u''), expand=True),
        key=lambda r: getattr(r, 'datetime', now))
    results.reverse()
    return render_template('search.html', results=results, now=now, newlimit=newlimit)
