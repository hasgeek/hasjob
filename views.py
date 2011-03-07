# -*- coding: utf-8 -*-

from flask import render_template, redirect, url_for, request

from app import app
import forms

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/detail/<id>')
def jobdetail(id):
    return "Coming soon"


@app.route('/detail/')
def detailroot():
    return redirect(url_for(index))


@app.route('/new', methods=['GET', 'POST'])
def newjob():
    form = forms.PostingForm(request.form)
    if request.method == 'POST' and form.validate():
        return "Coming soon"
    return render_template('postjob.html', form=form)


@app.route('/search')
def search():
    return "Coming soon"
