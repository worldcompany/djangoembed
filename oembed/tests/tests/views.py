from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import simplejson

import oembed
from oembed.models import StoredOEmbed, StoredProvider
from oembed.tests.tests.base import BaseOEmbedTestCase

class OEmbedViewTestCase(BaseOEmbedTestCase):
    def test_missing_endpoint(self):
        response = self.client.get('/oembed/json/?url=http://www.nothere.com/asdf/')
        self.assertEqual(response.status_code, 404)
    
    def test_bad_request(self):
        # no url provided raises bad request (400)
        response = self.client.get('/oembed/json/')
        self.assertEqual(response.status_code, 400)
    
    def test_basic_handling(self):
        response = self.client.get('/oembed/json/?url=%s' % self.category_url)
        self.assertEqual(response.status_code, 200)
        response_json = simplejson.loads(response.content)
        
        stored_oembed = StoredOEmbed.objects.get(match=self.category_url)
        self.assertEqual(response_json, stored_oembed.response)
        
    def test_stored_provider_signals(self):
        response = self.client.get('/oembed/json/?url=%s' % self.youtube_url)
        
        # Check some response details - this provider doesn't provide upstream
        self.assertEqual(response.status_code, 404)
        
        # re-register the youtube provider to provide upstream
        yt = StoredProvider.objects.get(endpoint_url='http://www.youtube.com/oembed')
        yt.provides = True
        yt.save()
        
        # now we should be able to get the youtube object through the endpoint
        response = self.client.get('/oembed/json/?url=%s' % self.youtube_url)
        self.assertEqual(response.status_code, 200)
        
        stored = StoredOEmbed.objects.get(match=self.youtube_url)
        self.assertEqual(simplejson.loads(response.content), stored.response)
    
    def test_oembed_schema(self):
        response = self.client.get('/oembed/')
        self.assertEqual(response.status_code, 200)
        
        json_data = simplejson.loads(response.content)
        self.assertEqual(json_data, [
            {
                "matches": "http://example.com/testapp/blog/*/*/*/*/",
                "endpoint": "/oembed/json/",
                "type": "link"
            },
            {
                "matches": "http://example.com/testapp/category/*/",
                "endpoint": "/oembed/json/",
                "type": "photo"
            },
            {
                "matches": "http://example.com/testapp/rich/*/",
                "endpoint": "/oembed/json/",
                "type": "rich"
            }
        ])
        
        stored_provider = StoredProvider.objects.get(pk=100)
        stored_provider.provides = True
        stored_provider.save()
        
        expected = {
            'matches': 'http://www.active.com/*',
            'endpoint': '/oembed/json/',
            'type': 'photo'
        }
        
        response = self.client.get('/oembed/')
        self.assertEqual(response.status_code, 200)
        
        json_data = simplejson.loads(response.content)
        self.assertTrue(expected in json_data)
