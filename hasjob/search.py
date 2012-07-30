import os.path
from flask.ext.sqlalchemy import models_committed
from whoosh import fields, index
from whoosh.qparser import QueryParser
from whoosh.analysis import StemmingAnalyzer

from hasjob import models, app

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


def on_models_committed(sender, changes):
    index_required = False
    for model, change in changes:
        if isinstance(model, (models.JobType, models.JobCategory, models.JobPost)):
            index_required = True
            break
    if index_required:
        ix = index.open_dir(app.config['SEARCH_INDEX_PATH'])
        writer = ix.writer()
        for model, change in changes:
            mapping = model.search_mapping()
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


def delete_from_index(oblist):
    ix = index.open_dir(app.config['SEARCH_INDEX_PATH'])
    writer = ix.writer()
    for item in oblist:
        mapping = item.search_mapping()
        writer.delete_by_term('idref', mapping['idref'])
    writer.commit()


def configure():
    index_path = app.config['SEARCH_INDEX_PATH']
    models_committed.connect(on_models_committed, sender=app)
    if not os.path.exists(index_path):
        os.mkdir(index_path)
        ix = index.create_in(index_path, search_schema)
        writer = ix.writer()
        # Index everything since this is the first time
        for model in [models.JobType, models.JobCategory, models.JobPost]:
            for ob in model.query.all():
                mapping = ob.search_mapping()
                public = mapping.pop('public')
                if public:
                    writer.add_document(**mapping)
        writer.commit()
