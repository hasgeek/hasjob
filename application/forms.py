# -*- coding: utf-8 -*-

from flask import g, request
from flaskext.wtf import Form, TextField, TextAreaField, RadioField, \
                            FileField, BooleanField
from flaskext.wtf import Required, Email, Length, URL, ValidationError
from flaskext.wtf.html5 import EmailField

from uploads import process_image
from utils import simplify_text

import re

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
        validator = URL(message='Invalid URL. URLs must begin with '\
                                    'http:// or https://')
        return validator(form, field)


class ListingForm(Form):
    """Form for new job posts"""
    job_headline = TextField("Headline",
        description=("A single-line summary. This goes to the front page "
                        "and across the network"),
        validators=[Required("A headline is required"),
            Length(min=1, max=100, message="%(max)d characters maximum")])

    job_type = RadioField("Type", coerce=int,
        validators=[Required("The job type must be specified")])
    job_category = RadioField("Category", coerce=int,
        validators=[Required("Select a category")])

    job_location = TextField("Location",
        description=u"“Bangalore”, “Chennai”, “Pune”, etc or "
                    u"“Anywhere” (without quotes)",
        validators=[Required(u"If this job doesn’t have a fixed "
                                u"location, use “Anywhere”")])
    job_relocation_assist = BooleanField("Relocation assistance available")
    job_description = TextAreaField("Description",
        description=u"Our apologies for the mismatched font you see here. "
                    u"We’re working on it",
        validators=[Required("A description of the job is required")])
    job_perks = BooleanField("Job perks are available")
    job_perks_description = TextAreaField("Describe job perks",
        description=u"Stock options, free lunch, free conference passes, etc")
    job_how_to_apply = TextAreaField("How do people apply for this job?",
        description=u'Example: "Send a resume to kumar@company.com". '
                    u"Don’t worry about spambots seeing your email address. "
                    u"We’ll secure it",
        validators=[Required("HasGeek does not offer screening services. "
                            "Please specify how candidates may apply")])
    company_name = TextField("Name",
        description=u"The name of the organization where the position is. "
                    u"No intermediaries or unnamed stealth startups. Use "
                    u"your own real name if the company isn’t named yet",
        validators=[Required(u"This is required. Posting any name other "
                            u"than that of the actual organization is a "
                            u"violation of the ToS")])
    company_logo = FileField("Logo",
        description=u"Optional — Your company logo will appear at the top "
                    u"of your listing. 170px wide is optimal. We’ll resize"
                    u"automatically if it’s wider",
        )
    company_logo_remove = BooleanField("Remove existing logo")
    company_url = TextField("URL",
        description=u"Example: http://www.google.com",
        validators=[optional_url])
    poster_email = EmailField("Email",
        description=u"This is where we’ll send your confirmation email. "
                      u"It will not be revealed to applicants",
        validators=[Required("We need to confirm your email address before "
                                "the job can be listed"),
            Email("That does not appear to be a valid email address")])

    def validate_company_logo(form, field):
        if not request.files['company_logo']:
            return
        try:
            g.company_logo = process_image(request.files['company_logo'])
        except IOError, e:
            raise ValidationError(e.message)
        except KeyError, e:
            raise ValidationError("Unknown file format")

    def validate_job_headline(form, field):
        # XXX: These validations belong in a config file or in
        # the db, not here.
        field_text = field.data.lower()
        if simplify_text(field_text) == ('awesome coder wanted at '
                                            'awesome company'):
            raise ValidationError(u"Come on, write your own headline. "
                                u"You aren’t just another run-of-the-mill"
                                u"company, right?")

        if 'awesome' in field_text:
            raise ValidationError(u'We’ve had a bit too much awesome around '
                                    u'here lately. Got another adjective?')
        if 'rockstar' in field_text or \
                'rock star' in field_text or \
                'rock-star' in field_text:
            raise ValidationError(u'You are not rich enough to hire a '
                                    u'rockstar. Got another adjective?')

        if 'kickass' in field_text or \
                'kick ass' in field_text or \
                'kick-ass' in field_text:
            raise ValidationError(u'We don’t condone kicking asses around '
                                    u'here. Got another adjective?')

        if 'ninja' in field_text:
            raise ValidationError(u'Ninjas kill people. We can’t allow '
                                    u'that. Got another adjective?')

        if 'urgent' in field_text:
            raise ValidationError(u'Sorry, we can’t help with urgent '
                                u'requirements. Geeks don’t grow on trees')

    def validate_job_location(form, field):
        if QUOTES_RE.search(field.data) is not None:
            raise ValidationError(u"Don’t use quotes in the location name")


class ConfirmForm(Form):
    terms_accepted = BooleanField("I accept the terms of service",
        validators=[Required("You must accept the terms of service to "
                                "publish this listing")])
    #promocode = TextField("Promo code")


class WithdrawForm(Form):
    really_withdraw = BooleanField("Yes, I really want to withdraw "
                                    "the job listing",
        validators=[Required(u"If you don’t want to withdraw the listing, "
                                u"just close this page")])


class ReportForm(Form):
    report_code = RadioField("Code", coerce=int,
                                validators=[Required(u"Pick one")])
