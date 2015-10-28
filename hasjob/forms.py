# -*- coding: utf-8 -*-

import re
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher

import tldextract
from flask import g, request, Markup
from baseframe import __
import baseframe.forms as forms
from baseframe.forms.sqlalchemy import AvailableName
from baseframe.staticdata import webmail_domains
from wtforms.widgets import CheckboxInput, ListWidget
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from coaster.utils import getbool, get_email_domain
from flask.ext.lastuser import LastuserResourceException

from .models import (User, JobType, JobCategory, JobApplication, Board, EMPLOYER_RESPONSE, PAY_TYPE,
    CAMPAIGN_POSITION, CAMPAIGN_ACTION, BANNER_LOCATION, CURRENCY, Campaign, Domain)
from .uploads import process_image, UploadNotAllowed

from . import app, lastuser
from .utils import simplify_text, EMAIL_RE, URL_RE, PHONE_DETECT_RE, get_word_bag, string_to_number

QUOTES_RE = re.compile(ur'[\'"`‘’“”′″‴«»]+')

CAPS_RE = re.compile('[A-Z]')
SMALL_RE = re.compile('[a-z]')
INVALID_TWITTER_RE = re.compile('[^a-z0-9_]', re.I)


def content_css():
    return app.assets['css_editor'].urls()[0]


def optional_url(form, field):
    """
    Validate URL only if present.
    """
    if not field.data:
        raise forms.validators.StopValidation()
    else:
        if '://' not in field.data:
            field.data = 'http://' + field.data
        validator = forms.validators.URL(message="This does not appear to be a valid URL.")
        try:
            return validator(form, field)
        except forms.ValidationError as e:
            raise forms.StopValidation(unicode(e))


class ListingPayCurrencyField(forms.RadioField):
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


