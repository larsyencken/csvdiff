========
csvdiff
========

Synopsis
========

csvdiff [-o OUTPUT.json] [--style=STYLE] INDEXES FILE1.csv FILE2.csv

Description
===========

The **csvdiff** command compares the contents of two CSV files and outputs any differences. The files must be in a standard CSV format, comma-separated with a header row and optional double-quotes around fields. The output is a human-readable JSON patch format. The INDEXES parameter a comma-separated list of fields, constituting a primary key for the files in question.

The options are as follows:

-o OUTPUT       Write the JSON diff to the file OUTPUT instead of stdout.
--style=STYLE   Choose between three output styles ([compact]/pretty/summary).
                The compact and pretty formats output the entire diff;
                summary outputs a count of rows added, removed and changed.

Example
=======

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


Exit status
===========

The **csvdiff** command exits 0 when no difference exists, >0 when a difference exists (or on usage error).

Limitations
===========

- The comparison is insensitive to column order by design; columns need not occur in the same order in both files.
- All fields are untyped and treated as strings.

Bugs
====

The full source is available at https://github.com/larsyencken/csvdiff

Please report bugs to https://github.com/larsyencken/csvdiff/issues
