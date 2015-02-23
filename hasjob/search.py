# -*- coding: utf-8 -*-

from flask.ext.sqlalchemy import models_committed
from flask.ext.rq import job
from sqlalchemy.exc import ProgrammingError
from hasjob import models, app

from pyelasticsearch import ElasticSearch
es = ElasticSearch('http://localhost:9200/')

INDEXABLE = (models.JobPost,)
ES_INDEX = 'hasjob_dev'


def type_from_idref(idref):
    return idref.split('/')[0]


def id_from_idref(idref):
    return int(idref.split('/')[1])


def do_search(query, expand=False):
    """
    Returns search results
    """
    hits = []

    if query:
        hits = es.search(query, index=ES_INDEX)
        ids = map(lambda hit: id_from_idref(hit[u'_id']), hits['hits']['hits'])
        results = models.JobPost.get_by_ids(ids)
        # TODO Sort by score
        # check category & type and if present prepend this list with jobs with that category/type
        # and do a uniq
        return results


@job("hasjob-search")
def update_index(data):
    for change, mapping in data:
        if not mapping['public'] or change == 'update' or change == 'delete':
            delete_from_index([mapping])
        if change == 'insert' or change == 'update':
            es.bulk([es.update_op(doc=mapping, id=mapping['idref'], upsert=mapping, doc_as_upsert=True)],
                    index=ES_INDEX,
                    doc_type=type_from_idref(mapping['idref']))


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
    es.bulk((es.delete_op(id=mapping['idref'], doc_type=type_from_idref(mapping['idref'])) for mapping in oblist), index=ES_INDEX)


def configure_once():
    for model in INDEXABLE:
        try:
            records = map(lambda record: record.search_mapping(), model.query.all())
            es.bulk((es.index_op(record, id=record['idref']) for record in records),
                    index=ES_INDEX,
                    doc_type=model.idref)
        except ProgrammingError:
            pass


def configure():
    models_committed.connect(on_models_committed, sender=app)
