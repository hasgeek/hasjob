# -*- coding: utf-8 -*-

from collections import defaultdict
from cStringIO import StringIO
import unicodecsv
from flask import g, render_template
from ..models import db, EMPLOYER_RESPONSE, POSTSTATUS, EMPLOYER_RESPONSE
from .. import app, lastuser


@app.route('/admin/dashboard')
@lastuser.requires_permission('siteadmin')
def admin_dashboard():
    return render_template('admin_dashboard.html')


@app.route('/admin/dashboard/historical')
@lastuser.requires_permission('siteadmin')
def admin_dashboard_historical():
    return render_template('admin_historical.html')


@app.route('/admin/dashboard/daystats.csv')
@lastuser.requires_permission('siteadmin')
def admin_dashboard_daystats():
    daystats = defaultdict(dict)

    stats = db.session.query('hour', 'count').from_statement(
        '''SELECT DATE_TRUNC('hour', user_active_at.active_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(DISTINCT(user_active_at.user_id)) AS count FROM user_active_at WHERE user_active_at.active_at > DATE_TRUNC('hour', NOW() AT TIME ZONE 'UTC' - INTERVAL '4 days') GROUP BY hour'''
        ).params(timezone=g.user.timezone)
    for hour, count in stats:
        daystats[hour]['users'] = count

    stats = db.session.query('hour', 'count').from_statement(
        '''SELECT DATE_TRUNC('hour', "user".created_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM "user" WHERE "user".created_at > DATE_TRUNC('hour', NOW() AT TIME ZONE 'UTC' - INTERVAL '4 days') GROUP BY hour'''
        ).params(timezone=g.user.timezone)
    for hour, count in stats:
        daystats[hour]['newusers'] = count

    stats = db.session.query('hour', 'count').from_statement(
        '''SELECT DATE_TRUNC('hour', jobpost.datetime AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM jobpost WHERE jobpost.status IN :listed AND jobpost.datetime > DATE_TRUNC('hour', NOW() AT TIME ZONE 'UTC' - INTERVAL '4 days') GROUP BY hour'''
        ).params(timezone=g.user.timezone, listed=POSTSTATUS.LISTED)
    for hour, count in stats:
        daystats[hour]['jobs'] = count

    stats = db.session.query('hour', 'count').from_statement(
        '''SELECT DATE_TRUNC('hour', event_session.created_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM event_session WHERE event_session.user_id IS NOT NULL AND event_session.created_at > DATE_TRUNC('hour', NOW() AT TIME ZONE 'UTC' - INTERVAL '4 days') GROUP BY hour'''
        ).params(timezone=g.user.timezone)
    for hour, count in stats:
        daystats[hour]['usessions'] = count

    stats = db.session.query('hour', 'count').from_statement(
        '''SELECT DATE_TRUNC('hour', event_session.created_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM event_session WHERE event_session.anon_user_id IS NOT NULL AND event_session.created_at > DATE_TRUNC('hour', NOW() AT TIME ZONE 'UTC' - INTERVAL '4 days') GROUP BY hour'''
        ).params(timezone=g.user.timezone)
    for hour, count in stats:
        daystats[hour]['asessions'] = count

    stats = db.session.query('hour', 'count').from_statement(
        '''SELECT DATE_TRUNC('hour', job_application.created_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM job_application WHERE job_application.created_at > DATE_TRUNC('hour', NOW() AT TIME ZONE 'UTC' - INTERVAL '4 days') GROUP BY hour'''
        ).params(timezone=g.user.timezone)
    for hour, count in stats:
        daystats[hour]['applications'] = count

    stats = db.session.query('hour', 'count').from_statement(
        '''SELECT DATE_TRUNC('hour', job_application.replied_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM job_application WHERE job_application.response = :response AND job_application.replied_at > DATE_TRUNC('hour', NOW() AT TIME ZONE 'UTC' - INTERVAL '4 days') GROUP BY hour'''
        ).params(timezone=g.user.timezone, response=EMPLOYER_RESPONSE.REPLIED)
    for hour, count in stats:
        daystats[hour]['replies'] = count

    stats = db.session.query('hour', 'count').from_statement(
        '''SELECT DATE_TRUNC('hour', job_application.replied_at AT TIME ZONE 'UTC' AT TIME ZONE :timezone) AS hour, COUNT(*) AS count FROM job_application WHERE job_application.response = :response AND job_application.replied_at > DATE_TRUNC('hour', NOW() AT TIME ZONE 'UTC' - INTERVAL '4 days') GROUP BY hour'''
        ).params(timezone=g.user.timezone, response=EMPLOYER_RESPONSE.REJECTED)
    for hour, count in stats:
        daystats[hour]['rejections'] = count

    outfile = StringIO()
    out = unicodecsv.writer(outfile, 'excel')
    out.writerow(['hour', 'users', 'newusers', 'asessions', 'usessions', 'jobs', 'applications', 'replies', 'rejections'])

    for hour, c in daystats.items():
        out.writerow([hour.isoformat(),
            c.get('users', 0),
            c.get('newusers', 0),
            c.get('asessions', 0),
            c.get('usessions', 0),
            c.get('jobs', 0),
            c.get('applications', 0),
            c.get('replies', 0),
            c.get('rejections', 0),
            ])

    return outfile.getvalue(), 200, {'Content-Type': 'text/plain'}


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
            '''SELECT month, COUNT(user_id) AS users, PERCENTILE_CONT(ARRAY [0.5, 0.6, 0.7, 0.8, 0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.0]) WITHIN GROUP (ORDER BY count) AS centile FROM (SELECT month, COUNT(day) AS count, user_id FROM (SELECT DATE_TRUNC('month', user_active_at.active_at) AS month, DATE_TRUNC('day', user_active_at.active_at) AS day, user_active_at.user_id FROM user_active_at, job_application WHERE user_active_at.user_id = job_application.user_id AND DATE_TRUNC('month', user_active_at.active_at) = DATE_TRUNC('month', job_application.created_at) GROUP BY month, day, user_active_at.user_id) AS month_day_user GROUP BY month, user_id ORDER BY month, user_id) AS daycounts WHERE month > '2013-01-01' GROUP BY month ORDER BY month;''')
    elif q == 'r':
        userdays = db.session.query('month', 'users', 'centile').from_statement(
            '''SELECT month, COUNT(user_id) AS users, PERCENTILE_CONT(ARRAY [0.5, 0.6, 0.7, 0.8, 0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.0]) WITHIN GROUP (ORDER BY count) AS centile FROM (SELECT month, COUNT(day) AS count, user_id FROM (SELECT DATE_TRUNC('month', user_active_at.active_at) AS month, DATE_TRUNC('day', user_active_at.active_at) AS day, user_active_at.user_id FROM user_active_at, job_application WHERE user_active_at.user_id = job_application.user_id AND job_application.response = :response AND DATE_TRUNC('month', user_active_at.active_at) = DATE_TRUNC('month', job_application.replied_at) GROUP BY month, day, user_active_at.user_id) AS month_day_user GROUP BY month, user_id ORDER BY month, user_id) AS daycounts WHERE month > '2013-01-01' GROUP BY month ORDER BY month;''').params(
            response=EMPLOYER_RESPONSE.REPLIED)

    outfile = StringIO()
    out = unicodecsv.writer(outfile, 'excel')
    out.writerow(['month', '50%', '60%', '70%', '80%', '90%',
        '91%', '92%', '93%', '94%', '95%', '96%', '97%', '98%', '99%', '100%', 'users'])

    for month, users, centile in userdays:
        out.writerow([month.strftime('%Y-%m')] + [round(c, 2) for c in centile] + [users])

    return outfile.getvalue(), 200, {'Content-Type': 'text/plain'}
