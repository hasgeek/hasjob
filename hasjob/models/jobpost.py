from datetime import datetime
from werkzeug import cached_property
from coaster.sqlalchemy import timestamp_columns
from baseframe import cache
from . import agelimit, db, POSTSTATUS, EMPLOYER_RESPONSE, BaseMixin, TimestampMixin
from .jobtype import JobType
from .jobcategory import JobCategory
from .user import User
from ..utils import random_long_key, random_hash_key
import re, requests


class JobPost(BaseMixin, db.Model):
    __tablename__ = 'jobpost'
    idref = 'post'

    # Metadata
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship(User, primaryjoin=user_id == User.id, backref='jobposts')
    hashid = db.Column(db.String(5), nullable=False, unique=True)
    datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Published
    closed_datetime = db.Column(db.DateTime, nullable=True)  # If withdrawn or rejected
    sticky = db.Column(db.Boolean, nullable=False, default=False)

    # Job description
    headline = db.Column(db.Unicode(100), nullable=False)
    type_id = db.Column(None, db.ForeignKey('jobtype.id'), nullable=False)
    type = db.relation(JobType, primaryjoin=type_id == JobType.id)
    category_id = db.Column(None, db.ForeignKey('jobcategory.id'), nullable=False)
    category = db.relation(JobCategory, primaryjoin=category_id == JobCategory.id)
    location = db.Column(db.Unicode(80), nullable=False)
    relocation_assist = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.UnicodeText, nullable=False)
    perks = db.Column(db.UnicodeText, nullable=False)
    how_to_apply = db.Column(db.UnicodeText, nullable=False)
    hr_contact = db.Column(db.Boolean, nullable=True)

    # Company details
    company_name = db.Column(db.Unicode(80), nullable=False)
    company_logo = db.Column(db.Unicode(255), nullable=True)
    company_url = db.Column(db.Unicode(255), nullable=False, default=u'')
    fullname = db.Column(db.Unicode(80), nullable=True)
    email = db.Column(db.Unicode(80), nullable=False)
    email_domain = db.Column(db.Unicode(80), nullable=False, index=True)
    md5sum = db.Column(db.String(32), nullable=False, index=True)

    # Payment, audit and workflow fields
    words = db.Column(db.UnicodeText, nullable=True)  # All words in description, perks and how_to_apply
    promocode = db.Column(db.String(40), nullable=True)
    status = db.Column(db.Integer, nullable=False, default=POSTSTATUS.DRAFT)
    ipaddr = db.Column(db.String(45), nullable=False)
    useragent = db.Column(db.Unicode(250), nullable=True)
    edit_key = db.Column(db.String(40), nullable=False, default=random_long_key)
    email_verify_key = db.Column(db.String(40), nullable=False, default=random_long_key)
    email_sent = db.Column(db.Boolean, nullable=False, default=False)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    payment_value = db.Column(db.Integer, nullable=False, default=0)
    payment_received = db.Column(db.Boolean, nullable=False, default=False)
    reviewer_id = db.Column(None, db.ForeignKey('user.id'), nullable=True)
    reviewer = db.relationship(User, primaryjoin=reviewer_id == User.id, backref="reviewed_posts")
    review_datetime = db.Column(db.DateTime, nullable=True)
    review_comments = db.Column(db.Unicode(250), nullable=True)

    admins = db.relationship(User, secondary=lambda: jobpost_admin_table)

    def admin_is(self, user):
        if user is None:
            return False
        return user == self.user or user in self.admins

    def is_draft(self):
        return self.status == POSTSTATUS.DRAFT

    def is_listed(self):
        now = datetime.utcnow()
        return (self.status in [POSTSTATUS.CONFIRMED, POSTSTATUS.REVIEWED]) and (
            self.datetime > now - agelimit)

    def is_flagged(self):
        return self.status == POSTSTATUS.FLAGGED

    def is_old(self):
        return self.datetime <= datetime.utcnow() - agelimit

    def search_mapping(self):
        """
        Returns a dictionary suitable for search indexing.
        """
        content = '\n'.join((self.headline,
                            self.location,
                            self.company_name,
                            self.company_url,
                            self.description,
                            self.perks))

        return {'title': self.headline,
                'content': content,
                'public': self.is_listed(),
                'idref': u'%s/%s' % (self.idref, self.id),
                }

    @cached_property  # For multiple accesses in a single request
    def viewcounts(self):
        return viewcounts_by_id(self.id)

    @cached_property  # For multiple accesses in a single request
    def viewstats(self):
        now = datetime.utcnow()
        delta = now - self.datetime
        if delta.days < 2:  # Less than two days
            if delta.seconds < 21600:  # Less than 6 hours
                return 'q', viewstats_by_id_qhour(self.id)
            else:
                return 'h', viewstats_by_id_hour(self.id)
        else:
            return 'd', viewstats_by_id_day(self.id)

    def reports(self):
        if not self.flags:
            return []
        counts = {}
        for flag in self.flags:
            counts[flag.reportcode] = counts.setdefault(flag.reportcode, 0) + 1
        return [{'count': i[2], 'title': i[1]} for i in sorted([(k.seq, k.title, v) for k, v in counts.items()])]


