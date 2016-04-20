.. :changelog:

History
-------

dev
~~~

* Add the --sep option for different delimiters.

0.3.1 (2016-04-20)
~~~~~~~~~~~~~~~~~~

* Fix a bug in summary mode.
* Check for rows bleeding into one another.

0.3.0 (2015-01-07)
~~~~~~~~~~~~~~~~~~

* Standardise patch format with a JSON schema.
* Provide a matching csvpatch command applying diffs.
* Add a man page and docs for csvpatch.
* Use exit codes to indicate difference.
* Add a --quiet option to csvdiff.

0.2.0 (2014-12-30)
~~~~~~~~~~~~~~~~~~

* Uses click for the command-line interface.
* Drop YAML support in favour of pretty-printed JSON.
* Uses --style option to change output style.
* Provides a full man page.

0.1.0 (2014-03-15)
~~~~~~~~~~~~~~~~~~

* First release on PyPI.
* Generates a JSON or YAML difference between two CSV files
* Specify multiple key components with ``-k``
* Can provide a difference summary
* Assumes files use standard comma-separation, double-quoting and a header row with field names
