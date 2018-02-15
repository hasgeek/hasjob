# -*- coding: utf-8 -*-

from collections import defaultdict
from urlparse import urljoin
import requests
from flask_rq import job
from coaster.utils import text_blocks
from coaster.nlp import extract_named_entities
from . import app
from .models import (db, JobPost, JobLocation, Board, BoardAutoDomain, BoardAutoLocation, board_auto_tag_table,
    board_auto_jobtype_table, board_auto_jobcategory_table, Tag, JobPostTag, TAG_TYPE)


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
        post = JobPost.query.options(db.joinedload('locations'), db.joinedload('taglinks')).get(jobpost_id)
        # Find all boards that match and that don't have an all-match criteria
        query = Board.query.join(BoardAutoDomain).filter(BoardAutoDomain.domain == post.email_domain)
        query = query.union(Board.query.join(board_auto_jobtype_table).filter(
            board_auto_jobtype_table.c.jobtype_id == post.type_id))
        query = query.union(Board.query.join(board_auto_jobcategory_table).filter(
            board_auto_jobcategory_table.c.jobcategory_id == post.category_id))
        if post.geonameids:
            query = query.union(Board.query.join(BoardAutoLocation).filter(
                BoardAutoLocation.geonameid.in_(post.geonameids)))
        if post.taglinks:
            query = query.union(Board.query.join(board_auto_tag_table).filter(
                board_auto_tag_table.c.tag_id.in_(
                    [tl.tag_id for tl in post.taglinks if tl.status in TAG_TYPE.TAG_PRESENT])))
        for board in query:
            # Some criteria match. Does this board require all to match?
            if not board.auto_all:
                # No? Add it
                board.add(post)
            else:
                # Yes? Check all the filters again
                if board.auto_domains and post.email_domain not in board.auto_domains:
                    # This board requires specific domains and none match. Skip.
                    continue
                if board.auto_locations:
                    if not set(board.auto_geonameids).intersection(set(post.geonameids)):
                        # This board requires specific locations and none match. Skip.
                        continue
                if board.auto_tags:
                    if not set(board.auto_keywords).intersection(
                            {tl.tag for tl in post.taglinks if tl.status in TAG_TYPE.TAG_PRESENT}):
                        # This board requires specific keywords and none match. Skip.
                        continue
                if board.auto_types and post.type not in board.auto_types:
                    # This board requires specific job types and none match. Skip.
                    continue
                if board.auto_categories and post.category not in board.auto_categories:
                    # This board requires specific job categories and none match. Skip.
                    continue
                # No reason to exclude? Add it to the board
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
