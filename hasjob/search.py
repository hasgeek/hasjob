# -*- coding: utf-8 -*-

from flask.ext.sqlalchemy import models_committed
from flask.ext.rq import job
from hasjob import models, app

INDEXABLE = (models.JobPost,)


def type_from_idref(idref):
    return idref.split('/')[0]


def id_from_idref(idref):
    return int(idref.split('/')[1])


def do_search(query, expand=False):
    """
    Returns search results
    """
    if query:
        hits = app.elastic_search.search(query, index=app.config.get('ES_INDEX'))
        ids = map(lambda hit: id_from_idref(hit[u'_id']), hits['hits']['hits'])
        job_post_ids = map(lambda post: post.id, models.JobPost.get_by_ids(ids))
        # Handles the event of the index returning an id that isn't present in the DB
        return [models.JobPost.query.get(id) for id in filter(lambda id: id in job_post_ids, ids)]


@job("hasjob-search")
def update_index(data):
    for change, mapping in data:
        if not mapping['public'] or change == 'update' or change == 'delete':
            delete_from_index([mapping])
        if change == 'insert' or change == 'update':
            app.elastic_search.bulk([app.elastic_search.update_op(doc=mapping, id=mapping['idref'], upsert=mapping, doc_as_upsert=True)], index=app.config.get('ES_INDEX'), doc_type=type_from_idref(mapping['idref']))


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
    app.elastic_search.bulk([app.elastic_search.delete_op(id=mapping['idref'],
     doc_type=type_from_idref(mapping['idref'])) for mapping in oblist], index=app.config.get('ES_INDEX'))


def configure_once():
    for model in INDEXABLE:
        records = map(lambda record: record.search_mapping(), model.query.all())
        app.elastic_search.bulk([app.elastic_search.index_op(record, id=record['idref']) for record in records],
                index=app.config.get('ES_INDEX'),
                doc_type=model.idref)


def configure():
    models_committed.connect(on_models_committed, sender=app)
