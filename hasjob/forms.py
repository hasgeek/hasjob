# -*- coding: utf-8 -*-

import re
from flask import g, request
from flask.ext.wtf import Form, TextField, TextAreaField, RadioField, FileField, BooleanField
from flask.ext.wtf import Required, Email, Length, URL, ValidationError
from flask.ext.wtf.html5 import EmailField

from uploads import process_image, UploadNotAllowed
from utils import simplify_text

QUOTES_RE = re.compile(ur'[\'"`‘’“”′″‴]+')


def boolint(value):
    return bool(int(value))


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
    job_type = RadioField("Type", coerce=int, validators=[Required("The job type must be specified")])
    job_category = RadioField("Category", coerce=int, validators=[Required("Select a category")])
    job_location = TextField("Location",
        description=u'“Bangalore”, “Chennai”, “Pune”, etc or “Anywhere” (without quotes)',
        validators=[Required(u"If this job doesn’t have a fixed location, use “Anywhere”")])
    job_relocation_assist = BooleanField("Relocation assistance available")
    job_description = TextAreaField("Description",
        description=u"Our apologies for the mismatched font you see here. We’re (still) working on it",
        validators=[Required("A description of the job is required")])
    job_perks = BooleanField("Job perks are available")
    job_perks_description = TextAreaField("Describe job perks",
        description=u"Stock options, free lunch, free conference passes, etc")
    job_how_to_apply = TextAreaField("How do people apply for this job?",
        description=u'Example: "Send a resume to kumar@company.com". '
                    u"Don’t worry about spambots seeing your email address. "
                    u"We’ll secure it",
        validators=[Required(u"HasGeek does not offer screening services. Please specify how candidates may apply")])
    hr_contact = RadioField(u"Is it okay for recruiters and other "
        u"intermediaries to contact you about this listing?", coerce=boolint,
        description=u"We’ll display a notice to this effect on the listing",
        default=0,
        choices=[(0, u"No, it is NOT OK"), (1, u"Yes, recruiters may contact me")])
    company_name = TextField("Name",
        description=u"The name of the organization where the position is. "
                    u"No intermediaries or unnamed stealth startups. Use your own real name if the company isn’t named "
                    u"yet. We do not accept listings from third parties such as HR consultants. Such listings may be "
                    u"removed without notice.",
        validators=[Required(u"This is required. Posting any name other than that of the actual organization is a violation of the ToS")])
    company_logo = FileField("Logo",
        description=u"Optional — Your company logo will appear at the top of your listing. "
                    u"170px wide is optimal. We’ll resize automatically if it’s wider",
        )  # validators=[file_allowed(uploaded_logos, "That image type is not supported")])
    company_logo_remove = BooleanField("Remove existing logo")
    company_url = TextField("URL",
        description=u"Example: http://www.google.com",
        validators=[optional_url])
    poster_email = EmailField("Email",
        description=u"This is where we’ll send your confirmation email. "
                    u"It will not be revealed to applicants",
        validators=[Required("We need to confirm your email address before the job can be listed"),
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
        except UploadNotAllowed:
            raise ValidationError("Unsupported file format. We accept JPEG, PNG and GIF")

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
