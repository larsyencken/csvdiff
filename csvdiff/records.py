# -*- coding: utf-8 -*-
#
#  records.py
#  csvdiff
#

import csv

from . import error


def load(file_or_stream):
    istream = (open(file_or_stream)
               if not hasattr(file_or_stream, 'read')
               else file_or_stream)

    return csv.DictReader(istream)


def index(record_seq, index_columns):
    try:
        return {
            tuple(r[i] for i in index_columns): r
            for r in record_seq
        }
    except KeyError as k:
        error.abort('invalid column name {k} as key'.format(k=k))


def save(record_seq, fieldnames, ostream):
    writer = csv.DictWriter(ostream, fieldnames)
    writer.writeheader()
    for r in record_seq:
        writer.writerow()


def compare(lhs_records, rhs_records, index_columns):
    """
    Diff two sets of records, using the index columns as the primary key for
    both datasets.
    """
    lhs_indexed = index(lhs_records, index_columns)
    rhs_indexed = index(rhs_records, index_columns)

    diff = compare_indexed(lhs_indexed, rhs_indexed, index_columns)
    return diff


def compare_indexed(lhs_indexed, rhs_indexed, index_columns):
    # examine keys for overlap
    removed, added, shared = compare_keys(lhs_indexed, rhs_indexed)

    # check for changed rows
    changed = compare_rows(lhs_indexed, rhs_indexed, shared)

    diff = assemble_diff(removed, added, changed, lhs_indexed, rhs_indexed,
                         index_columns)

    return diff


def compare_keys(lhs_recs, rhs_recs):
    lhs_keys = set(lhs_recs)
    rhs_keys = set(rhs_recs)
    removed = lhs_keys.difference(rhs_keys)
    shared = lhs_keys.intersection(rhs_keys)
    added = rhs_keys.difference(lhs_keys)
    return removed, added, shared


def compare_rows(lhs_recs, rhs_recs, keys):
    "Return the set of keys which have changed."
    return set(
        k for k in keys
        if sorted(lhs_recs[k].items()) != sorted(rhs_recs[k].items())
    )


def assemble_diff(removed, added, changed, lhs_recs, rhs_recs, index_columns):
    diff = {}
    diff[u'removed'] = [lhs_recs[k] for k in removed]
    diff[u'added'] = [rhs_recs[k] for k in added]
    diff[u'changed'] = [{'key': list(k),
                         'fields': record_diff(lhs_recs[k], rhs_recs[k])}
                        for k in changed]
    diff['_index'] = index_columns
    return diff


def record_diff(lhs, rhs):
    "Diff an individual row."
    delta = {}
    for k in set(lhs).union(rhs):
        from_ = lhs[k]
        to_ = rhs[k]
        if from_ != to_:
            delta[k] = {'from': from_, 'to': to_}

    return delta
