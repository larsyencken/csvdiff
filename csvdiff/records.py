# -*- coding: utf-8 -*-
#
#  records.py
#  csvdiff
#

from typing.io import TextIO
from typing import Any, Dict, Tuple, Iterator, List, Sequence
import csv
import sys

from . import error


Column = str
PrimaryKey = Tuple[str, ...]
Record = Dict[Column, Any]
Index = Dict[PrimaryKey, Record]


ROW_INDEX = '_row'


class InvalidKeyError(Exception):
    pass


class SafeDictReader:
    """
    A CSV reader that streams records but gives nice errors if lines fail to parse.
    """
    def __init__(self, istream: TextIO, sep: str = ',') -> None:
        # bump the built-in limits on field sizes
        csv.field_size_limit(2**24)

        self.reader = csv.DictReader(istream, delimiter=sep)

    def __iter__(self) -> Iterator[Record]:
        for lineno, od in enumerate(self.reader, 2):
            if any(k is None for k in od):
                error.abort('CSV parse error on line {}'.format(lineno))

            # remap to an unordered dictionary, and add line number
            d = dict(od)
            d[ROW_INDEX] = lineno

            yield d

    @property
    def fieldnames(self):
        return self.reader._fieldnames


def load(file_or_stream: Any, sep: str = ',') -> SafeDictReader:
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
            for row_no, r in enumerate(record_seq)
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
    # order records by their row number
    records = sorted(records, key=lambda r: r.get(ROW_INDEX, sys.maxsize))

    writer = csv.DictWriter(ostream, fieldnames)
    writer.writeheader()
    for r in records:
        r = r.copy()
        del r[ROW_INDEX]

        writer.writerow(r)


def sort(records: Sequence[Record]) -> List[Record]:
    "Sort records into a canonical order, suitable for comparison."
    return sorted(records, key=_record_key)


def _record_key(record: Record) -> List[Tuple[Column, str]]:
    "An orderable representation of this record."
    return sorted(record.items())


def _index_row(row: Record, row_no: int, index_col: str):
    "Calculate the indexing key from a row."
    if index_col == ROW_INDEX:
        return row_no

    return row[index_col]
