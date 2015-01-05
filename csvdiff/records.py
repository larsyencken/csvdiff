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
        writer.writerow(r)


def sort(recs):
    return sorted(recs, key=_record_key)


def _record_key(r):
    return sorted(r.items())