@cache.memoize(timeout=86400)
def viewcounts_by_id(jobpost_id):
    return {
        'viewed': UserJobView.query.filter_by(jobpost_id=jobpost_id).count(),
        'opened': UserJobView.query.filter_by(jobpost_id=jobpost_id, applied=True).count(),
        'applied': JobApplication.query.filter_by(jobpost_id=jobpost_id).count()
        }


def viewstats_helper(jobpost_id, interval, limit, daybatch=False):
    post = JobPost.query.get(jobpost_id)
    if not post.datetime:
        return {}
    viewed = UserJobView.query.filter_by(jobpost_id=jobpost_id).all()
    opened = [v for v in viewed if v.applied == True]
    applied = db.session.query(JobApplication.created_at).filter_by(jobpost_id=jobpost_id).all()

    # Now batch them by size
    now = datetime.utcnow()
    delta = now - post.datetime
    if daybatch:
        batches, remainder = divmod(delta.days, interval)
        if delta.seconds:
            remainder = True
    else:
        batches, remainder = divmod(int(delta.total_seconds()), interval)

    if remainder or batches == 0:
        batches += 1

    cviewed = batches * [0]
    copened = batches * [0]
    capplied = batches * [0]

    for clist, source, attr in [
            (cviewed, viewed, 'created_at'),
            (copened, opened, 'updated_at'),
            (capplied, applied, 'created_at')]:
        for item in source:
            sourcedate = getattr(item, attr)
            if sourcedate < post.datetime:
                # This happens when the user creates a listing when logged in. Their 'viewed' date will be
                # for the draft, whereas the confirmed listing's datetime will be later. There should
                # be just one instance of this.
                sourcedate = post.datetime
            itemdelta = sourcedate - post.datetime
            if daybatch:
                clist[int(itemdelta.days // interval)] += 1
            else:
                clist[int(int(itemdelta.total_seconds()) // interval)] += 1

    if limit and batches > limit:
        cviewed = cviewed[:limit]
        copened = copened[:limit]
        capplied = capplied[:limit]

    return {
        'max': max([max(cviewed), max(copened), max(capplied)]),
        'length': max([len(cviewed), len(copened), len(capplied)]),
        'viewed': cviewed,
        'opened': copened,
        'applied': capplied,
        }


@cache.memoize(timeout=900)
def viewstats_by_id_qhour(jobpost_id):
    return viewstats_helper(jobpost_id, 900, 24)


@cache.memoize(timeout=3600)
def viewstats_by_id_hour(jobpost_id):
    return viewstats_helper(jobpost_id, 3600, 48)


@cache.memoize(timeout=86400)
def viewstats_by_id_day(jobpost_id):
    return viewstats_helper(jobpost_id, 1, 30, daybatch=True)


jobpost_admin_table = db.Table('jobpost_admin', db.Model.metadata,
    *(timestamp_columns + (
    db.Column('user_id', None, db.ForeignKey('user.id'), primary_key=True),
    db.Column('jobpost_id', None, db.ForeignKey('jobpost.id'), primary_key=True)
    )))


class UserJobView(TimestampMixin, db.Model):
    __tablename__ = 'userjobview'
    #: User who saw a listing
    user_id = db.Column(None, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship(User)
    #: Job listing they saw
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), primary_key=True)
    jobpost = db.relationship(JobPost)
    #: Has the user viewed apply instructions?
    applied = db.Column(db.Boolean, default=False, nullable=False)


class JobApplication(BaseMixin, db.Model):
    __tablename__ = 'job_application'
    #: Hash id (to hide database ids)
    hashid = db.Column(db.String(40), nullable=False, unique=True)
    #: User who applied for this listing
    user_id = db.Column(None, db.ForeignKey('user.id'))
    user = db.relationship(User, foreign_keys=user_id)
    #: Job listing they applied to
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'))
    #: User's email address
    email = db.Column(db.Unicode(80), nullable=False)
    #: User's phone number
    phone = db.Column(db.Unicode(80), nullable=False)
    #: User's message
    message = db.Column(db.UnicodeText, nullable=False)
    #: Employer's response code
    response = db.Column(db.Integer, nullable=False, default=EMPLOYER_RESPONSE.NEW)
    #: Employer's response message
    response_message = db.Column(db.UnicodeText, nullable=True)
    #: Bag of words, for spam analysis
    words = db.Column(db.UnicodeText, nullable=True)
    #: Admin who replied for this listing
    replied_by_id = db.Column(None, db.ForeignKey('user.id'), nullable=True)
    replied_by = db.relationship(User, foreign_keys=replied_by_id)

    def __init__(self, **kwargs):
        super(JobApplication, self).__init__(**kwargs)
        if self.hashid is None:
            self.hashid = unique_long_hash()

    @property
    def status(self):
        return EMPLOYER_RESPONSE[self.response]

    def is_new(self):
        return self.response == EMPLOYER_RESPONSE.NEW

    def is_pending(self):
        return self.response == EMPLOYER_RESPONSE.PENDING

    def is_ignored(self):
        return self.response == EMPLOYER_RESPONSE.IGNORED

    def is_replied(self):
        return self.response == EMPLOYER_RESPONSE.REPLIED

    def is_flagged(self):
        return self.response == EMPLOYER_RESPONSE.FLAGGED

    def is_spam(self):
        return self.response == EMPLOYER_RESPONSE.SPAM

    def is_rejected(self):
        return self.response == EMPLOYER_RESPONSE.REJECTED

    def can_reply(self):
        return self.response in (EMPLOYER_RESPONSE.NEW, EMPLOYER_RESPONSE.PENDING, EMPLOYER_RESPONSE.IGNORED)

    def can_reject(self):
        return self.response in (EMPLOYER_RESPONSE.NEW, EMPLOYER_RESPONSE.PENDING, EMPLOYER_RESPONSE.IGNORED)

    def can_ignore(self):
        return self.response in (EMPLOYER_RESPONSE.NEW, EMPLOYER_RESPONSE.PENDING)

    def can_report(self):
        return self.response in (EMPLOYER_RESPONSE.NEW, EMPLOYER_RESPONSE.PENDING,
            EMPLOYER_RESPONSE.IGNORED, EMPLOYER_RESPONSE.REJECTED)


JobApplication.jobpost = db.relationship(JobPost,
    backref=db.backref('applications', order_by=(
        db.case(value=JobApplication.response, whens={
            EMPLOYER_RESPONSE.NEW: 0,
            EMPLOYER_RESPONSE.PENDING: 1,
            EMPLOYER_RESPONSE.IGNORED: 2,
            EMPLOYER_RESPONSE.REPLIED: 3,
            EMPLOYER_RESPONSE.REJECTED: 4,
            EMPLOYER_RESPONSE.FLAGGED: 5,
            EMPLOYER_RESPONSE.SPAM: 6
            }),
        db.desc(JobApplication.created_at)), cascade='all, delete-orphan'))


class GeoJobView(db.Model):
    __tablename__ = 'geojobview'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'))
    jobpost = db.relationship(JobPost)
    geo_id = db.Column(db.Integer,nullable=False)

    def __repr__(self):
        return "<GeoJobView %s %s>" % (self.geonameid, self.name)


def add_geoview(jobpost_id, geoid):
    count = GeoJobView.query.count() + 1
    for i in geoid:
        temp = GeoJobView(id=count)
        count += 1
        temp.jobpost_id = jobpost_id
        temp.geo_id = i
        db.session.add(temp)


def insert_geotag(jobpost_id, location):
    geoid_list = get_geoid(location)
    add_geoview(jobpost_id, geoid_list)


def get_geoid(text=''):
    loc_list = text2location(text)
    geoid = list()
    for i in loc_list:
        geoid += loc_request(i)
    return geoid


# Right now using a simple parser
# What has to be done for Anywhere
def text2location(text=''):
    SPLIT_RE = re.compile(" ?, ?| or | ?/ ?")
    loc_list = re.split(SPLIT_RE, text)
    loc_list.append(text)
    loc_list = filter(None, loc_list)
    return loc_list


def loc_request(name='', formatted=True, maxRows=1, lang='en', username='thanmaim', style='full'):
    base = 'http://api.geonames.org/searchJSON'
    uri = base + '?formatted=' + str(formatted).lower()
    uri += '&q=' + name
    uri += '&maxRows=' + str(maxRows)
    uri += '&lang=' + lang
    uri += '&username=' + username
    uri += '&style=' + style
    headers = {'Accept': 'application/json'}
    response = requests.get(uri)
    if response.status_code == 200:
        try:
            geonames = response.json()["geonames"]
            return [g['geonameId'] for g in geonames]
        except KeyError, e:
            return response_format(list())
    else:
        return list()


def unique_hash(model=JobPost):
    """
    Returns a unique hash for a given model
    """
    while 1:
        hashid = random_hash_key()
        if model.query.filter_by(hashid=hashid).count() == 0:
            break
    return hashid


def unique_long_hash(model=JobApplication):
    """
    Returns a long unique hash for a given model
    """
    while 1:
        hashid = random_long_key()
        if model.query.filter_by(hashid=hashid).count() == 0:
            break
    return hashid
