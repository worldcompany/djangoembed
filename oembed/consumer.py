import re

import oembed
from oembed.constants import OEMBED_DEFAULT_PARSE_HTML, URL_RE
from oembed.exceptions import OEmbedException
from oembed.parsers import text_parser, html_parser


class OEmbedConsumer(object):
    def parse(self, text, *args, **kwargs):
        if OEMBED_DEFAULT_PARSE_HTML:
            return self.parse_html(text, *args, **kwargs)
        else:
            return self.parse_text(text, *args, **kwargs)
    
    def parse_html(self, text, *args, **kwargs):
        parser = html_parser()
        return parser.parse(text, *args, **kwargs)
    
    def parse_text(self, text, *args, **kwargs):
        parser = text_parser()
        return parser.parse(text, *args, **kwargs)
        
    def extract(self, text, *args, **kwargs):
        if OEMBED_DEFAULT_PARSE_HTML:
            return self.extract_oembeds_html(text, *args, **kwargs)
        else:
            return self.extract_oembeds(text, *args, **kwargs)
    
    def extract_oembeds(self, text, maxwidth=None, maxheight=None, resource_type=None):
        """
        Scans a block of text and extracts oembed data on any urls,
        returning it in a list of dictionaries
        """
        parser = text_parser()
        urls = parser.extract_urls(text)
        return self.handle_extracted_urls(urls, maxwidth, maxheight, resource_type)
    
    def extract_oembeds_html(self, text, maxwidth=None, maxheight=None, resource_type=None):
        parser = html_parser()
        urls = parser.extract_urls(text)
        return self.handle_extracted_urls(urls, maxwidth, maxheight, resource_type)
    
    def handle_extracted_urls(self, url_set, maxwidth=None, maxheight=None, resource_type=None):
        embeds = []
        
        for user_url in url_set:
            try:
                resource = oembed.site.embed(user_url, maxwidth=maxwidth, maxheight=maxheight)
            except OEmbedException:
                continue
            else:
                if not resource_type or resource.type == resource_type:
                    data = resource.get_data()
                    data['original_url'] = user_url
                    embeds.append(data)
        
        return embeds
    
    def strip(self, text, *args, **kwargs):
        """
        Try to maintain parity with what is extracted by extract since strip
        will most likely be used in conjunction with extract
        """
        if OEMBED_DEFAULT_PARSE_HTML:
            extracted = self.extract_oembeds_html(text, *args, **kwargs)
        else:
            extracted = self.extract_oembeds(text, *args, **kwargs)
        
        matches = [r['original_url'] for r in extracted]
        match_handler = lambda m: m.group() not in matches and m.group() or ''
        
        return re.sub(URL_RE, match_handler, text)
