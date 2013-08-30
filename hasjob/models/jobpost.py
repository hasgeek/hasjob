from datetime import datetime
from werkzeug import cached_property
from baseframe import cache
from coaster.sqlalchemy import TimestampMixin
from hasjob.models import agelimit, db, POSTSTATUS
from hasjob.models.jobtype import JobType
from hasjob.models.jobcategory import JobCategory
from hasjob.models.user import User
from hasjob.utils import random_long_key, random_hash_key


class JobPost(db.Model):
    __tablename__ = 'jobpost'
    idref = 'post'

    # Metadata
    id = db.Column(db.Integer, primary_key=True)
    hashid = db.Column(db.String(5), nullable=False, unique=True)
    created_datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Published
    closed_datetime = db.Column(db.DateTime, nullable=True)  # If withdrawn or rejected
    #modified_datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    sticky = db.Column(db.Boolean, nullable=False, default=False)

    # Job description
    headline = db.Column(db.Unicode(100), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('jobtype.id'), nullable=False)
    type = db.relation(JobType, primaryjoin=type_id == JobType.id)
    category_id = db.Column(db.Integer, db.ForeignKey('jobcategory.id'), nullable=False)
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
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    review_datetime = db.Column(db.DateTime, nullable=True)
    review_comments = db.Column(db.Unicode(250), nullable=True)

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
                            self.perks,
                            self.how_to_apply))

        return {'title': self.headline,
                'content': content,
                'public': self.is_listed(),
                'idref': u'%s/%s' % (self.idref, self.id),
                }

    @cached_property  # For multiple accesses in a single request
    def viewcounts(self):
        return viewcounts_by_id(self.id)


@cache.memoize(timeout=86400)
def viewcounts_by_id(jobpost_id):
    return {
        'all': UserJobView.query.filter_by(jobpost_id=jobpost_id).count(),
        'applied': UserJobView.query.filter_by(jobpost_id=jobpost_id, applied=True).count()
        }


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


def unique_hash(model=JobPost):
    """
    Returns a unique hash for a given model
    """
    while 1:
        hashid = random_hash_key()
        if model.query.filter_by(hashid=hashid).count() == 0:
            break
    return hashid
