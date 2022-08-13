from flask import render_template

from .. import app


@app.errorhandler(403)
def error_403(_exc):
    return render_template('errors/403.html.jinja2'), 403


@app.errorhandler(404)
def error_404(_exc):
    return render_template('errors/404.html.jinja2'), 404


@app.errorhandler(410)
def error_410(_exc):
    return render_template('errors/410.html.jinja2'), 410


@app.errorhandler(500)
def error_500(_exc):
    return render_template('errors/500.html.jinja2'), 500
