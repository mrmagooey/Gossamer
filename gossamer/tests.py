from models import Silk, Spider, ExternalDomainError
import re
from tornado.testing import AsyncTestCase
from tornado.httpclient import HTTPResponse
from lxml.etree import XPathEvalError

class TestSilk(AsyncTestCase):
    def test_can_create_silk_instance(self):
        s = Silk(self.io_loop)
        s.stop()

        
    def test_get(self):
        s = Silk(self.io_loop)
        s.get('http://www.google.com', self.stop)
        response = self.wait()
        self.assertIn("Google", response.body)

        
    def test_local_file_storage(self):
        s = Silk(self.io_loop)
        s.fetch_and_save('http://www.google.com', self.stop)
        response = self.wait()
        s.get_local_file('http://www.google.com', self.stop)
        local_file = self.wait()
        self.assertEqual(response.body, local_file.body)
        s.delete_local_file('http://www.google.com')
        
        
    def test_parse_url(self):
        s = Silk(self.io_loop)
        s.parse_url('//text()','http://www.google.com', self.stop)
        xpath_elements = self.wait()
        self.assertTrue(type(xpath_elements=='list'))
        
        
    def test_parse(self):
        s = Silk(self.io_loop)
        s.get('http://www.google.com', self.stop)
        response = self.wait()
        s.parse('//text()', response, self.stop)
        xpath_elements = self.wait()
        self.assertTrue(type(xpath_elements=='list'))
        text_string = ''.join(xpath_elements)
        self.assertIn('google',text_string)

        
    def test_incorrect_parse_xpath(self):
        s = Silk(self.io_loop)
        s.parse_url('//count()','http://www.google.com', self.stop)
        try:
            self.wait()
        except XPathEvalError:
            pass

        
    def test_debug_setting(self):
        """
        Test that with debug=True that files are being saved to the local disk.
        """
        s = Silk(self.io_loop, debug=True)
        s.get('http://www.google.com', self.stop)
        response = self.wait()
        s.get_local_file('http://www.google.com', self.stop)
        cached_response = self.wait()
        self.assertEqual(response.body, cached_response.body)
        s.delete_local_file('http://www.google.com')


    def test_restrict_scraping_domains(self):
        domains = [
            'www.dmoz.org',
        ]

        s = Silk(self.io_loop, allowed_domains=domains)
        s.get('http://www.dmoz.org', self.stop)
        response = self.wait()
        self.assertIn("dmoz", response.body)

        s.get('http://google.com', self.stop)
        response = self.wait()
        self.assertEqual(response.body, '')

        domains2 = [
            'www.google.com',
        ]

        s2 = Silk(self.io_loop, allowed_domains=domains2)
        s2.get('http://www.dmoz.org', self.stop)
        response = self.wait()
        self.assertEqual(len(response.body), 0)

        s2.get('http://google.com', self.stop)
        response = self.wait()
        self.assertEqual(len(response.body), 0)

        domains3 = [
            'www.dmoz.org',
            'www.google.com',
        ]

        s3 = Silk(self.io_loop, allowed_domains=domains3)
        s3.get('http://www.dmoz.org', self.stop)
        response = self.wait()
        self.assertIn("dmoz", response.body)

        s3.get('http://www.google.com', self.stop)
        response = self.wait()
        self.assertIn("Google", response.body)


    def test_restrict_scraping_domains_fail_loudly(self):
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
        
            

class TestSpider(AsyncTestCase):

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

        
    def test_find_urls(self):
        s = Silk(self.io_loop, allowed_domains=['www.dmoz.org'], fail_silent=False)
        s.get('http://www.dmoz.org/Computers/Programming/Languages/Python/Books/', self.stop)
        response = self.wait()
        spider = Spider()
        spider._find_urls(response, self.stop)
        links = self.wait()
        self.assertTrue(len(links) > 0)
        
    def test_crawl(self):
        spider = Spider()
        s = Silk(self.io_loop, allowed_domains=['www.dmoz.org'])
        s.register(spider)
        s.crawl('http://www.dmoz.org/Computers/Programming/Languages/Python/Books/',
                self.stop)
        
        
    def test_spider_prints_urls_without_callback(self):
        allow_regex = ['Python','Ruby']
        deny_regex = ['Deutsch']
        
        spider1 = Spider(allow_regex, deny_regex, callback=None)
        s = Silk(self.io_loop, allowed_domains=['www.dmoz.org'], fail_silent=False)
        s.register(spider1)
        s.crawl('http://www.dmoz.org/Computers/Programming/Languages/Python/Books/',
                self.stop)

        
        
        
        
