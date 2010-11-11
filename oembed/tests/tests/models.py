import datetime

import oembed
from oembed.exceptions import OEmbedMissingEndpoint
from oembed.models import StoredOEmbed, StoredProvider, AggregateMedia
from oembed.providers import DjangoProvider
from oembed.tests.tests.base import BaseOEmbedTestCase

from oembed.tests.models import Blog, Category, Rich


class ModelTestCase(BaseOEmbedTestCase):
    def test_stored_oembeds(self):
        video = oembed.site.embed(self.youtube_url)
        stored = StoredOEmbed.objects.get(match=self.youtube_url)
        self.assertEqual(stored.response, video.get_data())
    
        photo = oembed.site.embed(self.flickr_url)
        stored = StoredOEmbed.objects.get(match=self.flickr_url)
        self.assertEqual(stored.response, photo.get_data())
        
        # now create some on-the-fly
        link = oembed.site.embed(self.blog_url)
        stored = StoredOEmbed.objects.get(match=self.blog_url)
        self.assertEqual(stored.response, link.get_data())

        photo = oembed.site.embed(self.category_url)
        stored = StoredOEmbed.objects.get(match=self.category_url)
        self.assertEqual(stored.response, photo.get_data())
        
        rich = oembed.site.embed(self.rich_url)
        stored = StoredOEmbed.objects.get(match=self.rich_url)
        self.assertEqual(stored.response, rich.get_data())
    
    def test_stored_providers(self):
        active = StoredProvider.objects.get(pk=100)
        inactive = StoredProvider.objects.get(pk=101)
        
        active_qs = StoredProvider.objects.active()
        self.assertTrue(active in active_qs)
        self.assertFalse(inactive in active_qs)
        
        provider_list = oembed.site.get_providers()
        self.assertTrue(active in provider_list)
        self.assertFalse(inactive in provider_list)
        
        active.active = False
        active.save()
        provider_list = oembed.site.get_providers()
        self.assertFalse(active in provider_list)

    def test_media_aggregation(self):
        r = Rich(name='Test', slug='test', content='Hey check this out: %s' % self.youtube_url)
        r.save()

        am_queryset = AggregateMedia.objects.all()
        self.assertEqual(am_queryset.count(), 1)

        aggregated_object = am_queryset[0]
        self.assertEqual(aggregated_object.url, self.youtube_url)
        self.assertEqual(aggregated_object.media, StoredOEmbed.objects.get(match=self.youtube_url))

        self.assertQuerysetEqual(r.media.all(), am_queryset)
        self.assertQuerysetEqual(r.videos.all(), am_queryset)
        self.assertQuerysetEqual(r.photos.all(), [])

        r.content = 'Whoa i changed my mind, you should check this out: %s' % self.flickr_url
        r.save()

        am_queryset = AggregateMedia.objects.all()

        # the youtube one sticks around, but records from the rel table are killed
        self.assertEqual(am_queryset.count(), 2)

        # the flickr embed is there
        aggregated_object = am_queryset.get(url=self.flickr_url)

        # check that the flickr aggregated object GFKs to the StoredOEmbed
        self.assertEqual(aggregated_object.media, StoredOEmbed.objects.get(match=self.flickr_url))

        # the m2m fields should all be cleared out now
        self.assertQuerysetEqual(r.media.all(), am_queryset.filter(url=self.flickr_url))
        self.assertQuerysetEqual(r.videos.all(), [])
        self.assertQuerysetEqual(r.photos.all(), am_queryset.filter(url=self.flickr_url))

        r.content = 'Just text please'
        r.save()

        self.assertQuerysetEqual(r.media.all(), [])
        self.assertQuerysetEqual(r.videos.all(), [])
        self.assertQuerysetEqual(r.photos.all(), [])

    def test_internal_media_aggregation(self):
        category1 = Category.objects.get(pk=1)
        
        r = Rich(name='Container', slug='container', content='Check this out: %s' % self.category_url)
        r.save()

        am_queryset = AggregateMedia.objects.all()
        self.assertEqual(am_queryset.count(), 1)

        aggregated_object = am_queryset[0]
        self.assertEqual(aggregated_object.url, self.category_url)
        self.assertEqual(aggregated_object.media, category1) # gfk to actual category

        self.assertQuerysetEqual(r.media.all(), am_queryset)
        self.assertQuerysetEqual(r.videos.all(), [])
        self.assertQuerysetEqual(r.photos.all(), am_queryset)
