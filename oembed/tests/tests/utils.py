from django.contrib.sites.models import Site

from oembed.tests.tests.base import BaseOEmbedTestCase
from oembed.utils import size_to_nearest, relative_to_full, load_class, cleaned_sites, scale

class OEmbedUtilsTestCase(BaseOEmbedTestCase):
    def test_size_to_nearest(self):
        sizes = ((100, 100), (200, 200), (300, 300))

        self.assertEqual((300, 200), size_to_nearest(400, 200, sizes, False))
        self.assertEqual((100, 100), size_to_nearest(100, 100, sizes, False))
        self.assertEqual((200, 300), size_to_nearest(250, 500, sizes, False))
        
        # if force_fit is False then jump to the largest on None
        self.assertEqual((100, 300), size_to_nearest(150, None, sizes, False))
        self.assertEqual((300, 100), size_to_nearest(None, 150, sizes, False))

        # if force_fit is True then scale to the nearest size for the one
        # that is defined
        self.assertEqual((100, 100), size_to_nearest(150, None, sizes, True))
        self.assertEqual((100, 100), size_to_nearest(None, 150, sizes, True))
        self.assertEqual((200, 200), size_to_nearest(220, None, sizes, True))
        self.assertEqual((200, 200), size_to_nearest(None, 220, sizes, True))


        # if both dimensions are None use the largest possible
        self.assertEqual((300, 300), size_to_nearest(None, None, sizes, False))
        self.assertEqual((300, 300), size_to_nearest(None, None, sizes, True))

        # if a dimension is too small scale it up to the minimum
        self.assertEqual((100, 300), size_to_nearest(50, 300, sizes, False))
        self.assertEqual((100, 100), size_to_nearest(50, 300, sizes, True))
        self.assertEqual((100, 300), size_to_nearest(50, None, sizes, False))
        self.assertEqual((100, 100), size_to_nearest(50, None, sizes, True))

        # test when things are too large
        self.assertEqual((200, 200), size_to_nearest(400, 200, sizes, True))
        self.assertEqual((100, 100), size_to_nearest(100, 100, sizes, True))
        self.assertEqual((200, 200), size_to_nearest(250, 500, sizes, True))
        
        # test Nones around the edges
        self.assertEqual((100, 100), size_to_nearest(100, None, sizes, True))
        self.assertEqual((100, 100), size_to_nearest(None, 100, sizes, True))
        
    def test_size_to_nearest_defaults(self):
        self.assertEqual((800, 600), size_to_nearest(800, 600))
        self.assertEqual((800, 600), size_to_nearest(850, 650))

        self.assertEqual((800, 300), size_to_nearest(None, 350))
        self.assertEqual((400, 800), size_to_nearest(450, None))

        self.assertEqual((800, 300), size_to_nearest(None, 350))
        self.assertEqual((400, 800), size_to_nearest(450, None))
        
        self.assertEqual((200, 200), size_to_nearest(400, 250, force_fit=True))

    def test_relative_to_full(self):
        self.assertEqual('http://test.com/a/b/', relative_to_full('/a/b/', 'http://test.com'))
        self.assertEqual('http://test.com/a/b/', relative_to_full('/a/b/', 'http://test.com/c/d/?cruft'))
        self.assertEqual('http://test.com/a/b/', relative_to_full('http://test.com/a/b/', 'http://test.com'))
        self.assertEqual('http://blah.com/a/b/', relative_to_full('http://blah.com/a/b/', 'http://test.com'))
        self.assertEqual('/a/b/', relative_to_full('/a/b/', ''))
    
    def test_load_class(self):
        parser_class = load_class('oembed.parsers.html.HTMLParser')
        self.assertEqual(parser_class.__name__, 'HTMLParser')
        self.assertEqual(parser_class.__module__, 'oembed.parsers.html')
    
    def test_cleaned_sites(self):
        sites = Site.objects.all()
        cleaned = cleaned_sites()
        example = cleaned[1] # example site
        self.assertEquals(example[1], 'example.com')
        self.assertEquals(example[2], 'http://example.com')
        self.assertEquals(example[0], 'https?:\/\/(?:www[^\.]*\.)?example.com')
        
        www2_site = Site.objects.create(name='Test Site', domain='www2.testsite.com')
        mobile_site = Site.objects.create(name='Mobile Site', domain='m.testsite.com')
        
        cleaned = cleaned_sites()
        self.assertEquals(cleaned[www2_site.pk][1], 'Test Site')
        self.assertEquals(cleaned[www2_site.pk][2], 'http://www2.testsite.com')
        self.assertEquals(cleaned[www2_site.pk][0], 'https?:\/\/(?:www[^\.]*\.)?testsite.com')
        
        self.assertEquals(cleaned[mobile_site.pk][1], 'Mobile Site')
        self.assertEquals(cleaned[mobile_site.pk][2], 'http://m.testsite.com')
        self.assertEquals(cleaned[mobile_site.pk][0], 'https?:\/\/(?:www[^\.]*\.)?m.testsite.com')
    
    def test_scale(self):
        self.assertEqual(scale(640, 480, 320), (320, 240))
        self.assertEqual(scale(640, 480, 500, 240), (320, 240))
        self.assertEqual(scale(640, 480, 320, 500), (320, 240))
        self.assertEqual(scale(640, 480, 320, 240), (320, 240))
        
        self.assertEqual(scale(640, 480, 700), (640, 480))
        self.assertEqual(scale(640, 480, 700, 500), (640, 480))
