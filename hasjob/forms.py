# -*- coding: utf-8 -*-

import re
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher

import tldextract
from flask import g, request, Markup
from baseframe.forms import (Form, ValidEmail, ValidUrl, AllUrlsValid, TinyMce4Field, UserSelectMultiField,
    AnnotatedTextField, FormField, NullTextField, ValidName, NoObfuscatedEmail, TextListField, GeonameSelectMultiField)
from baseframe.forms.sqlalchemy import AvailableName
from wtforms import (TextField, TextAreaField, RadioField, FileField, BooleanField,
    ValidationError, validators)
from wtforms.widgets import CheckboxInput, ListWidget
from wtforms.fields.html5 import EmailField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from coaster.utils import getbool, get_email_domain
from flask.ext.lastuser import LastuserResourceException

from .models import User, JobType, JobCategory, JobApplication, Board, EMPLOYER_RESPONSE, PAY_TYPE, webmail_domains
from .uploads import process_image, UploadNotAllowed

from . import app, lastuser
from .utils import simplify_text, EMAIL_RE, URL_RE, PHONE_DETECT_RE, get_word_bag

QUOTES_RE = re.compile(ur'[\'"`‘’“”′″‴«»]+')

CAPS_RE = re.compile('[A-Z]')
SMALL_RE = re.compile('[a-z]')


def content_css():
    return app.assets['css_editor'].urls()[0]


def optional_url(form, field):
    """
    Validate URL only if present.
    """
    if not field.data:
        raise validators.StopValidation()
    else:
        if ':' not in field.data:
            field.data = 'http://' + field.data
        validator = validators.URL(message="This does not appear to be a valid URL.")
        try:
            return validator(form, field)
        except validators.ValidationError as e:
            raise validators.StopValidation(unicode(e))


class ListingPayCurrencyField(RadioField):
    """
    A custom field to get around the annoying pre-validator.
    """
    def pre_validate(self, form):
        if form.job_pay_type.data in (PAY_TYPE.ONETIME, PAY_TYPE.RECURRING):
            if not self.data:
                raise ValueError("Pick one")
            else:
                return super(ListingPayCurrencyField, self).pre_validate(form)
        else:
            self.data = None


def invalid_urls():
    return app.config.get('INVALID_URLS', [])


