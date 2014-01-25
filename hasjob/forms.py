# -*- coding: utf-8 -*-

import re
from difflib import SequenceMatcher

from flask import g, request, Markup
from baseframe.forms import Form, ValidEmailDomain, RichTextField, HiddenMultiField
from wtforms import TextField, TextAreaField, RadioField, FileField, BooleanField, ValidationError, validators
from wtforms.fields.html5 import EmailField
from coaster import getbool

from .models import JobApplication, EMPLOYER_RESPONSE
from .uploads import process_image, UploadNotAllowed

from . import app, lastuser
from .utils import simplify_text, EMAIL_RE, URL_RE, PHONE_DETECT_RE, get_word_bag

QUOTES_RE = re.compile(ur'[\'"`‘’“”′″‴]+')

CAPS_RE = re.compile('[A-Z]')
SMALL_RE = re.compile('[a-z]')


def optional_url(form, field):
    """
    Validate URL only if present.
    """
    if not field.data:
        return
    else:
        if ':' not in field.data:
            field.data = 'http://' + field.data
        validator = validators.URL(message="Invalid URL. URLs must begin with http:// or https://")
        return validator(form, field)


class ListingForm(Form):
    """Form for new job posts"""
    job_headline = TextField("Headline",
        description="A single-line summary. This goes to the front page and across the network",
        validators=[validators.Required("A headline is required"),
            validators.Length(min=1, max=100, message="%(max)d characters maximum")])
    job_type = RadioField("Type", coerce=int, validators=[validators.Required("The job type must be specified")])
    job_category = RadioField("Category", coerce=int, validators=[validators.Required("Select a category")])
    job_location = TextField("Location",
        description=u'“Bangalore”, “Chennai”, “Pune”, etc or “Anywhere” (without quotes)',
        validators=[validators.Required(u"If this job doesn’t have a fixed location, use “Anywhere”"),
            validators.Length(min=3, max=80, message="%(max)d characters maximum")])
    job_relocation_assist = BooleanField("Relocation assistance available")
    job_description = RichTextField("Description",
        description=u"Don’t just describe the job, tell a compelling story for why someone should work for you",
        validators=[validators.Required("A description of the job is required")],
        tinymce_options={'convert_urls': True})
    job_perks = BooleanField("Job perks are available")
    job_perks_description = TextAreaField("Describe job perks",
        description=u"Stock options, free lunch, free conference passes, etc")
    job_how_to_apply = TextAreaField("What should a candidate submit when applying for this job?",
         description=u"Example: “Include your LinkedIn and GitHub profiles.” "
                     u"We now require candidates to apply through the job board only. "
                     u"Do not include any contact information here. Candidates CANNOT "
                     u"attach resumes or other documents, so do not ask for that",
         validators=[validators.Required(u"HasGeek does not offer screening services. "
                                         u"Please specify what candidates should submit")])
    company_name = TextField("Name",
        description=u"The name of the organization where the position is. "
                    u"No intermediaries or unnamed stealth startups. Use your own real name if the company isn’t named "
                    u"yet. We do not accept listings from third parties such as recruitment consultants. Such listings "
                    u"may be removed without notice",
        validators=[validators.Required(u"This is required. Posting any name other than that of the actual organization is a violation of the ToS"),
            validators.Length(min=5, max=80, message="%(max)d characters maximum")])
    company_logo = FileField("Logo",
        description=u"Optional — Your company logo will appear at the top of your listing. "
                    u"170px wide is optimal. We’ll resize automatically if it’s wider",
        )  # validators=[file_allowed(uploaded_logos, "That image type is not supported")])
    company_logo_remove = BooleanField("Remove existing logo")
    company_url = TextField("URL",
        description=u"Example: http://www.google.com",
        validators=[optional_url])
    hr_contact = RadioField(u"Is it okay for recruiters and other "
        u"intermediaries to contact you about this listing?", coerce=getbool,
        description=u"We’ll display a notice to this effect on the listing",
        default=0,
        choices=[(0, u"No, it is NOT OK"), (1, u"Yes, recruiters may contact me")])
    # Deprecated 2013-11-20
    # poster_name = TextField("Name",
    #     description=u"This is your name, for our records. Will not be revealed to applicants",
    #     validators=[validators.Required("We need your name")])
    poster_email = EmailField("Email",
        description=u"This is where we’ll send your confirmation email and all job applications. "
                    u"We recommend using a shared email address such as jobs@your-company.com. "
                    u"Listings are classified by your email domain. "
                    u"Your email address will not be revealed to applicants until you respond",
        validators=[validators.Required("We need to confirm your email address before the job can be listed"),
            validators.Length(min=5, max=80, message="%(max)d characters maximum"),
            validators.Email("That does not appear to be a valid email address"),
            ValidEmailDomain()])
    collaborators = HiddenMultiField(u"Collaborators",
        description=u"If someone is helping you evaluate candidates, type their names here. "
                    u"They must have a HasGeek account. They will not receive email notifications "
                    u"— use a shared email address above for that — but they will be able to respond "
                    u"to candidates who apply")


    def validate_company_name(form, field):
        caps = len(CAPS_RE.findall(field.data))
        small = len(SMALL_RE.findall(field.data))
        if small == 0 or caps / float(small) > 0.8:
            raise ValidationError("Surely your company isn't named in uppercase?")

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
        caps = len(CAPS_RE.findall(field.data))
        small = len(SMALL_RE.findall(field.data))
        if small == 0 or caps / float(small) > 0.5:
            raise ValidationError("No shouting, please. Reduce the number of capital letters in your headline")
        for word_list, message in app.config.get('BANNED_WORDS', []):
            for word in word_list:
                if word in field.data.lower():
                    raise ValidationError(message)

    def validate_job_location(form, field):
        if QUOTES_RE.search(field.data) is not None:
            raise ValidationError(u"Don’t use quotes in the location name")

        caps = len(CAPS_RE.findall(field.data))
        small = len(SMALL_RE.findall(field.data))
        if small == 0 or caps / float(small) > 0.5:
            raise ValidationError("Surely this location isn't named in uppercase?")

    def validate_job_description(form, field):
        if EMAIL_RE.search(field.data) is not None:
            raise ValidationError(u"Do not include contact information in the listing")

    def validate_job_perks_description(form, field):
        if EMAIL_RE.search(field.data) is not None:
            raise ValidationError(u"Do not include contact information in the listing")

    def validate_job_how_to_apply(form, field):
        if EMAIL_RE.search(field.data) is not None or URL_RE.search(field.data) is not None:
            raise ValidationError(u"Do not include contact information in the listing")


