#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_csvdiff
----------------------------------

Tests for `csvdiff` module.
"""

import unittest

from cStringIO import StringIO

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
        self.assertEquals(
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
        self.assertEquals(diff['added'], {
            'd': {'name': 'd', 'sheep': 8}
        })
        self.assertEquals(diff['removed'], {
            'b': {'name': 'b', 'sheep': 12}
        })
        self.assertEquals(diff['changed'], {
            'c': {'sheep': {'from': 0, 'to': 2}}
        })
        self.assertEquals(set(diff), set(['added', 'removed', 'changed']))

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