class ListingForm(Form):
    """Form for new job posts"""
    job_headline = TextField("Headline",
        description="A single-line summary. This goes to the front page and across the network",
        validators=[validators.Required("A headline is required"),
            validators.Length(min=1, max=100, message="%(max)d characters maximum"),
            NoObfuscatedEmail(u"Do not include contact information in the post")])
    job_type = RadioField("Type", coerce=int, validators=[validators.Required("The job type must be specified")])
    job_category = RadioField("Category", coerce=int, validators=[validators.Required("Select a category")])
    job_location = TextField("Location",
        description=u'“Bangalore”, “Chennai”, “Pune”, etc or “Anywhere” (without quotes)',
        validators=[validators.Required(u"If this job doesn’t have a fixed location, use “Anywhere”"),
            validators.Length(min=3, max=80, message="%(max)d characters maximum")])
    job_relocation_assist = BooleanField("Relocation assistance available")
    job_description = TinyMce4Field("Description",
        content_css=content_css,
        description=u"Don’t just describe the job, tell a compelling story for why someone should work for you",
        validators=[validators.Required("A description of the job is required"),
            AllUrlsValid(invalid_urls=invalid_urls),
            NoObfuscatedEmail(u"Do not include contact information in the post")],
        tinymce_options={'convert_urls': True})
    job_perks = BooleanField("Job perks are available")
    job_perks_description = TinyMce4Field("Describe job perks",
        content_css=content_css,
        description=u"Stock options, free lunch, free conference passes, etc",
        validators=[AllUrlsValid(invalid_urls=invalid_urls),
            NoObfuscatedEmail(u"Do not include contact information in the post")])
    job_pay_type = RadioField("What does this job pay?", coerce=int,
        choices=PAY_TYPE.items())
    job_pay_currency = ListingPayCurrencyField("Currency", choices=[("INR", "INR"), ("USD", "USD"), ("EUR", "EUR")])
    job_pay_cash_min = TextField("Minimum")
    job_pay_cash_max = TextField("Maximum")
    job_pay_equity = BooleanField("Equity compensation is available")
    job_pay_equity_min = TextField("Minimum")
    job_pay_equity_max = TextField("Maximum")
    job_how_to_apply = TextAreaField("What should a candidate submit when applying for this job?",
        description=u"Example: “Include your LinkedIn and GitHub profiles.” "
                    u"We now require candidates to apply through the job board only. "
                    u"Do not include any contact information here. Candidates CANNOT "
                    u"attach resumes or other documents, so do not ask for that",
        validators=[
            validators.Required(u"We do not offer screening services. Please specify what candidates should submit"),
            NoObfuscatedEmail(u"Do not include contact information in the post")])
    company_name = TextField("Name",
        description=u"The name of the organization where the position is. "
                    u"No intermediaries or unnamed stealth startups. Use your own real name if the organization isn’t named "
                    u"yet. We do not accept posts from third parties such as recruitment consultants. Such posts "
                    u"may be removed without notice",
        validators=[validators.Required(u"This is required. Posting any name other than that of the actual organization is a violation of the ToS"),
            validators.Length(min=4, max=80, message="The name must be within %(min)d to %(max)d characters")])
    company_logo = FileField("Logo",
        description=u"Optional — Your organization’s logo will appear at the top of your post.",
        )  # validators=[file_allowed(uploaded_logos, "That image type is not supported")])
    company_logo_remove = BooleanField("Remove existing logo")
    company_url = TextField("URL",
        description=u"Example: http://www.google.com",
        validators=[optional_url, validators.Length(min=0, max=255, message="%(max)d characters maximum"), ValidUrl()])
    hr_contact = RadioField(u"Is it okay for recruiters and other "
        u"intermediaries to contact you about this post?", coerce=getbool,
        description=u"We’ll display a notice to this effect on the post",
        default=0,
        choices=[(0, u"No, it is NOT OK"), (1, u"Yes, recruiters may contact me")])
    # Deprecated 2013-11-20
    # poster_name = TextField("Name",
    #     description=u"This is your name, for our records. Will not be revealed to applicants",
    #     validators=[validators.Required("We need your name")])
    poster_email = EmailField("Email",
        description=Markup(u"This is where we’ll send your confirmation email and all job applications. "
                    u"We recommend using a shared email address such as jobs@your-organization.com. "
                    u"<strong>Listings are classified by your email domain,</strong> "
                    u"so use a work email address. "
                    u"Your email address will not be revealed to applicants until you respond"),
        validators=[validators.Required("We need to confirm your email address before the job can be listed"),
            validators.Length(min=5, max=80, message="%(max)d characters maximum"),
            ValidEmail("That does not appear to be a valid email address")])
    collaborators = UserSelectMultiField(u"Collaborators",
        description=u"If someone is helping you evaluate candidates, type their names here. "
                    u"They must have a HasGeek account. They will not receive email notifications "
                    u"— use a shared email address above for that — but they will be able to respond "
                    u"to candidates who apply",
        usermodel=User, lastuser=lastuser)

    def validate_job_type(form, field):
        # This validator exists primarily for this assignment, used later in the form by other validators
        form.job_type_ob = JobType.query.get(field.data)
        if not form.job_type_ob:
            raise ValidationError("Please select a job type")

    def validate_company_name(form, field):
        if len(field.data) > 6:
            caps = len(CAPS_RE.findall(field.data))
            small = len(SMALL_RE.findall(field.data))
            if small == 0 or caps / float(small) > 0.8:
                raise ValidationError(u"Surely your organization isn’t named in uppercase?")

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
        if simplify_text(field.data) in (
                'awesome coder wanted at awesome company',
                'pragmatic programmer wanted at outstanding organisation',
                'pragmatic programmer wanted at outstanding organization') or (
                g.board and g.board.newjob_headline and simplify_text(field.data) == simplify_text(g.board.newjob_headline)):
            raise ValidationError(u"Come on, write your own headline. You aren’t just another run-of-the-mill employer, right?")
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

    def validate_job_pay_cash_min(form, field):
        if form.job_pay_type.data in (PAY_TYPE.ONETIME, PAY_TYPE.RECURRING):
            data = field.data.strip()
            if not data:
                raise ValidationError("Please specify what this job pays")
            if not data[0].isdigit():
                data = data[1:]  # Remove currency symbol
            data = data.replace(',', '').strip()  # Remove thousands separator
            if data.isdigit():
                field.data = int(data)
            else:
                raise ValidationError("Unrecognised value %s" % field.data)
        else:
            field.data = None

    def validate_job_pay_cash_max(form, field):
        if form.job_pay_type.data in (PAY_TYPE.ONETIME, PAY_TYPE.RECURRING):
            data = field.data.strip()
            if data:
                if not data[0].isdigit():
                    data = data[1:]  # Remove currency symbol
                data = data.replace(',', '').strip()  # Remove thousands separator
            if data and data.isdigit():
                field.data = int(data)
            else:
                raise ValidationError("Unrecognised value %s" % field.data)
        else:
            field.data = None

    def validate_job_pay_equity_min(form, field):
        if form.job_pay_equity.data:
            data = field.data.strip()
            if data:
                if not data[-1].isdigit():
                    data = field.data[:-1]  # Remove % symbol
                data = data.replace(',', '').strip()  # Remove thousands separator
                try:
                    field.data = Decimal(data)
                except InvalidOperation:
                    raise ValidationError("Please enter a percentage between 0% and 100%")
            else:
                raise ValidationError("Unrecognised value %s" % field.data)
        else:
            # Discard submission if equity checkbox is unchecked
            field.data = None

    def validate_job_pay_equity_max(form, field):
        if form.job_pay_equity.data:
            data = field.data.strip()
            if data:
                if not data[-1].isdigit():
                    data = field.data[:-1]  # Remove % symbol
                data = data.replace(',', '').strip()  # Remove thousands separator
                try:
                    field.data = Decimal(data)
                except InvalidOperation:
                    raise ValidationError("Please enter a percentage between 0% and 100%")
            else:
                raise ValidationError("Unrecognised value %s" % field.data)
        else:
            # Discard submission if equity checkbox is unchecked
            field.data = None

    def validate(self, extra_validators=None):
        success = super(ListingForm, self).validate(extra_validators)
        if success:
            if (not self.job_type_ob.nopay_allowed) and self.job_pay_type.data == PAY_TYPE.NOCASH:
                self.job_pay_type.errors.append(u"“%s” cannot pay nothing" % self.job_type_ob.title)
                success = False

            if (not self.job_type_ob.webmail_allowed) and get_email_domain(self.poster_email.data) in webmail_domains:
                self.poster_email.errors.append(
                    u"Public webmail accounts like Gmail are not accepted. Please use your corporate email address")
                success = False

            # Check for cash pay range
            if self.job_pay_type.data in (PAY_TYPE.ONETIME, PAY_TYPE.RECURRING):
                if self.job_pay_cash_min.data == 0:
                    if self.job_pay_cash_max.data == 10000000:
                        self.job_pay_cash_max.errors.append(u"Please select a range")
                        success = False
                    else:
                        self.job_pay_cash_min.errors.append(u"Please specify a minimum non-zero pay")
                        success = False
                else:
                    if self.job_pay_cash_max.data == 10000000:
                        if self.job_pay_currency.data == 'INR':
                            figure = u'1 crore'
                        else:
                            figure = u'10 million'
                        self.job_pay_cash_max.errors.append(
                            u"You’ve selected an upper limit of {figure}. That can’t be right".format(figure=figure))
                        success = False
                    elif (self.job_pay_type.data == PAY_TYPE.RECURRING
                            and self.job_pay_currency.data == 'INR'
                            and self.job_pay_cash_min.data < 60000):
                        self.job_pay_cash_min.errors.append(
                            u"That’s rather low. Did you specify monthly pay instead of annual pay? Multiply by 12")
                        success = False
                    elif self.job_pay_cash_max.data > self.job_pay_cash_min.data * 4:
                        self.job_pay_cash_max.errors.append(u"Please select a narrower range, with maximum within 4× minimum")
                        success = False
            if self.job_pay_equity.data:
                if self.job_pay_equity_min.data == 0:
                    if self.job_pay_equity_max.data == 100:
                        self.job_pay_equity_max.errors.append(u"Please select a range")
                        success = False
                else:
                    if self.job_pay_equity_min.data <= Decimal('1.0'):
                        multiplier = 10
                    elif self.job_pay_equity_min.data <= Decimal('2.0'):
                        multiplier = 8
                    elif self.job_pay_equity_min.data <= Decimal('3.0'):
                        multiplier = 6
                    else:
                        multiplier = 4

                    if self.job_pay_equity_max.data > self.job_pay_equity_min.data * multiplier:
                        self.job_pay_equity_max.errors.append(
                            u"Please select a narrower range, with maximum within %d× minimum" % multiplier)
                        success = False
        return success


