from setuptools import setup
requires = ['lxml', 'urllib2']

setup(
    name = 'gossamer',
    version = '0.1',
    url="https://github.com/mrmagooey/Gossamer",
    author="Peter Davis",
    description="Simple Python Scraper",
    packages=['gossamer'],
    install_requires = requires,
)