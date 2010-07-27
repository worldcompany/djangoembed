import os
import re

from BeautifulSoup import BeautifulSoup # use BS to parse HTML (it's easy!)
import lxml.html # use lxml.html to parse HTML (it's fast!)
import StringIO

from django.template import RequestContext, Context
from django.template.loader import render_to_string, select_template
from django.utils.safestring import mark_safe

import oembed
from oembed.constants import (CONSUMER_URLIZE_ALL, OEMBED_BLOCK_ELEMENTS,
    URL_RE, STANDALONE_URL_RE)
from oembed.exceptions import OEmbedException
from oembed.utils import mock_request


class BaseParser(object):
    def render_oembed(self, oembed_resource, original_url, template_dir=None,
                      context=None):
        """
        Render the oembed resource and return as a string.
        
        Template directory will always fall back to 'oembed/[type].html', but
        a custom template dir can be passed in using the kwargs.
        
        Templates are given two context variables:
        - response: an OEmbedResource
        - original_url: the url that was passed to the consumer
        """
        provided_context = context or Context()
        context = RequestContext(mock_request())
        context.update(provided_context)
        
        # templates are named for the resources they display, i.e. video.html
        template_name = '%s.html' % oembed_resource.type
        
        # set up template finder to fall back to the link template
        templates = [os.path.join('oembed', template_name), 'oembed/link.html']
        
        # if there's a custom template dir, look there first
        if template_dir:
            templates.insert(0, os.path.join('oembed', template_dir, template_name))
        
        template = select_template(templates)
        
        context.push()
        context['response'] = oembed_resource
        context['original_url'] = original_url
        rendered = template.render(context)
        context.pop()
        
        return rendered.strip() # rendering template may add whitespace
    
    def parse(self, text, maxwidth=None, maxheight=None, template_dir=None,
              context=None, urlize_all_links=CONSUMER_URLIZE_ALL):
        """
        Scans a block of text, replacing anything matching a provider pattern
        with an OEmbed html snippet, if possible.
        
        Templates should be stored at oembed/{format}.html, so for example:
            
            oembed/video.html
        
        An optional template_dir can be provided, allowing for
        
            oembed/[template_dir]/video.html
            
        These templates are passed a context variable, ``response``, which is
        an OEmbedResource, as well as the ``original_url``
        """
        context = context or Context()
        context['maxwidth'] = maxwidth
        context['maxheight'] = maxheight
        
        return self.parse_data(text, maxwidth, maxheight, template_dir,
                               context, urlize_all_links)

    def parse_data(self, text, maxwidth, maxheight, template_dir, context,
                   urlize_all_links):
        """
        Implemented on all subclasses, this method contains the logic to
        process embeddable content in ``text``
        """
        raise NotImplementedError('Subclasses must define a parse_data method')
    
    def extract_urls(self, text):
        """
        Implemented on all subclasses, this method contains the logic to
        extract a list or set of urls from text
        """
        raise NotImplementedError('Subclasses must define a extract_urls method')


class TextBlockParser(BaseParser):
    def parse_data(self, text, maxwidth, maxheight, template_dir, context,
                   urlize_all_links):
        """
        Parses a block of text indiscriminately
        """
        # create a dictionary of user urls -> rendered responses
        replacements = {}
        user_urls = set(re.findall(URL_RE, text))
        
        for user_url in user_urls:
            try:
                resource = oembed.site.embed(user_url, maxwidth=maxwidth, maxheight=maxheight)
            except OEmbedException:
                if urlize_all_links:
                    replacements[user_url] = '<a href="%(LINK)s">%(LINK)s</a>' % {'LINK': user_url}
            else:
                context['minwidth'] = min(maxwidth, resource.width)
                context['minheight'] = min(maxheight, resource.height)
                
                replacement = self.render_oembed(
                    resource, 
                    user_url, 
                    template_dir=template_dir, 
                    context=context
                )
                replacements[user_url] = replacement.strip()
        
        # go through the text recording URLs that can be replaced
        # taking note of their start & end indexes
        user_urls = re.finditer(URL_RE, text)
        matches = []
        for match in user_urls:
            if match.group() in replacements:
                matches.append([match.start(), match.end(), match.group()])
        
        # replace the URLs in order, offsetting the indices each go
        for indx, (start, end, user_url) in enumerate(matches):
            replacement = replacements[user_url]
            difference = len(replacement) - len(user_url)
            
            # insert the replacement between two slices of text surrounding the
            # original url
            text = text[:start] + replacement + text[end:]
            
            # iterate through the rest of the matches offsetting their indices
            # based on the difference between replacement/original
            for j in xrange(indx + 1, len(matches)):
                matches[j][0] += difference
                matches[j][1] += difference
        return mark_safe(text)
    
    def extract_urls(self, text):
        return set(re.findall(URL_RE, text))


