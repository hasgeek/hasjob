# -*- coding: utf-8 -*-

from flaskext.wtf import Form, TextField, TextAreaField, RadioField, FileField, BooleanField
from flaskext.wtf import Required, Email, Length, URL

class PostingForm(Form):
    """Form for new job posts"""
    job_headline = TextField("Headline", validators=[Required(), Length(min=1, max=100)])
    job_category = RadioField("Category", choices=[('python', 'Python Programmer'), ('android', 'Android Programmer')], validators=[Required()])
    job_location = TextField("Location", validators=[Required()])
    job_relocation_assist = BooleanField("Relocation assist")
    job_description = TextAreaField("Description", validators=[Required()])
    job_perks = TextAreaField("Job perks")
    job_how_to_apply = TextAreaField("How to apply", validators=[Required()])
    company_name = TextField("Company name")
    company_logo = FileField("Logo")
    company_url = TextField("URL", validators=[Required(), URL()])
    poster_email = TextField("Email", validators=[Required(), Email()])

class ConfirmForm(Form):
    terms_accepted = BooleanField("Accept terms")
    promocode = TextField("Promo code")