class ListingForm(forms.Form):
    """Form for new job posts"""
    job_headline = forms.StringField("Headline",
        description=Markup("A single-line summary. This goes to the front page and across the network. "
            """<a id="abtest" class="no-jshidden" href="#">A/B test it?</a>"""),
        validators=[forms.validators.DataRequired("A headline is required"),
            forms.validators.StripWhitespace(),
            forms.validators.Length(min=1, max=100, message="%(max)d characters maximum"),
            forms.validators.NoObfuscatedEmail(u"Do not include contact information in the post")])
    job_headlineb = forms.NullTextField("Headline B",
        description=u"An alternate headline that will be shown to 50% of users. You’ll get a count of views per headline",
        validators=[forms.validators.Optional(),
            forms.validators.StripWhitespace(),
            forms.validators.Length(min=1, max=100, message="%(max)d characters maximum"),
            forms.validators.NoObfuscatedEmail(u"Do not include contact information in the post")])
    job_type = forms.RadioField("Type", coerce=int, validators=[forms.validators.InputRequired("The job type must be specified")])
    job_category = forms.RadioField("Category", coerce=int, validators=[forms.validators.InputRequired("Select a category")])
    job_location = forms.StringField("Location",
        description=u'“Bangalore”, “Chennai”, “Pune”, etc or “Anywhere” (without quotes)',
        validators=[forms.validators.DataRequired(u"If this job doesn’t have a fixed location, use “Anywhere”"),
            forms.validators.StripWhitespace(),
            forms.validators.Length(min=3, max=80, message="%(max)d characters maximum")])
    job_relocation_assist = forms.BooleanField("Relocation assistance available")
    job_description = forms.TinyMce4Field("Description",
        content_css=content_css,
        description=u"Don’t just describe the job, tell a compelling story for why someone should work for you",
        validators=[forms.validators.DataRequired("A description of the job is required"),
            forms.validators.AllUrlsValid(invalid_urls=invalid_urls),
            forms.validators.NoObfuscatedEmail(u"Do not include contact information in the post")],
        tinymce_options={'convert_urls': True})
    job_perks = forms.BooleanField("Job perks are available")
    job_perks_description = forms.TinyMce4Field("Describe job perks",
        content_css=content_css,
        description=u"Stock options, free lunch, free conference passes, etc",
        validators=[forms.validators.AllUrlsValid(invalid_urls=invalid_urls),
            forms.validators.NoObfuscatedEmail(u"Do not include contact information in the post")])
    job_pay_type = forms.RadioField("What does this job pay?", coerce=int,
        validators=[forms.validators.InputRequired("You need to specify what this job pays")],
        choices=PAY_TYPE.items())
    job_pay_currency = ListingPayCurrencyField("Currency", choices=CURRENCY.items())
    job_pay_cash_min = forms.StringField("Minimum")
    job_pay_cash_max = forms.StringField("Maximum")
    job_pay_equity = forms.BooleanField("Equity compensation is available")
    job_pay_equity_min = forms.StringField("Minimum")
    job_pay_equity_max = forms.StringField("Maximum")
    job_how_to_apply = forms.TextAreaField("What should a candidate submit when applying for this job?",
        description=u"Example: “Include your LinkedIn and GitHub profiles.” "
                    u"We now require candidates to apply through the job board only. "
                    u"Do not include any contact information here. Candidates CANNOT "
                    u"attach resumes or other documents, so do not ask for that",
        validators=[
            forms.validators.DataRequired(u"We do not offer screening services. Please specify what candidates should submit"),
            forms.validators.NoObfuscatedEmail(u"Do not include contact information in the post")])
    company_name = forms.StringField("Name",
        description=u"The name of the organization where the position is. "
                    u"No intermediaries or unnamed stealth startups. Use your own real name if the organization isn’t named "
                    u"yet. We do not accept posts from third parties such as recruitment consultants. Such posts "
                    u"may be removed without notice",
        validators=[forms.validators.DataRequired(u"This is required. Posting any name other than that of the actual organization is a violation of the ToS"),
            forms.validators.StripWhitespace(),
            forms.validators.Length(min=4, max=80, message="The name must be within %(min)d to %(max)d characters")])
    company_logo = forms.FileField("Logo",
        description=u"Optional — Your organization’s logo will appear at the top of your post.",
        )  # validators=[file_allowed(uploaded_logos, "That image type is not supported")])
    company_logo_remove = forms.BooleanField("Remove existing logo")
    company_url = forms.URLField("URL",
        description=u"Your organization’s website",
        validators=[forms.validators.DataRequired(), forms.validators.StripWhitespace(), optional_url,
            forms.validators.Length(max=255, message="%(max)d characters maximum"), forms.validators.ValidUrl()])
    hr_contact = forms.RadioField(u"Is it okay for recruiters and other "
        u"intermediaries to contact you about this post?", coerce=getbool,
        description=u"We’ll display a notice to this effect on the post",
        default=0,
        choices=[(0, u"No, it is NOT OK"), (1, u"Yes, recruiters may contact me")])
    # Deprecated 2013-11-20
    # poster_name = forms.StringField("Name",
    #     description=u"This is your name, for our records. Will not be revealed to applicants",
    #     validators=[forms.validators.DataRequired("We need your name")])
    poster_email = forms.EmailField("Email",
        description=Markup(u"This is where we’ll send your confirmation email and all job applications. "
                    u"We recommend using a shared email address such as jobs@your-organization.com. "
                    u"<strong>Listings are classified by your email domain,</strong> "
                    u"so use a work email address. "
                    u"Your email address will not be revealed to applicants until you respond"),
        validators=[forms.validators.DataRequired("We need to confirm your email address before the job can be listed"),
            forms.validators.StripWhitespace(),
            forms.validators.Length(min=5, max=80, message="%(max)d characters maximum"),
            forms.validators.ValidEmail("This does not appear to be a valid email address")])
    twitter = forms.AnnotatedNullTextField("Twitter",
        description=(u"Optional — your organization’s Twitter account. "
            u"We’ll tweet mentioning you so you get included on replies"),
        prefix='@', validators=[
            forms.validators.Optional(),
            forms.validators.StripWhitespace(),
            forms.validators.Length(min=0, max=15, message=u"Twitter accounts can’t be over %(max)d characters long")])
    collaborators = forms.UserSelectMultiField(u"Collaborators",
        description=u"If someone is helping you evaluate candidates, type their names here. "
                    u"They must have a HasGeek account. They will not receive email notifications "
                    u"— use a shared email address above for that — but they will be able to respond "
                    u"to candidates who apply",
        usermodel=User, lastuser=lastuser)

    def validate_twitter(self, field):
        if field.data.startswith('@'):
            field.data = field.data[1:]
        if INVALID_TWITTER_RE.search(field.data):
            raise forms.ValidationError("That does not appear to be a valid Twitter account")

    def validate_poster_email(form, field):
        field.data = field.data.lower()

    def validate_job_type(form, field):
        # This validator exists primarily for this assignment, used later in the form by other validators
        form.job_type_ob = JobType.query.get(field.data)
        if not form.job_type_ob:
            raise forms.ValidationError("Please select a job type")

    def validate_company_name(form, field):
        if len(field.data) > 6:
            caps = len(CAPS_RE.findall(field.data))
            small = len(SMALL_RE.findall(field.data))
            if small == 0 or caps / float(small) > 0.8:
                raise forms.ValidationError(u"Surely your organization isn’t named in uppercase?")

    def validate_company_logo(form, field):
        if not request.files['company_logo']:
            return
        try:
            g.company_logo = process_image(request.files['company_logo'])
        except IOError, e:
            raise forms.ValidationError(e.message)
        except KeyError, e:
            raise forms.ValidationError("Unknown file format")
        except UploadNotAllowed:
            raise forms.ValidationError("Unsupported file format. We accept JPEG, PNG and GIF")

    def validate_job_headline(form, field):
        if simplify_text(field.data) in (
                'awesome coder wanted at awesome company',
                'pragmatic programmer wanted at outstanding organisation',
                'pragmatic programmer wanted at outstanding organization') or (
                g.board and g.board.newjob_headline and simplify_text(field.data) == simplify_text(g.board.newjob_headline)):
            raise forms.ValidationError(u"Come on, write your own headline. You aren’t just another run-of-the-mill employer, right?")
        caps = len(CAPS_RE.findall(field.data))
        small = len(SMALL_RE.findall(field.data))
        if small == 0 or caps / float(small) > 1.0:
            raise forms.ValidationError("No shouting, please. Reduce the number of capital letters in your headline")
        for word_list, message in app.config.get('BANNED_WORDS', []):
            for word in word_list:
                if word in field.data.lower():
                    raise forms.ValidationError(message)

    def validate_job_headlineb(self, field):
        return self.validate_job_headline(field)

    def validate_job_location(form, field):
        if QUOTES_RE.search(field.data) is not None:
            raise forms.ValidationError(u"Don’t use quotes in the location name")

        caps = len(CAPS_RE.findall(field.data))
        small = len(SMALL_RE.findall(field.data))
        if small == 0 or caps / float(small) > 0.5:
            raise forms.ValidationError("Surely this location isn't named in uppercase?")

    def validate_job_pay_cash_min(form, field):
        if form.job_pay_type.data in (PAY_TYPE.ONETIME, PAY_TYPE.RECURRING):
            data = field.data.strip()
            if not data:
                raise forms.ValidationError("Please specify what this job pays")
            data = string_to_number(data)
            if data is None:
                raise forms.ValidationError("Unrecognised value %s" % field.data)
            else:
                field.data = data
        else:
            field.data = None

    def validate_job_pay_cash_max(form, field):
        if form.job_pay_type.data in (PAY_TYPE.ONETIME, PAY_TYPE.RECURRING):
            data = string_to_number(field.data.strip())
            if data is None:
                raise forms.ValidationError("Unrecognised value %s" % field.data)
            else:
                field.data = data
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
                    raise forms.ValidationError("Please enter a percentage between 0% and 100%")
            else:
                raise forms.ValidationError("Unrecognised value %s" % field.data)
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
                    raise forms.ValidationError("Please enter a percentage between 0% and 100%")
            else:
                raise forms.ValidationError("Unrecognised value %s" % field.data)
        else:
            # Discard submission if equity checkbox is unchecked
            field.data = None

    def validate(self):
        success = super(ListingForm, self).validate(send_signals=False)
        if success:
            if (not self.job_type_ob.nopay_allowed) and self.job_pay_type.data == PAY_TYPE.NOCASH:
                self.job_pay_type.errors.append(u"“%s” cannot pay nothing" % self.job_type_ob.title)
                success = False

            domain_name = get_email_domain(self.poster_email.data)
            domain = Domain.get(domain_name)
            if domain and domain.is_banned:
                self.poster_email.errors.append(u"%s is banned from posting jobs on Hasjob" % domain_name)
                success = False
            elif (not self.job_type_ob.webmail_allowed) and domain_name in webmail_domains:
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
                    elif (self.job_pay_type.data == PAY_TYPE.RECURRING and
                            self.job_pay_currency.data == 'INR' and
                            self.job_pay_cash_min.data < 60000):
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
        self.send_signals()
        return success

    def populate_from(self, post):
        self.job_headline.data = post.headline
        self.job_headlineb.data = post.headlineb
        self.job_type.data = post.type_id
        self.job_category.data = post.category_id
        self.job_location.data = post.location
        self.job_relocation_assist.data = post.relocation_assist
        self.job_description.data = post.description
        self.job_perks.data = True if post.perks else False
        self.job_perks_description.data = post.perks
        self.job_how_to_apply.data = post.how_to_apply
        self.company_name.data = post.company_name
        self.company_url.data = post.company_url
        self.poster_email.data = post.email
        self.twitter.data = post.twitter
        self.hr_contact.data = int(post.hr_contact or False)
        self.collaborators.data = post.admins
        self.job_pay_type.data = post.pay_type
        if post.pay_type is None:
            # This kludge required because WTForms doesn't know how to handle None in forms
            self.job_pay_type.data = -1
        self.job_pay_currency.data = post.pay_currency
        self.job_pay_cash_min.data = post.pay_cash_min
        self.job_pay_cash_max.data = post.pay_cash_max
        self.job_pay_equity.data = bool(post.pay_equity_min and post.pay_equity_max)
        self.job_pay_equity_min.data = post.pay_equity_min
        self.job_pay_equity_max.data = post.pay_equity_max


