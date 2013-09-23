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
    )

from hasjob import app, lastuser
from hasjob.models import JobCategory, JobPost, JobType, POSTSTATUS, newlimit
from hasjob.search import do_search
from hasjob.views.helper import getposts, getallposts
from hasjob.uploads import uploaded_logos

webmail_domains = set(['gmail.com', 'yahoo.com', 'yahoo.co.in', 'hotmail.com', 'outlook.com', 'aol.com', 'live.com'])


@app.route('/')
def index(basequery=None, type=None, category=None, md5sum=None, domain=None):
    now = datetime.utcnow()
    posts = list(getposts(basequery, sticky=True))
    if posts:
        employer_name = posts[0].company_name
    else:
        employer_name = u'a single employer'

    if basequery is None and posts:
        # Group posts by email_domain on index page only
        grouped = OrderedDict()
        for post in posts:
            if post.sticky:
                # Make sticky posts appear in a group of one
                grouped.setdefault(('s', post.hashid), []).append(post)
                # if post.email_domain in webmail_domains:
                #     grouped.setdefault(('se', post.md5sum), []).append(post)
                # else:
                #     grouped.setdefault(('sd', post.email_domain), []).append(post)
            elif post.email_domain in webmail_domains:
                grouped.setdefault(('ne', post.md5sum), []).append(post)
            else:
                grouped.setdefault(('nd', post.email_domain), []).append(post)
    else:
        grouped = None

    return render_template('index.html', posts=posts, grouped=grouped, now=now,
                           newlimit=newlimit, jobtype=type, jobcategory=category,
                           md5sum=md5sum, domain=domain, employer_name=employer_name,
                           siteadmin=lastuser.has_permission('siteadmin'))


@app.route('/type/<name>')
def browse_by_type(name):
    if name == 'all':
        return redirect(url_for('index'))
    ob = JobType.query.filter_by(name=name).first_or_404()
    basequery = JobPost.query.filter_by(type_id=ob.id)
    return index(basequery=basequery, type=ob)


@app.route('/at/<domain>')
def browse_by_domain(domain):
    if not domain:
        abort(404)
    basequery = JobPost.query.filter_by(email_domain=domain)
    return index(basequery=basequery, domain=domain)


@app.route('/category/<name>')
def browse_by_category(name):
    if name == 'all':
        return redirect(url_for('index'))
    ob = JobCategory.query.filter_by(name=name).first_or_404()
    basequery = JobPost.query.filter_by(category_id=ob.id)
    return index(basequery=basequery, category=ob)


@app.route('/by/<md5sum>')
def browse_by_email(md5sum):
    if not md5sum:
        abort(404)
    basequery = JobPost.query.filter_by(md5sum=md5sum)
    return index(basequery=basequery, md5sum=md5sum)


@app.route('/feed')
def feed(basequery=None, type=None, category=None, md5sum=None, domain=None):
    title = "All jobs"
    if type:
        title = type.title
    elif category:
        title = category.title
    elif md5sum or domain:
        title = u"Jobs at a single employer"
    posts = list(getposts(basequery, showall=True))
    if posts:  # Can't do this unless posts is a list
        updated = posts[0].datetime.isoformat() + 'Z'
        if md5sum:
            title = posts[0].company_name
    else:
        updated = datetime.utcnow().isoformat() + 'Z'
    return Response(render_template('feed.xml', posts=posts, updated=updated, title=title),
        content_type='application/atom+xml; charset=utf-8')


@app.route('/type/<name>/feed')
def feed_by_type(name):
    if name == 'all':
        return redirect(url_for('feed'))
    ob = JobType.query.filter_by(name=name).first_or_404()
    basequery = JobPost.query.filter_by(type_id=ob.id)
    return feed(basequery=basequery, type=ob)


@app.route('/category/<name>/feed')
def feed_by_category(name):
    if name == 'all':
        return redirect(url_for('feed'))
    ob = JobCategory.query.filter_by(name=name).first_or_404()
    basequery = JobPost.query.filter_by(category_id=ob.id)
    return feed(basequery=basequery, category=ob)


@app.route('/by/<md5sum>/feed')
def feed_by_email(md5sum):
    if not md5sum:
        abort(404)
    basequery = JobPost.query.filter_by(md5sum=md5sum)
    return feed(basequery=basequery, md5sum=md5sum)


@app.route('/at/<domain>/feed')
def feed_by_domain(domain):
    if not domain:
        abort(404)
    basequery = JobPost.query.filter_by(email_domain=domain)
    return feed(basequery=basequery, domain=domain)


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


@app.route('/sitemap.xml')
def sitemap():
    sitemapxml = '<?xml version="1.0" encoding="UTF-8"?>\n'\
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    # Add job type pages to sitemap
    for item in JobType.query.all():
        sitemapxml += '  <url>\n'\
                      '    <loc>%s</loc>\n' % url_for('browse_by_type', name=item.name, _external=True) + \
                      '  </url>\n'
    # Add job category pages to sitemap
    for item in JobCategory.query.all():
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


@app.route('/search')
def search():
    now = datetime.utcnow()
    results = sorted(do_search(request.args.get('q', u''), expand=True),
        key=lambda r: getattr(r, 'datetime', now))
    results.reverse()
    return render_template('search.html', results=results, now=now, newlimit=newlimit)
