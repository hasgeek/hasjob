import csv
from collections import defaultdict
from io import StringIO

from flask import g, render_template

from baseframe import __
from coaster.views import route, viewdata

from .. import app, lastuser
from ..models import EMPLOYER_RESPONSE, POST_STATE, db, sa
from .admin import AdminView


@route('/admin/dashboard')
class AdminDashboard(AdminView):
    __decorators__ = [lastuser.requires_permission('siteadmin')]

    @route('')
    @viewdata(tab=True, index=0, title=__("Dashboard"))
    def dashboard(self):
        return render_template('admin_dashboard.html.jinja2')

    @route('historical')
    @viewdata(tab=True, index=1, title=__("Historical"))
    def historical(self):
        return render_template('admin_historical.html.jinja2')

    @route('daystats.csv', defaults={'period': 'day'})
    @route('weekstats.csv', defaults={'period': 'week'})
    def daystats(self, period):
        if period == 'day':
            trunc = 'hour'
            interval = '2 days'
        else:
            trunc = 'day'
            interval = '2 weeks'

        stats = defaultdict(dict)

        statsq = (
            db.session.query(sa.text('slot'), sa.text('count'))
            .from_statement(
                sa.text(
                    '''SELECT DATE_TRUNC(:trunc, user_active_at.active_at AT TIME ZONE :timezone) AS slot, COUNT(DISTINCT(user_active_at.user_id)) AS count FROM user_active_at WHERE user_active_at.active_at AT TIME ZONE :timezone > DATE_TRUNC(:trunc, NOW() AT TIME ZONE :timezone - INTERVAL :interval) GROUP BY slot ORDER BY slot'''
                )
            )
            .params(trunc=trunc, interval=interval, timezone=g.user.timezone)
        )
        for slot, count in statsq:
            stats[slot]['users'] = count

        statsq = (
            db.session.query(sa.text('slot'), sa.text('count'))
            .from_statement(
                sa.text(
                    '''SELECT DATE_TRUNC(:trunc, "user".created_at AT TIME ZONE :timezone) AS slot, COUNT(*) AS count FROM "user" WHERE "user".created_at AT TIME ZONE :timezone > DATE_TRUNC(:trunc, NOW() AT TIME ZONE :timezone - INTERVAL :interval) GROUP BY slot ORDER BY slot'''
                )
            )
            .params(trunc=trunc, interval=interval, timezone=g.user.timezone)
        )
        for slot, count in statsq:
            stats[slot]['newusers'] = count

        statsq = (
            db.session.query(sa.text('slot'), sa.text('count'))
            .from_statement(
                sa.text(
                    '''SELECT DATE_TRUNC(:trunc, jobpost.datetime AT TIME ZONE :timezone) AS slot, COUNT(*) AS count FROM jobpost WHERE jobpost.status IN :listed AND jobpost.datetime AT TIME ZONE :timezone > DATE_TRUNC(:trunc, NOW() AT TIME ZONE :timezone - INTERVAL :interval) GROUP BY slot ORDER BY slot'''
                )
            )
            .params(
                trunc=trunc,
                interval=interval,
                timezone=g.user.timezone,
                listed=tuple(POST_STATE.PUBLIC),
            )
        )
        for slot, count in statsq:
            stats[slot]['jobs'] = count

        statsq = (
            db.session.query(sa.text('slot'), sa.text('count'))
            .from_statement(
                sa.text(
                    '''SELECT DATE_TRUNC(:trunc, event_session.created_at AT TIME ZONE :timezone) AS slot, COUNT(DISTINCT(anon_user_id)) AS count FROM event_session WHERE event_session.anon_user_id IS NOT NULL AND event_session.created_at AT TIME ZONE :timezone > DATE_TRUNC(:trunc, NOW() AT TIME ZONE :timezone - INTERVAL :interval) GROUP BY slot ORDER BY slot'''
                )
            )
            .params(trunc=trunc, interval=interval, timezone=g.user.timezone)
        )
        for slot, count in statsq:
            stats[slot]['anon_users'] = count

        statsq = (
            db.session.query(sa.text('slot'), sa.text('count'))
            .from_statement(
                sa.text(
                    '''SELECT DATE_TRUNC(:trunc, job_application.created_at AT TIME ZONE :timezone) AS slot, COUNT(*) AS count FROM job_application WHERE job_application.created_at AT TIME ZONE :timezone > DATE_TRUNC(:trunc, NOW() AT TIME ZONE :timezone - INTERVAL :interval) GROUP BY slot ORDER BY slot'''
                )
            )
            .params(trunc=trunc, interval=interval, timezone=g.user.timezone)
        )
        for slot, count in statsq:
            stats[slot]['applications'] = count

        statsq = (
            db.session.query(sa.text('slot'), sa.text('count'))
            .from_statement(
                sa.text(
                    '''SELECT DATE_TRUNC(:trunc, job_application.replied_at AT TIME ZONE :timezone) AS slot, COUNT(*) AS count FROM job_application WHERE job_application.response = :response AND job_application.replied_at AT TIME ZONE :timezone > DATE_TRUNC(:trunc, NOW() AT TIME ZONE :timezone - INTERVAL :interval) GROUP BY slot ORDER BY slot'''
                )
            )
            .params(
                trunc=trunc,
                interval=interval,
                timezone=g.user.timezone,
                response=EMPLOYER_RESPONSE.REPLIED,
            )
        )
        for slot, count in statsq:
            stats[slot]['replies'] = count

        statsq = (
            db.session.query(sa.text('slot'), sa.text('count'))
            .from_statement(
                sa.text(
                    '''SELECT DATE_TRUNC(:trunc, job_application.replied_at AT TIME ZONE :timezone) AS slot, COUNT(*) AS count FROM job_application WHERE job_application.response = :response AND job_application.replied_at AT TIME ZONE :timezone > DATE_TRUNC(:trunc, NOW() AT TIME ZONE :timezone - INTERVAL :interval) GROUP BY slot ORDER BY slot'''
                )
            )
            .params(
                trunc=trunc,
                interval=interval,
                timezone=g.user.timezone,
                response=EMPLOYER_RESPONSE.REJECTED,
            )
        )
        for slot, count in statsq:
            stats[slot]['rejections'] = count

        outfile = StringIO()
        out = csv.writer(outfile, 'excel')
        out.writerow(
            [
                'slot',
                'newusers',
                'users',
                'anon_users',
                'jobs',
                'applications',
                'replies',
                'rejections',
            ]
        )

        for slot, c in sorted(stats.items()):
            out.writerow(
                [
                    slot.isoformat(),
                    c.get('newusers', 0),
                    c.get('users', 0),
                    c.get('anon_users', 0),
                    c.get('jobs', 0),
                    c.get('applications', 0),
                    c.get('replies', 0),
                    c.get('rejections', 0),
                ]
            )

        return outfile.getvalue(), 200, {'Content-Type': 'text/plain'}

    @route('historical/userdays_all.csv', defaults={'q': 'a'})
    @route('historical/userdays_candidates.csv', defaults={'q': 'c'})
    @route('historical/userdays_responses.csv', defaults={'q': 'r'})
    def historical_userdays(self, q):
        if q == 'a':
            userdays = db.session.query(
                sa.text('month'), sa.text('users'), sa.text('centile')
            ).from_statement(
                sa.text(
                    '''SELECT month, COUNT(user_id) AS users, PERCENTILE_CONT(ARRAY [0.5, 0.6, 0.7, 0.8, 0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.0]) WITHIN GROUP (ORDER BY count) AS centile FROM (SELECT month, COUNT(day) AS count, user_id FROM (SELECT DATE_TRUNC('month', user_active_at.active_at) AS month, DATE_TRUNC('day', user_active_at.active_at) AS day, user_id FROM user_active_at GROUP BY month, day, user_id) AS month_day_user GROUP BY month, user_id ORDER BY month, user_id) AS daycounts WHERE month > '2013-01-01' GROUP BY month ORDER BY month;'''
                )
            )
        elif q == 'c':
            userdays = db.session.query(
                sa.text('month'), sa.text('users'), sa.text('centile')
            ).from_statement(
                sa.text(
                    '''SELECT month, COUNT(user_id) AS users, PERCENTILE_CONT(ARRAY [0.5, 0.6, 0.7, 0.8, 0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.0]) WITHIN GROUP (ORDER BY count) AS centile FROM (SELECT month, COUNT(day) AS count, user_id FROM (SELECT DATE_TRUNC('month', user_active_at.active_at) AS month, DATE_TRUNC('day', user_active_at.active_at) AS day, user_active_at.user_id FROM user_active_at, job_application WHERE user_active_at.user_id = job_application.user_id AND DATE_TRUNC('month', user_active_at.active_at) = DATE_TRUNC('month', job_application.created_at) GROUP BY month, day, user_active_at.user_id) AS month_day_user GROUP BY month, user_id ORDER BY month, user_id) AS daycounts WHERE month > '2013-01-01' GROUP BY month ORDER BY month;'''
                )
            )
        elif q == 'r':
            userdays = (
                db.session.query(sa.text('month'), sa.text('users'), sa.text('centile'))
                .from_statement(
                    sa.text(
                        '''SELECT month, COUNT(user_id) AS users, PERCENTILE_CONT(ARRAY [0.5, 0.6, 0.7, 0.8, 0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.0]) WITHIN GROUP (ORDER BY count) AS centile FROM (SELECT month, COUNT(day) AS count, user_id FROM (SELECT DATE_TRUNC('month', user_active_at.active_at) AS month, DATE_TRUNC('day', user_active_at.active_at) AS day, user_active_at.user_id FROM user_active_at, job_application WHERE user_active_at.user_id = job_application.user_id AND job_application.response = :response AND DATE_TRUNC('month', user_active_at.active_at) = DATE_TRUNC('month', job_application.replied_at) GROUP BY month, day, user_active_at.user_id) AS month_day_user GROUP BY month, user_id ORDER BY month, user_id) AS daycounts WHERE month > '2013-01-01' GROUP BY month ORDER BY month;'''
                    )
                )
                .params(response=EMPLOYER_RESPONSE.REPLIED)
            )

        outfile = StringIO()
        out = csv.writer(outfile, 'excel')
        out.writerow(
            [
                'month',
                '50%',
                '60%',
                '70%',
                '80%',
                '90%',
                '91%',
                '92%',
                '93%',
                '94%',
                '95%',
                '96%',
                '97%',
                '98%',
                '99%',
                '100%',
                'users',
            ]
        )

        for month, users, centile in userdays:
            out.writerow(
                [month.strftime('%Y-%m')] + [round(c, 2) for c in centile] + [users]
            )

        return outfile.getvalue(), 200, {'Content-Type': 'text/plain'}


AdminDashboard.init_app(app)
