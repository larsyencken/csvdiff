#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_csvdiff
----------------------------------

Tests for `csvdiff` module.
"""

from __future__ import absolute_import, print_function, division

from os import path
import unittest
import json
import tempfile

from io import StringIO

import csvdiff


class TestCsvdiff(unittest.TestCase):
    def setUp(self):
        csvdiff.DEBUG = True
        self.examples = path.join(path.dirname(__file__), 'examples')
        self.a_file = path.join(self.examples, 'a.csv')
        self.b_file = path.join(self.examples, 'b.csv')

    def test_summarize(self):
        lhs = {
            'a': {'name': 'a', 'sheep': 7},
            'b': {'name': 'b', 'sheep': 12},
            'c': {'name': 'c', 'sheep': 0},
        }
        rhs = {
            'a': {'name': 'a', 'sheep': 7},
            'c': {'name': 'c', 'sheep': 2},
            'd': {'name': 'd', 'sheep': 8},
        }
        diff = csvdiff.diff_records(lhs, rhs)
        o = StringIO()
        csvdiff.summarize_diff(diff, len(lhs), stream=o)
        self.assertEqual(
            o.getvalue(),
            "1 rows removed (33.3%)\n"
            "1 rows added (33.3%)\n"
            "1 rows changed (33.3%)\n"
        )

    def test_needs_args(self):
        self.assertRaises(csvdiff.FatalError,
                          csvdiff.main,
                          [])

    def test_needs_keys(self):
        self.assertRaises(csvdiff.FatalError,
                          csvdiff.main,
                          [self.a_file, self.b_file])

    def test_needs_valid_key(self):
        self.assertRaises(csvdiff.FatalError,
                          csvdiff.main,
                          ['--key=asasdfa', self.a_file, self.b_file])

    def test_diff_command(self):
        t = tempfile.NamedTemporaryFile(delete=True)
        csvdiff.main(['--key=id', '-o', t.name, self.a_file, self.b_file])

        diff = json.load(open(t.name))

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

        self.assertEquals(diff['added'],
                          expected['added'])
        self.assertEquals(diff['removed'],
                          expected['removed'])
        self.assertEquals(sorted(diff['changed'], key=lambda r: r['key']),
                          sorted(expected['changed'], key=lambda r: r['key']))

    def test_diff_records(self):
        lhs = {
            'a': {'name': 'a', 'sheep': 7},
            'b': {'name': 'b', 'sheep': 12},
            'c': {'name': 'c', 'sheep': 0},
        }
        rhs = {
            'a': {'name': 'a', 'sheep': 7},
            'c': {'name': 'c', 'sheep': 2},
            'd': {'name': 'd', 'sheep': 8},
        }

        diff = csvdiff.diff_records(lhs, rhs)
        self.assertEqual(diff['added'], [
            {'name': 'd', 'sheep': 8}
        ])
        self.assertEqual(diff['removed'], [
            {'name': 'b', 'sheep': 12}
        ])
        self.assertEqual(diff['changed'], [
            {'key': 'c',
             'fields': {'sheep': {'from': 0, 'to': 2}}}
        ])
        self.assertEqual(set(diff), set(['added', 'removed', 'changed']))

    def test_diff_records_multikey(self):
        lhs = {
            ('a', 1): {'name': 'a', 'type': 1, 'sheep': 7},
            ('b', 1): {'name': 'b', 'type': 1, 'sheep': 12},
            ('c', 1): {'name': 'c', 'type': 1, 'sheep': 0},
        }
        rhs = {
            ('a', 1): {'name': 'a', 'type': 1, 'sheep': 7},
            ('c', 1): {'name': 'c', 'type': 1, 'sheep': 2},
            ('d', 1): {'name': 'd', 'type': 1, 'sheep': 8},
        }

        diff = csvdiff.diff_records(lhs, rhs)
        self.assertEqual(diff['added'], [
            {'name': 'd', 'sheep': 8, 'type': 1}
        ])
        self.assertEqual(diff['removed'], [
            {'name': 'b', 'sheep': 12, 'type': 1}
        ])
        self.assertEqual(diff['changed'], [
            {'key': ('c', 1),
             'fields': {'sheep': {'from': 0, 'to': 2}}}
        ])
        self.assertEqual(set(diff), set(['added', 'removed', 'changed']))

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
