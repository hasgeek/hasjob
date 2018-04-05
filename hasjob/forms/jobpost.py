# -*- coding: utf-8 -*-

import re
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher

from flask import g, request, Markup
from baseframe import _, __
import baseframe.forms as forms
from baseframe.utils import is_public_email_domain
from coaster.utils import getbool, get_email_domain
from flask_lastuser import LastuserResourceException

from ..models import User, JobType, JobApplication, EMPLOYER_RESPONSE, PAY_TYPE, CURRENCY, Domain
from ..uploads import process_image, UploadNotAllowed

from .. import app, lastuser
from ..utils import simplify_text, EMAIL_RE, URL_RE, PHONE_DETECT_RE, get_word_bag, string_to_number

from . import content_css, invalid_urls, optional_url

QUOTES_RE = re.compile(ur'[\'"`‘’“”′″‴«»]+')

CAPS_RE = re.compile('[A-Z]')
SMALL_RE = re.compile('[a-z]')
INVALID_TWITTER_RE = re.compile('[^a-z0-9_]', re.I)


class ListingPayCurrencyField(forms.RadioField):
    """
    A custom field to get around the annoying pre-validator.
    """
    def pre_validate(self, form):
        if form.job_pay_type.data in (PAY_TYPE.ONETIME, PAY_TYPE.RECURRING):
            if not self.data:
                raise ValueError(_("Pick one"))
            else:
                return super(ListingPayCurrencyField, self).pre_validate(form)
        else:
            self.data = None


