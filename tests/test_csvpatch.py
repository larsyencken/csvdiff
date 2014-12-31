# -*- coding: utf-8 -*-
#
#  test_csvpatch.py
#  csvdiff
#

from __future__ import absolute_import, print_function, division

import os
from os import path
import unittest
import json
import tempfile
from io import StringIO  # noqa

import csvdiff
from csvdiff import patch

from click.testing import CliRunner


class TestCsvpatch(unittest.TestCase):
    def setUp(self):
        csvdiff.DEBUG = True
        self.examples = path.join(path.dirname(__file__), 'examples')
        self.a_file = path.join(self.examples, 'a.csv')
        self.b_file = path.join(self.examples, 'b.csv')
        self.runner = CliRunner()

    def main(self, *args):
        t = tempfile.NamedTemporaryFile(delete=True)
        result = self.runner.invoke(csvdiff.patch, ('--output', t.name) + args)
        diff = None
        if path.exists(t.name) and os.stat(t.name).st_size:
            with open(t.name) as istream:
                diff = json.load(istream)

        return result.exit_code, diff

    def test_schema_is_valid(self):
        assert not patch.is_valid({})

    def test_apply_patch(self):
        pass

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
