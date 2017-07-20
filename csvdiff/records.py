# -*- coding: utf-8 -*-
#
#  records.py
#  csvdiff
#

import six

import csv

from . import error


class InvalidKeyError(Exception):
    pass


def load(file_or_stream, sep=','):
    istream = (open(file_or_stream)
               if not hasattr(file_or_stream, 'read')
               else file_or_stream)

    # unicode delimiters are not ok in Python 2
    if six.PY2 and isinstance(sep, six.text_type):
        sep = sep.encode('utf8')

    return SafeDictReader(istream, sep=sep)


class SafeDictReader:
    """
    A CSV reader that streams records but gives nice errors if lines fail to parse.
    """
    def __init__(self, istream, sep=None):
        self.reader = csv.DictReader(istream, delimiter=sep)

    def __iter__(self):
        for lineno, r in enumerate(self.reader, 2):
            if any(k is None for k in r):
                error.abort('CSV parse error on line {}'.format(lineno))

            yield r

    @property
    def fieldnames(self):
        return self.reader._fieldnames


def index(record_seq, index_columns):
    try:
        obj = {
            tuple(r[i] for i in index_columns): r
            for r in record_seq
        }

        return obj
    except KeyError as k:
        raise InvalidKeyError('invalid column name {k} as key'.format(k=k))


def filter_ignored(sequence, ignore_columns):
    for key in sequence:
        for i in ignore_columns:
            sequence[key].pop(i)
    return sequence


def save(record_seq, fieldnames, ostream):
    writer = csv.DictWriter(ostream, fieldnames)
    writer.writeheader()
    for r in record_seq:
        writer.writerow(r)


def sort(recs):
    return sorted(recs, key=_record_key)


def _record_key(r):
    return sorted(r.items())
