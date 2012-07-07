from hasjob import app

@app.route('/search')
def search():
    now = datetime.utcnow()
    results = sorted(do_search(request.args.get('q', u''), expand=True),
        key=lambda r: getattr(r, 'datetime', now))
    results.reverse()
    return render_template('search.html', results=results, now=now, newlimit=newlimit)
