# -*- coding: utf-8 -*-
from tornado.httpclient import AsyncHTTPClient, HTTPResponse, HTTPRequest
#from tornado.ioloop import IOLoop
from tornado import gen, ioloop

from lxml import html
import functools
import os
import re
from cStringIO import StringIO
import datetime
import Queue

class Silk(object):
    """
    Core of the gossamer library. Is in charge of:
    - Parsing start pages (i.e. those given by the `start_urls` variable)
    - Spawning spiders (based on `spiders` variable)
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
                 start_urls=[], allowed_domains=None, fail_silent=True, max_requests=10):
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

        self.max_requests = max_requests

        self._request_queue = Queue.Queue()
        fetch_task = ioloop.PeriodicCallback(self._fetch,
                                      1.0/self.max_requests*1000,
                                      self.loop)
        fetch_task.start()

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

    def _fetch(self):
        try:
            request_tuple = self._request_queue.get(block=False)
            url = request_tuple[0]
            callback = request_tuple[1]
        except Queue.Empty:
            return None
        except IndexError:
            raise Exception("Incorrect request tuple passed to add_requests(), correct form is \
                            (url, callback)")
        self.client.fetch(url, callback)


    def add_request(self, url, callback):
        self._request_queue.put((url,callback))


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
                self.add_request(url, callback)
        elif not self.fail_silent:
            raise ExternalDomainError(url)
        else:
            fake_request = HTTPRequest(url)
            buffer = StringIO()
            buffer.write('')
            response = HTTPResponse(fake_request, 418, buffer=buffer)
            callback(response)

    @gen.engine
    def _crawl(self, url, callback):
        """
        Takes urls from Spiders and passes the fetched urls back to the list of Spiders

        """

    @gen.engine
    def crawl(self, url, callback=None):
        """
        get() html from url
        If callback provided then the silk instance calls the callback on the starting url.

        call parse
        Pass it to the registered children strands
        """
        response = yield gen.Task(self.get, url)
        if self.spiders:
            for spider in self.spiders:
                spider._crawl(response)


    def _local_file_name(self, url):

        if len(url) > 40: # shorten long urls
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
        def _save(data, callback):
            file_path = self._local_file_name(url)
            if not os.path.exists(self.save_directory):
                os.mkdir(self.save_directory)
            with open(file_path,'w') as html_file: # blocking
                html_file.write(data.body)
                html_file.close()
            callback(data)
        callback_partial = functools.partial(_save, callback=callback)
        self.add_request(url, callback_partial)


    def parse(self, xpath=None, httpresponse=None, callback=None):
        """
        Returns a list of matched `xpath` elements in `httpresponse` to `callback`.

          "Any way you look at it, all the information that a person accumulates in a
           lifetime is just a drop in the bucket."
             - BatÙ
        """
        html_tree = html.document_fromstring(httpresponse.body)
        callback(html_tree.xpath(xpath))


    def parse_url(self, xpath, url, callback):
        """
        Async function that returns a list of matched xpath elements from url to callback.
        """
        parse_partial = functools.partial(self.parse, xpath, callback=callback)
        self.get(url, parse_partial)


    def register(self, spider):
        """
        Takes either a single spider object, or an iterable of spider objects

          "Each of those things are just a small part of it."
            - Major Motoko Kusanagi
        """
        spider.silk = self
        try:
            self.spiders.append(spider)
        except AttributeError:
            self.spiders = [spider]




class Spider(object):
    """
    An instance of Silk() can have multiple Spiders(), each Spider() may, in turn, have
    multiple Spiders(). A Spider has a single regular expression that it attempts to match
    to the html that

    For each spider to be used, it must know:
       a) who its parent object is (whether Silk() or Spider())
       b) what regular expressions it should be detecting within a html document
       c) what the html document is that it should be parsing

    Each Spider is expecting to be passed some well formatted html from its parent Spider
    or Silk instance.

    """

    IGNORED_EXTENSIONS = [
        # images
        'mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif',
        'tiff', 'ai', 'drw', 'dxf', 'eps', 'ps', 'svg',

        # audio
        'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff',

        # video
        '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'rm', 'swf', 'wmv',
        'm4a',

        # office suites
        'xls', 'ppt', 'doc', 'docx', 'odt', 'ods', 'odg', 'odp',

        # other
        'css', 'pdf', 'doc', 'exe', 'bin', 'rss', 'zip', 'rar',
    ]

    def __init__(self, allow_regex=[], deny_regex=[], html_only=True,
                 follow=False, callback=None):
        """

        "And where does the newborn go from here? The net is vast and infinite."
            - Major Motoko Kusanagi, Puppet Master
        """
        if len(allow_regex) == 0:
            allow_regex = [''] # match everything
        if len(deny_regex) == 0:
            deny_regex = ['%%'] # match nothing (%% is url unsafe and shouldn't be found)
        self.allow_regex = [re.compile(regex) for regex in allow_regex]
        self.deny_regex = [re.compile(regex) for regex in deny_regex]
        self.html_only = html_only
        self.follow = follow
        self.callback = callback

        self.silk = None # set by Silk instance when register() called


    def _find_urls(self, httpresponse, callback):
        """
        Identifies urls in `httpresponse` and provides links that satisfy `allow_regex` and
        `deny_regex` and returns them as a list to the `callback`.

        """
        links=[]
        for link_tuple in html.iterlinks(httpresponse.body):
            link = link_tuple[2]
            if self.html_only:
                try:
                    link_extension = link.split('.')[-1]
                    if link_extension in self.IGNORED_EXTENSIONS:
                        continue
                except IndexError:
                    pass
            if all([re_allow.search(link) for re_allow in self.allow_regex]) and not\
               all([re_deny.search(link) for re_deny in self.deny_regex]):
                links.append(link)
        callback(links)

    @gen.engine
    def _crawl(self, httpresponse, callback):
        links = yield gen.Task(self._find_urls, httpresponse)
        if self.follow == True:
            self.silk.add_request(links)
        callback(links)



class ExternalDomainError(Exception):
    def __init__(self, url):
        Exception.__init__(self, "Access outside of allowed_domains attempted: %s"%url)