class ApplicationForm(forms.Form):
    apply_email = forms.RadioField("Email", validators=[forms.validators.DataRequired("Pick an email address")],
        description="Add new email addresses from your profile")
    apply_phone = forms.StringField("Phone",
        validators=[forms.validators.DataRequired("Specify a phone number"),
            forms.validators.StripWhitespace(),
            forms.validators.Length(min=1, max=15, message="%(max)d characters maximum")],
        description="A phone number the employer can reach you at")
    apply_message = forms.TinyMce4Field("Job application",
        content_css=content_css,
        validators=[forms.validators.DataRequired("You need to say something about yourself"),
            forms.validators.AllUrlsValid()],
        description=u"Please provide all details the employer has requested. To add a resume, "
        u"post it on LinkedIn or host the file on Dropbox and insert the link here")
    apply_optin = forms.BooleanField("Optional: sign me up for a better Hasjob experience",
        description=u"Hasjob’s maintainers may contact you about new features and can see this application for reference")

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
            # If choices is [] or [(None, None)]
            if not self.apply_email.choices or not self.apply_email.choices[0][0]:
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
            raise forms.ValidationError("Your application is very similar to one previously identified as spam")

        # Check for email and phone numbers in the message

        # Prepare text by replacing non-breaking spaces with spaces (for phone numbers) and removing URLs.
        # URLs may contain numbers that are not phone numbers.
        phone_search_text = URL_RE.sub('', field.data.replace('&nbsp;', ' ').replace('&#160;', ' ').replace(u'\xa0', ' '))
        if EMAIL_RE.search(field.data) is not None or PHONE_DETECT_RE.search(phone_search_text) is not None:
            raise forms.ValidationError("Do not include your email address or phone number in the application")


