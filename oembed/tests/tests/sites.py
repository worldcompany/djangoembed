from django.utils import simplejson

import oembed
from oembed.exceptions import AlreadyRegistered, NotRegistered, OEmbedMissingEndpoint
from oembed.models import StoredProvider, StoredOEmbed
from oembed.resources import OEmbedResource
from oembed.tests.oembed_providers import BlogProvider
from oembed.tests.tests.base import BaseOEmbedTestCase


class ProviderSiteTestCase(BaseOEmbedTestCase):
    def test_register(self):
        oembed.site.unregister(BlogProvider)
        self.assertRaises(NotRegistered, oembed.site.unregister, BlogProvider)
        
        oembed.site.register(BlogProvider)
        self.assertRaises(AlreadyRegistered, oembed.site.register, BlogProvider)
    
    def test_get_provider(self):
        oembed.site.unregister(BlogProvider)
        self.assertRaises(OEmbedMissingEndpoint, oembed.site.provider_for_url, self.blog_url)
        
        oembed.site.register(BlogProvider)
        provider = oembed.site.provider_for_url(self.blog_url)
        self.assertTrue(isinstance(provider, BlogProvider))
    
    def test_embed(self):
        oembed.site.unregister(BlogProvider)
        self.assertRaises(OEmbedMissingEndpoint, oembed.site.embed, self.blog_url)
        
        oembed.site.register(BlogProvider)
        resource = oembed.site.embed(self.blog_url)
        
        self.assertTrue(isinstance(resource, OEmbedResource))
    
    def test_object_caching(self):
        StoredOEmbed.objects.all().delete()
        
        for i in range(3):
            resource = oembed.site.embed(self.blog_url)
            self.assertEqual(StoredOEmbed.objects.count(), 1)
        
        for i in range(3):
            resource = oembed.site.embed(self.blog_url, maxwidth=400, maxheight=400)
            self.assertEqual(StoredOEmbed.objects.count(), 2)
        
        for i in range(3):
            resource = oembed.site.embed(self.blog_url, maxwidth=400)
            self.assertEqual(StoredOEmbed.objects.count(), 3)
    
    def test_autodiscovery(self):
        resp = self.client.get('/oembed/')
        json = simplejson.loads(resp.content)
        
        providers = oembed.site.store_providers(json)
        self.assertEqual(len(providers), 3)
        
        blog_provider, category_provider, rich_provider = providers
        
        self.assertEqual(blog_provider.wildcard_regex, 'http://example.com/testapp/blog/*/*/*/*/')
        self.assertEqual(blog_provider.regex, 'http://example.com/testapp/blog/.+?/.+?/.+?/.+?/')
        self.assertEqual(blog_provider.resource_type, 'link')
        self.assertEqual(blog_provider.endpoint_url, 'http://example.com/oembed/json/')
        
        self.assertEqual(category_provider.wildcard_regex, 'http://example.com/testapp/category/*/')
        self.assertEqual(category_provider.regex, 'http://example.com/testapp/category/.+?/')
        self.assertEqual(category_provider.resource_type, 'photo')
        self.assertEqual(category_provider.endpoint_url, 'http://example.com/oembed/json/')
        
        self.assertEqual(rich_provider.wildcard_regex, 'http://example.com/testapp/rich/*/')
        self.assertEqual(rich_provider.regex, 'http://example.com/testapp/rich/.+?/')
        self.assertEqual(rich_provider.resource_type, 'rich')
        self.assertEqual(rich_provider.endpoint_url, 'http://example.com/oembed/json/')
