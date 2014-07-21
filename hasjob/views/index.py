# -*- coding: utf-8 -*-

from datetime import datetime
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from flask import (
    abort,
    redirect,
    render_template,
    request,
    Response,
    url_for,
    g
    )

from hasjob import app, lastuser
from hasjob.models import db, webmail_domains, JobCategory, JobPost, JobType, POSTSTATUS, newlimit, JobLocation
from hasjob.search import do_search
from hasjob.views.helper import getposts, getallposts, location_geodata
from hasjob.uploads import uploaded_logos


@app.route('/', subdomain='<subdomain>')
@app.route('/')
def index(basequery=None, type=None, category=None, md5sum=None, domain=None,
        location=None, title=None, showall=False, statuses=None):
    now = datetime.utcnow()
    if g.user or g.kiosk or g.board:
        showall = True
    posts = list(getposts(basequery, sticky=True, showall=showall, statuses=statuses))
    if posts:
        employer_name = posts[0].company_name
    else:
        employer_name = u'a single employer'

    if basequery is None and posts and not g.kiosk:
        # Group posts by email_domain on index page only, when not in kiosk mode
        grouped = OrderedDict()
        for post in posts:
            if post.sticky:
                # Make sticky posts appear in a group of one
                grouped.setdefault(('s', post.hashid), []).append(post)
                # if post.email_domain in webmail_domains:
                #     grouped.setdefault(('se', post.md5sum), []).append(post)
                # else:
                #     grouped.setdefault(('sd', post.email_domain), []).append(post)
            elif post.status == POSTSTATUS.ANNOUNCEMENT:
                # Make announcements also appear in a group of one
                grouped.setdefault(('a', post.hashid), []).append(post)
            elif post.email_domain in webmail_domains:
                grouped.setdefault(('ne', post.md5sum), []).append(post)
            else:
                grouped.setdefault(('nd', post.email_domain), []).append(post)
    else:
        grouped = None

    return render_template('index.html', posts=posts, grouped=grouped, now=now,
                           newlimit=newlimit, jobtype=type, jobcategory=category, title=title,
                           md5sum=md5sum, domain=domain, employer_name=employer_name,
                           location=location, showall=showall,
                           siteadmin=lastuser.has_permission('siteadmin'))


@app.route('/drafts', subdomain='<subdomain>')
@app.route('/drafts')
@lastuser.requires_login
def browse_drafts():
    basequery = JobPost.query.filter_by(user=g.user)
    return index(basequery=basequery, statuses=[POSTSTATUS.DRAFT, POSTSTATUS.PENDING])


@app.route('/type/<name>', subdomain='<subdomain>')
@app.route('/type/<name>')
def browse_by_type(name):
    if name == 'all':
        return redirect(url_for('index'))
    ob = JobType.query.filter_by(name=name).first_or_404()
    basequery = JobPost.query.filter_by(type_id=ob.id)
    return index(basequery=basequery, type=ob, title=ob.title)


@app.route('/at/<domain>', subdomain='<subdomain>')
@app.route('/at/<domain>')
def browse_by_domain(domain):
    if not domain:
        abort(404)
    basequery = JobPost.query.filter_by(email_domain=domain)
    return index(basequery=basequery, domain=domain, title=domain, showall=True)


@app.route('/category/<name>', subdomain='<subdomain>')
@app.route('/category/<name>')
def browse_by_category(name):
    if name == 'all':
        return redirect(url_for('index'))
    ob = JobCategory.query.filter_by(name=name).first_or_404()
    basequery = JobPost.query.filter_by(category_id=ob.id)
    return index(basequery=basequery, category=ob, title=ob.title)


@app.route('/by/<md5sum>', subdomain='<subdomain>')
@app.route('/by/<md5sum>')
def browse_by_email(md5sum):
    if not md5sum:
        abort(404)
    basequery = JobPost.query.filter_by(md5sum=md5sum)
    return index(basequery=basequery, md5sum=md5sum, showall=True)


@app.route('/in/<location>', subdomain='<subdomain>')
@app.route('/in/<location>')
def browse_by_location(location):
    geodata = location_geodata(location)
    if not geodata:
        abort(404)
    basequery = JobPost.query.filter(db.and_(
        JobLocation.jobpost_id == JobPost.id, JobLocation.geonameid == geodata['geonameid']))
    return index(basequery=basequery, location=geodata, title=geodata['short_title'])


@app.route('/feed', subdomain='<subdomain>')
@app.route('/feed')
def feed(basequery=None, type=None, category=None, md5sum=None, domain=None, location=None):
    title = "All jobs"
    if type:
        title = type.title
    elif category:
        title = category.title
    elif md5sum or domain:
        title = u"Jobs at a single employer"
    elif location:
        title = u"Jobs in {location}".format(location=location['short_title'])
    posts = list(getposts(basequery, showall=True))
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
                      '    <loc>%s</loc>\n' % url_for('jobdetail', hashid=post.hashid, _external=True) + \
                      '    <lastmod>%s</lastmod>\n' % (post.datetime.isoformat() + 'Z') + \
                      '    <changefreq>monthly</changefreq>\n'\
                      '  </url>\n'
    sitemapxml += '</urlset>'
    return Response(sitemapxml, content_type='text/xml; charset=utf-8')


@app.route('/logo/<hashid>', subdomain='<subdomain>')
@app.route('/logo/<hashid>')
def logoimage(hashid):
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
