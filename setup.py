#!/usr/bin/env python

from distutils.core import setup
requires = ['lxml']

setup(
    name = 'gossamer',
    version = '0.1.2',
    description="Simple Python Scraper",
    packages=['gossamer'],
    install_requires = requires,
)