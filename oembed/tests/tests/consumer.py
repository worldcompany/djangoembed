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
