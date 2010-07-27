import simplejson

from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.test import TestCase

import oembed
from oembed.providers import BaseProvider
from oembed.resources import OEmbedResource

from oembed.tests.settings import MEDIA_ROOT, MEDIA_URL

class BaseOEmbedTestCase(TestCase):
    fixtures = ['oembed_testdata.json']
    urls = 'oembed.tests.urls'
    
    # third party providers (StoredProvider)
    flickr_url = 'http://www.flickr.com/photos/neilkrug/2554073003/'
    youtube_url = 'http://www.youtube.com/watch?v=nda_OSWeyn8'
    
    # django providers (DjangoProvider and DjangoDatebasedProvider)
    category_url = 'http://example.com/testapp/category/1/'
    blog_url = 'http://example.com/testapp/blog/2010/may/01/entry-1/'
    rich_url = 'http://example.com/testapp/rich/rich-one/'
    
    category_embed = '<img src="http://example.com/media/images/breugel_babel2_800x661.jpg" alt="Category 1" ></img>'
    
    def setUp(self):
        "Set up test environment"
        # load up all the providers and register the test-only provider
        oembed.autodiscover()
        
        # refresh the attribute-cached time the db providers were last updated
        oembed.site._db_updated = None
        
        self.media_root, self.media_url = settings.MEDIA_ROOT, settings.MEDIA_URL
        settings.MEDIA_ROOT = MEDIA_ROOT
        settings.MEDIA_URL = MEDIA_URL
    
    def tearDown(self):
        settings.MEDIA_ROOT = self.media_root
        settings.MEDIA_URL = self.media_url

    def _sort_by_pk(self, list_or_qs):
        # decorate, sort, undecorate using the pk of the items
        # in the list or queryset
        annotated = [(item.pk, item) for item in list_or_qs]
        annotated.sort()
        return map(lambda item_tuple: item_tuple[1], annotated)
    
    def assertQuerysetEqual(self, a, b):
        # assert list or queryset a is the same as list or queryset b
        return self.assertEqual(self._sort_by_pk(a), self._sort_by_pk(b))
