#!/usr/bin/env python

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

requires = [
        'atom',
        'enaml',
        'BTSync',
    ]

dependency_links=[
    "https://github.com/ademan/python-btsync/archive/packaging.zip#egg=BTSync",
    ]

setup(name='syncnet',
    version='0.0.1',
    description='Encrypted, distributed web.',
    long_description=README,
    classifiers=[
      "Programming Language :: Python",
      ],
    packages=find_packages(),
    package_data={
        'syncnet': ['*.enaml'],
    },
    install_requires=requires,
    dependency_links=dependency_links,
    )
