#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='csvdiff',
    version='0.1.0',
    description='Generate a diff between two CSV files.',
    long_description=readme + '\n\n' + history,
    author='Lars Yencken',
    author_email='lars@yencken.org',
    url='https://github.com/larsyencken/csvdiff',
    packages=[
        'csvdiff',
    ],
    package_dir={'csvdiff': 'csvdiff'},
    entry_points={
        'console_scripts': [
            'csvdiff = csvdiff:main',
        ],
    },
    include_package_data=True,
    install_requires=[
    ],
    license="BSD",
    zip_safe=False,
    keywords='csvdiff',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
    test_suite='tests',
)
