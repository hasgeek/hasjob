from flask import g

from baseframe import __
import baseframe.forms as forms

from ..models import CURRENCY, JobCategory, JobType
from ..models.board import board_jobcategory_table, board_jobtype_table
from .helper import content_css


def format_geonameids(geonameids):
    if not geonameids:
        return []
    return [int(geonameid) for geonameid in geonameids]


def get_currency_choices():
    choices = [('', __('None'))]
    choices.extend(list(CURRENCY.items()))
    return choices


class FiltersetForm(forms.Form):
    title = forms.StringField(
        __("Title"),
        description=__("A title shown to viewers"),
        validators=[forms.validators.DataRequired()],
        filters=[forms.filters.strip()],
    )
    description = forms.TinyMce4Field(
        __("Description"),
        content_css=content_css,
        description=__("Description shown to viewers and search engines"),
        validators=[forms.validators.DataRequired()],
    )
    types = forms.QuerySelectMultipleField(
        __("Job types"),
        widget=forms.ListWidget(),
        option_widget=forms.CheckboxInput(),
        get_label='title',
        validators=[forms.validators.Optional()],
    )
    categories = forms.QuerySelectMultipleField(
        __("Job categories"),
        widget=forms.ListWidget(),
        option_widget=forms.CheckboxInput(),
        get_label='title',
        validators=[forms.validators.Optional()],
    )
    geonameids = forms.GeonameSelectMultiField("Locations", filters=[format_geonameids])
    remote_location = forms.BooleanField(__("Match remote jobs"))
    pay_cash_currency = forms.RadioField(
        __("Currency"),
        choices=get_currency_choices(),
        default='',
        validators=[forms.validators.Optional()],
    )
    pay_cash = forms.IntegerField(
        __("Pay"),
        description=__("Minimum pay"),
        validators=[forms.validators.Optional()],
    )
    keywords = forms.StringField(
        __("Keywords"),
        validators=[forms.validators.Optional()],
        filters=[forms.filters.strip()],
    )
    auto_domains = forms.AutocompleteMultipleField(
        __("Domains"),
        autocomplete_endpoint='/api/1/domain/autocomplete',
        results_key='domains',
    )
    auto_tags = forms.AutocompleteMultipleField(
        __("Tags"), autocomplete_endpoint='/api/1/tag/autocomplete', results_key='tags'
    )

    def set_queries(self):
        if not self.edit_parent:
            self.edit_parent = g.board
        self.types.query = (
            JobType.query.join(board_jobtype_table)
            .filter(board_jobtype_table.c.board_id == self.edit_parent.id)
            .order_by(JobType.title)
        )
        self.categories.query = (
            JobCategory.query.join(board_jobcategory_table)
            .filter(board_jobcategory_table.c.board_id == self.edit_parent.id)
            .order_by(JobType.title)
        )
