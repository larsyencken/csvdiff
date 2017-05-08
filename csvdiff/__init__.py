#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  __init__.py
#  csvdiff
#

from __future__ import absolute_import, print_function, division

import sys

import click

from . import records, patch, error


__author__ = 'Lars Yencken'
__email__ = 'lars@yencken.org'
__version__ = '0.3.1'


if sys.version_info.major == 2:
    import StringIO as io
else:
    import io


# exit codes for the command-line
EXIT_SAME = 0
EXIT_DIFFERENT = 1
EXIT_ERROR = 2


def diff_files(from_file, to_file, index_columns, sep=',', ignored_columns=None):
    """
    Diff two CSV files, returning the patch which transforms one into the
    other.
    """
    with open(from_file) as from_stream:
        with open(to_file) as to_stream:
            from_records = records.load(from_stream, sep=sep)
            to_records = records.load(to_stream, sep=sep)
            return patch.create(from_records, to_records, index_columns,
                                ignore_columns=ignored_columns)


def diff_records(from_records, to_records, index_columns):
    """
    Diff two sequences of dictionary records, returning the patch which
    transforms one into the other.
    """
    return patch.create(from_records, to_records, index_columns)


def patch_file(patch_stream, fromcsv_stream, tocsv_stream, strict=True,
               sep=','):
    """
    Apply the patch to the source CSV file, and save the result to the target
    file.
    """
    diff = patch.load(patch_stream)

    from_records = records.load(fromcsv_stream, sep=sep)
    to_records = patch.apply(diff, from_records, strict=strict)

    # what order should the columns be in?
    if to_records:
        # have data, use a nice ordering
        all_columns = to_records[0].keys()
        index_columns = diff['_index']
        fieldnames = _nice_fieldnames(all_columns, index_columns)
    else:
        # no data, use the original order
        fieldnames = from_records.fieldnames

    records.save(to_records, fieldnames, tocsv_stream)


def patch_records(diff, from_records, strict=True):
    """
    Apply the patch to the sequence of records, returning the transformed
    records.
    """
    return patch.apply(diff, from_records, strict=strict)


def _nice_fieldnames(all_columns, index_columns):
    "Indexes on the left, other fields in alphabetical order on the right."
    non_index_columns = set(all_columns).difference(index_columns)
    return index_columns + sorted(non_index_columns)


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
@click.option('--quiet', '-q', is_flag=True,
              help="Don't output anything, just use exit codes")
@click.option('--sep', default=',',
              help='Separator to use between fields [default: comma]')
@click.option('--ignore_columns', '-i', type=CSVType(),
              help='a comma seperated list of columns to ignore from the comparison')
def csvdiff_cmd(index_columns, from_csv, to_csv, style=None, output=None,
                sep=',', quiet=False, ignore_columns=None):
    """
    Compare two csv files to see what rows differ between them. The files
    are each expected to have a header row, and for each row to be uniquely
    identified by one or more indexing columns.
    """

    if ignore_columns is not None:
        for i in ignore_columns:
            if i in index_columns:
                error.abort("You can't ignore an index column")

    ostream = (open(output, 'w') if output
               else io.StringIO() if quiet
               else sys.stdout)

    try:
        if style == 'summary':
            _diff_and_summarize(from_csv, to_csv, index_columns, ostream,
                                sep=sep, ignored_columns=ignore_columns)
        else:
            compact = (style == 'compact')
            _diff_files_to_stream(from_csv, to_csv, index_columns, ostream,
                                  compact=compact, sep=sep, ignored_columns=ignore_columns)

    except records.InvalidKeyError as e:
        error.abort(e.args[0])

    finally:
        ostream.close()


def _diff_files_to_stream(from_csv, to_csv, index_columns, ostream,
                          compact=False, sep=',', ignored_columns=None):
    diff = diff_files(from_csv, to_csv, index_columns, sep=sep, ignored_columns=ignored_columns)
    patch.save(diff, ostream, compact=compact)
    exit_code = (EXIT_SAME
                 if patch.is_empty(diff)
                 else EXIT_DIFFERENT)
    sys.exit(exit_code)


def _diff_and_summarize(from_csv, to_csv, index_columns, stream=sys.stdout,
                        sep=',', ignored_columns=None):
    """
    Print a summary of the difference between the two files.
    """
    from_records = list(records.load(from_csv, sep=sep))
    to_records = records.load(to_csv, sep=sep)
    diff = patch.create(from_records, to_records, index_columns, ignored_columns)
    _summarize_diff(diff, len(from_records), stream=stream)
    exit_code = (EXIT_SAME
                 if patch.is_empty(diff)
                 else EXIT_DIFFERENT)
    sys.exit(exit_code)


def _summarize_diff(diff, orig_size, stream=sys.stdout):
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
        print(u'files are identical', file=stream)


@click.command()
@click.argument('input_csv', type=click.Path(exists=True))
@click.option('--input', '-i', type=click.Path(exists=True),
              help='Read the JSON patch from the given file.')
@click.option('--output', '-o', type=click.Path(),
              help='Write the transformed CSV to the given file.')
@click.option('--strict/--no-strict', default=True,
              help='Whether or not to tolerate a changed source document '
                   '(default: strict)')
def csvpatch_cmd(input_csv, input=None, output=None, strict=True):
    """
    Apply the changes from a csvdiff patch to an existing CSV file.
    """
    patch_stream = (sys.stdin
                    if input is None
                    else open(input))
    tocsv_stream = (sys.stdout
                    if output is None
                    else open(output, 'w'))
    fromcsv_stream = open(input_csv)

    try:
        patch_file(patch_stream, fromcsv_stream, tocsv_stream, strict=strict)

    except patch.InvalidPatchError as e:
        error.abort('reading patch, {0}'.format(e.args[0]))

    finally:
        patch_stream.close()
        fromcsv_stream.close()
        tocsv_stream.close()
