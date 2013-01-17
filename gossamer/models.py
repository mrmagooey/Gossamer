
from tornado.httpclient import AsyncHTTPClient
from tornado.ioloop import IOLoop
from tornado import gen
from lxml import etree
import functools
import os


class Silk(object):
    current_dir = os.getcwd()
    local_loop = IOLoop.instance()
    
    
    def setup(self, loop=local_loop, debug=False, save_directory='debug_html_files'):
        self.loop = loop.instance()
        self.client = AsyncHTTPClient(loop)
        
        self.debug = debug
        if os.path.isabs(save_directory):
            self.save_directory = save_directory
        else:
            self.save_directory = os.path.join(self.current_dir, save_directory)
            
        if loop is self.local_loop:
            loop.start()
            
            
    @gen.engine
    def get(self, url, callback):
        if self.debug:
            # check if a local copy of url exists
            local_file = yield gen.Task(self.get_local_file, url)
            # if so, get the local copy and pass it to callback
            if local_file:
                callback(local_file)
            else:
                # if not, fetch the url, save a local copy and pass the response to callback
                callback(self.fetch_and_save_local_file(url))

        else:
            self.client.fetch(url, callback)
            
            
    def _local_file_name(self, url):
        # shorten long urls
        if len(url) > 40:
            url = url[:20] + url[-20:]
        file_name= url.replace('/','_')+ '.html'
        file_path = os.path.join(self.save_directory, file_name)
        return file_path

        
    def get_local_file(self, url):
        file_path = self._local_file_name(url)
        return open(file_path,'rb').read()

    def delete_local_file(self, url):
        file_path = self._local_file_name(url)
        try:
            os.remove(file_path)
            return True
        except IOError:
            return False

        
    @gen.engine
    def fetch_and_save(self, url, callback):
        file_path = self._local_file_name(url)
        data = yield gen.Task(self.client.fetch, url)
        if not os.path.exists(self.save_directory):
            os.mkdir(self.save_directory)
        open(file_path,'wb').write(data.body)
        callback(data)


    def parse(self, xpath, url, callback):
        """
        Async function that returns a list of matched xpath elements from url to callback.
        """
        def _parse(xpath, callback, response):
            html_tree = etree.HTML(response.body)
            callback(html_tree.xpath(xpath))
        p = functools.partial(_parse, xpath ,callback)
        self.get(url, p)







