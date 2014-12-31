#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_csvdiff
----------------------------------

Tests for `csvdiff` module.
"""

from __future__ import absolute_import, print_function, division

import os
from os import path
import unittest
import json
import tempfile
from io import StringIO

import csvdiff

from click.testing import CliRunner


class TestCsvdiff(unittest.TestCase):
    def setUp(self):
        csvdiff.DEBUG = True
        self.examples = path.join(path.dirname(__file__), 'examples')
        self.a_file = path.join(self.examples, 'a.csv')
        self.b_file = path.join(self.examples, 'b.csv')
        self.runner = CliRunner()

    def main(self, *args):
        t = tempfile.NamedTemporaryFile(delete=True)
        result = self.runner.invoke(csvdiff.csvdiff_cmd,
                                    ('--output', t.name) + args)
        diff = None
        if path.exists(t.name) and os.stat(t.name).st_size:
            with open(t.name) as istream:
                diff = json.load(istream)

        return result.exit_code, diff

    def test_summarize(self):
        lhs = [
            {'name': 'a', 'sheep': 7},
            {'name': 'b', 'sheep': 12},
            {'name': 'c', 'sheep': 0},
        ]
        rhs = [
            {'name': 'a', 'sheep': 7},
            {'name': 'c', 'sheep': 2},
            {'name': 'd', 'sheep': 8},
        ]
        diff = csvdiff.diff_records(lhs, rhs, ['name'])
        o = StringIO()
        csvdiff._summarize_diff(diff, len(lhs), stream=o)
        self.assertEqual(
            o.getvalue(),
            "1 rows removed (33.3%)\n"
            "1 rows added (33.3%)\n"
            "1 rows changed (33.3%)\n"
        )

    def test_needs_args(self):
        exit_code, _ = self.main()
        assert exit_code != 0

    def test_needs_enough_arguments(self):
        exit_code, _ = self.main(self.a_file, self.b_file)
        assert exit_code != 0

    def test_needs_valid_key(self):
        exit_code, _ = self.main('abcd', self.a_file, self.b_file)
        assert exit_code != 0

    def test_diff_command(self):
        exit_code, diff = self.main('id', self.a_file, self.b_file)
        self.assertEqual(exit_code, 0)

        expected = {
            'added': [{'id': '5', 'name': 'mira', 'amount': '81'}],
            'removed': [{'id': '2', 'name': 'eva', 'amount': '63'}],
            'changed': [
                {'key': ['1'],
                 'fields': {'amount': {'from': '20', 'to': '23'}}},
                {'key': ['6'],
                 'fields': {'amount': {'from': '10', 'to': '13'}}},
            ],
        }

        self.assertEqual(diff['added'],
                         expected['added'])
        self.assertEqual(diff['removed'],
                         expected['removed'])
        self.assertEqual(sorted(diff['changed'], key=lambda r: r['key']),
                         sorted(expected['changed'], key=lambda r: r['key']))

    def test_diff_records(self):
        lhs = [
            {'name': 'a', 'sheep': 7},
            {'name': 'b', 'sheep': 12},
            {'name': 'c', 'sheep': 0},
        ]
        rhs = [
            {'name': 'a', 'sheep': 7},
            {'name': 'c', 'sheep': 2},
            {'name': 'd', 'sheep': 8},
        ]

        diff = csvdiff.diff_records(lhs, rhs, ['name'])
        self.assertEqual(diff['added'], [
            {'name': 'd', 'sheep': 8}
        ])
        self.assertEqual(diff['removed'], [
            {'name': 'b', 'sheep': 12}
        ])
        self.assertEqual(diff['changed'], [
            {'key': ['c'],
             'fields': {'sheep': {'from': 0, 'to': 2}}}
        ])
        self.assertEqual(set(diff), set(['added', 'removed', 'changed',
                                         '_index']))

    def test_diff_records_multikey(self):
        lhs = [
            {'name': 'a', 'type': 1, 'sheep': 7},
            {'name': 'b', 'type': 1, 'sheep': 12},
            {'name': 'c', 'type': 1, 'sheep': 0},
        ]
        rhs = [
            {'name': 'a', 'type': 1, 'sheep': 7},
            {'name': 'c', 'type': 1, 'sheep': 2},
            {'name': 'd', 'type': 1, 'sheep': 8},
        ]

        diff = csvdiff.diff_records(lhs, rhs, ['name', 'type'])
        self.assertEqual(diff['added'], [
            {'name': 'd', 'sheep': 8, 'type': 1}
        ])
        self.assertEqual(diff['removed'], [
            {'name': 'b', 'sheep': 12, 'type': 1}
        ])
        self.assertEqual(diff['changed'], [
            {'key': ['c', 1],
             'fields': {'sheep': {'from': 0, 'to': 2}}}
        ])
        self.assertEqual(set(diff), set(['added', 'removed', 'changed',
                                         '_index']))

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
