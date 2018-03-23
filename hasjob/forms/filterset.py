# -*- coding: utf-8 -*-

from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.widgets import CheckboxInput, ListWidget
from baseframe import __
import baseframe.forms as forms
from ..models import CURRENCY, JobType, JobCategory


def format_geonameids(geonameids):
    if not geonameids:
        return []
    return [int(geonameid) for geonameid in geonameids]


def get_currency_choices():
    choices = [('', __('None'))]
    choices.extend(CURRENCY.items())
    return choices


class FiltersetAssocationsForm(forms.Form):
    types = QuerySelectMultipleField(__("Job types"),
        widget=ListWidget(), option_widget=CheckboxInput(),
        query_factory=lambda: JobType.query.order_by('title'), get_label='title',
        validators=[forms.validators.Optional()],
        description=__(u"Select the job types this filterset should match"))
    categories = QuerySelectMultipleField(__("Job categories"),
        widget=ListWidget(), option_widget=CheckboxInput(),
        query_factory=lambda: JobCategory.query.order_by('title'), get_label='title',
        validators=[forms.validators.Optional()],
        description=__(u"Select the job categories this filterset should match"))
    geonameids = forms.GeonameSelectMultiField("Locations",
        description=__("Locations"), filters=[format_geonameids])
    auto_domains = forms.AutocompleteMultipleField(__("Domains"),
        autocomplete_endpoint='/api/1/domain/autocomplete', results_key='domains',
        description=__("Domains that should be matched for"))
    auto_tags = forms.AutocompleteMultipleField(__("Tags"),
        autocomplete_endpoint='/api/1/tag/autocomplete', results_key='tags',
        description=__("Tags that should be matched for"))


class FiltersetForm(forms.Form):
    title = forms.StringField(__("Title"), description=__("A title shown to viewers"),
        validators=[forms.validators.DataRequired()], filters=[forms.filters.strip()])
    description = forms.TinyMce4Field(__("Description"),
	    description=__("Description shown to viewers and search engines"),
	    validators=[forms.validators.DataRequired()])
    remote_location = forms.BooleanField(__("Match remote jobs"))
    pay_cash_currency = forms.RadioField(__("Currency"), choices=get_currency_choices(), default='',
        validators=[forms.validators.Optional()])
    pay_cash = forms.IntegerField(__("Pay"), description=__("Minimum pay"),
        validators=[forms.validators.Optional()])
    keywords = forms.StringField(__("Keywords"), description=__("Keywords"),
        validators=[forms.validators.Optional()], filters=[forms.filters.strip()])
    proxy = forms.FormField(FiltersetAssocationsForm, "")
