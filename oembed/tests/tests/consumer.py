import oembed

from oembed.tests.tests.base import BaseOEmbedTestCase
from oembed.consumer import OEmbedConsumer
from oembed.resources import OEmbedResource


class ConsumerTestCase(BaseOEmbedTestCase):
    def setUp(self):
        "Set up test environment"
        super(ConsumerTestCase, self).setUp()
        self.oembed_client = OEmbedConsumer()

    def test_parse_text(self):
        consumed = self.oembed_client.parse_text(self.category_url)
        self.assertEqual(consumed, self.category_embed)
    
    def test_parse_html(self):
        consumed = self.oembed_client.parse_html('<p>%s</p>' % self.category_url)
        self.assertEqual(consumed, '<p>%s</p>' % self.category_embed)
    
    def test_extract_oembeds(self):
        embeds = self.oembed_client.extract_oembeds(self.category_url)
        self.assertEqual(len(embeds), 1)
        self.assertEqual(embeds[0]['original_url'], self.category_url)
        
        embeds = self.oembed_client.extract_oembeds(self.category_url, resource_type='photo')
        self.assertEqual(len(embeds), 1)
        self.assertEqual(embeds[0]['original_url'], self.category_url)
        
        embeds = self.oembed_client.extract_oembeds(self.category_url, resource_type='video')
        self.assertEqual(len(embeds), 0)
    
    def test_extract_oembeds_html(self):
        embeds = self.oembed_client.extract_oembeds_html('<p>%s</p>' % self.category_url)
        self.assertEqual(len(embeds), 1)
        self.assertEqual(embeds[0]['original_url'], self.category_url)
        
        embeds = self.oembed_client.extract_oembeds_html('<p>%s</p>' % self.category_url, resource_type='photo')
        self.assertEqual(len(embeds), 1)
        self.assertEqual(embeds[0]['original_url'], self.category_url)
        
        embeds = self.oembed_client.extract_oembeds_html('<p>%s</p>' % self.category_url, resource_type='video')
        self.assertEqual(len(embeds), 0)
        
        embeds = self.oembed_client.extract_oembeds_html('<p><a href="%s">Some link</a></p>' % self.category_url)
        self.assertEqual(len(embeds), 0)
        
        embeds = self.oembed_client.extract_oembeds_html('<p><a href="/some-link/">%s</a></p>' % self.category_url)
        self.assertEqual(len(embeds), 0)
    
    def test_strip(self):
        test_string = 'testing [%s] [http://www.google.com]' % self.category_url
        expected = 'testing [] [http://www.google.com]'
        
        self.assertEqual(self.oembed_client.strip(test_string), expected)
        
        # with width & height
        self.assertEqual(self.oembed_client.strip(test_string, 600, 400), expected)
        
        # with resource_type
        self.assertEqual(self.oembed_client.strip(test_string, resource_type='photo'), expected)
        self.assertEqual(self.oembed_client.strip(test_string, resource_type='link'), test_string)
    
    def test_strip_html(self):
        test_string = '<a href="%(match)s">%(match)s</a> <p>%(no_match)s</p>' % \
            {'match': self.category_url, 'no_match': 'http://www.google.com'}
        expected = test_string
        
        self.assertEqual(self.oembed_client.strip(test_string), expected)
    
    def test_strip_html_failure(self):
        # show how strip can fail when handling html - it picks up the match
        # in the p tag then replaces it everywhere, including in the a tags
        test_string = '<a href="%(match)s">%(match)s</a> <p>%(match)s</p> <p>%(no_match)s</p>' % \
            {'match': self.category_url, 'no_match': 'http://www.google.com'}
        expected = test_string
        actual = '<a href=""></a> <p></p> <p>http://www.google.com</p>'
        
        self.assertEqual(self.oembed_client.strip(test_string), actual)
