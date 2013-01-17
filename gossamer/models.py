
from tornado.httpclient import AsyncHTTPClient
from tornado.ioloop import IOLoop
from lxml import etree
import functools

class Silk(object):

    local_loop = IOLoop.instance()

    
    def setup(self,loop=local_loop, debug=False):
        self.loop = loop.instance()
        self.client = AsyncHTTPClient(loop)
        self.debug = debug

    def get(self, url, callback):
        self.client.fetch(url, callback)

        
    def parse(self, xpath, url, callback):
        """
        Async function that returns a list of matched xpath elements from url to callback.
        """
        def _parse(xpath, callback, response):
            html_tree = etree.HTML(response.body)
            callback(html_tree.xpath(xpath))
        p = functools.partial(_parse, xpath ,callback)
        self.get(url, p)

        
    def save(self, response):
        pass

        
        
        
    
