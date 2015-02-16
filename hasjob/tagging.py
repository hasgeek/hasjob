# -*- coding: utf-8 -*-

from collections import defaultdict
from urlparse import urljoin
import requests
from flask.ext.rq import job
from coaster.utils import text_blocks
from coaster.nlp import extract_named_entities
from . import app
from .models import (db, JobPost, JobLocation, Board, BoardDomain, BoardLocation,
    Tag, JobPostTag, TAG_TYPE)


@job('hasjob')
def tag_locations(jobpost_id):
    if app.config.get('HASCORE_SERVER'):
        with app.test_request_context():
            post = JobPost.query.get(jobpost_id)
            url = urljoin(app.config['HASCORE_SERVER'], '/1/geo/parse_locations')
            response = requests.get(url, params={'q': post.location, 'bias': ['IN', 'US'], 'special': ['Anywhere', 'Remote', 'Home']}).json()
            if response.get('status') == 'ok':
                remote_location = False
                results = response.get('result', [])
                geonames = defaultdict(dict)
                tokens = []
                for item in results:
                    if item.get('special'):
                        remote_location = True
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

                post.remote_location = remote_location
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


@job('hasjob')
def add_to_boards(jobpost_id):
    with app.test_request_context():
        post = JobPost.query.get(jobpost_id)
        for board in Board.query.join(BoardDomain).join(BoardLocation).filter(db.or_(
                BoardDomain.domain == post.email_domain,
                BoardLocation.geonameid.in_([l.geonameid for l in post.locations])
                )):
            board.add(post)
        db.session.commit()


def tag_named_entities(post):
        entities = extract_named_entities(text_blocks(post.tag_content()))
        links = set()
        for entity in entities:
            tag = Tag.get(entity, create=True)
            link = JobPostTag.get(post, tag)
            if not link:
                link = JobPostTag(jobpost=post, tag=tag, status=TAG_TYPE.AUTO)
                post.taglinks.append(link)
            links.add(link)
        for link in post.taglinks:
            if link.status == TAG_TYPE.AUTO and link not in links:
                link.status = TAG_TYPE.REMOVED


@job('hasjob')
def tag_jobpost(jobpost_id):
    with app.test_request_context():
        post = JobPost.query.get(jobpost_id)
        tag_named_entities(post)
        db.session.commit()