class ApplicationForm(Form):
    apply_email = RadioField("Email", validators=[validators.Required("Pick an email address")],
        description="Add new email addresses from your profile")
    apply_phone = TextField("Phone",
        validators=[validators.Required("Specify a phone number"),
            validators.Length(min=1, max=15, message="%(max)d characters maximum")],
        description="A phone number the employer can reach you at")
    apply_message = TinyMce4Field("Job application",
        content_css=content_css,
        validators=[validators.Required("You need to say something about yourself"),
            AllUrlsValid()],
        description=u"Please provide all details the employer has requested. To add a resume, "
        u"post it on LinkedIn or host the file on Dropbox and insert the link here")
    apply_optin = BooleanField("Optional: sign me up for a better Hasjob experience",
        description=u"Hasjob’s maintainers may contact about new features and can see this application for reference")

    def __init__(self, *args, **kwargs):
        super(ApplicationForm, self).__init__(*args, **kwargs)
        self.apply_email.choices = []
        if g.user:
            self.apply_email.description = Markup(
                u'Add new email addresses from <a href="{}" target="_blank">your profile</a>'.format(
                    g.user.profile_url))
            try:
                self.apply_email.choices = [(e, e) for e in lastuser.user_emails(g.user)]
            except LastuserResourceException:
                self.apply_email.choices = [(g.user.email, g.user.email)]
            if not self.apply_email.choices:
                self.apply_email.choices = [
                    ('', Markup('<em>You have not verified your email address</em>'))
                ]

    def validate_apply_message(form, field):
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


