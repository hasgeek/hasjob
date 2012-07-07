from hasjob import app

@app.route('/tos')
def terms_of_service():
    return render_template('tos.html')


@app.route('/stats')
def stats():
    return render_template('stats.html')
