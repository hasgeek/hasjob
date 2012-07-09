from collections import defaultdict
from datetime import datetime, timedelta, date

from flask import jsonify, render_template

from hasjob import app
from hasjob.models import agelimit, JobType
from hasjob.views.helper import getposts

@app.route('/stats')
def stats():
    return render_template('stats.html')

@app.route('/stats/listings_by_date.json')
def stats_listings_by_date():
    now = datetime.utcnow()
    jobs = getposts()
    # Why is this code so complicated? How hard is it to get a count by date?
    # Just because we store datetime instead of date?
    listings_by_date = {}
    looper = now - agelimit
    for x in range(agelimit.days):
        listings_by_date[date(year=looper.year, month=looper.month, day=looper.day)] = 0
        looper += timedelta(days=1)
    for job in jobs:
        listings_by_date[date(year=job.datetime.year, month=job.datetime.month, day=job.datetime.day)] += 1
    listings_by_date = listings_by_date.items() # Convert from dict to list
    listings_by_date.sort()                     # and sort by date
    return jsonify(data=[[(x, listings_by_date[x][1]) for x in range(len(listings_by_date))]],
                   options={
                            'series': {'bars': {'show': True}},
                            'xaxis': {'show': True, 'min': 0, 'max': len(listings_by_date),
                                      'ticks': [(x, listings_by_date[x][0].strftime('%b %d')) for x in range(len(listings_by_date))]
                                     },
                            'yaxis': {'min': 0, 'tickSize': 1, 'tickDecimals': 0},
                            }
                   )


@app.route('/stats/listings_by_type.json')
def stats_listings_by_type():
    jobs = getposts()
    typecount = defaultdict(int)
    for job in jobs:
        typecount[job.type_id] += 1
    all_types = list(JobType.query.filter_by(public=True).order_by(JobType.seq).all())
    all_types.reverse() # Charts are drawn bottom to top
    data = []
    labels = []
    for x in range(len(all_types)):
        data.append([x, typecount[all_types[x].id]])
        labels.append([x, all_types[x].title])
    return jsonify(data=[{'data': data}],
                   options={
                            'series': {'bars': {'show': True, 'horizontal': True}},
                            'yaxis': {'show': True, 'min': 0, 'max': len(all_types), 'ticks': labels},
                            'xaxis': {'min': 0, 'tickSize': 1, 'tickDecimals': 0},
                            }
                   )
