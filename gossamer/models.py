# -*- coding: utf-8 -*-
from tornado.httpclient import AsyncHTTPClient, HTTPResponse, HTTPRequest
#from tornado.ioloop import IOLoop
from tornado import gen
from lxml import etree
import functools
import os
import re
from cStringIO import StringIO

class Silk(object):
    """
    Core of the gossamer library. Is in charge of:
    - Parsing start pages (i.e. those given by the `start_urls` variable)
    - Spawning child strands (based on `strands` variable)
    - Rate limiting all external fetch requests (based_on )
    - Returning 

    However, it is not in charge of starting the main event loop and is only passed the
    pre-made processes event loop singleton, which is .start()ed externally to the class.
    
      "The advent of computers, and the subsequent accumulation of incalculable data
       has given rise to a new system of memory and thought parallel to your own. Humanity
       has underestimated the consequences of computerization."
         - Puppet Master
    """
    current_dir = os.getcwd()

    
    def __init__(self, loop, debug=False, save_directory='debug_html_files',
                 start_urls=[], allowed_domains=None, fail_silent=True):
        self.fail_silent = fail_silent
        
        if allowed_domains:
            domains = [d.replace('.', r'\.') for d in allowed_domains]
            self.domain_regex = re.compile(r'(.*\.)?(%s)' % '|'.join(domains))
        else:
            self.domain_regex = re.compile(r'')
            
        self.loop = loop
        self.client = AsyncHTTPClient(self.loop)
        self.debug = debug
        if os.path.isabs(save_directory):
            self.save_directory = save_directory
        else:
            self.save_directory = os.path.join(self.current_dir, save_directory)
            
            
    def stop(self):
        """
        Stops the event loop provided when the Silk() instance was created.
        
        Returns True.
        
          "Life perpetuates itself through diversity and this includes the ability to
           sacrifice itself when necessary."
             - Puppet Master
        """
        self.loop.stop()
        return True
        

    @gen.engine
    def get(self, url, callback):
        """
        Takes a target `url` and `callback` function. Asynchronously fetches the `url` and
        returns a tornado.httpclient.HTTPResponse object to the `callback` function.

        If a allowed_domains is set and a url fails to match the domain name, the function will
        either return an empty response with response code 418, or raise ExternalDomainError(),
        depending on whether fail_silent was True in the Silk() instatiation.
        
        If debug was set when the Silk object was created, this function will attempt to
        retrieve the html file from the local disk, and if not found will fetch the remote
        resource at `url`, save the received response body to disk (at a location
        determined by the `self.save_directory` variable)and continue to call the
        `callback` function with the tornado.httpclient.HTTPResonse object. In this way, fast
        iteration of scraping logic can be implemented using locally saved html objects, rather
        than continually requesting the same resources from the remote server.
        
          "That's all it is. Information."
            - BatÙ

        """
        if self.domain_regex.search(url):
            if self.debug:
                local_file = yield gen.Task(self.get_local_file, url)
                if local_file:
                    callback(local_file)
                else:
                    self.fetch_and_save(url, callback)
            else:
                self.client.fetch(url, callback)
        elif not self.fail_silent:
            raise ExternalDomainError(url)
        else:
            fake_request = HTTPRequest(url)
            buffer = StringIO()
            buffer.write('')
            response = HTTPResponse(fake_request, 418, buffer=buffer)
            callback(response)
            
            
    def _local_file_name(self, url):
        # shorten long urls
        if len(url) > 40:
            url = url[:20] + url[-20:]
        file_name= url.replace('/','_')+ '.html'
        file_path = os.path.join(self.save_directory, file_name)
        return file_path

        
    def get_local_file(self, url, callback):
        file_path = self._local_file_name(url)
        try:
            local_file_contents = open(file_path,'rb').read()
            fake_request = HTTPRequest(url)
            buffer = StringIO()
            buffer.write(local_file_contents)
            response = HTTPResponse(fake_request, 200, buffer=buffer)
            callback(response)
        except IOError:
            callback(None)
            
        
    def delete_local_file(self, url, callback=None):
        file_path = self._local_file_name(url)
        os.remove(file_path)
        if callback:
            callback()
        
    @gen.engine
    def fetch_and_save(self, url, callback):
        file_path = self._local_file_name(url)
        data = yield gen.Task(self.client.fetch, url)
        if not os.path.exists(self.save_directory):
            os.mkdir(self.save_directory)
            
        with open(file_path,'w') as html_file:
            html_file.write(data.body)
            html_file.close()
        callback(data)


    def parse(self, xpath, url, callback):
        """
        Async function that returns a list of matched xpath elements from url to callback.

          "Any way you look at it, all the information that a person accumulates in a
           lifetime is just a drop in the bucket."
             - BatÙ
        """
        def _parse(xpath, callback, response):
            html_tree = etree.HTML(response.body)
            callback(html_tree.xpath(xpath))
        p = functools.partial(_parse, xpath ,callback)
        self.get(url, p)

    def run_strands(self):
        """

        
          "Each of those things are just a small part of it. I collect information to use in my
           own way. All of that blends to create a mixture that forms me and gives rise to
           my conscience."
            - Major Motoko Kusanagi
        """


class Strand(object):
    """
    Calling pattern:
    
    Strand(allow, deny, regex, depth, callback)
    
    An instance of Silk() can have multiple Strands(), each Strand() may, in turn, have
    multiple Strands(). A Strand has a single regular expression that it attempts to match
    to the html that 

    For each strand to be used, it must know:
       a) who its parent object is (whether Silk() or Strand())
       b) what regular expressions it should be detecting within a html document
       c) what the html document is that it should be parsing
    
    Each Strand is expecting to be passed some well formatted html from its parent Strand
    or Silk instance.

        "And where does the newborn go from here? The net is vast and infinite. "
            - Major Motoko Kusanagi, Puppet Master
    """    
    def __init__(self):
        pass


class ExternalDomainError(Exception):
    def __init__(self, url):
        Exception.__init__(self, "Access outside of allowed_domains attempted: %s"%url)
    