class ListingForm(forms.Form):
    """Form for new job posts"""
    job_headline = forms.StringField(__("Headline"),
        description=Markup(__("A single-line summary. This goes to the front page and across the network. "
            """<a id="abtest" class="no-jshidden" href="#">A/B test it?</a>""")),
        validators=[forms.validators.DataRequired(__("A headline is required")),
            forms.validators.Length(min=1, max=100, message=__("%%(max)d characters maximum")),
            forms.validators.NoObfuscatedEmail(__(u"Do not include contact information in the post"))],
        filters=[forms.filters.strip()])
    job_headlineb = forms.StringField(__("Headline B"),
        description=__(u"An alternate headline that will be shown to 50%% of users. "
            u"You’ll get a count of views per headline"),
        validators=[forms.validators.Optional(),
            forms.validators.Length(min=1, max=100, message=__("%%(max)d characters maximum")),
            forms.validators.NoObfuscatedEmail(__(u"Do not include contact information in the post"))],
        filters=[forms.filters.strip(), forms.filters.none_if_empty()])
    job_type = forms.RadioField(__("Type"), coerce=int,
        validators=[forms.validators.InputRequired(__("The job type must be specified"))])
    job_category = forms.RadioField(__("Category"), coerce=int,
        validators=[forms.validators.InputRequired(__("Select a category"))])
    job_location = forms.StringField(__("Location"),
        description=__(u'“Bangalore”, “Chennai”, “Pune”, etc or “Anywhere” (without quotes)'),
        validators=[forms.validators.DataRequired(__(u"If this job doesn’t have a fixed location, use “Anywhere”")),
            forms.validators.Length(min=3, max=80, message=__("%%(max)d characters maximum"))],
        filters=[forms.filters.strip()])
    job_relocation_assist = forms.BooleanField(__("Relocation assistance available"))
    job_description = forms.TinyMce4Field(__("Description"),
        content_css=content_css,
        description=__(u"Don’t just describe the job, tell a compelling story for why someone should work for you"),
        validators=[forms.validators.DataRequired(__("A description of the job is required")),
            forms.validators.AllUrlsValid(invalid_urls=invalid_urls),
            forms.validators.NoObfuscatedEmail(__(u"Do not include contact information in the post"))],
        tinymce_options={'convert_urls': True})
    job_perks = forms.BooleanField(__("Job perks are available"))
    job_perks_description = forms.TinyMce4Field(__("Describe job perks"),
        content_css=content_css,
        description=__(u"Stock options, free lunch, free conference passes, etc"),
        validators=[forms.validators.AllUrlsValid(invalid_urls=invalid_urls),
            forms.validators.NoObfuscatedEmail(__(u"Do not include contact information in the post"))])
    job_pay_type = forms.RadioField(__("What does this job pay?"), coerce=int,
        validators=[forms.validators.InputRequired(__("You need to specify what this job pays"))],
        choices=PAY_TYPE.items())
    job_pay_currency = ListingPayCurrencyField(__("Currency"), choices=CURRENCY.items(), default=CURRENCY.INR)
    job_pay_cash_min = forms.StringField(__("Minimum"))
    job_pay_cash_max = forms.StringField(__("Maximum"))
    job_pay_equity = forms.BooleanField(__("Equity compensation is available"))
    job_pay_equity_min = forms.StringField(__("Minimum"))
    job_pay_equity_max = forms.StringField(__("Maximum"))
    job_how_to_apply = forms.TextAreaField(__("What should a candidate submit when applying for this job?"),
        description=__(u"Example: “Include your LinkedIn and GitHub profiles.” "
                       u"We now require candidates to apply through the job board only. "
                       u"Do not include any contact information here. Candidates CANNOT "
                       u"attach resumes or other documents, so do not ask for that"),
        validators=[
            forms.validators.DataRequired(__(u"We do not offer screening services. Please specify what candidates should submit")),
            forms.validators.NoObfuscatedEmail(__(u"Do not include contact information in the post"))])
    company_name = forms.StringField(__("Employer name"),
        description=__(u"The name of the organization where the position is. "
                       u"If your stealth startup doesn't have a name yet, use your own. "
                       u"We do not accept posts from third parties such as recruitment consultants. "
                       u"Such posts may be removed without notice"),
        validators=[forms.validators.DataRequired(__(u"This is required. Posting any name other than that of the actual organization is a violation of the ToS")),
            forms.validators.Length(min=4, max=80, message=__("The name must be within %%(min)d to %%(max)d characters"))],
        filters=[forms.filters.strip()])
    company_logo = forms.FileField(__("Logo"),
        description=__(u"Optional — Your organization’s logo will appear at the top of your post."),
        )  # validators=[file_allowed(uploaded_logos, "That image type is not supported")])
    company_logo_remove = forms.BooleanField(__("Remove existing logo"))
    company_url = forms.URLField(__("URL"),
        description=__(u"Your organization’s website"),
        validators=[forms.validators.DataRequired(), optional_url,
            forms.validators.Length(max=255, message=__("%%(max)d characters maximum")), forms.validators.ValidUrl()],
        filters=[forms.filters.strip()])
    hr_contact = forms.RadioField(__(u"Is it okay for recruiters and other "
        u"intermediaries to contact you about this post?"), coerce=getbool,
        description=__(u"We’ll display a notice to this effect on the post"),
        default=0,
        choices=[(0, __(u"No, it is NOT OK")), (1, __(u"Yes, recruiters may contact me"))])
    # Deprecated 2013-11-20
    # poster_name = forms.StringField(__("Name"),
    #     description=__(u"This is your name, for our records. Will not be revealed to applicants"),
    #     validators=[forms.validators.DataRequired(__("We need your name"))])
    poster_email = forms.EmailField(__("Email"),
        description=Markup(__(u"This is where we’ll send your confirmation email and all job applications. "
                    u"We recommend using a shared email address such as jobs@your-organization.com. "
                    u"<strong>Listings are classified by your email domain,</strong> "
                    u"so use a work email address. "
                    u"Your email address will not be revealed to applicants until you respond")),
        validators=[
            forms.validators.DataRequired(__("We need to confirm your email address before the job can be listed")),
            forms.validators.Length(min=5, max=80, message=__("%%(max)d characters maximum")),
            forms.validators.ValidEmail(__("This does not appear to be a valid email address"))],
        filters=[forms.filters.strip()])
    twitter = forms.AnnotatedTextField(__("Twitter"),
        description=__(u"Optional — your organization’s Twitter account. "
            u"We’ll tweet mentioning you so you get included on replies"),
        prefix='@', validators=[
            forms.validators.Optional(),
            forms.validators.Length(min=0, max=15, message=__(u"Twitter accounts can’t be over %%(max)d characters long"))],
        filters=[forms.filters.strip(), forms.filters.none_if_empty()])
    collaborators = forms.UserSelectMultiField(__(u"Collaborators"),
        description=__(u"If someone is helping you evaluate candidates, type their names here. "
                       u"They must have a HasGeek account. They will not receive email notifications "
                       u"— use a shared email address above for that — but they will be able to respond "
                       u"to candidates who apply"),
        usermodel=User, lastuser=lastuser)

    def validate_twitter(self, field):
        if field.data.startswith('@'):
            field.data = field.data[1:]
        if INVALID_TWITTER_RE.search(field.data):
            raise forms.ValidationError(_("That does not appear to be a valid Twitter account"))

    def validate_poster_email(form, field):
        field.data = field.data.lower()

    def validate_job_type(form, field):
        # This validator exists primarily for this assignment, used later in the form by other validators
        form.job_type_ob = JobType.query.get(field.data)
        if not form.job_type_ob:
            raise forms.ValidationError(_("Please select a job type"))

    def validate_company_name(form, field):
        if len(field.data) > 6:
            caps = len(CAPS_RE.findall(field.data))
            small = len(SMALL_RE.findall(field.data))
            if small == 0 or caps / float(small) > 0.8:
                raise forms.ValidationError(_(u"Surely your organization isn’t named in uppercase?"))

    def validate_company_logo(form, field):
        if not ('company_logo' in request.files and request.files['company_logo']):
            return
        try:
            g.company_logo = process_image(request.files['company_logo'])
        except IOError, e:
            raise forms.ValidationError(e.message)
        except KeyError, e:
            raise forms.ValidationError(_("Unknown file format"))
        except UploadNotAllowed:
            raise forms.ValidationError(_("Unsupported file format. We accept JPEG, PNG and GIF"))

    def validate_job_headline(form, field):
        if simplify_text(field.data) in (
                'awesome coder wanted at awesome company',
                'pragmatic programmer wanted at outstanding organisation',
                'pragmatic programmer wanted at outstanding organization') or (
                g.board and g.board.newjob_headline and simplify_text(field.data) == simplify_text(g.board.newjob_headline)):
            raise forms.ValidationError(_(u"Come on, write your own headline. You aren’t just another run-of-the-mill employer, right?"))
        caps = len(CAPS_RE.findall(field.data))
        small = len(SMALL_RE.findall(field.data))
        if small == 0 or caps / float(small) > 1.0:
            raise forms.ValidationError(_("No shouting, please. Reduce the number of capital letters in your headline"))
        for word_list, message in app.config.get('BANNED_WORDS', []):
            for word in word_list:
                if word in field.data.lower():
                    raise forms.ValidationError(message)

    def validate_job_headlineb(self, field):
        return self.validate_job_headline(field)

    def validate_job_location(form, field):
        if QUOTES_RE.search(field.data) is not None:
            raise forms.ValidationError(_(u"Don’t use quotes in the location name"))

        caps = len(CAPS_RE.findall(field.data))
        small = len(SMALL_RE.findall(field.data))
        if small == 0 or caps / float(small) > 0.5:
            raise forms.ValidationError(_("Surely this location isn't named in uppercase?"))

    def validate_job_pay_cash_min(form, field):
        if form.job_pay_type.data in (PAY_TYPE.ONETIME, PAY_TYPE.RECURRING):
            data = field.data.strip()
            if not data:
                raise forms.ValidationError(_("Please specify what this job pays"))
            data = string_to_number(data)
            if data is None:
                raise forms.ValidationError(_("Unrecognised value %%s") % field.data)
            else:
                field.data = data
        else:
            field.data = None

    def validate_job_pay_cash_max(form, field):
        if form.job_pay_type.data in (PAY_TYPE.ONETIME, PAY_TYPE.RECURRING):
            data = string_to_number(field.data.strip())
            if data is None:
                raise forms.ValidationError(_("Unrecognised value %%s") % field.data)
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
                    raise forms.ValidationError(_("Please enter a percentage between 0%% and 100%%"))
            else:
                raise forms.ValidationError(_("Unrecognised value %%s") % field.data)
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
                    raise forms.ValidationError(_("Please enter a percentage between 0%% and 100%%"))
            else:
                raise forms.ValidationError(_("Unrecognised value %%s") % field.data)
        else:
            # Discard submission if equity checkbox is unchecked
            field.data = None

    def validate(self):
        success = super(ListingForm, self).validate(send_signals=False)
        if success:
            if (not self.job_type_ob.nopay_allowed) and self.job_pay_type.data == PAY_TYPE.NOCASH:
                self.job_pay_type.errors.append(_(u"“%%s” cannot pay nothing") % self.job_type_ob.title)
                success = False

            domain_name = get_email_domain(self.poster_email.data)
            domain = Domain.get(domain_name)
            if domain and domain.is_banned:
                self.poster_email.errors.append(_(u"%%s is banned from posting jobs on Hasjob") % domain_name)
                success = False
            elif (not self.job_type_ob.webmail_allowed) and is_public_email_domain(domain_name, default=False):
                self.poster_email.errors.append(
                    _(u"Public webmail accounts like Gmail are not accepted. Please use your corporate email address"))
                success = False

            # Check for cash pay range
            if self.job_pay_type.data in (PAY_TYPE.ONETIME, PAY_TYPE.RECURRING):
                if self.job_pay_cash_min.data == 0:
                    if self.job_pay_cash_max.data == 10000000:
                        self.job_pay_cash_max.errors.append(_(u"Please select a range"))
                        success = False
                    else:
                        self.job_pay_cash_min.errors.append(_(u"Please specify a minimum non-zero pay"))
                        success = False
                else:
                    if self.job_pay_cash_max.data == 10000000:
                        if self.job_pay_currency.data == 'INR':
                            figure = _(u"1 crore")
                        else:
                            figure = _(u"10 million")
                        self.job_pay_cash_max.errors.append(
                            _(u"You’ve selected an upper limit of {figure}. That can’t be right").format(figure=figure))
                        success = False
                    elif (self.job_pay_type.data == PAY_TYPE.RECURRING and
                            self.job_pay_currency.data == 'INR' and
                            self.job_pay_cash_min.data < 60000):
                        self.job_pay_cash_min.errors.append(
                            _(u"That’s rather low. Did you specify monthly pay instead of annual pay? Multiply by 12"))
                        success = False
                    elif self.job_pay_cash_max.data > self.job_pay_cash_min.data * 4:
                        self.job_pay_cash_max.errors.append(_(u"Please select a narrower range, with maximum within 4× minimum"))
                        success = False
            if self.job_pay_equity.data:
                if self.job_pay_equity_min.data == 0:
                    if self.job_pay_equity_max.data == 100:
                        self.job_pay_equity_max.errors.append(_(u"Please select a range"))
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
                            _(u"Please select a narrower range, with maximum within %%d× minimum") % multiplier)
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
    apply_email = forms.RadioField(__("Email"), validators=[forms.validators.DataRequired(__("Pick an email address"))],
        description=__("Add new email addresses from your profile"))
    apply_phone = forms.StringField(__("Phone"),
        validators=[forms.validators.DataRequired(__("Specify a phone number")),
            forms.validators.Length(min=1, max=15, message=__("%%(max)d characters maximum"))],
        filters=[forms.filters.strip()],
        description=__("A phone number the employer can reach you at"))
    apply_message = forms.TinyMce4Field(__("Job application"),
        content_css=content_css,
        validators=[forms.validators.DataRequired(__("You need to say something about yourself")),
            forms.validators.AllUrlsValid()],
        description=__(u"Please provide all details the employer has requested. To add a resume, "
        u"post it on LinkedIn or host the file on Dropbox and insert the link here"))
    apply_optin = forms.BooleanField(__("Optional: sign me up for a better Hasjob experience"),
        description=__(u"Hasjob’s maintainers may contact you about new features and can see this application for reference"))

    def __init__(self, *args, **kwargs):
        super(ApplicationForm, self).__init__(*args, **kwargs)
        self.apply_email.choices = []
        if g.user:
            self.apply_email.description = Markup(
                _(u'Add new email addresses from <a href="{}" target="_blank">your profile</a>').format(
                    g.user.profile_url))
            try:
                self.apply_email.choices = [(e, e) for e in lastuser.user_emails(g.user)]
            except LastuserResourceException:
                self.apply_email.choices = [(g.user.email, g.user.email)]
            # If choices is [] or [(None, None)]
            if not self.apply_email.choices or not self.apply_email.choices[0][0]:
                self.apply_email.choices = [
                    ('', Markup(_("<em>You have not verified your email address</em>")))
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
            raise forms.ValidationError(_("Your application is very similar to one previously identified as spam"))

        # Check for email and phone numbers in the message

        # Prepare text by replacing non-breaking spaces with spaces (for phone numbers) and removing URLs.
        # URLs may contain numbers that are not phone numbers.
        phone_search_text = URL_RE.sub('', field.data.replace('&nbsp;', ' ').replace('&#160;', ' ').replace(u'\xa0', ' '))
        if EMAIL_RE.search(field.data) is not None or PHONE_DETECT_RE.search(phone_search_text) is not None:
            raise forms.ValidationError(_("Do not include your email address or phone number in the application"))


class KioskApplicationForm(forms.Form):
    apply_fullname = forms.StringField(__("Fullname"), validators=[forms.validators.DataRequired(__("Specify your name"))],
        description=__("Your full name"))
    apply_email = forms.StringField(__("Email"),
        validators=[forms.validators.DataRequired(__("Specify an email address"))],
        description=__("Your email address"))
    apply_phone = forms.StringField(__("Phone"),
        validators=[forms.validators.DataRequired(__("Specify a phone number")),
            forms.validators.Length(min=1, max=15, message=__("%%(max)d characters maximum"))],
        description=__("A phone number the employer can reach you at"))
    apply_message = forms.TinyMce4Field(__("Job application"),
        content_css=content_css,
        validators=[forms.validators.DataRequired(__("You need to say something about yourself")),
            forms.validators.AllUrlsValid()],
        description=__(u"Please provide all details the employer has requested. To add a resume, "
        u"post it on LinkedIn or host the file on Dropbox and insert the link here"))

    def validate_email(form, field):
        oldapp = JobApplication.query.filter_by(jobpost=form.post, user=None, email=field.data).count()
        if oldapp:
            raise forms.ValidationError(_("You have already applied for this position"))
