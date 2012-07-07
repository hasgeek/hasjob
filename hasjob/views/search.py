from datetime import datetime
from flask import render_template, request
from hasjob import app
from hasjob.models import newlimit
from hasjob.search import do_search

@app.route('/search')
def search():
    now = datetime.utcnow()
    results = sorted(do_search(request.args.get('q', u''), expand=True),
        key=lambda r: getattr(r, 'datetime', now))
    results.reverse()
    return render_template('search.html', results=results, now=now, newlimit=newlimit)
