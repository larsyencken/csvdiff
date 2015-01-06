# -*- coding: utf-8 -*-
#
#  error.py
#  csvdiff
#

from __future__ import absolute_import, print_function, division

import sys

DEBUG = False


class FatalError(Exception):
    pass


def abort(message=None):
    if DEBUG:
        raise FatalError(message)

    print(message, file=sys.stderr)
    sys.exit(1)
