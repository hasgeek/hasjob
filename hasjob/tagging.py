# -*- coding: utf-8 -*-

from collections import defaultdict
from urlparse import urljoin
import requests
from flask.ext.rq import job
from . import app
from .models import db, JobPost, JobLocation


@job('hasjob')
def tag_locations(jobpost_id):
    if app.config.get('HASCORE_SERVER'):
        post = JobPost.query.get(jobpost_id)
        url = urljoin(app.config['HASCORE_SERVER'], '/1/geo/parse_locations')
        response = requests.get(url, params={'q': post.location, 'lang': 'en', 'bias': ['IN', 'US'], 'special': ['Anywhere', 'Remote', 'Home']}).json()
        if response.get('status') == 'ok':
            results = response.get('result', [])
            geonames = defaultdict(dict)
            tokens = []
            for item in results:
                if item.get('special'):
                    post.remote_location = True
                geoname = item.get('geoname', {})
                if geoname:
                    geonames[geoname['geonameid']]['geonameid'] = geoname['geonameid']
                    geonames[geoname['geonameid']]['primary'] = geonames[geoname['geonameid']].get('primary', True)
                    for type, related in geoname.get('related', {}).items():
                        if type in ['admin2', 'admin1', 'country', 'continent']:
                            geonames[related['geonameid']]['geonameid'] = related['geonameid']
                            geonames[related['geonameid']]['primary'] = False

                    tokens.append({'token': item.get('token', ''), 'geoname': {
                        'name': geoname['name'],
                        'geonameid': geoname['geonameid'],
                        }})
                else:
                    tokens.append({'token': item.get('token', '')})

                if item.get('special'):
                    tokens[-1]['remote'] = True

            post.parsed_location = {'tokens': tokens}

            for locdata in geonames.values():
                loc = JobLocation.query.get((jobpost_id, locdata['geonameid']))
                if loc is None:
                    loc = JobLocation(jobpost=post, geonameid=locdata['geonameid'])
                    db.session.add(loc)
                    db.session.flush()
                loc.primary = locdata['primary']
            for location in post.locations:
                if location.geonameid not in geonames:
                    db.session.delete(location)
            db.session.commit()
