===============================
csvdiff
===============================

.. image:: https://badge.fury.io/py/csvdiff.png
    :target: http://badge.fury.io/py/csvdiff

.. image:: https://travis-ci.org/larsyencken/csvdiff.png?branch=master
        :target: https://travis-ci.org/larsyencken/csvdiff

.. image:: https://pypip.in/d/csvdiff/badge.png
        :target: https://crate.io/packages/csvdiff

Overview
--------

Generate a diff between two CSV files on the command-line.

Installing
----------

``pip install csvdiff``

Examples
--------

For example, suppose we have ``a.csv``::

    id,name,amount
    1,bob,20
    2,eva,63
    3,sarah,7
    4,jeff,19
    6,fred,10

and a matching file after some changes, ``b.csv``::

    id,name,amount
    1,bob,23
    3,sarah,7
    4,jeff,19
    5,mira,81
    6,fred,13

Now we can ask for a summary of differences::

    $ csvdiff --style=summary id a.csv b.csv
    1 rows removed (20.0%)
    1 rows added (20.0%)
    2 rows changed (40.0%)

Or look at the full diff pretty printed, to make it more readable::

    $ csvdiff --style=pretty id a.csv b.csv
    {
      "added": [
        {
          "amount": "81",
          "id": "5",
          "name": "mira"
        }
      ],
      "changed": [
        {
          "fields": {
            "amount": {
              "from": "20",
              "to": "23"
            }
          },
          "key": [
            "1"
          ]
        },
        {
          "fields": {
            "amount": {
              "from": "10",
              "to": "13"
            }
          },
          "key": [
            "6"
          ]
        }
      ],
      "removed": [
        {
          "amount": "63",
          "id": "2",
          "name": "eva"
        }
      ]
    }

It gives us the full listing of added and removed rows, as well as a listing of what fields changed for that shared a key.

For more usage options, run ``csvdiff --help``.

License
-------

BSD license
