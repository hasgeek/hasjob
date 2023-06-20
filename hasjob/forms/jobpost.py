import re
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher

import baseframe.forms as forms
from baseframe import _, __
from baseframe.utils import is_public_email_domain
from flask import Markup, g, request
from flask_lastuser import LastuserResourceError

from coaster.utils import get_email_domain, getbool

from .. import app, lastuser
from ..models import CURRENCY, PAY_TYPE, Domain, JobApplication, JobType, User
from ..uploads import UploadNotAllowed, process_image
from ..utils import (
    EMAIL_RE,
    PHONE_DETECT_RE,
    URL_RE,
    get_word_bag,
    simplify_text,
    string_to_number,
)
from .helper import content_css, invalid_urls, optional_url

QUOTES_RE = re.compile(r'[\'"`‘’“”′″‴«»]+')

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
                return super().pre_validate(form)
        else:
            self.data = None


class ListingForm(forms.Form):
    """Form for new job posts"""

    job_headline = forms.StringField(
        __("Headline"),
        description=Markup(
            __(
                "A single-line summary. This goes to the front page and across the network. "
                """<a id="abtest" class="no-jshidden" href="#">A/B test it?</a>"""
            )
        ),
        validators=[
            forms.validators.DataRequired(__("A headline is required")),
            forms.validators.Length(
                min=1, max=100, message=__("%(max)d characters maximum")
            ),
            forms.validators.NoObfuscatedEmail(
                __("Do not include contact information in the post")
            ),
        ],
        filters=[forms.filters.strip()],
    )
    job_headlineb = forms.StringField(
        __("Headline B"),
        description=__(
            "An alternate headline that will be shown to 50%% of users. "
            "You’ll get a count of views per headline"
        ),
        validators=[
            forms.validators.Optional(),
            forms.validators.Length(
                min=1, max=100, message=__("%(max)d characters maximum")
            ),
            forms.validators.NoObfuscatedEmail(
                __("Do not include contact information in the post")
            ),
        ],
        filters=[forms.filters.strip(), forms.filters.none_if_empty()],
    )
    job_type = forms.RadioField(
        __("Type"),
        coerce=int,
        validators=[
            forms.validators.InputRequired(__("The job type must be specified"))
        ],
    )
    job_category = forms.RadioField(
        __("Category"),
        coerce=int,
        validators=[forms.validators.InputRequired(__("Select a category"))],
    )
    job_location = forms.StringField(
        __("Location"),
        description=__(
            '“Bangalore”, “Chennai”, “Pune”, etc or “Anywhere” (without quotes)'
        ),
        validators=[
            forms.validators.DataRequired(
                __("If this job doesn’t have a fixed location, use “Anywhere”")
            ),
            forms.validators.Length(
                min=3, max=80, message=__("%(max)d characters maximum")
            ),
        ],
        filters=[forms.filters.strip()],
    )
    job_relocation_assist = forms.BooleanField(__("Relocation assistance available"))
    job_description = forms.TinyMce4Field(
        __("Description"),
        content_css=content_css,
        description=__(
            "Don’t just describe the job, tell a compelling story for why someone"
            " should work for you"
        ),
        validators=[
            forms.validators.DataRequired(__("A description of the job is required")),
            forms.validators.AllUrlsValid(invalid_urls=invalid_urls),
            forms.validators.NoObfuscatedEmail(
                __("Do not include contact information in the post")
            ),
        ],
        tinymce_options={'convert_urls': True},
    )
    job_perks = forms.BooleanField(__("Job perks are available"))
    job_perks_description = forms.TinyMce4Field(
        __("Describe job perks"),
        content_css=content_css,
        description=__("Stock options, free lunch, free conference passes, etc"),
        validators=[
            forms.validators.AllUrlsValid(invalid_urls=invalid_urls),
            forms.validators.NoObfuscatedEmail(
                __("Do not include contact information in the post")
            ),
        ],
    )
    job_pay_type = forms.RadioField(
        __("What does this job pay?"),
        coerce=int,
        validators=[
            forms.validators.InputRequired(__("You need to specify what this job pays"))
        ],
        choices=list(PAY_TYPE.items()),
    )
    job_pay_currency = ListingPayCurrencyField(
        __("Currency"), choices=list(CURRENCY.items()), default=CURRENCY.INR
    )
    job_pay_cash_min = forms.StringField(__("Minimum"))
    job_pay_cash_max = forms.StringField(__("Maximum"))
    job_pay_equity = forms.BooleanField(__("Equity compensation is available"))
    job_pay_equity_min = forms.StringField(__("Minimum"))
    job_pay_equity_max = forms.StringField(__("Maximum"))
    job_how_to_apply = forms.TextAreaField(
        __("What should a candidate submit when applying for this job?"),
        description=__(
            "Example: “Include your LinkedIn and GitHub profiles.” "
            "We now require candidates to apply through the job board only. "
            "Do not include any contact information here. Candidates CANNOT "
            "attach resumes or other documents, so do not ask for that"
        ),
        validators=[
            forms.validators.DataRequired(
                __(
                    "We do not offer screening services. Please specify what candidates"
                    " should submit"
                )
            ),
            forms.validators.NoObfuscatedEmail(
                __("Do not include contact information in the post")
            ),
        ],
    )
    company_name = forms.StringField(
        __("Employer name"),
        description=__(
            "The name of the organization where the position is."
            " If your stealth startup doesn't have a name yet, use your own."
            " We do not accept posts from third parties such as recruitment"
            " consultants. Such posts may be removed without notice"
        ),
        validators=[
            forms.validators.DataRequired(
                __(
                    "This is required. Posting any name other than that of the actual"
                    " organization is a violation of the ToS"
                )
            ),
            forms.validators.Length(
                min=4,
                max=80,
                message=__("The name must be within %(min)d to %(max)d characters"),
            ),
        ],
        filters=[forms.filters.strip()],
    )
    company_logo = forms.FileField(
        __("Logo"),
        description=__(
            "Optional — Your organization’s logo will appear at the top of your post."
        ),
        # validators=[file_allowed(uploaded_logos, "That image type is not supported")])
    )
    company_logo_remove = forms.BooleanField(__("Remove existing logo"))
    company_url = forms.URLField(
        __("URL"),
        description=__("Your organization’s website"),
        validators=[
            forms.validators.DataRequired(),
            optional_url,
            forms.validators.Length(max=255, message=__("%(max)d characters maximum")),
            forms.validators.ValidUrl(),
        ],
        filters=[forms.filters.strip()],
    )
    hr_contact = forms.RadioField(
        __(
            "Is it okay for recruiters and other "
            "intermediaries to contact you about this post?"
        ),
        coerce=getbool,
        description=__("We’ll display a notice to this effect on the post"),
        default=0,
        choices=[
            (0, __("No, it is NOT OK")),
            (1, __("Yes, recruiters may contact me")),
        ],
    )
    poster_email = forms.EmailField(
        __("Email"),
        description=Markup(
            __(
                "This is where we’ll send your confirmation email and all job"
                " applications. We recommend using a shared email address such as"
                " jobs@your-organization.com. <strong>Listings are classified by your"
                " email domain,</strong> so use a work email address. Your email"
                " address will not be revealed to applicants until you respond"
            )
        ),
        validators=[
            forms.validators.DataRequired(
                __("We need to confirm your email address before the job can be listed")
            ),
            forms.validators.Length(
                min=5, max=80, message=__("%(max)d characters maximum")
            ),
            forms.validators.ValidEmail(
                __("This does not appear to be a valid email address")
            ),
        ],
        filters=[forms.filters.strip()],
    )
    #: Twitter support is disabled due to API access change in April 2023
    # twitter = forms.AnnotatedTextField(
    #     __("Twitter"),
    #     description=__(
    #         "Optional — your organization’s Twitter account. "
    #         "We’ll tweet mentioning you so you get included on replies"
    #     ),
    #     prefix='@',
    #     validators=[
    #         forms.validators.Optional(),
    #         forms.validators.Length(
    #             min=0,
    #             max=15,
    #             message=__("Twitter accounts can’t be over %(max)d characters long"),
    #         ),
    #     ],
    #     filters=[forms.filters.strip(), forms.filters.none_if_empty()],
    # )
    collaborators = forms.UserSelectMultiField(
        __("Collaborators"),
        description=__(
            "If someone is helping you evaluate candidates, type their names here."
            " They must have a Hasgeek account. They will not receive email"
            " notifications — use a shared email address above for that — but they will"
            " be able to respond to candidates who apply"
        ),
        usermodel=User,
        lastuser=lastuser,
    )

    def validate_twitter(self, field):
        if field.data.startswith('@'):
            field.data = field.data[1:]
        if INVALID_TWITTER_RE.search(field.data):
            raise forms.ValidationError(
                _("That does not appear to be a valid Twitter account")
            )

    def validate_poster_email(self, field):
        field.data = field.data.lower()

    def validate_job_type(self, field):
        # This validator exists primarily for this assignment, used later in the form
        # by other validators
        self.job_type_ob = JobType.query.get(field.data)
        if not self.job_type_ob:
            raise forms.ValidationError(_("Please select a job type"))

    def validate_company_name(self, field):
        if len(field.data) > 6:
            caps = len(CAPS_RE.findall(field.data))

            # small = len(SMALL_RE.findall(field.data))  # deprecated on 30-11-2018
            # if small == 0 or caps / float(small) > 0.8:  # deprecated on 30-11-2018

            # For now, only 6 capital letters are allowed in company name
            if caps > 6:
                raise forms.ValidationError(
                    _("Surely your organization isn’t named in uppercase?")
                )

    def validate_company_logo(self, field):
        if not ('company_logo' in request.files and request.files['company_logo']):
            return
        try:
            g.company_logo = process_image(request.files['company_logo'])
        except OSError:
            raise forms.ValidationError(
                _("This image could not be processed")
            ) from None
        except KeyError:
            raise forms.ValidationError(_("Unknown file format")) from None
        except UploadNotAllowed:
            raise forms.ValidationError(
                _("Unsupported file format. We accept JPEG, PNG and GIF")
            ) from None

    def validate_job_headline(self, field):
        if simplify_text(field.data) in (
            'awesome coder wanted at awesome company',
            'pragmatic programmer wanted at outstanding organisation',
            'pragmatic programmer wanted at outstanding organization',
        ) or (
            g.board
            and g.board.newjob_headline
            and simplify_text(field.data) == simplify_text(g.board.newjob_headline)
        ):
            raise forms.ValidationError(
                _(
                    "Come on, write your own headline. You aren’t just another"
                    " run-of-the-mill employer, right?"
                )
            )
        caps = len(CAPS_RE.findall(field.data))
        small = len(SMALL_RE.findall(field.data))
        if small == 0 or caps / float(small) > 1.0:
            raise forms.ValidationError(
                _(
                    "No shouting, please. Reduce the number of capital letters in your"
                    " headline"
                )
            )
        for word_list, message in app.config.get('BANNED_WORDS', []):
            for word in word_list:
                if word in field.data.lower():
                    raise forms.ValidationError(message)

    def validate_job_headlineb(self, field):
        return self.validate_job_headline(field)

    def validate_job_location(self, field):
        if QUOTES_RE.search(field.data) is not None:
            raise forms.ValidationError(_("Don’t use quotes in the location name"))

        caps = len(CAPS_RE.findall(field.data))
        small = len(SMALL_RE.findall(field.data))
        if small == 0 or caps / float(small) > 1.0:
            raise forms.ValidationError(
                _("Surely this location isn't named in uppercase?")
            )

    def validate_job_pay_cash_min(self, field):
        if self.job_pay_type.data in (PAY_TYPE.ONETIME, PAY_TYPE.RECURRING):
            data = field.data.strip()
            if not data:
                raise forms.ValidationError(_("Please specify what this job pays"))
            data = string_to_number(data)
            if data is None:
                raise forms.ValidationError(_("Unrecognised value %s") % field.data)
            field.data = data
        else:
            field.data = None

    def validate_job_pay_cash_max(self, field):
        if self.job_pay_type.data in (PAY_TYPE.ONETIME, PAY_TYPE.RECURRING):
            data = string_to_number(field.data.strip())
            if data is None:
                raise forms.ValidationError(_("Unrecognised value %s") % field.data)
            field.data = data
        else:
            field.data = None

    def validate_job_pay_equity_min(self, field):
        if self.job_pay_equity.data:
            data = field.data.strip()
            if data:
                if not data[-1].isdigit():
                    data = field.data[:-1]  # Remove % symbol
                data = data.replace(',', '').strip()  # Remove thousands separator
                try:
                    field.data = Decimal(data)
                except InvalidOperation:
                    raise forms.ValidationError(
                        _("Please enter a percentage between 0%% and 100%%")
                    ) from None
            else:
                raise forms.ValidationError(_("Unrecognised value %s") % field.data)
        else:
            # Discard submission if equity checkbox is unchecked
            field.data = None

    def validate_job_pay_equity_max(self, field):
        if self.job_pay_equity.data:
            data = field.data.strip()
            if data:
                if not data[-1].isdigit():
                    data = field.data[:-1]  # Remove % symbol
                data = data.replace(',', '').strip()  # Remove thousands separator
                try:
                    field.data = Decimal(data)
                except InvalidOperation:
                    raise forms.ValidationError(
                        _("Please enter a percentage between 0%% and 100%%")
                    ) from None
            else:
                raise forms.ValidationError(_("Unrecognised value %s") % field.data)
        else:
            # Discard submission if equity checkbox is unchecked
            field.data = None

    def validate(self, *args, **kwargs):
        success = super().validate(*args, **kwargs)
        if success:
            if (
                not self.job_type_ob.nopay_allowed
            ) and self.job_pay_type.data == PAY_TYPE.NOCASH:
                self.job_pay_type.errors.append(
                    _("“%s” cannot pay nothing") % self.job_type_ob.title
                )
                success = False

            domain_name = get_email_domain(self.poster_email.data)
            domain = Domain.get(domain_name)
            if domain and domain.is_banned:
                self.poster_email.errors.append(
                    _("%s is banned from posting jobs on Hasjob") % domain_name
                )
                success = False
            elif (not self.job_type_ob.webmail_allowed) and is_public_email_domain(
                domain_name, default=False
            ):
                self.poster_email.errors.append(
                    _(
                        "Public webmail accounts like Gmail are not accepted. Please"
                        " use your corporate email address"
                    )
                )
                success = False

            # Check for cash pay range
            if self.job_pay_type.data in (PAY_TYPE.ONETIME, PAY_TYPE.RECURRING):
                if self.job_pay_cash_min.data == 0:
                    if self.job_pay_cash_max.data == 10000000:
                        self.job_pay_cash_max.errors.append(_("Please select a range"))
                        success = False
                    else:
                        self.job_pay_cash_min.errors.append(
                            _("Please specify a minimum non-zero pay")
                        )
                        success = False
                else:
                    if self.job_pay_cash_max.data == 10000000:
                        if self.job_pay_currency.data == 'INR':
                            figure = _("1 crore")
                        else:
                            figure = _("10 million")
                        self.job_pay_cash_max.errors.append(
                            _(
                                "You’ve selected an upper limit of {figure}. That can’t"
                                " be right"
                            ).format(figure=figure)
                        )
                        success = False
                    elif (
                        self.job_pay_type.data == PAY_TYPE.RECURRING
                        and self.job_pay_currency.data == 'INR'
                        and self.job_pay_cash_min.data < 60000
                    ):
                        self.job_pay_cash_min.errors.append(
                            _(
                                "That’s rather low. Did you specify monthly pay instead"
                                " of annual pay? Multiply by 12"
                            )
                        )
                        success = False
                    elif self.job_pay_cash_max.data > self.job_pay_cash_min.data * 4:
                        self.job_pay_cash_max.errors.append(
                            _(
                                "Please select a narrower range, with maximum within 4×"
                                " minimum"
                            )
                        )
                        success = False
            if self.job_pay_equity.data:
                if self.job_pay_equity_min.data == 0:
                    if self.job_pay_equity_max.data == 100:
                        self.job_pay_equity_max.errors.append(
                            _("Please select a range")
                        )
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

                    if (
                        self.job_pay_equity_max.data
                        > self.job_pay_equity_min.data * multiplier
                    ):
                        self.job_pay_equity_max.errors.append(
                            _(
                                "Please select a narrower range, with maximum within"
                                " %d× minimum"
                            )
                            % multiplier
                        )
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
        # self.twitter.data = post.twitter
        self.hr_contact.data = int(post.hr_contact or False)
        self.collaborators.data = post.admins
        self.job_pay_type.data = post.pay_type
        if post.pay_type is None:
            # This kludge required because WTForms doesn't know how to handle None in
            # forms
            self.job_pay_type.data = -1
        self.job_pay_currency.data = post.pay_currency
        self.job_pay_cash_min.data = post.pay_cash_min
        self.job_pay_cash_max.data = post.pay_cash_max
        self.job_pay_equity.data = bool(post.pay_equity_min and post.pay_equity_max)
        self.job_pay_equity_min.data = post.pay_equity_min
        self.job_pay_equity_max.data = post.pay_equity_max


