import tldextract
from flask import Markup

import baseframe.forms as forms
from baseframe import _, __
from baseframe.utils import is_public_email_domain

from .. import lastuser
from ..models import Board, JobCategory, JobType, User
from .helper import content_css


def jobtype_label(jobtype):
    annotations = []
    if jobtype.nopay_allowed:
        annotations.append(_('zero pay allowed'))
    if jobtype.webmail_allowed:
        annotations.append(_('webmail address allowed'))
    if annotations:
        return Markup('%s <small><em>(%s)</em></small>') % (
            jobtype.title,
            ', '.join(annotations),
        )
    else:
        return jobtype.title


class BoardOptionsForm(forms.Form):
    restrict_listing = forms.BooleanField(
        __("Restrict direct posting on this board to owners and the following users"),
        default=True,
        description=__(
            "As the owner of this board, you can always cross-add jobs from other boards on Hasjob"
        ),
    )
    posting_users = forms.UserSelectMultiField(
        __("Allowed users"),
        description=__(
            "These users will be allowed to post jobs on this board under the following terms"
        ),
        usermodel=User,
        lastuser=lastuser,
    )
    # Allow turning this off only in siteadmin-approved boards (deleted in the view for non-siteadmins)
    require_pay = forms.BooleanField(
        __("Require pay data for posting on this board?"),
        default=True,
        description=__(
            "Hasjob requires employers to reveal what they intend to pay, "
            "but you can make it optional for jobs posted from this board. "
            "Pay data is used to match candidates to jobs. We recommend you collect it"
        ),
    )
    newjob_headline = forms.StringField(
        __("Headline"),
        description=__(
            "Optional – The sample headline shown to employers when posting a job"
        ),
        validators=[
            forms.validators.Length(
                min=0, max=100, message=__("%%(max)d characters maximum")
            )
        ],
        filters=[forms.filters.strip(), forms.filters.none_if_empty()],
    )
    newjob_blurb = forms.TinyMce4Field(
        __("Posting instructions"),
        description=__(
            "Optional – What should we tell employers when they post a job on your board? "
            "Leave blank to use the default text"
        ),
        content_css=content_css,
        validators=[forms.validators.AllUrlsValid()],
    )
    types = forms.QuerySelectMultipleField(
        __("Job types"),
        widget=forms.ListWidget(),
        option_widget=forms.CheckboxInput(),
        query_factory=lambda: JobType.query.filter_by(private=False).order_by(
            JobType.seq
        ),
        get_label=jobtype_label,
        validators=[
            forms.validators.DataRequired(
                __("You need to select at least one job type")
            )
        ],
        description=__(
            "Jobs listed directly on this board can use one of the types enabled here"
        ),
    )
    categories = forms.QuerySelectMultipleField(
        __("Job categories"),
        widget=forms.ListWidget(),
        option_widget=forms.CheckboxInput(),
        query_factory=lambda: JobCategory.query.filter_by(private=False).order_by(
            JobCategory.seq
        ),
        get_label='title',
        validators=[
            forms.validators.DataRequired(
                __("You need to select at least one category")
            )
        ],
        description=__(
            "Jobs listed directly on this board can use one of the categories enabled here"
        ),
    )


