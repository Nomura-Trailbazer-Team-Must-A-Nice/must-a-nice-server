import datetime
from enum import Enum

from mongoengine import Document, DateTimeField, QuerySet
from mongoengine.base import BaseDocument as MongoEngineBaseDocument

FIELDS_TO_IGNORE_FOR_CHANGELOG = {'changelog'}


class BaseModifiedQuerySet(QuerySet):
    def insert(self, doc_or_docs, load_bulk=True, write_concern=None, signal_kwargs=None, validate=True):
        if not isinstance(doc_or_docs, list):
            doc_or_docs = [doc_or_docs]
        if validate:
            _ = [doc.validate() for doc in doc_or_docs]
        for document in doc_or_docs:
            document.created_at = datetime.datetime.utcnow()
            document.updated_at = datetime.datetime.utcnow()
        return super().insert(doc_or_docs, load_bulk, write_concern, signal_kwargs)

    def update(
            self,
            upsert=False,
            multi=True,
            write_concern=None,
            read_concern=None,
            full_result=False,
            validate=True,
            **update
    ):
        if validate:
            def get_updated_document(document):
                for key, value in update.items():
                    if '__' in key:  # ignore special keys, e.g. `set_on_insert__`, `__raw__`
                        continue
                    setattr(document, key, value)
                return document

            new_documents = [get_updated_document(doc) for doc in self]
            _ = [doc.validate() for doc in new_documents]

        update['updated_at'] = datetime.datetime.utcnow()
        update['set_on_insert__created_at'] = update['updated_at']
        return super().update(upsert,
                              multi,
                              write_concern,
                              read_concern,
                              full_result,
                              **update)

    def find_or_create(self, **update):
        utc_now = datetime.datetime.utcnow()
        raw = {'$setOnInsert':
                   {'created_at': utc_now,
                    'updated_at': utc_now,
                    **update}}
        return super().modify(upsert=True, new=True, __raw__=raw)

class BaseDocument(Document):
    def __str__(self):
        return f"{self.__class__.__name__} <{self.to_dict()}>"

    created_at = DateTimeField()
    updated_at = DateTimeField()
    meta = {'abstract': True,
            'strict': False,
            'indexes': [{'fields': ('updated_at',)}],
            'queryset_class': BaseModifiedQuerySet}

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.datetime.utcnow()
        if self._get_changed_fields() or not self.updated_at:
            self.updated_at = datetime.datetime.utcnow()
        return super().save(*args, **kwargs)

    def modify(self, query=None, **update):
        update['updated_at'] = datetime.datetime.utcnow()
        return super().modify(query, **update)

    def to_dict(self, keep_enum=True):
        """Converts a mongoengine document to a dict"""
        res = {}
        for k in self._db_field_map:
            v = getattr(self, k)
            if v is not None:
                res[k] = v
            # handle Enum fields
            if not keep_enum and isinstance(v, Enum):
                res[k] = v.value
        if 'id' in res:
            res["id"] = str(self["id"])
        return res

    @classmethod
    def transform_mongo_doc_to_dict(cls, mongo_doc):
        return mongo_doc.to_mongo().to_dict()

    @classmethod
    def transform_mongo_list_to_list_of_dicts(cls, mongo_list):
        response = []
        for item in mongo_list:
            if isinstance(item, list):
                response.append(cls.transform_mongo_list_to_list_of_dicts(item))
            elif isinstance(item, MongoEngineBaseDocument):
                response.append(cls.transform_mongo_doc_to_dict(item))
            else:
                response.append(item)
        return response