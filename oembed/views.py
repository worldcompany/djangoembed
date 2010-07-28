import re

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse, get_resolver
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.template import defaultfilters
from django.utils import simplejson
from django.utils.encoding import smart_str

import oembed
from oembed.consumer import OEmbedConsumer
from oembed.exceptions import OEmbedException, OEmbedMissingEndpoint
from oembed.providers import DjangoProvider, HTTPProvider


resolver = get_resolver(None)


def json(request, *args, **kwargs):
    """
    The oembed endpoint, or the url to which requests for metadata are passed.
    Third parties will want to access this view with URLs for your site's
    content and be returned OEmbed metadata.
    """
    # coerce to dictionary
    params = dict(request.GET.items())
    
    callback = params.pop('callback', None)
    url = params.pop('url', None)
    
    if not url:
        return HttpResponseBadRequest('Required parameter missing: URL')
    
    try:
        provider = oembed.site.provider_for_url(url)
        if not provider.provides:
            raise OEmbedMissingEndpoint()
    except OEmbedMissingEndpoint:
        raise Http404('No provider found for %s' % url)
    
    query = dict([(smart_str(k), smart_str(v)) for k, v in params.items() if v])
    
    try:
        resource = oembed.site.embed(url, **query)
    except OEmbedException, e:
        raise Http404('Error embedding %s: %s' % (url, str(e)))

    response = HttpResponse(mimetype='application/json')
    json = resource.json
    
    if callback:
        response.write('%s(%s)' % (defaultfilters.force_escape(callback), json))
    else:
        response.write(json)
    
    return response


def consume_json(request):
    """
    Extract and return oembed content for given urls.

    Required GET params:
        urls - list of urls to consume

    Optional GET params:
        width - maxwidth attribute for oembed content
        height - maxheight attribute for oembed content
        template_dir - template_dir to use when rendering oembed

    Returns:
        list of dictionaries with oembed metadata and renderings, json encoded
    """
    client = OEmbedConsumer()
    
    urls = request.GET.getlist('urls')
    width = request.GET.get('width')
    height = request.GET.get('height')
    template_dir = request.GET.get('template_dir')

    output = {}

    for url in urls:
        try:
            provider = oembed.site.provider_for_url(url)
        except OEmbedMissingEndpoint:
            oembeds = None
            rendered = None
        else:
            oembeds = url
            rendered = client.parse_text(url, width, height, template_dir=template_dir)

        output[url] = {
            'oembeds': oembeds,
            'rendered': rendered,
        }

    return HttpResponse(simplejson.dumps(output), mimetype='application/json')

def oembed_schema(request):
    """
    A site profile detailing valid endpoints for a given domain.  Allows for
    better auto-discovery of embeddable content.

    OEmbed-able content lives at a URL that maps to a provider.
    """
    current_domain = Site.objects.get_current().domain
    url_schemes = [] # a list of dictionaries for all the urls we can match
    endpoint = reverse('oembed_json') # the public endpoint for our oembeds
    providers = oembed.site.get_providers()

    for provider in providers:
        # first make sure this provider class is exposed at the public endpoint
        if not provider.provides:
            continue
        
        match = None
        if isinstance(provider, DjangoProvider):
            # django providers define their regex_list by using urlreversing
            url_pattern = resolver.reverse_dict.get(provider._meta.named_view)

            # this regex replacement is set to be non-greedy, which results
            # in things like /news/*/*/*/*/ -- this is more explicit
            if url_pattern:
                regex = re.sub(r'%\(.+?\)s', '*', url_pattern[0][0][0])
                match = 'http://%s/%s' % (current_domain, regex)
        elif isinstance(provider, HTTPProvider):
            match = provider.url_scheme
        else:
            match = provider.regex

        if match:
            url_schemes.append({
                'type': provider.resource_type,
                'matches': match,
                'endpoint': endpoint
            })
    
    url_schemes.sort(key=lambda item: item['matches'])
    
    response = HttpResponse(mimetype='application/json')
    response.write(simplejson.dumps(url_schemes))
    return response
