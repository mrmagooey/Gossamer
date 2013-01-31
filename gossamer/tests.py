from models import Silk, Spider, ExternalDomainError
import re
import tornado.web
from tornado.ioloop import IOLoop
from tornado.testing import AsyncTestCase
from tornado.httpclient import HTTPResponse
from tornado.httpserver import HTTPServer
from lxml.etree import XPathEvalError
import multiprocessing
import SimpleHTTPServer
import SocketServer
import os

LOCAL_PORT = 8888
LOCAL_URL = 'http://127.0.0.1:%s/%s'

class TestSilk(AsyncTestCase):
    
    @classmethod
    def setUpClass(cls):
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        def quiet_log(self, format, *args):
            return
        Handler.log_message = quiet_log
        current_dir = os.getcwd()
        os.chdir(os.path.join(current_dir, 'test_html'))
        httpd = SocketServer.TCPServer(("", LOCAL_PORT), Handler)
        cls.p = multiprocessing.Process(target=httpd.serve_forever)
        cls.p.start()
        os.chdir(current_dir)
    
    
    @classmethod
    def tearDownClass(cls):
        cls.p.terminate()

        
    def test_can_create_silk_instance(self):
        Silk(self.io_loop)
        
        
    def test_simplehttpserver(self):
        s = Silk(self.io_loop)
        s.get(LOCAL_URL%(LOCAL_PORT,'/'), self.stop)
        response = self.wait()
        self.assertEqual(response.code, 200)
        s.get(LOCAL_URL%(LOCAL_PORT,'thisdoesnotexist.html'),self.stop)
        response = self.wait()
        self.assertEqual(response.code, 404)

        
    def test_start(self):
        s = Silk()
        s.loop = IOLoop.instance()
        s.start()

        
    def test_get(self):
        s = Silk(self.io_loop)
        s.get(LOCAL_URL%(LOCAL_PORT,'index.html'),self.stop)
        response = self.wait()
        self.assertIn("Test paragraph", response.body)

        
    def test_local_file_storage(self):
        s = Silk(self.io_loop)
        s.fetch_and_save(LOCAL_URL%(LOCAL_PORT,'index.html'), self.stop)
        response = self.wait()
        s.get_local_file(LOCAL_URL%(LOCAL_PORT,'index.html'), self.stop)
        local_file = self.wait()
        self.assertEqual(response.body, local_file.body)
        s.delete_local_file(LOCAL_URL%(LOCAL_PORT,'index.html'))
        
        
    def test_parse_url(self):
        s = Silk(self.io_loop)
        s.parse_url('//text()', LOCAL_URL%(LOCAL_PORT,'index.html'), self.stop)
        xpath_elements = self.wait()
        self.assertTrue(type(xpath_elements=='list'))
        
        
    def test_parse(self):
        s = Silk(self.io_loop)
        s.get(LOCAL_URL%(LOCAL_PORT,'index.html'), self.stop)
        response = self.wait()
        s.parse('//text()', response, self.stop)
        xpath_elements = self.wait()
        self.assertTrue(type(xpath_elements=='list'))
        text_string = ''.join(xpath_elements)
        self.assertIn('test',text_string)

        
    def test_incorrect_parse_xpath(self):
        s = Silk(self.io_loop)
        s.parse_url('//count()',LOCAL_URL%(LOCAL_PORT,'index.html'), self.stop)
        try:
            self.wait()
        except XPathEvalError:
            pass

        
    def test_debug_setting(self):
        """
        Test that with debug=True that files are being saved to the local disk.
        """
        s = Silk(self.io_loop, debug=True)
        s.get(LOCAL_URL%(LOCAL_PORT,'index.html'), self.stop)
        response = self.wait()
        s.get_local_file(LOCAL_URL%(LOCAL_PORT,'index.html'), self.stop)
        cached_response = self.wait()
        self.assertEqual(response.body, cached_response.body)
        s.delete_local_file(LOCAL_URL%(LOCAL_PORT,'index.html'))


    def test_domains_single_domain(self):
        domains = [
            '127.0.0.1:%s'%(LOCAL_PORT),
        ]
        
        s = Silk(self.io_loop, allowed_domains=domains)
        s.get(LOCAL_URL%(LOCAL_PORT,'index.html'), self.stop)
        response = self.wait()
        self.assertIn("test paragraph", response.body)
        
        s.get('http://google.com', self.stop)
        response = self.wait()
        self.assertEqual(response.body, '') # Silently fails and returns an empty body

        
    def test_subdomain(self):
        domains = [
            'www.google.com',
        ]
        
        s = Silk(self.io_loop, allowed_domains=domains)
        s.get('http://google.com', self.stop)
        response = self.wait()
        self.assertEqual(len(response.body), 0)
        
        s = Silk(self.io_loop, allowed_domains=domains)
        s.get('http://www.google.com', self.stop)
        response = self.wait()
        self.assertIn('google', response.body)

        
    def test_multiple_domains(self):
        domains = [
            'www.dmoz.org',
            'www.google.com',
        ]
        
        s3 = Silk(self.io_loop, allowed_domains=domains)
        s3.get('http://www.dmoz.org', self.stop)
        response = self.wait()
        self.assertIn("dmoz", response.body)
        s3.get('http://www.google.com', self.stop)
        response = self.wait()
        self.assertIn("Google", response.body)


    def test_domains_fail_loudly(self):
        domains = [
            'www.dmoz.org',
        ]

        s = Silk(self.io_loop, allowed_domains=domains, fail_silent=False)
        s.get('http://www.dmoz.org', self.stop)
        response = self.wait()
        self.assertIn("dmoz", response.body)
        try:
            s.get('http://google.com', self.stop)
            self.wait()
        except ExternalDomainError as ex:
            self.assertEquals(type(ExternalDomainError('')), type(ex))

            
    def test_add_requests(self):
        domains = [
            'www.dmoz.org',
        ]
        s = Silk(self.io_loop, allowed_domains=domains, fail_silent=False)
        s.add_request('http://www.dmoz.org/Computers/Programming/Languages/Python/Books/',
                       self.stop)
        response = self.wait()
        self.assertIn('dmoz', response.body)
        s.add_request('http://www.dmoz.org/Computers/Programming/Languages/Python/Books/',
                       self.stop)
        response = self.wait()
        self.assertIn('dmoz', response.body)

        
    def test_change_request_rate(self):
        raise Exception("no immediate idea how to test this")
            

