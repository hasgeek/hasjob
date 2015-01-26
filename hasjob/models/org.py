# -*- coding: utf-8 -*-

from flask.ext.lastuser.sqlalchemy import ProfileBase
from . import db, BaseScopedIdMixin, CoordinatesMixin

__all__ = ['Organization']


class Organization(ProfileBase, db.Model):
    """
    An organization that is listing jobs
    """
    __tablename__ = 'organization'
    #: URL/Email Domain for validating job listings
    domain = db.Column(db.Unicode(253), nullable=True, index=True)

    #: Logo
    logo_image = db.Column(db.Unicode(250), nullable=True)
    #: Cover image
    cover_image = db.Column(db.Unicode(250), nullable=True)
    #: Description of the organization
    description = db.Column(db.UnicodeText, nullable=False, default=u'')


class OrgLocation(BaseScopedIdMixin, CoordinatesMixin, db.Model):
    """
    Organization's physical location
    """
    __tablename__ = 'org_location'
    org_id = db.Column(None, db.ForeignKey('organization.id'), nullable=False)
    org = db.relationship(Organization, backref=db.backref('locations', cascade='all, delete-orphan'))
    parent = db.synonym('org')

    #: Name of this location (building name, etc)
    title = db.Column(db.Unicode(80), nullable=True)
    #: Address line 1
    address1 = db.Column(db.Unicode(80), nullable=True)
    #: Address line 2
    address2 = db.Column(db.Unicode(80), nullable=True)
    #: City
    city = db.Column(db.Unicode(80), nullable=True)
    #: State or province
    state = db.Column(db.Unicode(80), nullable=True)
    #: Postcode
    postcode = db.Column(db.Unicode(16), nullable=True)
    #: Country
    country = db.Column(db.Unicode(80), nullable=True)

    #: Geonameid for this location (automatically tagged from city/state/country)
    geonameid = db.Column(db.Integer, nullable=True, index=True)

    __table_args__ = (db.UniqueConstraint('org_id', 'url_id'),)

    def __repr__(self):
        return '<OrgLocation %r (%r, %r) for %s>' % (
            self.url_id, self.latitude, self.longitude,
            repr(self.org)[1:-1])
