#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  __init__.py
#  csvdiff
#

from __future__ import absolute_import, print_function, division

__author__ = 'Lars Yencken'
__email__ = 'lars@yencken.org'
__version__ = '0.1.0'

import sys
import optparse
import csv
import json
import functools

import yaml


DEBUG = False


class FatalError(Exception):
    pass


def csvdiff(lhs, rhs, indexes):
    lhs_recs = load_records(lhs, indexes)
    rhs_recs = load_records(rhs, indexes)

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


def load_records(filename, indexes):
    try:
        return {
            tuple(r[i] for i in indexes): r
            for r in csv.DictReader(open(filename))
        }
    except KeyError as k:
        abort('invalid column name {k} as key'.format(k=k))


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


def yaml_diff(diff, stream=sys.stdout):
    dump = functools.partial(yaml.safe_dump, stream=stream,
                             default_flow_style=False)

    # dump in three separate calls to force the order of these fields in the
    # YAML output
    dump({'removed': diff['removed']})
    dump({'added': diff['added']})
    dump({'changed': diff['changed']})


def json_diff(diff, stream=sys.stdout):
    json.dump(diff, stream)


def _create_option_parser():
    usage = \
"""%prog [options] lhs.csv rhs.csv

Diff the two CSV files."""  # nopep8

    parser = optparse.OptionParser(usage)
    parser.add_option('-k', '--key', action='store',
                      dest='key',
                      help='A comma separated list of key columns.')
    parser.add_option('-s', '--summary', action='store_true',
                      dest='summary',
                      help='Summarize the changes')
    parser.add_option('--yaml', action='store_true',
                      dest='yaml',
                      help='Print changes in more readable YAML format.')
    parser.add_option('-o', '--output', action='store', dest='output',
                      default='/dev/stdout',
                      help='Save the diff to the given filename')

    return parser


def _parse_keys(keys):
    indexes = map(int, keys.split(','))
    return indexes


def abort(message=None):
    if DEBUG:
        raise FatalError(message)

    print(message, file=sys.stderr)
    sys.exit(1)


def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    if not options.key:
        abort('you must specify one or more key columns with --key')

    elif len(args) != 2 or not options.key:
        parser.print_help()
        abort()

    lhs, rhs = args

    indexes = None
    if options.key:
        indexes = options.key.split(',')

    diff, orig_size = csvdiff(lhs, rhs, indexes)

    with open(options.output, 'w') as ostream:
        if options.summary:
            summarize_diff(diff, orig_size, ostream)

        elif options.yaml:
            yaml_diff(diff, ostream)

        else:
            json_diff(diff, ostream)