class TestSpider(AsyncTestCase):
    @classmethod
    def setUpClass(cls):
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        def quiet_log(self, format, *args):
            return
        Handler.log_message = quiet_log
        current_dir = os.getcwd()
        os.chdir(os.path.join(current_dir, 'test_html'))
        httpd = SocketServer.TCPServer(("", LOCAL_PORT), Handler)
        cls.p = multiprocessing.Process(target=httpd.serve_forever)
        cls.p.start()
        os.chdir(current_dir)
    
    
    @classmethod
    def tearDownClass(cls):
        cls.p.terminate()
        
        
    def test_can_create_spider_instance(self):
        Spider()
        allow_regex = [r'Python',r'Ruby']
        deny_regex = [r'Deutsch']
        Spider(allow_regex, deny_regex, callback=None)
        

    def test_can_register_spiders(self):
        spider1 = Spider()
        spider2 = Spider()
        s = Silk(self.io_loop)
        s.register(spider1)
        s.register(spider2)
        self.assertIn(spider1, s.spiders)
        self.assertIn(spider2, s.spiders)

        
    def test__find_urls(self):
        s = Silk(self.io_loop, allowed_domains=['www.dmoz.org'], fail_silent=False)
        s.get(LOCAL_URL%(LOCAL_PORT,'index.html'), self.stop)
        response = self.wait()
        spider = Spider()
        spider._find_urls(response, self.stop)
        links = self.wait()
        self.assertIn(['http://www.google.com',
                       'page1.html'], links)

        
    def test__crawl(self):
        spider = Spider()
        s = Silk(self.io_loop, allowed_domains=[''])
        s.register(spider)
        s.crawl(LOCAL_URL%(LOCAL_PORT,'index.html'), self.stop)
        
        
    def test_spider_prints_urls_without_callback(self):
        allow_regex = ['Python','Ruby']
        deny_regex = ['Deutsch']
        
        spider1 = Spider(allow_regex, deny_regex, callback=None)
        s = Silk(self.io_loop, allowed_domains=['www.dmoz.org'], fail_silent=False)
        s.register(spider1)
        s.crawl('http://www.dmoz.org/Computers/Programming/Languages/Python/Books/',
                self.stop)
        response = self.wait()
        
        
