__author__ = 'peterdavis'

import urllib2
import lxml
from lxml import etree

class Silk():
    opener =  urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]

    xpaths = dict()
    html_element_data = list()
    output = list()
    def _get_html_(self,url,save=True,save_directory="scraped_html"):
        """Using url, gets html and returns etree HTML object.
         If the url returns 404, function returns urllib.HTTP404 exception.
         If save is true, function will return an already saved version if it exists, or
         it saves the retrieved html to a directory above this file named 'save_directory'."""
        file_name= url.replace('/','_')+ '.html'
        file_path = os.path.join(current_dir,save_directory, file_name)
        if save:
            if os.path.exists(file_path):
                print 'file found: ', file_name
                return etree.HTML(open(file_name,'rb').read())

        #This will raise urllib2.HTTPError exception if it fails
        response = self.opener.open(url)

        #Deals with gzip encoding
        if response.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
            data = f.read()
        else:
            data = response.read()
        if save:
            open(file_path,'wb').write(data)
        return etree.HTML(data)

    def _get_resource_(self,url):
        """ Uses class urllib2.opener to return contents of url"""
        return self.opener.open(url).read()

    def _get_temp_resource_(self,url):
        """ Retrieves resource at url, saves to a temporary file, returns file-like object"""
        temp_file = NamedTemporaryFile(delete=True)
        temp_file.write(self._get_resource_(url))
        return temp_file

    def save_image_to_django_model(self, image_url, model, image_field):
        """
        Gets an image from 'image_url' and saves to the django 'models' 'image_field'.
        """
        try:
            image = self._get_temp_resource_(image_url)
        except urllib2.HTTPError:
            return False
        image_name = image_url.split('/')[-1]
        getattr(model,image_field).save(image_name, image)
        return True

    def __init__(self,xpath_dict,**kwargs):
        self.xpaths = xpath_dict
        if 'url' in kwargs:
            self.url = url
            for address in kwargs['url']:
                self.html_element_data.append(self._get_html_(address))
        elif 'data' in kwargs:
            self.parent_silk = kwargs['data']
            for output in kwargs['data']:
                for element in output[1]:
                    self.html_element_data.append(element)
        else:
            raise Exception('no data or url')
        self._run_()

    def _check_regex_(self,regex_string, data):
        return True

    def _run_(self):
        for data in self.html_element_data:
            invalid_data = False
            parse_list=list()
            for xpath_tuple in self.xpaths:
                xpath_name = xpath_tuple[0]
                xpath_string = xpath_tuple[1]
                requirements_tuple = xpath_tuple[2]
                parsed_data = data.xpath(xpath_string)

                if requirements_tuple[0] == 'required':
                    # Parsed_data must not be an empty list
                    if not parsed_data:
                        invalid_data = True
                        continue
                    # Check if regex supplied
                    if len(requirements_tuple) == 2:
                        invalid_data = not self._check_regex_(requirements_tuple[1],parsed_data)

                if requirements_tuple[0] == 'optional':
                    pass

                parse_list.append((xpath_name,parsed_data))

            # If the xpath set isn't found to validate against the data, don't save
            if invalid_data:
                continue
            else:
                for item in parse_list:
                    self.output.append(item)


    def __repr__(self):
        print self.output
        try:
            return "<Silk Instance>, URL/s:"+str(self.url)+", xpath:elements" + str(len(self.output))
        except AttributeError:
            return "<Silk Instance>, Parent:" + self.parent_silk.__repr__()

    def __iter__(self):
        for item in self.output:
            yield item

#instantiate silk
query_dict = [('table rows','/html/body/div[3]/div[3]/div[4]/table/tr',('required'))]

url=['http://en.wikipedia.org/wiki/Snes_games']
a = Silk(query_dict, url=url)
for xpath_item in a:
    print xpath_item

query_dict = [
              ('game name','td[1]//text()',('required')),
              ('game release date','td[3]/a//text()',('required')),
              ('game url','td[1]//a/@href',('optional'))
]

b = Silk(query_dict,data=a)
for xpath_item in b:
    print xpath_item
