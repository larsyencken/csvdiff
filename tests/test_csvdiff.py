#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_csvdiff
----------------------------------

Tests for `csvdiff` module.
"""

from __future__ import absolute_import, print_function, division

import unittest

from io import StringIO

import csvdiff


class TestCsvdiff(unittest.TestCase):
    def setUp(self):
        pass

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