class KioskApplicationForm(Form):
    apply_fullname = TextField("Fullname", validators=[validators.Required("Specify your name")],
        description="Your full name")
    apply_email = TextField("Email", validators=[validators.Required("Specify an email address")],
        description="Your email address")
    apply_phone = TextField("Phone",
        validators=[validators.Required("Specify a phone number"),
            validators.Length(min=1, max=15, message="%(max)d characters maximum")],
        description="A phone number the employer can reach you at")
    apply_message = TinyMce4Field("Job application",
        content_css=content_css,
        validators=[validators.Required("You need to say something about yourself"),
            AllUrlsValid()],
        description=u"Please provide all details the employer has requested. To add a resume, "
        u"post it on LinkedIn or host the file on Dropbox and insert the link here")

    def validate_email(form, field):
        oldapp = JobApplication.query.filter_by(jobpost=form.post, user=None, email=field.data).count()
        if oldapp:
            raise ValidationError("You have already applied for this position")


class ApplicationResponseForm(Form):
    response_message = TinyMce4Field("",
        content_css=content_css)


class ConfirmForm(Form):
    terms_accepted = BooleanField("I accept the terms of service",
        validators=[validators.Required("You must accept the terms of service to publish this post")])


class WithdrawForm(Form):
    really_withdraw = BooleanField("Yes, I really want to withdraw the job post",
        validators=[validators.Required(u"If you don’t want to withdraw the post, just close this page")])


class ReportForm(Form):
    report_code = RadioField("Code", coerce=int, validators=[validators.Required(u"Pick one")])


class RejectForm(Form):
    reason = TextField('Reason', validators=[validators.Required(u"Give a reason")])


class ModerateForm(Form):
    reason = TextAreaField('Reason',
        validators=[validators.Required(u"Give a reason"), validators.Length(max=250)])


class PinnedForm(Form):
    pinned = BooleanField("Pin this")


def jobtype_label(jobtype):
    annotations = []
    if jobtype.nopay_allowed:
        annotations.append(u'zero pay allowed')
    if jobtype.webmail_allowed:
        annotations.append(u'webmail address allowed')
    if annotations:
        return Markup(u'%s <small><em>(%s)</em></small>') % (jobtype.title, u', '.join(annotations))
    else:
        return jobtype.title


