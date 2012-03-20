# -*- coding: utf-8 -*-

import re
from flask import g, request
from flaskext.wtf import Form, TextField, TextAreaField, RadioField, FileField, BooleanField
from flaskext.wtf import Required, Email, Length, URL, ValidationError
from flaskext.wtf.html5 import URLField, EmailField

from uploads import process_image
from utils import simplify_text

QUOTES_RE = re.compile(ur'[\'"`‘’“”′″‴]+')


def optional_url(form, field):
    """
    Validate URL only if present.
    """
    if not field.data:
        return
    else:
        if ':' not in field.data:
            field.data = 'http://' + field.data
        validator = URL(message="Invalid URL. URLs must begin with http:// or https://")
        return validator(form, field)


class ListingForm(Form):
    """Form for new job posts"""
    job_headline = TextField("Headline",
        description="A single-line summary. This goes to the front page and across the network",
        validators=[Required("A headline is required"),
            Length(min=1, max=100, message="%(max)d characters maximum")])
    job_location = TextField("Location",
        description=u'“Bangalore”, “Chennai”, “Pune”, etc or “Anywhere” (without quotes)',
        validators=[Required(u"If this job doesn’t have a fixed location, use “Anywhere”")])
    job_description = TextAreaField("Description",
        description=u"Our apologies for the mismatched font you see here. We’re working on it",
        validators=[Required("A description of the job is required")])
    poster_email = EmailField("Email",
        description = u"This is where we’ll send confirmation email for your posting. "\
            u"It will not be revealed to users.",
        validators=[Required("We need to confirm your email address before the job can be listed"),
        Email("That does not appear to be a valid email address")])

    def validate_job_headline(form, field):
        # XXX: These validations belong in a config file or in the db, not here.
        if simplify_text(field.data) == 'awesome coder wanted at awesome company':
            raise ValidationError(u"Come on, write your own headline. You aren’t just another run-of-the-mill company, right?")
        if 'awesome' in field.data.lower():
            raise ValidationError(u'We’ve had a bit too much awesome around here lately. Got another adjective?')
        if 'rockstar' in field.data.lower() or 'rock star' in field.data.lower() or 'rock-star' in field.data.lower():
            raise ValidationError(u'You are not rich enough to hire a rockstar. Got another adjective?')
        if 'kickass' in field.data.lower() or 'kick ass' in field.data.lower() or 'kick-ass' in field.data.lower():
            raise ValidationError(u'We don’t condone kicking asses around here. Got another adjective?')
        if 'ninja' in field.data.lower():
            raise ValidationError(u'Ninjas kill people. We can’t allow that. Got another adjective?')
        if 'urgent' in field.data.lower():
            raise ValidationError(u'Sorry, we can’t help with urgent requirements. Geeks don’t grow on trees')

    def validate_job_location(form, field):
        if QUOTES_RE.search(field.data) is not None:
            raise ValidationError(u"Don’t use quotes in the location name")


class ConfirmForm(Form):
    terms_accepted = BooleanField("I accept the terms of service",
        validators=[Required("You must accept the terms of service to publish this listing")])
    #promocode = TextField("Promo code")

class WithdrawForm(Form):
    really_withdraw = BooleanField("Yes, I really want to withdraw the job listing",
        validators=[Required(u"If you don’t want to withdraw the listing, just close this page")])

class ReportForm(Form):
    report_code = RadioField("Code", coerce=int, validators=[Required(u"Pick one")])
