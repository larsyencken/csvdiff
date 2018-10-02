# -*- coding: utf-8 -*-
#
#  records.py
#  csvdiff
#

from typing.io import TextIO
from typing import Any, Dict, Tuple, Iterator, List, Sequence
import csv

from . import error


Column = str
PrimaryKey = Tuple[str, ...]
Record = Dict[Column, Any]
Index = Dict[PrimaryKey, Record]


class InvalidKeyError(Exception):
    pass


class SafeDictReader:
    """
    A CSV reader that streams records but gives nice errors if lines fail to parse.
    """
    def __init__(self, istream: TextIO, sep: str=',') -> None:
        self.reader = csv.DictReader(istream, delimiter=sep)

    def __iter__(self) -> Iterator[Record]:
        for lineno, r in enumerate(self.reader, 2):
            if any(k is None for k in r):
                error.abort('CSV parse error on line {}'.format(lineno))

            yield dict(r)

    @property
    def fieldnames(self):
        return self.reader._fieldnames


def load(file_or_stream: Any, sep: str=',') -> SafeDictReader:
    istream = (open(file_or_stream)
               if not hasattr(file_or_stream, 'read')
               else file_or_stream)
    return SafeDictReader(istream, sep=sep)


def index(record_seq: Iterator[Record], index_columns: List[str]) -> Index:
    if not index_columns:
        raise InvalidKeyError('must provide on or more columns to index on')

    try:
        obj = {
            tuple(r[i] for i in index_columns): r
            for r in record_seq
        }

        return obj

    except KeyError as k:
        raise InvalidKeyError('invalid column name {k} as key'.format(k=k))


def filter_ignored(index: Index, ignore_columns: List[Column]) -> Index:
    for record in index.values():
        # edit the record in-place
        for column in ignore_columns:
            del record[column]

    return index


def save(records: Sequence[Record], fieldnames: List[Column], ostream: TextIO):
    writer = csv.DictWriter(ostream, fieldnames)
    writer.writeheader()
    for r in records:
        writer.writerow(r)


def sort(records: Sequence[Record]) -> List[Record]:
    "Sort records into a canonical order, suitable for comparison."
    return sorted(records, key=_record_key)


def _record_key(record: Record) -> List[Tuple[Column, str]]:
    "An orderable representation of this record."
    return sorted(record.items())
