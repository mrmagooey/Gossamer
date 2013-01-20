from models import Silk, Strand, ExternalDomainError
import re
from tornado.testing import AsyncTestCase
from tornado.httpclient import HTTPResponse


class TestSilk(AsyncTestCase):
    def test_can_create_silk_instance(self):
        s = Silk(self.io_loop)
        s.stop()
        
    def test_can_get_page(self):
        s = Silk(self.io_loop)
        s.get('http://www.google.com', self.stop)
        response = self.wait()
        self.assertIn("Google", response.body)
        
        
    def test_can_parse(self):
        s = Silk(self.io_loop)
        s.parse('//text()','http://www.google.com', self.stop)
        xpath_elements = self.wait()
        self.assertTrue(type(xpath_elements=='list'))
        
        
    def test_local_file_storage(self):
        s = Silk(self.io_loop)
        s.fetch_and_save('http://www.google.com', self.stop)
        response = self.wait()
        s.get_local_file('http://www.google.com', self.stop)
        local_file = self.wait()
        self.assertEqual(response.body, local_file.body)
        s.delete_local_file('http://www.google.com')
        
        
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
        except ExternalDomainError as ex:
            self.assertEquals(type(ExternalDomainError('')), type(ex))
        
        
class TestStrand(AsyncTestCase):
    def test_can_create_strand_instance(self):
        allow_regex = r''
        st = Strand()
        st # stop flymake complaining
        
    def test_can_attach_strand_to_silk(self):
        s = Silk(self.io_loop)
        st = Strand()
        url = r'google'
        st

