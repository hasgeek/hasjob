from flask import render_template
from hasjob import app


@app.route('/tos', subdomain='<subdomain>')
@app.route('/tos')
def terms_of_service():
    return render_template('tos.html.jinja2')
