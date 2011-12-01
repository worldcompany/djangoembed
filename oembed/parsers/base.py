import os

from django.template import RequestContext, Context
from django.template.loader import render_to_string, select_template

from oembed.constants import CONSUMER_URLIZE_ALL
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
        context = RequestContext(context.get("request") or mock_request())
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

        try:
            text = unicode(text)
        except UnicodeDecodeError:
            text = unicode(text.decode('utf-8'))
        
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
