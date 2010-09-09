from urllib import urlencode
from django import template
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse, NoReverseMatch
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

from oembed.consumer import OEmbedConsumer
from oembed.exceptions import OEmbedMissingEndpoint

import oembed

register = template.Library()

def oembed_filter(input, args=None):
    if args:
        dimensions = args.lower().split('x')
        if len(dimensions) != 2:
            raise template.TemplateSyntaxError("Usage: [width]x[height], e.g. 600x400")
        width, height = map(int, dimensions)
    else:
        width = height = None

    client = OEmbedConsumer()
    return mark_safe(client.parse(input, width, height))

register.filter('oembed', oembed_filter)

@register.filter
def extract_oembeds(text, args=None):
    """
    Extract oembed resources from a block of text.  Returns a list
    of dictionaries.

    Max width & height can be specified:
    {% for embed in block_of_text|extract_oembeds:"400x300" %}

    Resource type can be specified:
    {% for photo_embed in block_of_text|extract_oembeds:"photo" %}

    Or both:
    {% for embed in block_of_text|extract_oembeds:"400x300xphoto" %}
    """
    resource_type = width = height = None
    if args:
        dimensions = args.lower().split('x')
        if len(dimensions) in (3, 1):
            resource_type = dimensions.pop()

        if len(dimensions) == 2:
            width, height = map(lambda x: int(x), dimensions)

    client = OEmbedConsumer()
    return client.extract(text, width, height, resource_type)


@register.filter
def strip_oembeds(text, args=None):
    """
    Take a block of text and strip all the embeds from it, optionally taking
    a maxwidth, maxheight / resource_type
    
    Usage:
    {{ post.content|strip_embeds }}
    
    {{ post.content|strip_embeds:"600x600xphoto" }}
    
    {{ post.content|strip_embeds:"video" }}
    """
    resource_type = width = height = None
    if args:
        dimensions = args.lower().split('x')
        if len(dimensions) in (3, 1):
            resource_type = dimensions.pop()

        if len(dimensions) == 2:
            width, height = map(lambda x: int(x), dimensions)
    
    client = OEmbedConsumer()
    return mark_safe(client.strip(text, width, height, resource_type))


class OEmbedNode(template.Node):
    def __init__(self, nodelist, width, height, template_dir, var_name):
        self.nodelist = nodelist
        self.width = width
        self.height = height
        self.template_dir = template_dir
        self.var_name = var_name

    def render(self, context):
        kwargs = {}
        if self.width and self.height:
            kwargs['maxwidth'] = self.width
            kwargs['maxheight'] = self.height
            kwargs['template_dir'] = self.template_dir
            kwargs['context'] = context

        client = OEmbedConsumer()
        parsed = client.parse(self.nodelist.render(context), **kwargs)
        if self.var_name:
            context[self.var_name] = parsed
            return ''
        else:
            return parsed

def do_oembed(parser, token):
    """
    A node which parses everything between its two nodes, and replaces any links
    with OEmbed-provided objects, if possible.

    Supports two optional argument, which is the maximum width and height,
    specified like so:

    {% oembed 640x480 %}http://www.viddler.com/explore/SYSTM/videos/49/{% endoembed %}

    and or the name of a sub tempalte directory to render templates from:

    {% oembed 320x240 in "comments" %}http://www.viddler.com/explore/SYSTM/videos/49/{% endoembed %}

    or:

    {% oembed in "comments" %}http://www.viddler.com/explore/SYSTM/videos/49/{% endoembed %}

    either of those will render templates in oembed/comments/oembedtype.html

    Additionally, you can specify a context variable to drop the rendered text in:

    {% oembed 600x400 in "comments" as var_name %}...{% endoembed %}
    {% oembed as var_name %}...{% endoembed %}
    """
    args = token.split_contents()
    template_dir = None
    var_name = None
    if len(args) > 2:
        if len(args) == 3 and args[1] == 'in':
            template_dir = args[2]
        elif len(args) == 3 and args[1] == 'as':
            var_name = args[2]
        elif len(args) == 4 and args[2] == 'in':
            template_dir = args[3]
        elif len(args) == 4 and args[2] == 'as':
            var_name = args[3]
        elif len(args) == 6 and args[4] == 'as':
            template_dir = args[3]
            var_name = args[5]
        else:
            raise template.TemplateSyntaxError("OEmbed either takes a single " \
                "(optional) argument: WIDTHxHEIGHT, where WIDTH and HEIGHT " \
                "are positive integers, and or an optional 'in " \
                " \"template_dir\"' argument set.")
        if template_dir:
            if not (template_dir[0] == template_dir[-1] and template_dir[0] in ('"', "'")):
                raise template.TemplateSyntaxError("template_dir must be quoted")
            template_dir = template_dir[1:-1]

    if len(args) >= 2 and 'x' in args[1]:
        width, height = args[1].lower().split('x')
        if not width and height:
            raise template.TemplateSyntaxError("OEmbed's optional WIDTHxHEIGH" \
                "T argument requires WIDTH and HEIGHT to be positive integers.")
    else:
        width, height = None, None
    nodelist = parser.parse(('endoembed',))
    parser.delete_first_token()
    return OEmbedNode(nodelist, width, height, template_dir, var_name)

register.tag('oembed', do_oembed)


class OEmbedAutodiscoverNode(template.Node):
    def __init__(self, obj):
        self.obj = obj

    def render(self, context):
        obj = template.resolve_variable(self.obj, context)
        domain = Site.objects.get_current().domain
        try:
            url = 'http://%s%s' % (domain, obj.get_absolute_url())
            regex = oembed.site.provider_for_url(url)
            provider = 'http://%s%s' % (domain, reverse('oembed_json'))
            params = {'url': url, 'format': 'json'}
            return '<link rel="alternate" type="application/json+oembed" href="%s?%s" />' % (provider, urlencode(params))
        except OEmbedMissingEndpoint:
            return ''

def do_autodiscover(parser, token):
    """
    Generates a &lt;link&gt; tag with oembed autodiscovery bits for an object.

    {% oembed_autodiscover video %}
    """
    args = token.split_contents()
    if len(args) != 2:
        raise template.TemplateSyntaxError('%s takes an object as its parameter.' % args[0])
    else:
        obj = args[1]
    return OEmbedAutodiscoverNode(obj)

register.tag('oembed_autodiscover', do_autodiscover)


class OEmbedURLSchemeNode(template.Node):
    def render(self, context):
        try:
            site_profile = reverse('oembed_schema')
            current_site = Site.objects.get_current()
            return '<link rel="alternate" type="application/json+oembed+scheme" href="http://%s%s" title="%s OEmbed Scheme" />' % \
                (current_site.domain, site_profile, current_site.name)
        except NoReverseMatch:
            return ''

def do_url_scheme(parser, token):
    """
    Generates a &lt;link&gt; tag with oembed autodiscovery bits.

    {% oembed_url_scheme %}
    """
    args = token.split_contents()
    if len(args) != 1:
        raise template.TemplateSyntaxError('%s takes no parameters.' % args[0])
    return OEmbedURLSchemeNode()

register.tag('oembed_url_scheme', do_url_scheme)
