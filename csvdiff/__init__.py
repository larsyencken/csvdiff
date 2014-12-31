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

import click

from . import records
from . import patch


def diff_files(from_file, to_file, index_columns):
    """
    Diff two CSV files, returning the patch which transforms one into the
    other.
    """
    from_records = records.load(from_file)
    to_records = records.load(to_file)
    return records.compare(from_records, to_records, index_columns)


def diff_records(from_records, to_records, index_columns):
    """
    Diff two sequences of dictionary records, returning the patch which
    transforms one into the other.
    """
    return records.compare(from_records, to_records, index_columns)


def diff_and_summarize(from_csv, to_csv, index_columns, stream=sys.stdout):
    """
    Print a summary of the difference between the two files.
    """
    from_records = records.load(from_csv)
    to_records = records.load(to_csv)
    diff = records.compare(from_records, to_records, index_columns)
    summarize_diff(diff, len(from_records), stream=stream)


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
def csvdiff_cmd(index_columns, from_csv, to_csv, style=None, output=None):
    """
    Compare two csv files to see what rows differ between them. The files
    are each expected to have a header row, and for each row to be uniquely
    identified by one or more indexing columns.
    """
    ostream = (sys.stdout
               if output is None
               else open(output, 'w'))

    if style == 'summary':
        diff_and_summarize(from_csv, to_csv, index_columns, ostream)
    else:
        compact = (style == 'compact')
        diff = diff_files(from_csv, to_csv, index_columns)
        patch.save(diff, ostream, compact=compact)

    ostream.close()


@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--input', '-i', type=click.Path(exists=True),
              help='Read the JSON patch from the given file.')
@click.option('--output', '-o', type=click.Path(),
              help='Write the transformed CSV to the given file.')
def patch_cmd(input_file, input=None, output=None):
    """
    Apply the changes from a csvdiff patch to an existing CSV file.
    """
    istream = (sys.stdin
               if input is None
               else open(input))
    ostream = (sys.stdout
               if output is None
               else open(output, 'w'))

    try:
        patch_stream(input_file, istream, ostream)

    finally:
        input.close()
        output.close()


def patch_stream(orig_file, patch_stream, ostream):
    diff = patch.load(patch_stream)
    orig = records.load(orig_file)
    patched = patch.apply(diff, orig)
    fieldnames = (sorted(patched[0].keys())
                  if patched
                  else orig.fieldnames)
    records.save(patched, fieldnames, ostream)