class ApplicationForm(forms.Form):
    apply_email = forms.RadioField(
        __("Email"),
        validators=[forms.validators.DataRequired(__("Pick an email address"))],
        description=__("Add new email addresses from your profile"),
    )
    apply_phone = forms.StringField(
        __("Phone"),
        validators=[
            forms.validators.DataRequired(__("Specify a phone number")),
            forms.validators.Length(
                min=1, max=15, message=__("%(max)d characters maximum")
            ),
        ],
        filters=[forms.filters.strip()],
        description=__("A phone number the employer can reach you at"),
    )
    apply_message = forms.TinyMce4Field(
        __("Job application"),
        content_css=content_css,
        validators=[
            forms.validators.DataRequired(
                __("You need to say something about yourself")
            ),
            forms.validators.AllUrlsValid(),
        ],
        description=__(
            "Please provide all details the employer has requested. To add a resume, "
            "post it on LinkedIn or host the file on Dropbox and insert the link here"
        ),
    )
    apply_optin = forms.BooleanField(
        __("Optional: sign me up for a better Hasjob experience"),
        description=__(
            "Hasjob’s maintainers may contact you about new features and can see this"
            " application for reference"
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_email.choices = []
        if g.user:
            self.apply_email.description = Markup(
                _(
                    'Add new email addresses from <a href="{}" target="_blank">your'
                    ' profile</a>'
                ).format(g.user.profile_url)
            )
            try:
                self.apply_email.choices = [
                    (e, e) for e in lastuser.user_emails(g.user)
                ]
            except LastuserResourceError:
                self.apply_email.choices = [(g.user.email, g.user.email)]
            # If choices is [] or [(None, None)]
            if not self.apply_email.choices or not self.apply_email.choices[0][0]:
                self.apply_email.choices = [
                    ('', Markup(_("<em>You have not verified your email address</em>")))
                ]

    def validate_apply_message(self, field):
        words = get_word_bag(field.data)
        self.words = words
        similar = False
        for oldapp in JobApplication.query.filter(JobApplication.response.SPAM).all():
            if oldapp.words:
                s = SequenceMatcher(None, words, oldapp.words)
                if s.ratio() > 0.8:
                    similar = True
                    break

        if similar:
            raise forms.ValidationError(
                _(
                    "Your application is very similar to one previously identified as"
                    " spam"
                )
            )

        # Check for email and phone numbers in the message

        # Prepare text by replacing non-breaking spaces with spaces (for phone numbers)
        # and removing URLs. URLs may contain numbers that are not phone numbers.
        phone_search_text = URL_RE.sub(
            '',
            field.data.replace('&nbsp;', ' ')
            .replace('&#160;', ' ')
            .replace('\xa0', ' '),
        )
        if (
            EMAIL_RE.search(field.data) is not None
            or PHONE_DETECT_RE.search(phone_search_text) is not None
        ):
            raise forms.ValidationError(
                _(
                    "Do not include your email address or phone number in the"
                    " application"
                )
            )


class KioskApplicationForm(forms.Form):
    apply_fullname = forms.StringField(
        __("Fullname"),
        validators=[forms.validators.DataRequired(__("Specify your name"))],
        description=__("Your full name"),
    )
    apply_email = forms.StringField(
        __("Email"),
        validators=[forms.validators.DataRequired(__("Specify an email address"))],
        description=__("Your email address"),
    )
    apply_phone = forms.StringField(
        __("Phone"),
        validators=[
            forms.validators.DataRequired(__("Specify a phone number")),
            forms.validators.Length(
                min=1, max=15, message=__("%(max)d characters maximum")
            ),
        ],
        description=__("A phone number the employer can reach you at"),
    )
    apply_message = forms.TinyMce4Field(
        __("Job application"),
        content_css=content_css,
        validators=[
            forms.validators.DataRequired(
                __("You need to say something about yourself")
            ),
            forms.validators.AllUrlsValid(),
        ],
        description=__(
            "Please provide all details the employer has requested. To add a resume, "
            "post it on LinkedIn or host the file on Dropbox and insert the link here"
        ),
    )

    def validate_email(self, field):
        oldapp = JobApplication.query.filter_by(
            jobpost=self.post, user=None, email=field.data
        ).count()
        if oldapp:
            raise forms.ValidationError(_("You have already applied for this position"))
