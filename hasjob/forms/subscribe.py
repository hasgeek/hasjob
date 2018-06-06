# -*- coding: utf-8 -*-

from baseframe import __
import baseframe.forms as forms
from ..models import EMAIL_FREQUENCY


class JobPostSubscriptionForm(forms.Form):
    email_frequency = forms.RadioField(__("Frequency"), coerce=int,
        choices=EMAIL_FREQUENCY.items(), default=EMAIL_FREQUENCY.DAILY,
        validators=[forms.validators.InputRequired(__(u"Pick one"))])
    email = forms.EmailField(__("Email"), validators=[forms.validators.DataRequired(__("Specify an email address")),
        forms.validators.Length(min=5, max=80, message=__("%%(max)d characters maximum")),
        forms.validators.ValidEmail(__("This does not appear to be a valid email address"))],
        filters=[forms.filters.strip()])
