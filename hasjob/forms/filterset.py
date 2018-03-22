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


class FiltersetForm(forms.Form):
    title = forms.StringField(__("Title"), description=__("A title shown to viewers"),
        validators=[forms.validators.DataRequired()], filters=[forms.filters.strip()])
    description = forms.TinyMce4Field(__("Description"),
	    description=__("Description shown to viewers and search engines"),
	    validators=[forms.validators.DataRequired()])
    geonameids = forms.GeonameSelectMultiField("Locations",
        description=__("Locations"), filters=[format_geonameids])
    remote_location = forms.BooleanField(__("Match remote jobs"))
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
    pay_cash_currency = forms.RadioField(__("Currency"), choices=CURRENCY.items(),
        validators=[forms.validators.Optional()])
    pay_cash = forms.IntegerField(__("Pay"), description=__("Minimum amount"),
        validators=[forms.validators.Optional()])
    keywords = forms.StringField(__("Keywords"), description=__("Keywords"),
        validators=[forms.validators.Optional()], filters=[forms.filters.strip()])
