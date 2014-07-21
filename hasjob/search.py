# -*- coding: utf-8 -*-

import os.path
from flask.ext.sqlalchemy import models_committed
from flask.ext.rq import job
import time
from sqlalchemy.exc import ProgrammingError
from whoosh import fields, index
from whoosh.index import LockError
from whoosh.qparser import QueryParser
from whoosh.analysis import StemmingAnalyzer

from hasjob import models, app


INDEXABLE = (models.JobType, models.JobCategory, models.JobPost)
search_schema = fields.Schema(title=fields.TEXT(stored=True),
                              content=fields.TEXT(analyzer=StemmingAnalyzer()),
                              idref=fields.ID(stored=True, unique=True))


# For search results
def ob_from_idref(idref):
    ref, objid = idref.split('/')
    if ref == 'post':
        return models.JobPost.query.get(int(objid))
    elif ref == 'type':
        return models.JobType.query.get(int(objid))
    elif ref == 'category':
        return models.JobCategory.query.get(int(objid))


def do_search(query, expand=False):
    """
    Returns search results
    """
    ix = index.open_dir(app.config['SEARCH_INDEX_PATH'])
    hits = []

    if query:
        parser = QueryParser("content", schema=ix.schema)
        try:
            qry = parser.parse(query)
        except:
            # query couldn't be parsed
            qry = None
        if qry is not None:
            searcher = ix.searcher()
            hits = searcher.search(qry, limit=1000)

    if expand:
        return (ob_from_idref(hit['idref']) for hit in hits)
    else:
        return hits


@job("hasjob-search")
def update_index(data):
    ix = index.open_dir(app.config['SEARCH_INDEX_PATH'])
    try:
        writer = ix.writer()
    except LockError:
        time.sleep(1)
        try:
            writer = ix.writer()
        except LockError:
            time.sleep(5)
            writer = ix.writer()
    for change, mapping in data:
        public = mapping.pop('public')
        if public:
            if change == 'insert':
                writer.add_document(**mapping)
            elif change == 'update':
                writer.update_document(**mapping)
            elif change == 'delete':
                writer.delete_by_term('idref', mapping['idref'])
        else:
            writer.delete_by_term('idref', mapping['idref'])
    writer.commit()


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
    ix = index.open_dir(app.config['SEARCH_INDEX_PATH'])
    writer = ix.writer()
    for item in oblist:
        mapping = item.search_mapping()
        writer.delete_by_term('idref', mapping['idref'])
    writer.commit()


def configure_once():
    index_path = app.config['SEARCH_INDEX_PATH']
    if not os.path.exists(index_path):
        os.mkdir(index_path)
        ix = index.create_in(index_path, search_schema)
        writer = ix.writer()
        # Index everything since this is the first time
        for model in [models.JobType, models.JobCategory, models.JobPost]:
            try:
                for ob in model.query.all():
                    mapping = ob.search_mapping()
                    public = mapping.pop('public')
                    if public:
                        writer.add_document(**mapping)
            except ProgrammingError:
                pass  # The table doesn't exist yet. This is really a new installation.
        writer.commit()

def configure():
    models_committed.connect(on_models_committed, sender=app)