class KioskApplicationForm(forms.Form):
    apply_fullname = forms.StringField("Fullname", validators=[forms.validators.DataRequired("Specify your name")],
        description="Your full name")
    apply_email = forms.StringField("Email", validators=[forms.validators.DataRequired("Specify an email address")],
        description="Your email address")
    apply_phone = forms.StringField("Phone",
        validators=[forms.validators.DataRequired("Specify a phone number"),
            forms.validators.Length(min=1, max=15, message="%(max)d characters maximum")],
        description="A phone number the employer can reach you at")
    apply_message = forms.TinyMce4Field("Job application",
        content_css=content_css,
        validators=[forms.validators.DataRequired("You need to say something about yourself"),
            forms.validators.AllUrlsValid()],
        description=u"Please provide all details the employer has requested. To add a resume, "
        u"post it on LinkedIn or host the file on Dropbox and insert the link here")

    def validate_email(form, field):
        oldapp = JobApplication.query.filter_by(jobpost=form.post, user=None, email=field.data).count()
        if oldapp:
            raise forms.ValidationError("You have already applied for this position")


class ApplicationResponseForm(forms.Form):
    response_message = forms.TinyMce4Field("",
        content_css=content_css)


class ConfirmForm(forms.Form):
    terms_accepted = forms.BooleanField("I accept the terms of service",
        validators=[forms.validators.DataRequired("You must accept the terms of service to publish this post")])


