import oembed

from oembed.tests.tests.base import BaseOEmbedTestCase
from oembed.parsers.base import TextParser, TextBlockParser, HTMLParser


class TextBlockParserTestCase(BaseOEmbedTestCase):
    def setUp(self):
        self.parser = TextBlockParser()
        super(TextBlockParserTestCase, self).setUp()
    
    def test_basic_handling(self):
        parsed = self.parser.parse(self.category_url)
        self.assertEqual(parsed, self.category_embed)
    
    def test_inline_link_handling(self):
        parsed = self.parser.parse('Testing %s' % self.category_url)
        self.assertEqual(parsed, 'Testing %s' % self.category_embed)
    
    def test_block_handling(self):
        parsed = self.parser.parse('Testing %(url)s\n%(url)s' % ({'url': self.category_url}))
        self.assertEqual(parsed, 'Testing %(embed)s\n%(embed)s' % ({'embed': self.category_embed}))
    
    def test_urlization(self):
        test_string = 'Testing http://www.google.com'
        parsed = self.parser.parse(test_string, urlize_all_links=False)
        self.assertEqual(parsed, test_string)
        
        parsed = self.parser.parse(test_string, urlize_all_links=True)
        self.assertEqual(parsed, 'Testing <a href="http://www.google.com">http://www.google.com</a>')
    
    def test_extraction(self):
        extracted = self.parser.extract_urls('Testing %s wha?' % self.category_url)
        self.assertEqual(extracted, set([self.category_url]))


class TextParserTestCase(BaseOEmbedTestCase):
    def setUp(self):
        self.parser = TextParser()
        super(TextParserTestCase, self).setUp()
    
    def test_basic_handling(self):
        parsed = self.parser.parse(self.category_url)
        self.assertEqual(parsed, self.category_embed)
    
    def test_inline_link_handling(self):
        parsed = self.parser.parse('Testing %s' % self.category_url)
        self.assertEqual(parsed, 'Testing <a href="http://example.com/testapp/category/1/">Category 1</a>')
    
    def test_block_handling(self):
        parsed = self.parser.parse('Testing %(url)s\n%(url)s' % ({'url': self.category_url}))
        self.assertEqual(parsed, 'Testing <a href="http://example.com/testapp/category/1/">Category 1</a>\n%s' % self.category_embed)

    def test_extraction(self):
        extracted = self.parser.extract_urls('Testing %s wha?' % self.category_url)
        self.assertEqual(extracted, set([self.category_url]))


class HTMLParserTestCase(BaseOEmbedTestCase):
    def setUp(self):
        self.parser = HTMLParser()
        super(HTMLParserTestCase, self).setUp()
    
    def test_basic_handling(self):
        parsed = self.parser.parse('<p>%s</p>' % self.category_url)
        self.assertEqual(parsed, '<p>%s</p>' % self.category_embed)
    
    def test_inline_link_handling(self):
        parsed = self.parser.parse('<p>Testing %s</p>' % self.category_url)
        self.assertEqual(parsed, '<p>Testing <a href="http://example.com/testapp/category/1/">Category 1</a></p>')
    
    def test_block_handling(self):
        parsed = self.parser.parse('<p>Testing %(url)s</p><p>%(url)s</p>' % ({'url': self.category_url}))
        self.assertEqual(parsed, '<p>Testing <a href="http://example.com/testapp/category/1/">Category 1</a></p><p>%s</p>' % self.category_embed)
    
    def test_buried_link(self):
        parsed = self.parser.parse('<p>Testing <a href="%(url)s"><span>%(url)s</span></a></p>' % ({'url': self.category_url}))
        self.assertEqual(parsed, '<p>Testing <a href="http://example.com/testapp/category/1/"><span>http://example.com/testapp/category/1/</span></a></p>')
    
    def test_outside_of_markup(self):
        parsed = self.parser.parse('%s<p>Wow this is bad</p>' % self.category_url)
        self.assertEqual(parsed, '%s<p>Wow this is bad</p>' % self.category_embed)

    def test_extraction(self):
        extracted = self.parser.extract_urls('<p>Testing %s wha?</p>' % self.category_url)
        self.assertEqual(extracted, set([self.category_url]))
        
        extracted = self.parser.extract_urls('<p>Testing <a href="%(url)s">%(url)s</a> wha?</p>' % ({'url': self.category_url}))
        self.assertEqual(extracted, set([]))
