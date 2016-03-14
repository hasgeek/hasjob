# -*- coding: utf-8 -*-

from baseframe import __
import baseframe.forms as forms
from . import content_css


class ApplicationResponseForm(forms.Form):
    response_message = forms.TinyMce4Field("",
        content_css=content_css)


class ConfirmForm(forms.Form):
    terms_accepted = forms.BooleanField(__("I accept the terms of service"),
        validators=[forms.validators.DataRequired(__("You must accept the terms of service to publish this post"))])


class WithdrawForm(forms.Form):
    really_withdraw = forms.BooleanField(__("Yes, I really want to withdraw the job post"),
        validators=[forms.validators.DataRequired(__(u"You must confirm withdrawal"))])


class ReportForm(forms.Form):
    report_code = forms.RadioField(__("Code"), coerce=int, validators=[forms.validators.InputRequired(__(u"Pick one"))])


class RejectForm(forms.Form):
    reason = forms.StringField(__("Reason"), validators=[forms.validators.DataRequired(__(u"Give a reason"))])


class ModerateForm(forms.Form):
    reason = forms.TextAreaField(__("Reason"),
        validators=[forms.validators.DataRequired(__(u"Give a reason")), forms.validators.Length(max=250)])


class PinnedForm(forms.Form):
    pinned = forms.BooleanField(__("Pin this"))


class NewLocationForm(forms.Form):
    geoname = forms.RadioField(__("Top locations"))


class EditLocationForm(forms.Form):
    description = forms.TinyMce4Field(__("Description"), content_css=content_css)
