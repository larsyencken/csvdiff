# -*- coding: utf-8 -*-
#
#  patch.py
#  csvdiff
#

"""
The the patch format.
"""

import sys
import json

from . import records
from . import error


SCHEMA = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'title': 'csvdiff',
    'description': 'The patch format used by csvdiff.',
    'type': 'object',
    'properties': {
        '_index': {
            'type': 'array',
            'minItems': 1,
            'items': {'type': 'string'},
        },
        'added': {
            'type': 'array',
            'items': {'type': 'object'},
        },
        'removed': {
            'type': 'array',
            'items': {'type': 'object'},
        },
        'changed': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'key': {'type': 'array',
                            'items': {'type': 'string'},
                            'minItems': 1},
                    'fields': {
                        'type': 'object',
                    },
                    'minProperties': 1,
                    'patternProperties': {
                        '.+': {'type': 'object',
                               'properties': {
                                   'from': {'type': 'string'},
                                   'to': {'type': 'string'},
                               },
                               'required': ['from', 'to']}
                    },
                },
            },
        },
    },
    'required': ['_index', 'added', 'changed', 'removed'],
}


def is_valid(diff):
    "Validate it against the schema."
    pass


def assemble(added, changed, removed, index_columns=None):
    d = {
        'added': added,
        'changed': changed,
        'removed': removed,
    }
    if index_columns is not None:
        d['_index'] = index_columns

    return d


def apply(diff, recs, strict=True):
    """
    Transform the records with the patch. May fail if the records do not
    match those expected in the patch.
    """
    index_columns = diff['_index']
    indexed = records.index(recs, index_columns, strict=strict)
    _add_records(indexed, diff['added'], index_columns, strict=strict)
    _remove_records(indexed, diff['removed'], index_columns, strict=strict)
    _update_records(indexed, diff['changed'], strict=strict)


def _add_records(indexed, recs_to_add, index_columns, strict=True):
    indexed_to_add = records.index(recs_to_add, index_columns)
    for k, r in indexed_to_add.items():
        if strict and k in indexed:
            error.abort(
                'error: key {0} already exists in source document'.format(k)
            )
        indexed[k] = r


def _remove_records(indexed, recs_to_remove, index_columns, strict=True):
    indexed_to_remove = records.index(recs_to_remove, index_columns)
    for k, r in indexed_to_remove.items():
        if strict:
            v = indexed.get(k)
            if v is None:
                error.abort(
                    'ERROR: key {0} does not exist in source '
                    'document'.format(k)
                )
            if v != r:
                error.abort(
                    'ERROR: source document version of {0} has '
                    'changed'.format(k)
                )

        del indexed[k]


def _update_records(indexed, deltas, strict=True):
    for delta in deltas:
        k = tuple(delta['key'])
        field_changes = delta['fields']

        r = indexed.get(k)

        # what happens when the record is missing?
        if r is None:
            if strict:
                error.abort(
                    'ERROR: source document is missing record '
                    'for {0}'.format(k)
                )
            continue

        r = indexed[k]
        for field, from_to in field_changes.items():
            expected = from_to['from']
            if strict and r.get(field) != expected:
                error.abort(
                    'ERROR: source document version of {0} has '
                    'changed {1} field'.format(k, field)
                )
            r[field] = from_to['to']


def load(istream, strict=True):
    "Deserialize a patch object."
    # XXX validate it if strict
    return json.load(istream)


def save(diff, stream=sys.stdout, compact=False):
    "Serialize a patch object."
    if compact:
        json.dump(diff, stream)
    else:
        json.dump(diff, stream, indent=2, sort_keys=True)
