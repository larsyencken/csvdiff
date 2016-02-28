#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

from collections import namedtuple
from contextlib import contextmanager
from io import StringIO
from os import path
import csv
import json
import os
import tempfile
import unittest

import csvdiff
from csvdiff import patch, records

from click.testing import CliRunner


class TestCsvdiff(unittest.TestCase):
    def setUp(self):
        csvdiff.DEBUG = True
        self.examples = path.join(path.dirname(__file__), 'examples')
        self.a_file = path.join(self.examples, 'a.csv')
        self.b_file = path.join(self.examples, 'b.csv')
        self.diff_file = path.join(self.examples, 'diff.json')
        self.bad_diff_file = path.join(self.examples, 'bad_diff.json')
        self.runner = CliRunner()

    def csvdiff_cmd(self, *args):
        RunResult = namedtuple('RunResult', 'exit_code diff output')
        t = tempfile.NamedTemporaryFile(delete=True)
        result = self.runner.invoke(csvdiff.csvdiff_cmd,
                                    ('--output', t.name) + args)
        diff = None
        if path.exists(t.name) and os.stat(t.name).st_size:
            with open(t.name) as istream:
                diff = json.load(istream)

        return RunResult(result.exit_code, diff, result.output)

    def csvdiff_summary_cmd(self, *args):
        RunResult = namedtuple('RunResult', 'exit_code summary output')
        t = tempfile.NamedTemporaryFile(delete=True)
        test_args = ('--output', t.name, '--style', 'summary')
        result = self.runner.invoke(csvdiff.csvdiff_cmd,
                                    test_args + args)
        with open(t.name, 'r') as istream:
            summary = istream.read()

        return RunResult(result.exit_code, summary, result.output)

    def patch_cmd(self, *args):
        RunResult = namedtuple('RunResult', 'exit_code records output')
        t = tempfile.NamedTemporaryFile(delete=True)
        result = self.runner.invoke(csvdiff.csvpatch_cmd,
                                    ('--output', t.name) + args)
        recs = None
        if path.exists(t.name) and os.stat(t.name).st_size:
            with open(t.name) as istream:
                recs = list(csv.DictReader(istream))

        return RunResult(result.exit_code, recs, result.output)

    def test_summarize(self):
        lhs = [
            {'name': 'a', 'sheep': '7'},
            {'name': 'b', 'sheep': '12'},
            {'name': 'c', 'sheep': '0'},
        ]
        rhs = [
            {'name': 'a', 'sheep': '7'},
            {'name': 'c', 'sheep': '2'},
            {'name': 'd', 'sheep': '8'},
        ]
        diff = csvdiff.diff_records(lhs, rhs, ['name'])
        assert patch.is_valid(diff)
        assert not patch.is_typed(diff)
        o = StringIO()
        csvdiff._summarize_diff(diff, len(lhs), stream=o)
        self.assertEqual(
            o.getvalue(),
            "1 rows removed (33.3%)\n"
            "1 rows added (33.3%)\n"
            "1 rows changed (33.3%)\n"
        )

    def test_summarize_cmd(self):
        lhs = [
            {'name': 'a', 'sheep': '7'},
            {'name': 'b', 'sheep': '12'},
            {'name': 'c', 'sheep': '0'},
        ]
        rhs = [
            {'name': 'a', 'sheep': '7'},
            {'name': 'c', 'sheep': '2'},
            {'name': 'd', 'sheep': '8'},
        ]
        with tmp_csv_files(lhs, rhs) as (lhs_file, rhs_file):
            result = self.csvdiff_summary_cmd('name', lhs_file, rhs_file)
            self.assertEquals(result.exit_code, 1)
            self.assertEquals(
                result.summary,
                "1 rows removed (33.3%)\n"
                "1 rows added (33.3%)\n"
                "1 rows changed (33.3%)\n"
            )

    def test_summarize_identical(self):
        lhs = [
            {'name': 'a', 'sheep': '7'},
            {'name': 'b', 'sheep': '12'},
            {'name': 'c', 'sheep': '0'},
        ]
        diff = csvdiff.diff_records(lhs, lhs, ['name'])
        assert patch.is_valid(diff)
        assert not patch.is_typed(diff)
        o = StringIO()
        csvdiff._summarize_diff(diff, len(lhs), stream=o)
        self.assertEqual(
            o.getvalue(),
            'files are identical\n'
        )

    def test_csvdiff_fails_without_enough_arguments(self):
        result = self.csvdiff_cmd()
        self.assertEquals(result.exit_code, 2)

        result = self.csvdiff_cmd(self.a_file, self.b_file)
        self.assertEquals(result.exit_code, 2)

    def test_csvdiff_fails_without_valid_key(self):
        result = self.csvdiff_cmd('abcd', self.a_file, self.b_file)
        assert result.exit_code != 0

    def test_diff_command_valid_usage_with_difference(self):
        result = self.csvdiff_cmd('id', self.a_file, self.b_file)
        self.assertEqual(result.exit_code, 1)
        diff = result.diff
        patch.validate(diff)
        assert patch.is_valid(diff)

        expected = {
            '_index': ['id'],
            'added': [{'id': '5', 'name': 'mira', 'amount': '81'}],
            'removed': [{'id': '2', 'name': 'eva', 'amount': '63'}],
            'changed': [
                {'key': ['1'],
                 'fields': {'amount': {'from': '20', 'to': '23'}}},
                {'key': ['6'],
                 'fields': {'amount': {'from': '10', 'to': '13'}}},
            ],
        }

        self.assertPatchesEqual(diff, expected)

    def test_diff_records_float_values(self):
        lhs = [
            {'name': 'a', 'sheep': 7.003},
            {'name': 'b', 'sheep': 12.},
            {'name': 'c', 'sheep': 0.},
            {'name': 'e', 'sheep': 3.02},
        ]
        rhs = [
            {'name': 'a', 'sheep': 7.001},
            {'name': 'c', 'sheep': 2.},
            {'name': 'd', 'sheep': 8.},
            {'name': 'e', 'sheep': 3.01},
        ]

        diff = csvdiff.diff_records(lhs, rhs, ['name'], precision=2)
        assert patch.is_valid(diff)
        assert not patch.is_typed(diff)

        # check the contents of the diff
        self.assertEqual(diff['added'], [
            {'name': 'd', 'sheep': 8.}
        ])
        self.assertEqual(diff['removed'], [
            {'name': 'b', 'sheep': 12.}
        ])
        self.assertEqual(diff['changed'], [
            {'key': ['c'],
             'fields': {'sheep': {'from': 0., 'to': 2.}}},
            {'key': ['e'],
             'fields': {'sheep': {'from': 3.02, 'to': 3.01}}},
        ])

        # check that we can apply the diff
        patched = csvdiff.patch_records(diff, lhs)
        self.assertRecordsEqual(rhs, patched, precision=2)

    def test_diff_records_str_values(self):
        lhs = [
            {'name': 'a', 'sheep': '7'},
            {'name': 'b', 'sheep': '12'},
            {'name': 'c', 'sheep': '0'},
        ]
        rhs = [
            {'name': 'a', 'sheep': '7'},
            {'name': 'c', 'sheep': '2'},
            {'name': 'd', 'sheep': '8'},
        ]

        diff = csvdiff.diff_records(lhs, rhs, ['name'])
        assert patch.is_valid(diff)
        assert not patch.is_typed(diff)

        # check the contents of the diff
        self.assertEqual(diff['added'], [
            {'name': 'd', 'sheep': '8'}
        ])
        self.assertEqual(diff['removed'], [
            {'name': 'b', 'sheep': '12'}
        ])
        self.assertEqual(diff['changed'], [
            {'key': ['c'],
             'fields': {'sheep': {'from': '0', 'to': '2'}}}
        ])

        # check that we can apply the diff
        patched = csvdiff.patch_records(diff, lhs)
        self.assertRecordsEqual(rhs, patched)

    def test_diff_records_nonstr_values(self):
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
        assert patch.is_valid(diff)
        assert patch.is_typed(diff)

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

        # check that we can apply the diff
        patched = csvdiff.patch_records(diff, lhs)
        self.assertRecordsEqual(rhs, patched)

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
        assert patch.is_valid(diff)
        assert patch.is_typed(diff)

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

        # check that we can apply the diff
        patched = csvdiff.patch_records(diff, lhs)
        self.assertRecordsEqual(rhs, patched)

    def test_patch_schema_is_valid(self):
        assert not patch.is_valid({})

    def test_patch_cmd_valid_args(self):
        result = self.patch_cmd('-i', self.diff_file, self.a_file)
        self.assertEqual(result.exit_code, 0)

        with open(self.b_file) as istream:
            expected = list(csv.DictReader(istream))

        self.assertRecordsEqual(result.records, expected)

    def test_patch_cmd_fails_when_json_is_invalid(self):
        result = self.patch_cmd('-i', self.a_file, self.a_file)
        self.assertEqual(result.exit_code, 2)
        assert 'ERROR' in result.output

    def test_patch_cmd_fails_when_json_doesnt_match_schema(self):
        result = self.patch_cmd('-i', self.bad_diff_file, self.a_file)
        self.assertEqual(result.exit_code, 2)
        assert 'ERROR' in result.output

    def test_patch_add(self):
        orig = [
            {'name': 'a', 'type': '1', 'sheep': '7'},
        ]
        diff = {
            '_index': ['name'],
            'added': [{'name': 'b', 'type': '1', 'sheep': '9'}],
            'changed': [],
            'removed': [],
        }
        expected = [
            {'name': 'a', 'type': '1', 'sheep': '7'},
            {'name': 'b', 'type': '1', 'sheep': '9'},
        ]
        self.assertRecordsEqual(patch.apply(diff, orig), expected)

    def test_patch_remove(self):
        orig = [
            {'name': 'a', 'type': '1', 'sheep': '7'},
        ]
        diff = {
            '_index': ['name'],
            'added': [],
            'changed': [],
            'removed': [{'name': 'a', 'type': '1', 'sheep': '7'}],
        }
        expected = []
        self.assertRecordsEqual(patch.apply(diff, orig), expected)

    def test_patch_change(self):
        orig = [
            {'name': 'a', 'type': '1', 'sheep': '7'},
        ]
        diff = {
            '_index': ['name'],
            'added': [],
            'changed': [{'key': ['a'], 'fields': {'sheep': {'from': '7',
                                                            'to': '8'}}}],
            'removed': [],
        }
        expected = [
            {'name': 'a', 'type': '1', 'sheep': '8'},
        ]
        self.assertRecordsEqual(patch.apply(diff, orig), expected)

    def test_almost_equal(self):
        assert patch._almost_equal(1., 1., 10)
        assert not patch._almost_equal(1., 2., 10)
        assert patch._almost_equal(1.1, 1.2, 0)
        assert not patch._almost_equal(1.1, 1.2, 1)

    def assertPatchesEqual(self, lhs, rhs):
        self.assertEqual(lhs['_index'], rhs['_index'])
        self.assertRecordsEqual(lhs['added'], rhs['added'])
        self.assertRecordsEqual(lhs['removed'], rhs['removed'])
        self.assertChangesEqual(lhs['changed'], rhs['changed'])

    def assertRecordsEqual(self, lhs, rhs):
        self.assertEqual(records.sort(lhs), records.sort(rhs))

    def assertChangesEqual(self, lhs, rhs):
        self.assertEqual(sorted(lhs, key=lambda r: r['key']),
                         sorted(rhs, key=lambda r: r['key']))

    def tearDown(self):
        pass


@contextmanager
def tmp_csv_files(*args):
    files = []
    for arg in args:
        t = tempfile.NamedTemporaryFile()
        save_as_csv(arg, t.name)
        files.append(t)

    yield [f.name for f in files]


def save_as_csv(records, filename):
    with open(filename, 'w') as ostream:
        header = sorted(records[0].keys())

        writer = csv.DictWriter(ostream, header)

        writer.writerow(dict(zip(header, header)))
        for record in records:
            writer.writerow(record)


if __name__ == '__main__':
    unittest.main()
