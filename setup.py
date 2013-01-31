#!/usr/bin/env python

from setuptools import setup

package_requires = ['lxml', 'tornado']

setup(
    name = 'gossamer',
    version = '0.1.2',
    description="Simple Python Scraper",
    packages=['gossamer'],
    requires = package_requires,
)