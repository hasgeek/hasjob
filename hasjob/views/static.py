from flask import redirect, render_template, Response, url_for
from hasjob import app


@app.route('/tos')
def terms_of_service():
    return render_template('tos.html')


@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='img/favicon.ico'))


@app.route('/robots.txt')
def robots():
    return Response("Disallow: /edit/*\n"
                    "Disallow: /confirm/*\n"
                    "Disallow: /withdraw/*\n"
                    "Disallow: /admin/*\n"
                    "",
                    content_type = 'text/plain; charset=utf-8')
