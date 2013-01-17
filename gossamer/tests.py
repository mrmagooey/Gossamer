from models import Silk
from tornado.testing import AsyncTestCase

class TestSilk(AsyncTestCase):
    
    def test_can_create_silk_instance(self):
        s = Silk()
        s # stop flymake complaining
        
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

    
    def test_local_file_storage(self):
        s = Silk()
        s.setup(self.io_loop)
        s.fetch_and_save('http://www.google.com', self.stop)
        response = self.wait()
        local_file = s.get_local_file('http://www.google.com')
        self.assertEqual(response.body, local_file)
        s.delete_local_file('http://www.google.com')
        
        
        


