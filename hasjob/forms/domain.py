# -*- coding: utf-8 -*-


# from flask import Markup
from baseframe import __
import baseframe.forms as forms

from . import content_css, invalid_urls


class DomainForm(forms.Form):
    title = forms.StringField(__(u"Common name"),
        validators=[forms.validators.DataRequired(), forms.validators.StripWhitespace(),
            forms.validators.Length(min=1, max=250, message=__("%(max)d characters maximum"))],
        description=__("The name of your organization, excluding legal suffixes like Pvt Ltd"))
    legal_title = forms.NullTextField(__("Legal name"),
        validators=[forms.validators.Optional(),
            forms.validators.Length(min=1, max=250, message=__("%%(max)d characters maximum"))],
        description=__(u"Optional — The full legal name of your organization"))
    # logo_url = forms.URLField(__("Logo URL"),  # TODO: Use ImgeeField
    #     validators=[forms.validators.Optional(),
    #         forms.validators.Length(min=0, max=250, message=__("%%(max)d characters maximum"))],
    #     description=Markup(__(u"Optional — Your organization’s logo. "
    #         u"Upload at <a target='_blank' href='https://images.hasgeek.com/'>images.hasgeek.com</a> "
    #         u"and use the Direct Link URL")))
    description = forms.TinyMce4Field(__("Description"),
        description=__("Who are you and why should someone work for you? Tell your story"),
        content_css=content_css, validators=[
            forms.validators.AllUrlsValid(invalid_urls=invalid_urls),
            forms.validators.NoObfuscatedEmail(__("Do not include contact information here"))])
