import os
from urllib2 import urlparse
try: 
    import Image
except ImportError:
    from PIL import Image
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.conf import settings
from django.core.files import storage
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse, NoReverseMatch
from django.test import TestCase
from django.utils import simplejson

import oembed
from oembed.providers import BaseProvider
from oembed.resources import OEmbedResource

from oembed.tests.settings import MEDIA_ROOT, MEDIA_URL, DEFAULT_FILE_STORAGE
from oembed.tests.storage import DummyMemoryStorage


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
    
    category_embed = '<img src="http://example.com/media/images/test_image1_800x600.jpg" alt="Category 1" ></img>'
    
    def setUp(self):
        "Set up test environment"
        # load up all the providers and register the test-only provider
        oembed.autodiscover()
        
        # refresh the attribute-cached time the db providers were last updated
        oembed.site._db_updated = None
        
        self.storage = DummyMemoryStorage()
        
        # monkeypatch default_storage
        self.orig_default_storage = storage.default_storage
        storage.default_storage = self.storage
        
        # swap media root & media url
        self.media_root, self.media_url = settings.MEDIA_ROOT, settings.MEDIA_URL
        settings.MEDIA_ROOT = MEDIA_ROOT
        settings.MEDIA_URL = MEDIA_URL

        # swap out template dirs
        self.template_dirs = settings.TEMPLATE_DIRS
        cur_dir = os.path.dirname(__file__)
        settings.TEMPLATE_DIRS = [os.path.join(os.path.dirname(cur_dir), 'templates')]
        
        # swap out file storage backend
        self.orig_file_storage = settings.DEFAULT_FILE_STORAGE
        settings.DEFAULT_FILE_STORAGE = DEFAULT_FILE_STORAGE

        # create 2 images for testing
        test_image = Image.new('CMYK', (1024, 768), (255, 255, 255, 255))
        self.test_img_buffer = StringIO()
        test_image.save(self.test_img_buffer, 'JPEG')
        
        self.test_img_file = ContentFile(self.test_img_buffer.getvalue())
        self.test_img_location = 'images/test_image1.jpg'
        storage.default_storage.save(self.test_img_location, self.test_img_file)

    def tearDown(self):
        settings.MEDIA_ROOT = self.media_root
        settings.MEDIA_URL = self.media_url
        settings.TEMPLATE_DIRS = self.template_dirs
        settings.DEFAULT_FILE_STORAGE = self.orig_file_storage
        storage.default_storage = self.orig_default_storage

    def _sort_by_pk(self, list_or_qs):
        # decorate, sort, undecorate using the pk of the items
        # in the list or queryset
        annotated = [(item.pk, item) for item in list_or_qs]
        annotated.sort()
        return map(lambda item_tuple: item_tuple[1], annotated)
    
    def assertQuerysetEqual(self, a, b):
        # assert list or queryset a is the same as list or queryset b
        return self.assertEqual(self._sort_by_pk(a), self._sort_by_pk(b))
