import re

from BeautifulSoup import BeautifulSoup # use BS to parse HTML (it's easy!)

import oembed
from oembed.constants import OEMBED_BLOCK_ELEMENTS, URL_RE, STANDALONE_URL_RE
from oembed.exceptions import OEmbedException
from oembed.parsers.base import BaseParser
from oembed.parsers.text import TextParser, TextBlockParser


class HTMLParser(BaseParser):
    """
    Use BeautifulSoup for easy html processing.
    """
    def parse_data(self, text, maxwidth, maxheight, template_dir, context,
                   urlize_all_links):                
        block_parser = TextBlockParser()
        original_template_dir = template_dir
        
        soup = BeautifulSoup(text)
        
        for user_url in soup.findAll(text=re.compile(URL_RE)):
            if not self.inside_a(user_url):
                if self.is_standalone(user_url):
                    template_dir = original_template_dir
                else:
                    template_dir = 'inline'
                
                replacement = block_parser.parse(
                    str(user_url),
                    maxwidth,
                    maxheight,
                    template_dir,
                    context,
                    urlize_all_links
                )
                user_url.replaceWith(replacement)
        
        return unicode(soup)
    
    def is_standalone(self, soupie):
        if re.match(STANDALONE_URL_RE, soupie):
            if soupie.parent.name in OEMBED_BLOCK_ELEMENTS:
                return True
        return False
    
    def inside_a(self, soupie):
        parent = soupie.parent
        while parent is not None:
            if parent.name == 'a':
                return True
            parent = parent.parent
        return False
    
    def extract_urls(self, text):
        block_parser = TextBlockParser()
        soup = BeautifulSoup(text)
        urls = set()
        url_list = []

        for user_url in soup.findAll(text=re.compile(URL_RE)):
            if not self.inside_a(user_url):
                block_urls = block_parser.extract_urls(unicode(user_url))
                
                for url in block_urls:
                    if url not in urls:
                        url_list.append(url)
                        urls.add(url)
        
        return url_list