class BoardTaggingForm(forms.Form):
    auto_domains = forms.TextListField(
        __("Email Domains"),
        description=__(
            "Jobs from any of these email domains will be automatically added to this board. "
            "One per line. Do NOT add the www prefix"
        ),
    )
    auto_geonameids = forms.GeonameSelectMultiField(
        __("Locations"),
        description=__(
            "Jobs in any of these locations will be automatically added to this board"
        ),
    )
    auto_keywords = forms.AutocompleteMultipleField(
        __("Tags"),
        autocomplete_endpoint='/api/1/tag/autocomplete',
        results_key='tags',
        description=__(
            "Jobs tagged with these keywords will be automatically added to this board"
        ),
    )
    auto_types = forms.QuerySelectMultipleField(
        __("Job types"),
        query_factory=lambda: JobType.query.filter_by(private=False).order_by(
            JobType.seq
        ),
        get_label='title',
        description=__("Jobs of this type will be automatically added to this board"),
    )
    auto_categories = forms.QuerySelectMultipleField(
        __("Job categories"),
        query_factory=lambda: JobCategory.query.filter_by(private=False).order_by(
            JobCategory.seq
        ),
        get_label='title',
        description=__(
            "Jobs of this category will be automatically added to this board"
        ),
    )
    auto_all = forms.BooleanField(
        __("All of the above criteria must match"),
        description=__(
            "Select this if, for example, you want to match all programming jobs in Bangalore "
            "and not all programming jobs or Bangalore-based jobs."
        ),
    )

    def validate_auto_domains(self, field):
        relist = []
        for item in field.data:
            item = item.strip()
            if ',' in item:
                relist.extend([x.strip() for x in item.split(',')])
            elif ' ' in item:
                relist.extend([x.strip() for x in item.split(' ')])
            else:
                relist.append(item)

        domains = set()
        for item in relist:
            if item:
                # FIXME: This will break domains where the subdomain handles email
                r = tldextract.extract(item.lower())
                d = '.'.join([r.domain, r.suffix])
                if not is_public_email_domain(d, default=False):
                    domains.add(d)
        field.data = list(domains)

    def validate_auto_geonameids(self, field):
        field.data = [int(x) for x in field.data if x.isdigit()]


class BoardForm(forms.Form):
    """
    Edit board settings.
    """

    title = forms.StringField(
        __("Title"),
        validators=[
            forms.validators.DataRequired(__("The board needs a name")),
            forms.validators.Length(
                min=1, max=80, message=__("%%(max)d characters maximum")
            ),
        ],
        filters=[forms.filters.strip()],
    )
    caption = forms.StringField(
        __("Caption"),
        description=__(
            "The title and caption appear at the top of the page. Keep them concise"
        ),
        validators=[
            forms.validators.Optional(),
            forms.validators.Length(
                min=0, max=80, message=__("%%(max)d characters maximum")
            ),
        ],
        filters=[forms.filters.strip(), forms.filters.none_if_empty()],
    )
    name = forms.AnnotatedTextField(
        __("URL Name"),
        prefix='https://',
        suffix='.hasjob.co',
        description=__("Optional — Will be autogenerated if blank"),
        validators=[
            forms.validators.ValidName(),
            forms.validators.Length(
                min=0, max=63, message=__("%%(max)d characters maximum")
            ),
            forms.AvailableName(
                __("This name has been taken by another board"), model=Board
            ),
        ],
    )
    description = forms.TinyMce4Field(
        __("Description"),
        description=__(
            "The description appears at the top of the board, above all jobs. "
            "Use it to introduce your board and keep it brief"
        ),
        content_css=content_css,
        validators=[
            forms.validators.DataRequired(
                __("A description of the job board is required")
            ),
            forms.validators.AllUrlsValid(),
        ],
    )
    userid = forms.SelectField(
        __("Owner"),
        validators=[forms.validators.DataRequired(__("Select an owner"))],
        description=__(
            "Select the user, organization or team who owns this board. "
            "Owners can add jobs to the board and edit these settings"
        ),
    )
    require_login = forms.BooleanField(
        __("Prompt users to login"),
        default=True,
        description=__(
            "If checked, users must login to see all jobs available. "
            "Logging in provides users better filtering for jobs that may be of interest to them, "
            "and allows employers to understand how well their post is performing"
        ),
    )
    options = forms.FormField(BoardOptionsForm, __("Direct posting options"))
    autotag = forms.FormField(BoardTaggingForm, __("Automatic posting options"))

    def validate_name(self, field):
        if field.data:
            if field.data in Board.reserved_names:
                raise forms.ValidationError(
                    _("This name is reserved. Please use another name")
                )

    def set_options(self, value):
        """Ignore FormField."""

    def set_autotag(self, value):
        """Ignore FormField."""