class TextParser(TextBlockParser):
    def parse_data(self, text, maxwidth, maxheight, template_dir, context, 
                   urlize_all_links):
        """
        Parses a block of text rendering links that occur on their own line
        normally but rendering inline links using a special template dir
        """
        block_parser = TextBlockParser()
        
        lines = text.splitlines()
        parsed = []
        
        for line in lines:
            if STANDALONE_URL_RE.match(line):
                user_url = line.strip()
                try:
                    resource = oembed.site.embed(user_url, maxwidth=maxwidth, maxheight=maxheight)
                    context['minwidth'] = min(maxwidth, resource.width)
                    context['minheight'] = min(maxheight, resource.height)
                except OEmbedException:
                    if urlize_all_links:
                        line = '<a href="%(LINK)s">%(LINK)s</a>' % {'LINK': user_url}
                else:
                    context['minwidth'] = min(maxwidth, resource.width)
                    context['minheight'] = min(maxheight, resource.height)
                    
                    line = self.render_oembed(
                        resource, 
                        user_url, 
                        template_dir=template_dir, 
                        context=context)
            else:
                line = block_parser.parse(line, maxwidth, maxheight, 'inline',
                                          context, urlize_all_links)
            
            parsed.append(line)
        
        return mark_safe('\n'.join(parsed))


class HTMLParser(BaseParser):
    """
    Use BeautifulSoup for easy html processing.
    """
    def parse_data(self, text, maxwidth, maxheight, template_dir, context,
                   urlize_all_links):                
        block_parser = TextBlockParser()
        original_template_dir = template_dir
        
        soup = BeautifulSoup(text)
        
        for user_url in soup.findAll(text=re.compile(URL_RE)):
            if not self.inside_a(user_url):
                if self.is_standalone(user_url):
                    template_dir = original_template_dir
                else:
                    template_dir = 'inline'
                
                replacement = block_parser.parse(
                    str(user_url),
                    maxwidth,
                    maxheight,
                    template_dir,
                    context,
                    urlize_all_links
                )
                user_url.replaceWith(replacement)
        
        return unicode(soup)
    
    def is_standalone(self, soupie):
        if re.match(STANDALONE_URL_RE, soupie):
            if soupie.parent.name in OEMBED_BLOCK_ELEMENTS:
                return True
        return False
    
    def inside_a(self, soupie):
        parent = soupie.parent
        while parent is not None:
            if parent.name == 'a':
                return True
            parent = parent.parent
        return False
    
    def extract_urls(self, text):
        block_parser = TextBlockParser()
        soup = BeautifulSoup(text)
        urls = set()
        
        for user_url in soup.findAll(text=re.compile(URL_RE)):
            if not self.inside_a(user_url):
                urls |= block_parser.extract_urls(unicode(user_url))
        
        return urls


class LXMLParser(BaseParser):
    """
    Use lxml.html, and lxml.etree for fast html processing.  This feature
    is not fully implemented yet.
    """
    def parse_data(self, text, maxwidth, maxheight, template_dir, context,
                   urlize_all_links):
        block_parser = TextBlockParser()
        text_parser = TextParser()
        
        try:
            parse_tree = lxml.html.fragment_fromstring(text, create_parent='div')
        except lxml.etree.XMLSyntaxError:
            return text
        
        if not parse_tree.getchildren():
            elements = [parse_tree]
        else:
            elements = parse_tree.xpath('.//*[not(self::a) and contains(text(), "http://")]')
        
        for element in elements:
            replacement = block_parser.parse(
                element.text,
                maxwidth,
                maxheight,
                template_dir,
                context,
                urlize_all_links
            )
            if replacement != element.text:
                element.text = ''
                new_elements = lxml.html.fragments_fromstring(replacement)
                for (i, e) in enumerate(new_elements):
                    element.insert(i, e)
        
        return lxml.html.tostring(parse_tree)
