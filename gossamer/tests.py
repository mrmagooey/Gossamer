import unittest
from models import Silk
from tornado.testing import AsyncTestCase

class TestSilk(AsyncTestCase):
    
    def test_can_create_silk_instance(self):
        s = Silk()
        
        
    def test_can_get_page(self):
        s = Silk()
        s.setup(self.io_loop)
        s.get('http://www.google.com', self.stop)
        response = self.wait()
        self.assertIn("Google", response.body)

        
    def test_can_parse(self):
        s = Silk()
        s.setup(self.io_loop)
        s.parse('//text()','http://www.google.com', self.stop)
        xpath_elements = self.wait()
        self.assertTrue(type(xpath_elements=='list'))

    
        
    def test_can_save_page(self):
        s = Silk()
        s.setup(self.io_loop, debug=True)


    def test_can_run_in_debug_mode(self):
        pass


