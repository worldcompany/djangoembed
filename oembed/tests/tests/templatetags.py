from django.template import Context, Template

import oembed
from oembed.models import StoredOEmbed
from oembed.tests.models import Category

from oembed.tests.tests.base import BaseOEmbedTestCase

class OEmbedTemplateTagTestCase(BaseOEmbedTestCase):
    template_string = '{% load oembed_tags %}{% oembed %}XXX{% endoembed %}'
    
    def test_oembed_tag(self):
        t = Template(self.template_string.replace('XXX', self.category_url))
        c = Context()
        result = t.render(c)
        self.assertEqual(result, self.category_embed)
        
        t = Template(self.template_string.replace('XXX', 'http://www.google.com/'))
        c = Context()
        result = t.render(c)
        self.assertEqual('<a href="%(LINK)s">%(LINK)s</a>' % {'LINK': 'http://www.google.com/'}, result)
    
    def test_oembed_filter(self):
        t = Template('{% load oembed_tags %}{{ test_string|oembed }}')
        c = Context({'test_string': self.category_url})
        result = t.render(c)
        self.assertEqual(result, self.category_embed)
        
        c = Context({'test_string': 'http://www.google.com/'})
        result = t.render(c)
        self.assertEqual('<a href="%(LINK)s">%(LINK)s</a>' % {'LINK': 'http://www.google.com/'}, result)
        
    def test_extract_filter(self):
        t = Template('{% load oembed_tags %}{% for embed in test_string|extract_oembeds %}{{ embed.original_url }}{% endfor %}')
        c = Context({'test_string': self.category_url})
        result = t.render(c)
        self.assertEqual(result, self.category_url)
        
        t = Template('{% load oembed_tags %}{% for embed in test_string|extract_oembeds:"photo" %}{{ embed.original_url }}{% endfor %}')
        c = Context({'test_string': self.category_url + ' ' + self.blog_url})
        result = t.render(c)
        self.assertEqual(result, self.category_url)
        
        t = Template('{% load oembed_tags %}{% for embed in test_string|extract_oembeds:"link" %}{{ embed.original_url }}{% endfor %}')
        c = Context({'test_string': self.category_url + ' ' + self.blog_url})
        result = t.render(c)
        self.assertEqual(result, self.blog_url)
    
    def test_strip_filter(self):
        t = Template('{% load oembed_tags %}{{ test_string|strip_oembeds }}')
        c = Context({'test_string': 'testing [%s]' % self.category_url})
        result = t.render(c)
        self.assertEqual(result, 'testing []')
        
        t = Template('{% load oembed_tags %}{{ test_string|strip_oembeds:"photo" }}')
        c = Context({'test_string': 'testing [%s]' % self.category_url})
        result = t.render(c)
        self.assertEqual(result, 'testing []')
        
        t = Template('{% load oembed_tags %}{{ test_string|strip_oembeds:"link" }}')
        c = Context({'test_string': 'testing [%s]' % self.category_url})
        result = t.render(c)
        self.assertEqual(result, c['test_string'])
    
    def test_autodiscover(self):
        t = Template('{% load oembed_tags %}{% oembed_autodiscover obj %}')
        c = Context({'obj': Category.objects.get(pk=1)})
        result = t.render(c)
        self.assertEqual(result, '<link rel="alternate" type="application/json+oembed" href="http://example.com/oembed/json/?url=http%3A%2F%2Fexample.com%2Ftestapp%2Fcategory%2F1%2F&format=json" />')

    def test_scheme(self):
        t = Template('{% load oembed_tags %}{% oembed_url_scheme %}')
        c = Context()
        result = t.render(c)
        self.assertEqual(result, '<link rel="alternate" type="application/json+oembed+scheme" href="http://example.com/oembed/" title="example.com OEmbed Scheme" />')