class WithdrawForm(forms.Form):
    really_withdraw = forms.BooleanField("Yes, I really want to withdraw the job post",
        validators=[forms.validators.DataRequired(u"You must confirm withdrawal")])


class ReportForm(forms.Form):
    report_code = forms.RadioField("Code", coerce=int, validators=[forms.validators.InputRequired(u"Pick one")])


class RejectForm(forms.Form):
    reason = forms.StringField('Reason', validators=[forms.validators.DataRequired(u"Give a reason")])


class ModerateForm(forms.Form):
    reason = forms.TextAreaField('Reason',
        validators=[forms.validators.DataRequired(u"Give a reason"), forms.validators.Length(max=250)])


class PinnedForm(forms.Form):
    pinned = forms.BooleanField("Pin this")


class NewLocationForm(forms.Form):
    geoname = forms.RadioField("Top locations")


class EditLocationForm(forms.Form):
    description = forms.TinyMce4Field("Description", content_css=content_css)


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


class BoardOptionsForm(forms.Form):
    restrict_listing = forms.BooleanField(u"Restrict direct posting on this board to owners and the following users",
        default=True,
        description=u"As the owner of this board, you can always cross-add jobs from other boards on Hasjob")
    posting_users = forms.UserSelectMultiField(u"Allowed users",
        description=u"These users will be allowed to post jobs on this board under the following terms",
        usermodel=User, lastuser=lastuser)
    # Allow turning this off only in siteadmin-approved boards (deleted in the view for non-siteadmins)
    require_pay = forms.BooleanField(u"Require pay data for posting on this board?", default=True,
        description=u"Hasjob requires employers to reveal what they intend to pay, "
            u"but you can make it optional for jobs posted from this board. "
            u"Pay data is used to match candidates to jobs. We recommend you collect it")
    newjob_headline = forms.NullTextField(u"Headline",
        description=u"The sample headline shown to employers when post a job",
        validators=[
            forms.validators.StripWhitespace(),
            forms.validators.Length(min=0, max=100, message="%(max)d characters maximum")])
    newjob_blurb = forms.TinyMce4Field(u"Posting instructions",
        description=u"What should we tell employers when they post a job on your board? "
            u"Leave blank to use the default text",
        content_css=content_css,
        validators=[forms.validators.AllUrlsValid()])
    types = QuerySelectMultipleField("Job types",
        widget=ListWidget(), option_widget=CheckboxInput(),
        query_factory=lambda: JobType.query.filter_by(private=False).order_by('seq'), get_label=jobtype_label,
        validators=[forms.validators.DataRequired(u"You need to select at least one job type")],
        description=u"Jobs listed directly on this board can use one of the types enabled here")
    categories = QuerySelectMultipleField("Job categories",
        widget=ListWidget(), option_widget=CheckboxInput(),
        query_factory=lambda: JobCategory.query.filter_by(private=False).order_by('seq'), get_label='title',
        validators=[forms.validators.DataRequired(u"You need to select at least one category")],
        description=u"Jobs listed directly on this board can use one of the categories enabled here")


