from six.moves.urllib.parse import SplitResult, urlsplit

from collections import OrderedDict
from uuid import uuid4

from sqlalchemy.exc import ProgrammingError

from flask import (
    Markup,
    Response,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from baseframe import _, request_is_xhr  # , dogpile
from coaster.utils import ParseError, for_tsquery, getbool, parse_isoformat, utcnow
from coaster.views import endpoint_for, render_with, requestargs

from .. import app, lastuser
from ..models import (
    CAMPAIGN_POSITION,
    CURRENCY,
    Board,
    BoardJobPost,
    Campaign,
    Domain,
    Filterset,
    JobApplication,
    JobCategory,
    JobLocation,
    JobPost,
    JobPostTag,
    JobType,
    Location,
    Tag,
    agelimit,
    db,
    newlimit,
    starred_job_table,
)
from ..uploads import uploaded_logos
from ..utils import string_to_number, strip_null
from ..views.helper import (
    bgroup,
    get_max_counts,
    get_post_viewcounts,
    getallposts,
    getposts,
    gettags,
    index_is_paginated,
    load_viewcounts,
    location_geodata,
    make_pay_graph,
    session_jobpost_ab,
)

allowed_index_params = {
    'l',  # Filter locations
    't',  # Filter job types
    'c',  # Filter job categories
    'currency',  # Filter currency code
    'equity',  # Filter equity flag
    'q',  # Search terms
    'startdate',  # For pagination by datetime
    'ph',  # For excluding pinned listings in additional pages
    'archive',  # Flag for loading from archive
}


def sanitized_index_params(kwargs):
    return {k: v for k, v in kwargs.items() if k in allowed_index_params}


def stickie_dict(
    post,
    url,
    pinned=False,
    show_viewcounts=False,
    show_pay=False,
    starred=False,
    is_bgroup=None,
):
    if show_viewcounts or show_pay:
        post_viewcounts = get_post_viewcounts(post.id)
    result = {
        'headline': post.headlineb if is_bgroup else post.headline,
        'url': url,
        'pinned': pinned,
        'starred': starred,
        'date': post.datetime.isoformat(),
        'location': post.location,
        'parsed_location': post.parsed_location,
        'company_name': post.company_name,
        'company_logo': post.url_for('logo'),
    }
    if show_viewcounts:
        result['viewcounts'] = {
            'listed': post_viewcounts['impressions'],
            'viewed': post_viewcounts['viewed'],
            'opened': post_viewcounts['opened'],
            'applied': post_viewcounts['applied'],
        }
    if show_pay:
        result['pay'] = post_viewcounts['pay_label']
    return result


def json_index(data):
    pinsandposts = data['pinsandposts']
    grouped = data['grouped']
    is_siteadmin = data['is_siteadmin']
    loadmore = data['loadmore']

    result = {
        'grouped': [],
        'posts': [],
        'loadmore': loadmore.isoformat() + 'Z' if loadmore else None,
    }
    if grouped:
        for grouping, group in grouped.items():
            rgroup = {'url': None, 'posts': []}

            # First, process the first item to get a URL for the entire group
            pinned, post, is_bgroup = group[0]
            if len(group) == 1:
                rgroup['url'] = post.url_for(b=is_bgroup)
            elif grouping[0] in ('sd', 'nd'):  # Grouped by domain
                rgroup['url'] = url_for('browse_by_domain', domain=grouping[1])
            elif grouping[0] in ('se', 'ne'):  # Grouped by email (webmail user)
                rgroup['url'] = url_for('browse_by_email', md5sum=grouping[1])

            for pinned, post, is_bgroup in group:
                rgroup['posts'].append(
                    stickie_dict(
                        post=post,
                        url=post.url_for(b=is_bgroup),
                        pinned=pinned,
                        is_bgroup=is_bgroup,
                        show_viewcounts=is_siteadmin
                        or g.user
                        and g.user.flags.get('is_employer_month'),
                        show_pay=is_siteadmin,
                        starred=g.user and post.id in g.starred_ids,
                    )
                )
            result['grouped'].append(rgroup)
    if pinsandposts:
        for pinned, post, is_bgroup in pinsandposts:
            result['posts'].append(
                stickie_dict(
                    post=post,
                    url=post.url_for(b=is_bgroup),
                    pinned=pinned,
                    is_bgroup=is_bgroup,
                    show_viewcounts=is_siteadmin
                    or g.user
                    and g.user.flags.get('is_employer_month'),
                    show_pay=is_siteadmin,
                    starred=g.user and post.id in g.starred_ids,
                )
            )

    return jsonify(result)


def fetch_jobposts(
    request_args,
    request_values,
    filters,
    is_index,
    board,
    board_jobs,
    gkiosk,
    basequery,
    md5sum,
    domain,
    location,
    title,
    showall,
    statusfilter,
    batched,
    ageless,
    template_vars,
    search_query=None,
    query_string=None,
):
    if basequery is None:
        basequery = JobPost.query

    # Apply request.args filters
    data_filters = {}
    f_types = filters.get('t') or request_args.getlist('t')
    while '' in f_types:
        f_types.remove('')
    f_types = [strip_null(f_type) for f_type in f_types]
    if f_types:
        data_filters['types'] = f_types
        basequery = basequery.join(JobType).filter(JobType.name.in_(f_types))
    f_categories = filters.get('c') or request_args.getlist('c')
    while '' in f_categories:
        f_categories.remove('')
    f_categories = [strip_null(f_category) for f_category in f_categories]
    if f_categories:
        data_filters['categories'] = f_categories
        basequery = basequery.join(JobCategory).filter(
            JobCategory.name.in_(f_categories)
        )

    f_domains = filters.get('d') or request_args.getlist('d')
    while '' in f_domains:
        f_domains.remove('')
    f_domains = [strip_null(f_domain) for f_domain in f_domains]
    if f_domains:
        basequery = basequery.join(Domain).filter(Domain.name.in_(f_domains))

    f_tags = filters.get('k') or request_args.getlist('k')
    while '' in f_tags:
        f_tags.remove('')
    f_tags = [strip_null(f_tag) for f_tag in f_tags]
    if f_tags:
        basequery = basequery.join(JobPostTag).join(Tag).filter(Tag.name.in_(f_tags))

    data_filters['location_names'] = r_locations = filters.get(
        'l'
    ) or request_args.getlist('l')
    if location:
        r_locations.append(location['geonameid'])
    f_locations = []
    remote_location = (
        getbool(filters.get('anywhere') or request_args.get('anywhere')) or False
    )
    if remote_location:
        data_filters['location_names'].append('anywhere')
    for rl in r_locations:
        if isinstance(rl, int) and rl > 0:
            f_locations.append(rl)
        elif rl == 'anywhere':
            remote_location = True
        elif rl.isdigit():
            f_locations.append(int(rl))
        elif rl:
            ld = location_geodata(rl)
            if ld:
                f_locations.append(ld['geonameid'])
    remote_location_query = basequery.filter(JobPost.remote_location.is_(True))
    if f_locations:
        locations_query = basequery.join(JobLocation).filter(
            JobLocation.geonameid.in_(f_locations)
        )
    else:
        locations_query = basequery.join(JobLocation)
    if f_locations and remote_location:
        data_filters['locations'] = f_locations
        data_filters['anywhere'] = True
        recency = JobPost.state.LISTED
        basequery = locations_query.filter(recency).union(
            remote_location_query.filter(recency)
        )
    elif f_locations:
        data_filters['locations'] = f_locations
        basequery = locations_query
    elif remote_location:
        data_filters['anywhere'] = True
        # Only works as a positive filter: you can't search for jobs that are NOT anywhere
        basequery = remote_location_query

    currency = filters.get('currency') or request_args.get('currency')
    if currency in CURRENCY.keys():
        data_filters['currency'] = currency
        basequery = basequery.filter(JobPost.pay_currency == currency)
        pay_graph = currency
    else:
        pay_graph = False
    if getbool(filters.get('equity') or request_args.get('equity')):
        # Only works as a positive filter: you can't search for jobs that DON'T pay in equity
        data_filters['equity'] = True
        basequery = basequery.filter(JobPost.pay_equity_min.isnot(None))

    if (
        filters.get('pay')
        or 'pay' in request_args
        or ('pmin' in request_args and 'pmax' in request_args)
    ):
        if 'pay' in request_args or filters.get('pay'):
            f_pay = (
                filters['pay']
                if filters.get('pay')
                else string_to_number(request_args['pay'])
            )
            if f_pay is not None:
                f_min = int(f_pay * 0.90)
                f_max = int(f_pay * 1.30)
            else:
                f_min = None
                f_max = None
        else:
            # Legacy URL with min/max values
            f_min = string_to_number(request_args['pmin'])
            f_max = string_to_number(request_args['pmax'])
            f_pay = f_min  # Use min for pay now
        if f_pay is not None and f_min is not None and f_max is not None:
            data_filters['pay'] = f_pay
            basequery = basequery.filter(
                JobPost.pay_cash_min < f_max, JobPost.pay_cash_max >= f_min
            )
    else:
        f_pay = None
        f_min = None
        f_max = None

    if getbool(request_args.get('archive')):
        ageless = True
        data_filters['archive'] = True
        statusfilter = JobPost.state.ARCHIVED

    if query_string:
        data_filters['query'] = search_query
        data_filters['query_string'] = query_string
        basequery = basequery.filter(
            JobPost.search_vector.match(search_query, postgresql_regconfig='english')
        )

    if data_filters:
        showall = True
        batched = True

    posts = getposts(
        basequery,
        pinned=True,
        showall=showall,
        statusfilter=statusfilter,
        ageless=ageless,
    ).all()

    if getbool(request_args.get('embed')):
        embed = True  # skipcq: PYL-W0621
        if posts:
            limit = string_to_number(request_args.get('limit'))
            if limit is not None:
                posts = posts[:limit]
            else:
                posts = posts[:8]
    else:
        embed = False

    if posts:
        employer_name = posts[0].company_name
    else:
        employer_name = 'a single employer'

    jobpost_ab = session_jobpost_ab()
    if is_index and posts and not gkiosk and not embed:
        # Group posts by email_domain on index page only, when not in kiosk mode
        grouped = OrderedDict()
        for post in posts:
            pinned = post.pinned
            if board is not None:
                # board_jobs only contains the last 30 days, no archive
                blink = board_jobs.get(post.id)
                if blink is not None:
                    pinned = blink.pinned
            if pinned:
                # Make pinned posts appear in a group of one
                grouped.setdefault(('s', post.hashid), []).append(
                    (pinned, post, bgroup(jobpost_ab, post))
                )
            elif post.state.ANNOUNCEMENT:
                # Make announcements also appear in a group of one
                grouped.setdefault(('a', post.hashid), []).append(
                    (pinned, post, bgroup(jobpost_ab, post))
                )
            elif post.domain.is_webmail:
                grouped.setdefault(('ne', post.md5sum), []).append(
                    (pinned, post, bgroup(jobpost_ab, post))
                )
            else:
                grouped.setdefault(('nd', post.email_domain), []).append(
                    (pinned, post, bgroup(jobpost_ab, post))
                )
        pinsandposts = None
    else:
        grouped = None
        if board:
            pinsandposts = []
            for post in posts:
                pinned = post.pinned
                if board is not None:
                    # board_jobs only contains the last 30 days, no archive
                    blink = board_jobs.get(post.id)
                    if blink is not None:
                        pinned = blink.pinned
                pinsandposts.append((pinned, post, bgroup(jobpost_ab, post)))
        else:
            pinsandposts = [
                (post.pinned, post, bgroup(jobpost_ab, post)) for post in posts
            ]

    # Pick a header campaign (only if not kiosk or an XHR reload)
    pay_graph_data = None

    loadmore = False
    if batched:
        # Figure out where the batch should start from
        startdate = None
        if 'startdate' in request_values:
            try:
                startdate = parse_isoformat(
                    request_values['startdate'].upper(), naive=False
                )
            except (ParseError, ValueError):
                abort(400)

        batchsize = 32

        # list of posts that were pinned at the time of first load
        pinned_hashids = request_args.getlist('ph')
        # Depending on the display mechanism (grouped or ungrouped), extract the batch
        if grouped:
            if not startdate:
                startindex = 0
                for row in grouped.values():
                    # break when a non-pinned post is encountered
                    if not row[0][0]:
                        break
                    else:
                        pinned_hashids.append(row[0][1].hashid)
            else:
                # Loop through group looking for start of next batch. See below to understand the
                # nesting structure of 'grouped'
                for startindex, row in enumerate(grouped.values()):  # noqa: B007
                    # Skip pinned posts when looking for starting index
                    if (
                        row[0][1].hashid not in pinned_hashids
                        and row[0][1].datetime < startdate
                    ):
                        break

            batch = list(grouped.items())[startindex : startindex + batchsize]
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
                for startindex, row in enumerate(pinsandposts):  # noqa: B007
                    # Skip pinned posts when looking for starting index
                    if (
                        row[1].hashid not in pinned_hashids
                        and row[1].datetime < startdate
                    ):
                        break

            batch = pinsandposts[startindex : startindex + batchsize]
            if startindex + batchsize < len(pinsandposts):
                # batch = [(pinned, post), ...]
                loadmore = batch[-1][1].datetime
            pinsandposts = batch

    query_params = request_args.to_dict(flat=False)
    if loadmore:
        query_params.update({'startdate': loadmore.isoformat(), 'ph': pinned_hashids})
    if location:
        data_filters['location_names'].append(location['name'])
        query_params.update({'l': location['name']})

    if pay_graph:
        pay_graph_data = make_pay_graph(pay_graph, posts, rmin=f_min, rmax=f_max)

    return {
        'posts': posts,
        'pinsandposts': pinsandposts,
        'grouped': grouped,
        'newlimit': newlimit,
        'title': title,
        'md5sum': md5sum,
        'domain': domain,
        'location': location,
        'employer_name': employer_name,
        'showall': showall,
        'f_locations': f_locations,
        'loadmore': loadmore,
        'query_params': sanitized_index_params(query_params),
        'data_filters': data_filters,
        'pay_graph_data': pay_graph_data,
        'paginated': index_is_paginated(),
        'template_vars': template_vars,
        'embed': embed,
    }


# @dogpile.region('hasjob_index')
def fetch_cached_jobposts(
    request_args,
    request_values,
    filters,
    is_index,
    board,
    board_jobs,
    gkiosk,
    basequery,
    md5sum,
    domain,
    location,
    title,
    showall,
    statusfilter,
    batched,
    ageless,
    template_vars,
    search_query=None,
    query_string=None,
):
    return fetch_jobposts(
        request_args,
        request_values,
        filters,
        is_index,
        board,
        board_jobs,
        gkiosk,
        basequery,
        md5sum,
        domain,
        location,
        title,
        showall,
        statusfilter,
        batched,
        ageless,
        template_vars,
        search_query,
        query_string,
    )


@app.route('/', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/', methods=['GET', 'POST'])
@render_with(
    {'text/html': 'index.html.jinja2', 'application/json': json_index}, json=False
)
def index(
    basequery=None,
    filters=None,
    md5sum=None,
    tag=None,
    domain=None,
    location=None,
    title=None,
    showall=True,
    statusfilter=None,
    batched=True,
    ageless=False,
    cached=False,
    query_string=None,
    filterset=None,
    template_vars=None,
):
    if filters is None:
        filters = {}
    if template_vars is None:
        template_vars = {}

    now = utcnow()
    is_siteadmin = lastuser.has_permission('siteadmin')
    board = g.board

    if board:
        board_jobs = {
            r.jobpost_id: r
            for r in BoardJobPost.query.join(BoardJobPost.jobpost)
            .filter(BoardJobPost.board == g.board, JobPost.state.LISTED)
            .options(db.load_only('jobpost_id', 'pinned'))
            .all()
        }

    else:
        board_jobs = {}

    if basequery is None:
        is_index = True
    else:
        is_index = False
    if basequery is None and not (
        g.user or g.kiosk or (board and not board.require_login)
    ):
        showall = False
        batched = False

    # `query_string` is user-supplied
    # `search_query` is PostgreSQL syntax
    if not query_string:
        query_string = request.args.get('q')
    if query_string:
        search_query = for_tsquery(query_string)
        try:
            # TODO: Can we do syntax validation without a database roundtrip?
            db.session.query(db.func.to_tsquery(search_query)).all()
        except ProgrammingError:
            db.session.rollback()
            g.event_data['search_syntax_error'] = (query_string, search_query)
            if not request_is_xhr():
                flash(
                    _("Search terms ignored because this didn’t parse: {query}").format(
                        query=search_query
                    ),
                    'danger',
                )
            search_query = None
    else:
        search_query = None

    if cached:
        data = fetch_cached_jobposts(
            request.args,
            request.values,
            filters,
            is_index,
            board,
            board_jobs,
            g.kiosk,
            basequery,
            md5sum,
            domain,
            location,
            title,
            showall,
            statusfilter,
            batched,
            ageless,
            template_vars,
            search_query,
            query_string,
        )
    else:
        data = fetch_jobposts(
            request.args,
            request.values,
            filters,
            is_index,
            board,
            board_jobs,
            g.kiosk,
            basequery,
            md5sum,
            domain,
            location,
            title,
            showall,
            statusfilter,
            batched,
            ageless,
            template_vars,
            search_query,
            query_string,
        )

    if data['data_filters']:
        # For logging
        g.event_data['filters'] = data['data_filters']

    if g.user:
        g.starred_ids = set(g.user.starred_job_ids(agelimit if not ageless else None))
    else:
        g.starred_ids = set()

    if is_siteadmin or (g.user and g.user.flags.get('is_employer_month')):
        load_viewcounts(data['posts'])
        show_viewcounts = True
    else:
        show_viewcounts = False

    if data['grouped']:
        g.impressions = {
            post.id: (pinflag, post.id, is_bgroup)
            for group in data['grouped'].values()
            for pinflag, post, is_bgroup in group
        }
    elif data['pinsandposts']:
        g.impressions = {
            post.id: (pinflag, post.id, is_bgroup)
            for pinflag, post, is_bgroup in data['pinsandposts']
        }

    if not g.kiosk:
        if g.preview_campaign:
            header_campaign = g.preview_campaign
        else:
            geonameids = g.user_geonameids + data['f_locations']
            header_campaign = Campaign.for_context(
                CAMPAIGN_POSITION.HEADER,
                board=g.board,
                user=g.user,
                anon_user=g.anon_user,
                geonameids=geonameids,
            )
    else:
        header_campaign = None

    # Test values for development:
    # if not g.user_geonameids:
    #     g.user_geonameids = [1277333, 1277331, 1269750]
    if (
        not location
        and 'l' not in request.args
        and g.user_geonameids
        and (g.user or g.anon_user)
        and ((not g.board.auto_locations) if g.board else True)
    ):
        # No location filters? Prompt the user
        ldata = location_geodata(g.user_geonameids)
        location_prompts = [
            ldata[geonameid] for geonameid in g.user_geonameids if geonameid in ldata
        ]
    else:
        location_prompts = []

    data['header_campaign'] = header_campaign
    data['now'] = now
    data['is_siteadmin'] = is_siteadmin
    data['location_prompts'] = location_prompts
    if data['domain'] and data['domain'] not in db.session:
        data['domain'] = db.session.merge(data['domain'])
    data['show_viewcounts'] = show_viewcounts

    max_counts = get_max_counts()
    data['max_impressions'] = max_counts['max_impressions']
    data['max_views'] = max_counts['max_views']
    data['max_opens'] = max_counts['max_opens']
    data['max_applied'] = max_counts['max_applied']

    if filterset:
        data['filterset'] = filterset

    return data


@app.route('/drafts', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/drafts', methods=['GET', 'POST'])
@lastuser.requires_login
def browse_drafts():
    basequery = JobPost.query.filter_by(user=g.user)
    return index(
        basequery=basequery,
        ageless=True,
        statusfilter=JobPost.state.UNPUBLISHED,
        cached=False,
    )


@app.route('/my', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/my', methods=['GET', 'POST'])
@lastuser.requires_login
def my_posts():
    basequery = JobPost.query.filter_by(user=g.user)
    return index(
        basequery=basequery, ageless=True, statusfilter=JobPost.state.MY, cached=False
    )


@app.route('/bookmarks', subdomain='<subdomain>')
@app.route('/bookmarks')
@lastuser.requires_login
def bookmarks():
    basequery = JobPost.query.join(starred_job_table).filter(
        starred_job_table.c.user_id == g.user.id
    )
    return index(
        basequery=basequery,
        ageless=True,
        statusfilter=JobPost.state.ARCHIVED,
        cached=False,
    )


@app.route('/applied', subdomain='<subdomain>')
@app.route('/applied')
@lastuser.requires_login
def applied():
    basequery = JobPost.query.join(JobApplication).filter(JobApplication.user == g.user)
    return index(
        basequery=basequery,
        ageless=True,
        statusfilter=JobPost.state.ARCHIVED,
        cached=False,
    )


@app.route('/type/<name>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/type/<name>', methods=['GET', 'POST'])
def browse_by_type(name):
    if name == 'all':
        return redirect(url_for('index'))
    return redirect(url_for('index', t=name), code=302)


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


@app.route('/category/<name>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/category/<name>', methods=['GET', 'POST'])
def browse_by_category(name):
    if name == 'all':
        return redirect(url_for('index'))
    return redirect(url_for('index', c=name), code=302)


@app.route('/by/<md5sum>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/by/<md5sum>', methods=['GET', 'POST'])
def browse_by_email(md5sum):
    if not md5sum:
        abort(404)
    basequery = JobPost.query.filter_by(md5sum=md5sum)
    jobpost = basequery.first_or_404()
    jobpost_user = jobpost.user
    return index(
        basequery=basequery,
        md5sum=md5sum,
        showall=True,
        cached=False,
        template_vars={'jobpost_user': jobpost_user},
    )


@app.route('/in/<location>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/in/<location>', methods=['GET', 'POST'])
def browse_by_location(location):
    loc = Location.get(location, g.board)
    if loc:
        geodata = {
            'geonameid': loc.id,
            'name': loc.name,
            'use_title': loc.title,
            'description': Markup(loc.description),
        }
    else:
        return redirect(url_for('index', l=location), code=302)
    if location != geodata['name']:
        return redirect(url_for('browse_by_location', location=geodata['name']))
    return index(location=geodata, title=geodata['use_title'])


@app.route('/in/anywhere', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/in/anywhere', methods=['GET', 'POST'])
def browse_by_anywhere():
    return redirect(url_for('index', l='anywhere'), code=302)


@app.route('/tag/<tag>', methods=['GET', 'POST'], subdomain='<subdomain>')
@app.route('/tag/<tag>', methods=['GET', 'POST'])
def browse_by_tag(tag):
    tag = Tag.query.filter_by(name=tag).first_or_404()
    basequery = JobPost.query.filter(
        db.and_(JobPostTag.jobpost_id == JobPost.id, JobPostTag.tag == tag)
    )
    return index(basequery=basequery, tag=tag, title=tag.title)


@app.route('/tag', subdomain='<subdomain>')
@app.route('/tag')
def browse_tags():
    return render_template(
        'tags.html.jinja2', tags=gettags(alltime=getbool(request.args.get('all')))
    )


# POST is required for pagination
@app.route('/f/<name>', subdomain='<subdomain>', methods=['GET', 'POST'])
@app.route('/f/<name>', methods=['GET', 'POST'])
@Filterset.is_url_for('view')
def filterset_view(name):
    filterset = Filterset.get(g.board, name)
    if not filterset:
        abort(404)
    return index(
        filters=filterset.to_filters(translate_geonameids=True),
        query_string=filterset.keywords,
        filterset=filterset,
        title=filterset.title,
    )


@app.route('/opensearch.xml', subdomain='<subdomain>')
@app.route('/opensearch.xml')
def opensearch():
    return Response(
        render_template('opensearch.xml'),
        mimetype='application/opensearchdescription+xml',
    )


@app.route('/feed', subdomain='<subdomain>')
@app.route('/feed')
def feed(
    basequery=None,
    type=None,  # noqa: A002
    category=None,
    md5sum=None,
    domain=None,
    location=None,
    tag=None,
    title=None,
):
    title = "All jobs"
    if type:
        title = type.title
    elif category:
        title = category.title
    elif md5sum or domain:
        title = "Jobs at a single employer"
    elif location:
        title = "Jobs in {location}".format(location=location['use_title'])
    elif tag:
        title = f"Jobs tagged {title}"
    posts = list(getposts(basequery, showall=True, limit=100))
    if posts:  # Can't do this unless posts is a list
        updated = posts[0].datetime.isoformat() + 'Z'
        if md5sum:
            title = posts[0].company_name
    else:
        updated = utcnow().isoformat() + 'Z'
    return Response(
        render_template('feed-atom.xml', posts=posts, updated=updated, title=title),
        content_type='application/atom+xml; charset=utf-8',
    )


@app.route('/feed/indeed', subdomain='<subdomain>')
@app.route('/feed/indeed')
def feed_indeed():
    title = "All jobs"
    posts = list(getposts(None, showall=True))
    if posts:  # Can't do this unless posts is a list
        updated = posts[0].datetime.isoformat() + 'Z'
    else:
        updated = utcnow().isoformat() + 'Z'
    return Response(
        render_template('feed-indeed.xml', posts=posts, updated=updated, title=title),
        content_type='textxml; charset=utf-8',
    )


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
    basequery = JobPost.query.filter(
        db.and_(
            JobLocation.jobpost_id == JobPost.id,
            JobLocation.geonameid == geodata['geonameid'],
        )
    )
    return feed(basequery=basequery, location=geodata)


@app.route('/in/anywhere/feed', subdomain='<subdomain>')
@app.route('/in/anywhere/feed')
def feed_by_anywhere():
    basequery = JobPost.query.filter(JobPost.remote_location.is_(True))
    return feed(basequery=basequery)


@app.route('/tag/<tag>/feed', subdomain='<subdomain>')
@app.route('/tag/<tag>/feed')
def feed_by_tag(tag):
    tag = Tag.query.filter_by(name=tag).first_or_404()
    basequery = JobPost.query.filter(
        db.and_(JobPostTag.jobpost_id == JobPost.id, JobPostTag.tag == tag)
    )
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
        return url_for(
            'archive',
            order_by=order_by,
            reverse=reverse,
            start=request.args.get('start'),
            limit=request.args.get('limit'),
        )

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
    count, posts = getallposts(
        order_by=order_by, desc=reverse, start=start, limit=limit
    )

    if request_is_xhr():
        tmpl = 'archive_inner.html.jinja2'
    else:
        tmpl = 'archive.html.jinja2'
    return render_template(
        tmpl,
        order_by=request.args.get('order_by'),
        posts=posts,
        start=start,
        limit=limit,
        count=count,
        # Pass some functions
        min=min,
        max=max,
        sortarchive=sortarchive,
    )


@app.route('/sitemap.xml', defaults={'key': None}, subdomain='<subdomain>')
@app.route('/sitemap.xml', defaults={'key': None})
@app.route('/sitemap.xml/<key>', subdomain='<subdomain>')
@app.route('/sitemap.xml/<key>')
def sitemap(key):
    authorized_sitemap = key == app.config.get('SITEMAP_KEY')

    sitemapxml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    )
    # Add featured boards to sitemap
    board_ids = []
    for board in Board.query.filter_by(featured=True).all():
        board_ids.append(board.id)
        sitemapxml += (
            '  <url>\n'
            '    <loc>{url}</loc>\n'
            '    <lastmod>{updated_at}</lastmod>\n'
            '    <changefreq>monthly</changefreq>\n'
            '  </url>\n'.format(
                url=board.url_for(_external=True),
                updated_at=board.updated_at.isoformat(),
            )
        )

    # Add filtered views to sitemap
    for item in Filterset.query.all():
        sitemapxml += (
            '  <url>\n'
            '    <loc>{url}</loc>\n'
            '    <lastmod>{updated_at}</lastmod>\n'
            '    <changefreq>daily</changefreq>\n'
            '  </url>\n'.format(
                url=item.url_for(_external=True), updated_at=item.updated_at.isoformat()
            )
        )

    # Add locations to sitemap
    for item in Location.query.filter(Location.board_id.in_(board_ids)).all():
        sitemapxml += (
            '  <url>\n'
            '    <loc>{url}</loc>\n'
            '    <lastmod>{updated_at}</lastmod>\n'
            '    <changefreq>monthly</changefreq>\n'
            '  </url>\n'.format(
                url=item.url_for(_external=True), updated_at=item.updated_at.isoformat()
            )
        )
    # Add live posts to sitemap
    for post in getposts(showall=True):
        sitemapxml += (
            '  <url>\n'
            '    <loc>{url}</loc>\n'
            '    <lastmod>{updated_at}</lastmod>\n'
            '    <changefreq>monthly</changefreq>\n'
            '  </url>\n'.format(
                url=post.url_for(_external=True), updated_at=post.datetime.isoformat()
            )
        )
    if authorized_sitemap:
        # Add domains to sitemap
        for domain in (
            Domain.query.filter(
                Domain.title.isnot(None),
                Domain.description.isnot(None),
                Domain.description != '',
            )
            .order_by(Domain.updated_at.desc())
            .all()
        ):
            sitemapxml += (
                '  <url>\n'
                '    <loc>{url}</loc>\n'
                '    <lastmod>{updated_at}</lastmod>\n'
                '    <changefreq>monthly</changefreq>\n'
                '  </url>\n'.format(
                    url=domain.url_for(_external=True),
                    updated_at=domain.updated_at.isoformat(),
                )
            )
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
    if post.state.UNACCEPTABLE:
        # Don't show logo if post has been rejected. Could be spam
        abort(410)
    return redirect(uploaded_logos.url(post.company_logo))


@app.route('/search', subdomain='<subdomain>')
@app.route('/search')
def search():
    return redirect(url_for('index', **sanitized_index_params(request.args)))


@app.route('/api/1/template/offline', subdomain='<subdomain>')
@app.route('/api/1/template/offline')
def offline():
    return render_template('offline.html.jinja2')


@app.route('/service-worker.js', methods=['GET'], subdomain='<subdomain>')
@app.route('/service-worker.js', methods=['GET'])
def sw():
    return app.send_static_file('service-worker.js')


@app.route('/manifest.json', methods=['GET'], subdomain='<subdomain>')
@app.route('/manifest.json', methods=['GET'])
def manifest():
    return Response(
        render_template('manifest.json.jinja2'), mimetype='application/json'
    )


@app.route('/api/1/embed.js', methods=['GET'], subdomain='<subdomain>')
@app.route('/api/1/embed.js', methods=['GET'])
def embed():
    return app.send_static_file('embed.js')


# For oEmbed. Needs to be moved somewhere better maintained than this.
embed_index_views = [
    'index',
    'browse_drafts',
    'browse_by_anywhere',
    'browse_by_category',
    'browse_by_domain',
    'browse_by_email',
    'browse_by_location',
    'browse_by_tag',
    'browse_by_type',
]


@app.route('/api/1/oembed', methods=['GET'])
@requestargs('url')
def oembed(url):
    """
    Endpoint to support oEmbed (see https://oembed.com/). Example request::

        https://hasjob.co/api/1/oembed?url=https://hasjob.co/

    Required for services like embed.ly, which need a registered oEmbed API handler.
    """

    endpoint, view_args = endpoint_for(url)
    if endpoint not in embed_index_views:
        return jsonify({})

    board = Board.get(view_args.get('subdomain', 'www'))
    iframeid = 'hasjob-iframe-' + str(uuid4())

    parsed_url = urlsplit(url)
    embed_url = SplitResult(
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.query
        + ('&' if parsed_url.query else '')
        + 'embed=1&iframeid='
        + iframeid,
        parsed_url.fragment,
    ).geturl()

    return jsonify(
        {
            'provider_url': url_for('index', subdomain=None, _external=True),
            'provider_name': app.config['SITE_TITLE'],
            'thumbnail_width': 200,
            'thumbnail_height': 200,
            'thumbnail_url': url_for(
                'static', filename='img/hasjob-logo-200x200.png', _external=True
            ),
            'author_name': board.title if board else app.config['SITE_TITLE'],
            'author_url': board.url_for(_external=True)
            if board
            else url_for('index', subdomain=None, _external=True),
            'title': ' | '.join([board.title, board.caption])
            if board
            else app.config['SITE_TITLE'],
            'html': (
                '<iframe id="{iframeid}" src="{url}" '
                'width="100%" height="724" frameborder="0" scrolling="no">'.format(
                    url=embed_url, iframeid=iframeid
                )
            ),
            'version': '1.0',
            'type': 'rich',
        }
    )

    return jsonify({})
