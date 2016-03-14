# -*- coding: utf-8 -*-

import tldextract
from flask import Markup
from baseframe import _, __
import baseframe.forms as forms
from baseframe.forms.sqlalchemy import AvailableName
from baseframe.staticdata import webmail_domains
from wtforms.widgets import CheckboxInput, ListWidget
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField

from ..models import User, JobType, JobCategory, Board

from .. import lastuser
from . import content_css


def jobtype_label(jobtype):
    annotations = []
    if jobtype.nopay_allowed:
        annotations.append(_(u'zero pay allowed'))
    if jobtype.webmail_allowed:
        annotations.append(_(u'webmail address allowed'))
    if annotations:
        return Markup(u'%s <small><em>(%s)</em></small>') % (jobtype.title, u', '.join(annotations))
    else:
        return jobtype.title


class BoardOptionsForm(forms.Form):
    restrict_listing = forms.BooleanField(__(u"Restrict direct posting on this board to owners and the following users"),
        default=True,
        description=__(u"As the owner of this board, you can always cross-add jobs from other boards on Hasjob"))
    posting_users = forms.UserSelectMultiField(__(u"Allowed users"),
        description=__(u"These users will be allowed to post jobs on this board under the following terms"),
        usermodel=User, lastuser=lastuser)
    # Allow turning this off only in siteadmin-approved boards (deleted in the view for non-siteadmins)
    require_pay = forms.BooleanField(__(u"Require pay data for posting on this board?"), default=True,
        description=__(u"Hasjob requires employers to reveal what they intend to pay, "
            u"but you can make it optional for jobs posted from this board. "
            u"Pay data is used to match candidates to jobs. We recommend you collect it"))
    newjob_headline = forms.NullTextField(__(u"Headline"),
        description=__(u"The sample headline shown to employers when post a job"),
        validators=[
            forms.validators.StripWhitespace(),
            forms.validators.Length(min=0, max=100, message=__("%(max)d characters maximum"))])
    newjob_blurb = forms.TinyMce4Field(__(u"Posting instructions"),
        description=__(u"What should we tell employers when they post a job on your board? "
            u"Leave blank to use the default text"),
        content_css=content_css,
        validators=[forms.validators.AllUrlsValid()])
    types = QuerySelectMultipleField(__("Job types"),
        widget=ListWidget(), option_widget=CheckboxInput(),
        query_factory=lambda: JobType.query.filter_by(private=False).order_by('seq'), get_label=jobtype_label,
        validators=[forms.validators.DataRequired(__(u"You need to select at least one job type"))],
        description=__(u"Jobs listed directly on this board can use one of the types enabled here"))
    categories = QuerySelectMultipleField(__("Job categories"),
        widget=ListWidget(), option_widget=CheckboxInput(),
        query_factory=lambda: JobCategory.query.filter_by(private=False).order_by('seq'), get_label='title',
        validators=[forms.validators.DataRequired(__(u"You need to select at least one category"))],
        description=__(u"Jobs listed directly on this board can use one of the categories enabled here"))


class BoardTaggingForm(forms.Form):
    tag_domains = forms.TextListField(__("Email Domains"),
        description=__("Jobs from any of these email domains will be automatically added to this board. "
        "One per line. Do NOT add the www prefix"))
    geonameids = forms.GeonameSelectMultiField(__("Locations"),
        description=__("Jobs in any of these locations will be automatically added to this board"))

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
    title = forms.StringField(__("Title"), validators=[
        forms.validators.DataRequired(__("The board needs a name")),
        forms.validators.StripWhitespace(),
        forms.validators.Length(min=1, max=80, message=__("%(max)d characters maximum"))])
    caption = forms.NullTextField(__("Caption"), validators=[
        forms.validators.Optional(),
        forms.validators.StripWhitespace(),
        forms.validators.Length(min=0, max=80, message=__("%(max)d characters maximum"))],
        description=__("The title and caption appear at the top of the page. Keep them concise"))
    name = forms.AnnotatedTextField(__("URL Name"), prefix='https://', suffix=u'.hasjob.co',
        description=__(u"Optional — Will be autogenerated if blank"),
        validators=[
            forms.validators.ValidName(),
            forms.validators.Length(min=0, max=63, message=__("%(max)d characters maximum")),
            AvailableName(__(u"This name has been taken by another board"), model=Board)])
    description = forms.TinyMce4Field(__(u"Description"),
        description=__(u"The description appears at the top of the board, above all jobs. "
            u"Use it to introduce your board and keep it brief"),
        content_css=content_css,
        validators=[forms.validators.DataRequired(__("A description of the job board is required")),
            forms.validators.AllUrlsValid()])
    userid = forms.RadioField(__(u"Owner"), validators=[forms.validators.DataRequired(__("Select an owner"))],
        description=__(u"Select the user or organization who owns this board. "
            "Owners can add jobs to the board and edit these settings"))
    require_login = forms.BooleanField(__(u"Prompt users to login"), default=True,
        description=__(u"If checked, users must login to see all jobs available. "
            u"Logging in provides users better filtering for jobs that may be of interest to them, "
            u"and allows employers to understand how well their post is performing"))
    options = forms.FormField(BoardOptionsForm, __(u"Direct posting options"))
    autotag = forms.FormField(BoardTaggingForm, __(u"Automatic posting options"))

    def validate_name(self, field):
        if field.data:
            if field.data in Board.reserved_names:
                raise forms.ValidationError(_(u"This name is reserved. Please use another name"))