class BoardTaggingForm(forms.Form):
    tag_domains = forms.TextListField("Email Domains",
        description="Jobs from any of these email domains will be automatically added to this board. "
        "One per line. Do NOT add the www prefix")
    geonameids = forms.GeonameSelectMultiField("Locations",
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
                # FIXME: This will break domains where the subdomain handles email
                r = tldextract.extract(item.lower())
                d = u'.'.join([r.domain, r.suffix])
                if d not in webmail_domains:
                    domains.add(d)
        field.data = list(domains)

    def validate_geonameids(self, field):
        field.data = [int(x) for x in field.data if x.isdigit()]


class BoardForm(forms.Form):
    """
    Edit board settings.
    """
    title = forms.StringField(u"Title", validators=[
        forms.validators.DataRequired("The board needs a name"),
        forms.validators.StripWhitespace(),
        forms.validators.Length(min=1, max=80, message="%(max)d characters maximum")])
    caption = forms.NullTextField(u"Caption", validators=[
        forms.validators.Optional(),
        forms.validators.StripWhitespace(),
        forms.validators.Length(min=0, max=80, message="%(max)d characters maximum")],
        description=u"The title and caption appear at the top of the page. Keep them concise")
    name = forms.AnnotatedTextField(u"URL Name", prefix='https://', suffix=u'.hasjob.co',
        description=u"Optional — Will be autogenerated if blank",
        validators=[forms.validators.ValidName(), forms.validators.Length(min=0, max=63, message="%(max)d characters maximum"),
            AvailableName(u"This name has been taken by another board", model=Board)])
    description = forms.TinyMce4Field(u"Description",
        description=u"The description appears at the top of the board, above all jobs. "
            u"Use it to introduce your board and keep it brief",
        content_css=content_css,
        validators=[forms.validators.DataRequired("A description of the job board is required"),
            forms.validators.AllUrlsValid()])
    userid = forms.RadioField(u"Owner", validators=[forms.validators.DataRequired("Select an owner")],
        description=u"Select the user or organization who owns this board. "
            "Owners can add jobs to the board and edit these settings")
    require_login = forms.BooleanField(u"Prompt users to login", default=True,
        description=u"If checked, users must login to see all jobs available. "
            u"Logging in provides users better filtering for jobs that may be of interest to them, "
            u"and allows employers to understand how well their post is performing")
    options = forms.FormField(BoardOptionsForm, u"Direct posting options")
    autotag = forms.FormField(BoardTaggingForm, u"Automatic posting options")

    def validate_name(self, field):
        if field.data:
            if field.data in Board.reserved_names:
                raise forms.ValidationError(u"This name is reserved. Please use another name")
            # existing = Board.query.filter_by(name=field.data).first()
            # if existing and existing != self.edit_obj:
            #     raise forms.ValidationError(u"This name has been taken by another board")


class CampaignContentForm(forms.Form):
    subject = forms.NullTextField(__("Subject"), description=__("A subject title shown to viewers"),
        validators=[forms.validators.Optional(), forms.validators.StripWhitespace()])
    blurb = forms.TinyMce4Field(__("Blurb"),
        description=__("Teaser to introduce the campaign and convince users to interact"),
        content_css=content_css,
        validators=[forms.validators.Optional(), forms.validators.AllUrlsValid()])
    description = forms.TinyMce4Field(__("Description"),
        description=__("Optional additional content to follow after the blurb"),
        content_css=content_css,
        validators=[forms.validators.Optional(), forms.validators.AllUrlsValid()])
    banner_image = forms.URLField(__("Banner image URL"), validators=[forms.validators.Optional()],  # TODO: Use ImgeeField
        description=__("An image to illustrate your campaign"))
    banner_location = forms.RadioField(__("Banner location"), choices=BANNER_LOCATION.items(), coerce=int,
        description=__("Where should this banner appear relative to text?"))


class CampaignForm(forms.Form):
    title = forms.StringField(__("Title"), description=__("A reference name for looking up this campaign again"),
        validators=[forms.validators.DataRequired(__("A title is required")), forms.validators.StripWhitespace()])
    start_at = forms.DateTimeField(__("Start at"), timezone=lambda: g.user.timezone if g.user else None)
    end_at = forms.DateTimeField(__("End at"), timezone=lambda: g.user.timezone if g.user else None)
    public = forms.BooleanField(__("This campaign is live"))
    position = forms.RadioField(__("Display position"), choices=CAMPAIGN_POSITION.items(), coerce=int)
    priority = forms.IntegerField(__("Priority"), default=0,
        description=__("A larger number is higher priority when multiple campaigns are running on the "
            "same dates. 0 implies lowest priority"))
    boards = QuerySelectMultipleField(__("Boards"),
        widget=ListWidget(), option_widget=CheckboxInput(),
        query_factory=lambda: Board.query.order_by('title'), get_label='list_title',
        validators=[forms.validators.Optional()],
        description=__(u"Select the boards this campaign is active on"))
    geonameids = forms.GeonameSelectMultiField("Locations",
        description=__("This campaign will be targetted at users and jobs with matching locations"))
    user_required = forms.RadioField(__("User is required"), coerce=getbool,
        choices=[
            (None, __(u"N/A – Don’t target by login status")),
            (True, __(u"Yes – Show to logged in users")),
            (False, __(u"No – Show to anonymous users"))])
    flags = forms.RadioMatrixField("Flags", coerce=getbool, fields=Campaign.flag_choices,
        description=__("All selected flags must match the logged in user for the campaign to be shown"),
        choices=[('None', __(u"N/A")), ('True', __(u"True")), ('False', __(u"False"))])
    content = forms.FormField(CampaignContentForm, __("Campaign content"))

    def validate_geonameids(self, field):
        field.data = [int(x) for x in field.data if x.isdigit()]

    def validate_end_at(self, field):
        if field.data <= self.start_at.data:
            raise forms.ValidationError(__(u"The campaign can’t end before it starts"))


class CampaignActionForm(forms.Form):
    title = forms.StringField(__("Title"), description=__("Contents of the call to action button"),
        validators=[forms.validators.DataRequired("You must provide some text"), forms.validators.StripWhitespace()])
    icon = forms.NullTextField(__("Icon"), validators=[forms.validators.Optional()],
        description=__("Optional Font-Awesome icon name"))
    public = forms.BooleanField(__("This action is live"))
    type = forms.RadioField(__("Type"), choices=CAMPAIGN_ACTION.items(), validators=[forms.validators.DataRequired(__("This is required"))])
    group = forms.NullTextField(__("RSVP group"), validators=[forms.validators.Optional()],
        description=__("If you have multiple RSVP actions, add an optional group name"))
    category = forms.RadioField(__("Category"), validators=[forms.validators.DataRequired(__("This is required"))],
        widget=forms.InlineListWidget(class_='button-bar', class_prefix='btn btn-'), choices=[
        (u'default', __(u"Default")),
        (u'primary', __(u"Primary")),
        (u'success', __(u"Success")),
        (u'info', __(u"Info")),
        (u'warning', __(u"Warning")),
        (u'danger', __(u"Danger")),
        ])
    message = forms.TinyMce4Field(__("Message"),
        description=__("Message shown after the user has performed an action (for forms and RSVP type)"),
        content_css=content_css,
        validators=[forms.validators.Optional(), forms.validators.AllUrlsValid()])
    link = forms.URLField(__("Link"), description=__(u"URL to redirect to, if type is “follow link”"),
        validators=[
            forms.validators.StripWhitespace(),
            optional_url,
            forms.validators.Length(min=0, max=250, message="%(max)d characters maximum"),
            forms.validators.ValidUrl()])
    form = forms.TextAreaField(__("Form JSON"), description=__("Form definition (for form type)"),
        validators=[forms.validators.Optional()])
    seq = forms.IntegerField(__("Sequence #"), validators=[forms.validators.DataRequired(__("This is required"))],
        description=__("Sequence number for displaying this action when multiple actions are available to the user"))


class DomainForm(forms.Form):
    title = forms.StringField(__(u"Common name"),
        validators=[forms.validators.DataRequired(), forms.validators.StripWhitespace()],
        description=__("The name of your organization, excluding legal suffixes like Pvt Ltd"))
    legal_title = forms.NullTextField(__("Legal name"), validators=[forms.validators.Optional()],
        description=__(u"Optional — The full legal name of your organization"))
    logo_url = forms.URLField(__("Logo URL"), validators=[forms.validators.Optional()],  # TODO: Use ImgeeField
        description=__(u"Optional — Your organization’s logo"))
    description = forms.TinyMce4Field(__("Description"),
        description=__("Who are you and why should someone work for you? Tell your story"),
        content_css=content_css, validators=[
            forms.validators.AllUrlsValid(invalid_urls=invalid_urls),
            forms.validators.NoObfuscatedEmail(u"Do not include contact information here")])


# --- Credits and bid forms ---------------------------------------------------

class GrantCreditsForm(forms.Form):
    users = forms.UserSelectMultiField(__("Users"),
        description=__(u"Select the users you’d like to grant credits to"),
        usermodel=User, lastuser=lastuser)
    value = forms.IntegerField(__("Credit value"), validators=[forms.validators.DataRequired()])
    memo = forms.StringField(__("Memo"), validators=[forms.validators.DataRequired()])

    def validate_value(self, field):
        if field.data == 0:
            raise forms.ValidationError("Value must be non-zero")


class PinBidForm(forms.Form):
    start_at = forms.DateTimeField(__("Start at"), timezone=lambda: g.user.timezone if g.user else None,
        description=__("When would you like to start pinning? (Timezone is {timezone})"))
    end_at = forms.DateTimeField(__("End at"), timezone=lambda: g.user.timezone if g.user else None,
        description=__("When do you want to take off the pin?"))
    geonameids = forms.GeonameSelectMultiField("Locations",
        description=__(u"Optional — Your post will be pinned only for users in matching locations. "
            u"Use this if you are not interested in targeting candidates in different locations from you. "
            u"Location matching is on the basis of IP address and is not 100%% accurate. "
            u"For reference, your current location appears to be {location}"))
    value = forms.IntegerField(__("Bid value"), default=1,
        description=__("How many credits per user? A higher value improves your chance of winning. "
            "If your bid wins, you will only be charged as many credits as the next highest bidder "
            "(with a floor price of 1 credit)"))
    load = forms.IntegerField(__("Load credits"),
        description=__(u"You have {count} credits available. Please specify how many you’d like to commit to this bid. "
            "Committed credits will not be available for use elsewhere until released from this bid"))

    def validate_start_at(self, field):
        if field.value < self.post.datetime:
            field.value = self.post.datetime

    def validate_end_at(self, field):
        if field.value > self.post.expiry_date:
            field.value = self.post.expiry_date
