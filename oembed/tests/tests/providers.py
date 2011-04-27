import datetime
import re

try: 
    import Image
except ImportError:
    from PIL import Image
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.contrib.sites.models import Site

import oembed
from oembed.providers import DjangoProvider, DjangoDateBasedProvider, DjangoProviderOptions
from oembed.consumer import OEmbedConsumer
from oembed.constants import OEMBED_ALLOWED_SIZES

from oembed.tests.models import Blog
from oembed.tests.oembed_providers import BlogProvider
from oembed.tests.tests.base import BaseOEmbedTestCase

class ProviderTestCase(BaseOEmbedTestCase):
    def test_resource_options(self):
        self.assertTrue(isinstance(BlogProvider._meta, DjangoProviderOptions))
        
        ops = BlogProvider._meta
        self.assertEqual(ops.model, Blog)
        self.assertEqual(ops.date_field, 'pub_date')
        self.assertEqual(ops.fields_to_match, {'entry_slug': 'slug'})
        self.assertEqual(ops.named_view, 'test_blog_detail')
    
    def test_meta_queryset_behavior(self):
        provider = BlogProvider()
        
        obj = provider.get_object('http://example.com/testapp/blog/2010/may/01/entry-1/')
        blog_obj = Blog.objects.get(slug='entry-1')
        self.assertEqual(obj, blog_obj)
        
        new_obj = Blog.objects.create(
            title='new entry',
            author='new author',
            pub_date=datetime.datetime(2010, 1, 1),
        )
        oembed_obj = provider.get_object('http://example.com/testapp/blog/2010/jan/01/new-entry/')
        
        self.assertEqual(new_obj, oembed_obj)
    
    def test_resource_object(self):
        provider = BlogProvider()
        resource = provider.request_resource('http://example.com/testapp/blog/2010/may/01/entry-1/')
        
        blog_obj = Blog.objects.get(slug='entry-1')
        self.assertEqual(blog_obj, resource.content_object)
    
    def test_django_provider(self):
        resource = oembed.site.embed(self.category_url)
        
        category_data = resource.get_data()
        
        # provider data is pulled from the sites table
        self.assertEqual(category_data['provider_url'], 'http://example.com')
        self.assertEqual(category_data['provider_name'], 'example.com')
        
        # resource data is pulled from the provider
        self.assertEqual(category_data['type'], 'photo')
        self.assertEqual(category_data['title'], 'Category 1')
        
        max_width, max_height = max(OEMBED_ALLOWED_SIZES)
        
        # image data
        self.assertTrue(category_data['width'] <= max_width)
        self.assertTrue(category_data['height'] <= max_height)
        
        w, h = category_data['width'], category_data['height']
        image_name = 'images/test_image1_%sx%s.jpg' % (w, h)
        
        self.assertEqual(category_data['url'], 'http://example.com/media/%s' % image_name)
        
        # just double check to be sure it got saved here
        self.assertTrue(image_name in self.storage._files)
        
        img_buf = StringIO(self.storage._files[image_name])
        img = Image.open(img_buf)
        img_width, img_height = img.size
        self.assertTrue(img_width == w or img_height == h)

        tw, th = category_data['thumbnail_width'], category_data['thumbnail_height']
        thumbnail_name = 'images/test_image1_%sx%s.jpg' % (tw, th)
        
        self.assertEqual(category_data['thumbnail_url'], 'http://example.com/media/%s' % thumbnail_name)
        
        self.assertTrue(thumbnail_name in self.storage._files)
        
        img_buf = StringIO(self.storage._files[thumbnail_name])
        img = Image.open(img_buf)
        img_width, img_height = img.size
        self.assertTrue(img_width == tw or img_height == th)
    
    def test_django_provider_image_sizing(self):
        resource = oembed.site.embed(self.category_url, maxwidth=450)
        
        category_data = resource.get_data()
        
        # provider data is pulled from the sites table
        self.assertEqual(category_data['width'], 400)
        w, h = category_data['width'], category_data['height']
        
        self.assertEqual(category_data['url'], 'http://example.com/media/images/test_image1_%sx%s.jpg' % (w, h))

        # specify both
        resource = oembed.site.embed(self.category_url, maxwidth=450, maxheight=200)
        
        category_data = resource.get_data()
        
        self.assertEqual(category_data['height'], 200)
        w, h = category_data['width'], category_data['height']
        
        self.assertEqual(category_data['url'], 'http://example.com/media/images/test_image1_%sx%s.jpg' % (w, h))

    def test_django_provider_url_match(self):
        # even though the sites table has example.com having no www., the regex
        # constructed should be able to correctly match the url below
        resource = oembed.site.embed('http://www.example.com/testapp/category/2/')
        
        category_data = resource.get_data()
        self.assertEqual(category_data['title'], 'Category 2')
        
        # try a https
        resource = oembed.site.embed('https://www.example.com/testapp/category/2/')
        
        category_data = resource.get_data()
        self.assertEqual(category_data['title'], 'Category 2')
    
    def test_django_datebased_provider(self):
        resource = oembed.site.embed(self.blog_url)
        
        blog_data = resource.get_data()
        
        # provider data is pulled from the sites table
        self.assertEqual(blog_data['provider_url'], 'http://example.com')
        self.assertEqual(blog_data['provider_name'], 'example.com')
        
        # resource data
        self.assertEqual(blog_data['type'], 'link')
        self.assertEqual(blog_data['title'], 'Entry 1')
        self.assertEqual(blog_data['url'], 'http://example.com/testapp/blog/2010/may/01/entry-1/')
        self.assertEqual(blog_data['author_name'], 'Charles')
    
    def test_django_rich_provider(self):
        resource = oembed.site.embed(self.rich_url)
        
        rich_data = resource.get_data()
        
        max_width, max_height = max(OEMBED_ALLOWED_SIZES)
        
        # image data
        self.assertTrue(rich_data['width'] <= max_width)
        self.assertTrue(rich_data['height'] <= max_height)
        
        self.assertEqual(rich_data['title'], 'Rich One')
        self.assertEqual(rich_data['html'], '<h1>Rich One</h1><p>This is rich one<br />Awesome!</p>\n')
    
    def test_meta_inheritance(self):
        class BaseTestProvider(DjangoProvider):
            class Meta:
                abstract = True
                test_attr = 'basetestprovider'
                image_processor = 'someimageprocessor'
        
        class BaseDateBasedProvider(BaseTestProvider, DjangoDateBasedProvider):
            class Meta:
                abstract = True
                test_attr = 'basedatebasedprovider'
        
        class BlogProviderMixin(DjangoProvider):
            class Meta:
                abstract = True
                year_part = 'blog_year'
                month_part = 'blog_month'
                day_part = 'blog_day'
        
        class BaseBlogProvider(BaseDateBasedProvider):
            resource_type = 'rich'
            
            class Meta:
                abstract = True
                model = Blog
                test_attr = 'baseblogprovider'
        
        class SomeBlogProvider(BaseBlogProvider):
            class Meta:
                named_view = 'test_blog_detail'
                fields_to_match = {'blog_id': 'id'}
                test_attr = 'someblogprovider'
        
        class MixinBlogProvider(BlogProviderMixin, BaseBlogProvider):
            class Meta:
                named_view = 'test_blog_detail'
                fields_to_match = {'blog_id': 'id'}
                test_attr = 'mixinblogprovider'
        
        ops = BaseTestProvider._meta
        self.assertTrue(ops.abstract)
        self.assertEqual(ops.test_attr, 'basetestprovider')
        self.assertEqual(ops.image_processor, 'someimageprocessor')
        
        ops = BaseDateBasedProvider._meta
        self.assertTrue(ops.abstract)
        self.assertEqual(ops.test_attr, 'basedatebasedprovider')
        self.assertEqual(ops.image_processor, 'someimageprocessor')
        
        ops = BaseBlogProvider._meta
        self.assertTrue(ops.abstract)
        self.assertEqual(ops.test_attr, 'baseblogprovider')
        self.assertEqual(ops.image_processor, 'someimageprocessor')
        self.assertEqual(ops.model, Blog)
        
        ops = SomeBlogProvider._meta
        self.assertFalse(ops.abstract)
        self.assertEqual(ops.test_attr, 'someblogprovider')
        self.assertEqual(ops.image_processor, 'someimageprocessor')
        self.assertEqual(ops.model, Blog)
        self.assertEqual(ops.fields_to_match, {'blog_id': 'id'})
        
        ops = MixinBlogProvider._meta
        self.assertFalse(ops.abstract)
        self.assertEqual(ops.test_attr, 'mixinblogprovider')
        self.assertEqual(ops.image_processor, 'someimageprocessor')
        self.assertEqual(ops.model, Blog)
        self.assertEqual(ops.fields_to_match, {'blog_id': 'id'})
        self.assertEqual(ops.year_part, 'blog_year')
        self.assertEqual(ops.month_part, 'blog_month')
        self.assertEqual(ops.day_part, 'blog_day')