class BoardOptionsForm(Form):
    restrict_listing = BooleanField(u"Restrict direct posting on this board to owners and the following users",
        default=True,
        description=u"As the owner of this board, you can always cross-add jobs from other boards on Hasjob")
    posting_users = UserSelectMultiField(u"Allowed users",
        description=u"These users will be allowed to post jobs on this board under the following terms",
        usermodel=User, lastuser=lastuser)
    # Allow turning this off only in siteadmin-approved boards (deleted in the view for non-siteadmins)
    require_pay = BooleanField(u"Require pay data for post on this board?", default=True,
        description=u"Hasjob requires employers to reveal what they intend to pay, "
            u"but you can make it optional for jobs posted from this board. "
            u"Pay data is used to match candidates to jobs. We recommend you collect it")
    newjob_headline = NullTextField(u"Headline",
        description=u"The sample headline shown to employers when post a job",
        validators=[validators.Length(min=0, max=100, message="%(max)d characters maximum")])
    newjob_blurb = TinyMce4Field(u"Posting instructions",
        description=u"What should we tell employers when they post a job on your board? "
            u"Leave blank to use the default text",
        content_css=content_css,
        validators=[AllUrlsValid()])
    types = QuerySelectMultipleField("Job types",
        widget=ListWidget(), option_widget=CheckboxInput(),
        query_factory=lambda: JobType.query.filter_by(private=False).order_by('seq'), get_label=jobtype_label,
        validators=[validators.Required(u"You need to select at least one job type")],
        description=u"Jobs listed directly on this board can use one of the types enabled here")
    categories = QuerySelectMultipleField("Job categories",
        widget=ListWidget(), option_widget=CheckboxInput(),
        query_factory=lambda: JobCategory.query.filter_by(private=False).order_by('seq'), get_label='title',
        validators=[validators.Required(u"You need to select at least one category")],
        description=u"Jobs listed directly on this board can use one of the categories enabled here")


class BoardTaggingForm(Form):
    tag_domains = TextListField("Email Domains",
        description="Jobs from any of these email domains will be automatically added to this board. "
        "One per line. Do NOT add the www prefix")
    tag_locations = GeonameSelectMultiField("Locations",
        description="Jobs in any of these locations will be automatically added to this board")

    def validate_tag_domains(self, field):
        relist = []
        for item in field.data:
            item = item.strip()
            if u',' in item:
                relist.extend([x.strip() for x in item.split(',')])
            elif u' ' in item:
                relist.extend([x.strip() for x in item.split(' ')])
            else:
                relist.append(item)

        domains = set()
        for item in relist:
            if item:
                r = tldextract.extract(item.lower())
                domains.add(u'.'.join([r.domain, r.suffix]))
        field.data = list(domains)

    def validate_tag_locations(self, field):
        field.data = [int(x) for x in field.data if x.isdigit()]


class BoardForm(Form):
    """
    Edit board settings.
    """
    title = TextField(u"Title", validators=[
        validators.Required("The board needs a name"),
        validators.Length(min=1, max=80, message="%(max)d characters maximum")])
    caption = NullTextField(u"Caption", validators=[
        validators.Optional(),
        validators.Length(min=0, max=80, message="%(max)d characters maximum")],
        description=u"The title and caption appear at the top of the page. Keep them concise")
    name = AnnotatedTextField(u"URL Name", prefix='https://', suffix=u'.hasjob.co',
        description=u"Optional — Will be autogenerated if blank",
        validators=[ValidName(), validators.Length(min=0, max=250, message="%(max)d characters maximum"),
            AvailableName(u"This name has been taken by another board", model=Board)])
    description = TinyMce4Field(u"Description",
        description=u"The description appears at the top of the board, above all jobs. "
            u"Use it to introduce your board and keep it brief",
        content_css=content_css,
        validators=[validators.Required("A description of the job board is required"),
            AllUrlsValid()])
    userid = RadioField(u"Owner", validators=[validators.Required("Select an owner")],
        description=u"Select the user or organization who owns this board. "
            "Owners can add jobs to the board and edit these settings")
    require_login = BooleanField(u"Prompt users to login", default=True,
        description=u"If checked, users must login to see all jobs available. "
            u"Logging in provides users better filtering for jobs that may be of interest to them, "
            u"and allows employers to understand how well their post is performing")
    options = FormField(BoardOptionsForm, u"Direct posting options")
    autotag = FormField(BoardTaggingForm, u"Automatic posting options")

    def validate_name(self, field):
        if field.data:
            if field.data in Board.reserved_names:
                raise ValidationError(u"This name is reserved. Please use another name")
            # existing = Board.query.filter_by(name=field.data).first()
            # if existing and existing != self.edit_obj:
            #     raise ValidationError(u"This name has been taken by another board")