class ApplicationForm(Form):
    apply_email = RadioField("Email", validators=[validators.Required("Pick an email address")],
        description="Add new email addresses from your profile")
    apply_phone = TextField("Phone",
        validators=[validators.Required("Specify a phone number"),
            validators.Length(min=1, max=15, message="%(max)d characters maximum")],
        description="A phone number the employer can reach you at")
    apply_message = RichTextField("Job application",
        description="Please provide all details the employer has requested")
    apply_document = FileField("Upload PDF")

    def __init__(self, *args, **kwargs):
        super(ApplicationForm, self).__init__(*args, **kwargs)
        self.apply_email.choices = []
        if g.user:
            self.apply_email.description = Markup(
                u'Add new email addresses from <a href="{}" target="_blank">your profile</a>'.format(
                    g.user.profile_url))
            self.apply_email.choices = [(e, e) for e in lastuser.user_emails(g.user)]
            if not self.apply_email.choices:
                self.apply_email.choices = [
                    ('', Markup('<em>You have not verified your email address</em>'))
                ]

    def validate_apply_message(form, field):
        if not (field.data or form.apply_document.data):
            raise ValidationError("You need to say something about yourself. You can upload a document for the same too!")
        words = get_word_bag(field.data)
        form.words = words
        similar = False
        for oldapp in JobApplication.query.filter_by(response=EMPLOYER_RESPONSE.SPAM).all():
            if oldapp.words:
                s = SequenceMatcher(None, words, oldapp.words)
                if s.ratio() > 0.8:
                    similar = True
                    break

        if similar:
            raise ValidationError("Your application is very similar to one previously identified as spam")

        # Check for email and phone numbers in the message

        # Prepare text by replacing non-breaking spaces with spaces (for phone numbers) and removing URLs.
        # URLs may contain numbers that are not phone numbers.
        phone_search_text = URL_RE.sub('', field.data.replace('&nbsp;', ' ').replace('&#160;', ' ').replace(u'\xa0', ' '))
        if EMAIL_RE.search(field.data) is not None or PHONE_DETECT_RE.search(phone_search_text) is not None:
            raise ValidationError("Do not include your email address or phone number in the application")


class ApplicationResponseForm(Form):
    response_message = RichTextField("")


class ConfirmForm(Form):
    terms_accepted = BooleanField("I accept the terms of service",
        validators=[validators.Required("You must accept the terms of service to publish this listing")])


class WithdrawForm(Form):
    really_withdraw = BooleanField("Yes, I really want to withdraw the job listing",
        validators=[validators.Required(u"If you don’t want to withdraw the listing, just close this page")])


class ReportForm(Form):
    report_code = RadioField("Code", coerce=int, validators=[validators.Required(u"Pick one")])


class RejectForm(Form):
    reason = TextField('Reason', validators=[validators.Required(u"Give a reason")])


class StickyForm(Form):
    sticky = BooleanField("Make this sticky?")
