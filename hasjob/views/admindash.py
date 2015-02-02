# -*- coding: utf-8 -*-

from cStringIO import StringIO
import unicodecsv
from flask import render_template
from ..models import db, EMPLOYER_RESPONSE
from .. import app, lastuser


@app.route('/admin/dashboard/historical')
@lastuser.requires_permission('siteadmin')
def admin_dashboard_historical():
    return render_template('admin_historical.html')


@app.route('/admin/dashboard/historical/userdays_all.csv', defaults={'q': 'a'})
@app.route('/admin/dashboard/historical/userdays_candidates.csv', defaults={'q': 'c'})
@app.route('/admin/dashboard/historical/userdays_responses.csv', defaults={'q': 'r'})
@lastuser.requires_permission('siteadmin')
def admin_dashboard_historical_userdays(q):
    if q == 'a':
        userdays = db.session.query('month', 'users', 'centile').from_statement(
            '''SELECT month, COUNT(user_id) AS users, PERCENTILE_CONT(ARRAY [0.5, 0.6, 0.7, 0.8, 0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.0]) WITHIN GROUP (ORDER BY count) AS centile FROM (SELECT month, COUNT(day) AS count, user_id FROM (SELECT DATE_TRUNC('month', user_active_at.active_at) AS month, DATE_TRUNC('day', user_active_at.active_at) AS day, user_id FROM user_active_at GROUP BY month, day, user_id) AS month_day_user GROUP BY month, user_id ORDER BY month, user_id) AS daycounts WHERE month > '2013-01-01' GROUP BY month ORDER BY month;''')
    elif q == 'c':
        userdays = db.session.query('month', 'users', 'centile').from_statement(
            '''SELECT month, COUNT(user_id) AS users, PERCENTILE_CONT(ARRAY [0.5, 0.6, 0.7, 0.8, 0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.0]) WITHIN GROUP (ORDER BY count) AS centile FROM (SELECT month, COUNT(day) AS count, user_id FROM (SELECT DATE_TRUNC('month', user_active_at.active_at) AS month, DATE_TRUNC('day', user_active_at.active_at) AS day, user_active_at.user_id FROM user_active_at WHERE user_active_at.user_id IN (SELECT DISTINCT(user_id) FROM job_application) GROUP BY month, day, user_id) AS month_day_user GROUP BY month, user_id ORDER BY month, user_id) AS daycounts WHERE month > '2013-01-01' GROUP BY month ORDER BY month;''')
    elif q == 'r':
        userdays = db.session.query('month', 'users', 'centile').from_statement(
            '''SELECT month, COUNT(user_id) AS users, PERCENTILE_CONT(ARRAY [0.5, 0.6, 0.7, 0.8, 0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.0]) WITHIN GROUP (ORDER BY count) AS centile FROM (SELECT month, COUNT(day) AS count, user_id FROM (SELECT DATE_TRUNC('month', user_active_at.active_at) AS month, DATE_TRUNC('day', user_active_at.active_at) AS day, user_active_at.user_id FROM user_active_at WHERE user_active_at.user_id IN (SELECT DISTINCT(user_id) FROM job_application WHERE response=:response) GROUP BY month, day, user_id) AS month_day_user GROUP BY month, user_id ORDER BY month, user_id) AS daycounts WHERE month > '2013-01-01' GROUP BY month ORDER BY month;''').params(
            response=EMPLOYER_RESPONSE.REPLIED)

    outfile = StringIO()
    out = unicodecsv.writer(outfile, 'excel')
    out.writerow(['month', '50%c', '60%c', '70%c', '80%c', '90%c',
        '91%c', '92%c', '93%c', '94%c', '95%c', '96%c', '97%c', '98%c', '99%c', '100%c', 'users'])

    for month, users, centile in userdays:
        out.writerow([month.strftime('%Y-%m')] + [round(c, 2) for c in centile] + [users])

    return outfile.getvalue(), 200, {'Content-Type': 'text/plain'}
