from baseframe import forms

from .. import app

__all__ = ['content_css', 'invalid_urls', 'optional_url']


def content_css():
    return app.assets['css_editor'].urls()[0]


def invalid_urls():
    return app.config.get('INVALID_URLS', [])


def optional_url(form, field):
    """
    Validate URL only if present.
    """
    if not field.data:
        raise forms.validators.StopValidation()
    else:
        if '://' not in field.data:
            field.data = 'http://' + field.data
        validator = forms.validators.URL(
            message="This does not appear to be a valid URL."
        )
        try:
            return validator(form, field)
        except forms.ValidationError as e:
            raise forms.StopValidation(str(e))
