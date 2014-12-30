#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  __init__.py
#  csvdiff
#

from __future__ import absolute_import, print_function, division

__author__ = 'Lars Yencken'
__email__ = 'lars@yencken.org'
__version__ = '0.2.0'

import sys
import csv
import json

import click

DIFF_SCHEMA = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'title': 'csvdiff',
    'description': 'The patch format used by csvdiff.',
    'type': 'object',
    'properties': {
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
    'required': ['added', 'changed', 'removed'],
}


DEBUG = False


class FatalError(Exception):
    pass


def csvdiff(lhs, rhs, index_columns):
    lhs_recs = load_indexed_records(lhs, index_columns)
    rhs_recs = load_indexed_records(rhs, index_columns)

    orig_size = len(lhs_recs)

    return diff_records(lhs_recs, rhs_recs), orig_size


def diff_records(lhs_recs, rhs_recs):
    # examine keys for overlap
    removed, added, shared = diff_keys(lhs_recs, rhs_recs)

    # check for changed rows
    changed = diff_shared(lhs_recs, rhs_recs, shared)

    # summarize changes
    diff = diff_summary(removed, added, changed, lhs_recs, rhs_recs)

    return diff


def load_indexed_records(filename, index_columns):
    try:
        return {
            tuple(r[i] for i in index_columns): r
            for r in load_records(filename)
        }
    except KeyError as k:
        abort('invalid column name {k} as key'.format(k=k))


def load_records(filename):
    istream = open(filename)
    reader = csv.DictReader(istream)
    return reader


def diff_keys(lhs_recs, rhs_recs):
    lhs_keys = set(lhs_recs)
    rhs_keys = set(rhs_recs)
    removed = lhs_keys.difference(rhs_keys)
    shared = lhs_keys.intersection(rhs_keys)
    added = rhs_keys.difference(lhs_keys)
    return removed, added, shared


def diff_shared(lhs_recs, rhs_recs, keys):
    "Return the set of keys which have changed."
    return set(
        k for k in keys
        if sorted(lhs_recs[k].items()) != sorted(rhs_recs[k].items())
    )


def diff_summary(removed, added, changed, lhs_recs, rhs_recs):
    diff = {}
    diff[u'removed'] = [lhs_recs[k] for k in removed]
    diff[u'added'] = [rhs_recs[k] for k in added]
    diff[u'changed'] = [{'key': k,
                         'fields': rec_diff(lhs_recs[k], rhs_recs[k])}
                        for k in changed]
    return diff


def rec_diff(lhs, rhs):
    "Diff an individual row."
    delta = {}
    for k in set(lhs).union(rhs):
        from_ = lhs[k]
        to_ = rhs[k]
        if from_ != to_:
            delta[k] = {'from': from_, 'to': to_}

    return delta


def summarize_diff(diff, orig_size, stream=sys.stdout):
    if orig_size == 0:
        # slightly arbitrary when the original data was empty
        orig_size = 1

    n_removed = len(diff['removed'])
    n_added = len(diff['added'])
    n_changed = len(diff['changed'])

    if n_removed or n_added or n_changed:
        print(u'%d rows removed (%.01f%%)' % (
            n_removed, 100 * n_removed / orig_size
        ), file=stream)
        print(u'%d rows added (%.01f%%)' % (
            n_added, 100 * n_added / orig_size
        ), file=stream)
        print(u'%d rows changed (%.01f%%)' % (
            n_changed, 100 * n_changed / orig_size
        ), file=stream)
    else:
        print('files are identical')


def json_diff(diff, stream=sys.stdout, compact=False):
    if compact:
        json.dump(diff, stream)
    else:
        json.dump(diff, stream, indent=2, sort_keys=True)


def abort(message=None):
    if DEBUG:
        raise FatalError(message)

    print(message, file=sys.stderr)
    sys.exit(1)


class CSVType(click.ParamType):
    name = 'csv'

    def convert(self, value, param, ctx):
        if isinstance(value, bytes):
            try:
                enc = getattr(sys.stdin, 'encoding', None)
                if enc is not None:
                    value = value.decode(enc)
            except UnicodeError:
                try:
                    value = value.decode(sys.getfilesystemencoding())
                except UnicodeError:
                    value = value.decode('utf-8', 'replace')
            return value.split(',')

        return value.split(',')

    def __repr__(self):
        return 'CSV'


@click.command()
@click.argument('index_columns', type=CSVType())
@click.argument('from_csv', type=click.Path(exists=True))
@click.argument('to_csv', type=click.Path(exists=True))
@click.option('--style',
              type=click.Choice(['compact', 'pretty', 'summary']),
              default='compact',
              help=('Instead of the default compact output, pretty-print '
                    'or give a summary instead'))
@click.option('--output', '-o', type=click.Path(),
              help='Output to a file instead of stdout')
def main(index_columns, from_csv, to_csv, style=None, output=None):
    """
    Compare two csv files to see what rows differ between them. The files
    are each expected to have a header row, and for each row to be uniquely
    identified by one or more indexing columns.
    """
    csvdiff_main(index_columns, from_csv, to_csv, style=style, output=output)


def csvdiff_main(index_columns, from_csv, to_csv, style=None, output=None):
    diff, orig_size = csvdiff(from_csv, to_csv, index_columns)

    if output is None:
        ostream = sys.stdout
    else:
        ostream = open(output, 'w')

    if style == 'summary':
        summarize_diff(diff, orig_size, ostream)
    else:
        compact = (style == 'compact')
        json_diff(diff, ostream, compact=compact)

    ostream.close()


@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--input', '-i', type=click.Path(exists=True),
              help='Read the JSON patch from the given file.')
@click.option('--output', '-o', type=click.Path(),
              help='Write the transformed CSV to the given file.')
def patch(input_file, input=None, output=None):
    """
    Apply the changes from a csvdiff patch to an existing CSV file.
    """
    if input is None:
        istream = sys.stdin
    else:
        istream = open(input)

    if output is None:
        ostream = sys.stdout
    else:
        ostream = open(output, 'w')

    try:
        diff = read_patch(istream)
        orig = load_records(input_file)
        patched = patch_records(orig, diff)
        save_records(patched, orig.fieldnames, ostream)

    finally:
        input.close()
        output.close()


def read_patch(istream):
    diff = json.load(istream)
    # XXX validate it
    return diff


def patch_records(orig, diff):
    raise Exception('not yet implemented')


def save_records(records, fieldnames, ostream):
    writer = csv.DictWriter(ostream, fieldnames)
    writer.writeheader()
    for r in records:
        writer.writerow(r)
