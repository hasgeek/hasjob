from flask import render_template

from .. import app


@app.errorhandler(403)
def error_403(e):
    return render_template('403.html.jinja2'), 403


@app.errorhandler(404)
def error_404(e):
    return render_template('404.html.jinja2'), 404


@app.errorhandler(410)
def error_410(e):
    return render_template('410.html.jinja2'), 410


@app.errorhandler(500)
def error_500(e):
    return render_template('500.html.jinja2'), 500
