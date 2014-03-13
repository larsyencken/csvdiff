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

import yaml


def csvdiff(lhs, rhs, indexes):
    lhs_recs = load_records(lhs, indexes)
    rhs_recs = load_records(rhs, indexes)

    removed, added, shared = diff_keys(lhs_recs, rhs_recs)

    changed = diff_shared(lhs_recs, rhs_recs, shared)

    diff = diff_summary(removed, added, changed, lhs_recs, rhs_recs)

    return diff


def load_records(filename, indexes):
    return {
        tuple(r[i] for i in indexes): r
        for r in csv.DictReader(open(filename))
    }


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
    diff['removed'] = {unicode(k): lhs_recs[k] for k in removed}
    diff['added'] = {unicode(k): rhs_recs[k] for k in added}
    diff['changed'] = {unicode(k): rec_diff(lhs_recs[k], rhs_recs[k])
                       for k in changed}
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


def summarize_diff(diff, stream=sys.stdout):
    n_removed = len(diff['removed'])
    n_added = len(diff['added'])
    n_changed = len(diff['changed'])

    if n_removed or n_added or n_changed:
        print('{0} rows removed'.format(n_removed), file=stream)
        print('{0} rows added'.format(n_added), file=stream)
        print('{0} rows changed'.format(n_changed), file=stream)
    else:
        print('files are identical')


def yaml_diff(diff, stream=sys.stdout):
    yaml.safe_dump(diff, stream, default_flow_style=False)


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

    return parser


def _parse_keys(keys):
    indexes = map(int, keys.split(','))
    return indexes


def main():
    argv = sys.argv[1:]
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    if len(args) != 2:
        parser.print_help()
        sys.exit(1)

    lhs, rhs = args

    indexes = None
    if options.key:
        indexes = options.key.split(',')

    diff = csvdiff(lhs, rhs, indexes)

    if options.summary:
        summarize_diff(diff)

    elif options.yaml:
        yaml_diff(diff)

    else:
        json.dump(diff, sys.stdout)
