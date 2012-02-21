

import urllib2
import os
from lxml import etree
from urlparse import urlparse, urlunparse
from tempfile import NamedTemporaryFile

current_dir = os.getcwd()

class Silk():
    opener =  urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]

    def __init__(self,xpath_dict,**kwargs):
        self.xpaths = dict()
        self.html_element_data = list()
        self.output = list()
        self.xpaths = xpath_dict
        if 'url' in kwargs:
            self.url = kwargs['url']
            self.html_element_data.append(self._get_html_(self.url))
        elif 'data' in kwargs:
            self.parent_silk = kwargs['data']
            for output in kwargs['data']:
                for element in output:
                    self.html_element_data.extend(element)
        else:
            raise Exception('no data or url')
        self._run_()

    def _get_html_(self,url,save=True,save_directory="scraped_html"):
        """Using url, gets html and returns etree HTML object.
         If the url returns 404, function returns urllib.HTTP404 exception.
         If save is true, function will return an already saved version if it exists, or
         it saves the retrieved html to a directory above this file named 'save_directory'."""
        file_name= url.replace('/','_')+ '.html'
        file_path = os.path.join(current_dir,save_directory)
        file_path_name = os.path.join(current_dir,save_directory, file_name)
        if save:
            if os.path.exists(file_path_name):
                print 'file found: ', file_name
                return etree.HTML(open(file_path_name,'rb').read())

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
            if os.path.exists(file_path):
                open(file_path_name,'wb').write(data)
            else:
                os.mkdir(file_path)
                open(file_path_name,'wb').write(data)
        return etree.HTML(data)

    def _get_resource_(self,url):
        """ Uses class urllib2.opener to return contents of url"""
        return self.opener.open(url).read()

    def _get_tempfile_resource_(self,url):
        """ Retrieves resource at url, saves to a temporary file, returns file-like object"""
        resource_url = self._validate_url_(url)
        temp_file = NamedTemporaryFile()
        temp_file.write(self._get_resource_(resource_url))
        return temp_file

    def save_image_to_django_model(self, image_url, model, image_field):
        """
        Gets an image from 'image_url' and saves to the django 'models' 'image_field'.
        """
        try:
            image = self._get_tempfile_resource_(image_url)
        except urllib2.HTTPError:
            return False
        image_name = image_url.split('/')[-1]
        getattr(model,image_field).save(image_name, image)
        return True


    def _check_regex_(self,regex_string, data):
        return True

    def _get_url_(self):
        try:
            return self.url
        except AttributeError:
            try:
                return self.parent_silk._get_url_()
            except AttributeError:
                raise Exception("No valid parent url found")

    def _validate_url_(self,url):
        new_url = list()
        url_components = urlparse(url)
        # if scheme, netloc or path are missing get parent url and use that
        parent_url_components = urlparse(self._get_url_())
        if url_components.scheme == '':
            new_url.append(parent_url_components.scheme)
        else:
            new_url.append(url_components.scheme)
        if url_components.netloc == '':
            new_url.append(parent_url_components.netloc)
        else:
            new_url.append(url_components.netloc)
        if url_components.path == '':
            new_url.append(parent_url_components.path)
        else:
            new_url.append(url_components.path)

        # Assume that if there are any params,queries or fragments
        # that the new url has them, if not probably not a url

        new_url.append(url_components.params)
        new_url.append(url_components.query)
        new_url.append(url_components.fragment)
        return urlunparse(new_url)

    def _run_(self):
        for data in self.html_element_data:
            invalid_data = False
            parse_list=list()
            for xpath_tuple in self.xpaths:
                xpath_name = xpath_tuple[0]
                xpath_string = xpath_tuple[1]
                requirements_tuple = xpath_tuple[2]
                parsed_data = data.xpath(xpath_string)

                if 'required' in requirements_tuple:
                    # Parsed_data must not be an empty list
                    if not parsed_data:
                        invalid_data = True
                        continue

                if requirements_tuple[0] == 'optional':
                    pass

                if 'get_resource' in requirements_tuple:
                    for i,data_element in enumerate(parsed_data):
                        parsed_data[i] = self._get_tempfile_resource_(data_element)

                if 'url' in requirements_tuple:
                    #run urlparse on parsed data, checking what data elements are present
                    for i,data_element in enumerate(parsed_data):
                        parsed_data[i] = self._validate_url_(data_element)
                        #todo work out what do if url fails
                print 'parsed_data ', parsed_data
                parse_list.append(parsed_data)

            # If the xpath set isn't found to validate against the data, don't save
            if invalid_data:
                continue
            else:
                parse_tuple = tuple(parse_list)
                self.output.append(parse_tuple)


    def __repr__(self):
        print self.output
        try:
            return "<Silk Instance>, URL/s:"+str(self.url)+", xpath:elements" + str(len(self.output))
        except AttributeError:
            return "<Silk Instance>, Parent:" + self.parent_silk.__repr__()

    def __iter__(self):
        for item in self.output:
            yield item


###Example Usage###
#
#query_dict = [('table rows','/html/body/div[3]/div[3]/div[4]/table/tr',('required'))]
#url='http://en.wikipedia.org/wiki/Snes_games'
#snes_table_rows_a_m = Silk(query_dict, url=url)
#
#query_dict = [
#              ('game name','td[1]//text()',('required')),
#              ('game release date','td[3]/a//text()',('required')),
#              ('game url','td[1]//a/@href',('optional','url'))
#]
#snes_games_a_m = Silk(query_dict,data=snes_table_rows_a_m)
#
#
#game_scrape_params = [
#    ('image url','/html/body/div[3]/div[3]/div[4]/table/tr[2]/td/a/img/@src', ('required','get_resource'))
#]
#print 'for loop'
#for item in snes_games_a_m:
#    try:
#        game_name = item[0][0]
#        game_release_year = item[1]
#        game_url = item[2][0]
#        print 'game url: ',game_url
#        game_scrape = Silk(game_scrape_params, url=game_url)
#        print 'game scrape',game_scrape
#
#        assert False
#    except IndexError:
#        pass
#
#

