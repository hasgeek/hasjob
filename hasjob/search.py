# -*- coding: utf-8 -*-

from flask.ext.sqlalchemy import models_committed
from flask.ext.rq import job
from sqlalchemy.exc import ProgrammingError
from hasjob import models, app

from pyelasticsearch import ElasticSearch
es = ElasticSearch('http://localhost:9200/')

INDEXABLE = (models.JobType, models.JobCategory, models.JobPost)


def id_from_idref(idref):
    return int(idref.split('/')[1])


def do_search(query, expand=False):
    """
    Returns search results
    """
    hits = []

    if query:
        hits = es.search(query, index='hasjob')
        ids = map(lambda hit: id_from_idref(hit[u'_id']), hits['hits']['hits'])
        results = models.JobPost.get_by_ids(ids)
        # TODO Sort by score
        # check category & type and if present prepend this list with jobs with that category/type
        # and do a uniq
        return results


@job("hasjob-search")
def update_index(data):
    # TODO
    pass


def on_models_committed(sender, changes):
    data = []
    for model, change in changes:
        if isinstance(model, INDEXABLE):
            data.append([change, model.search_mapping()])
    if data:
        try:
            update_index.delay(data)
        except RuntimeError:
            with app.test_request_context():
                update_index.delay(data)


@job("hasjob-search")
def delete_from_index(oblist):
    # TODO
    pass


def configure_once():
    for model in [models.JobType, models.JobCategory, models.JobPost]:
        try:
            records = map(lambda x: x.search_mapping(), model.query.all())
            es.bulk((es.index_op(record, id=record['idref']) for record in records),
                    index='hasjob',
                    doc_type=model.__name__)
        except ProgrammingError:
            pass


def configure():
    models_committed.connect(on_models_committed, sender=app)
