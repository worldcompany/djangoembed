import httplib2
import re

from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpRequest
from django.utils.importlib import import_module

from oembed.constants import DOMAIN_RE, OEMBED_ALLOWED_SIZES, SOCKET_TIMEOUT
from oembed.exceptions import OEmbedHTTPException


def size_to_nearest(width=None, height=None, allowed_sizes=OEMBED_ALLOWED_SIZES,
                    force_fit=False):
    """
    Generate some dimensions for resizing an object.  This function DOES NOT handle
    scaling, it simply calculates maximums.  These values should then be passed to
    the resize() method which will scale it and return the scaled width & height.
    """
    minwidth, minheight = min(allowed_sizes)
    maxwidth, maxheight = max(allowed_sizes)

    if not width and not height:
        return maxwidth, maxheight

    if width:
        width = int(width) > minwidth and int(width) or minwidth
    elif force_fit:
        width = maxwidth

    if height:
        height = int(height) > minheight and int(height) or minheight
    elif force_fit:
        height = maxheight

    for size in sorted(allowed_sizes):
        if width and not height:
            if width >= size[0]:
                maxwidth = size[0]
                if force_fit:
                    maxheight = size[1]
            else:
                break
        elif height and not width:
            if height >= size[1]:
                maxheight = size[1]
                if force_fit:
                    maxwidth = size[0]
            else:
                break
        else:
            if force_fit:
                if (width >= size[0]) and (height >= size[1]):
                    maxwidth, maxheight = size
                else:
                    break
            else:
                if width >= size[0]:
                    maxwidth = size[0]
                if height >= size[1]:
                    maxheight = size[1]
    return maxwidth, maxheight

def scale(width, height, new_width, new_height=None):
    # determine if resizing needs to be done (will not scale up)
    if width < new_width:
        if not new_height or height < new_height:
            return (width, height)
    
    # calculate ratios
    width_percent = (new_width / float(width))
    if new_height:
        height_percent = (new_height / float(height))
    
    if not new_height or width_percent < height_percent:
        new_height = int((float(height) * float(width_percent)))
    else:
        new_width = int((float(width) * float(height_percent)))
    
    return (new_width, new_height)

def fetch_url(url, method='GET', user_agent='django-oembed', timeout=SOCKET_TIMEOUT):
    """
    Fetch response headers and data from a URL, raising a generic exception
    for any kind of failure.
    """
    sock = httplib2.Http(timeout=timeout)
    request_headers = {
        'User-Agent': user_agent,
        'Accept-Encoding': 'gzip'}
    try:
        headers, raw = sock.request(url, headers=request_headers, method=method)
    except:
        raise OEmbedHTTPException('Error fetching %s' % url)
    return headers, raw

def get_domain(url):
    match = re.search(DOMAIN_RE, url)
    if match:
        return match.group()
    return ''

def relative_to_full(url, example_url):
    """
    Given a url which may or may not be a relative url, convert it to a full
    url path given another full url as an example
    """
    if re.match('https?:\/\/', url):
        return url
    domain = get_domain(example_url)
    if domain:
        return '%s%s' % (domain, url)
    return url

def mock_request():
    """
    Generate a fake request object to allow oEmbeds to use context processors.
    """
    current_site = Site.objects.get_current()
    request = HttpRequest()
    request.META['SERVER_NAME'] = current_site.domain
    return request

def load_class(path):
    """
    dynamically load a class given a string of the format
    
    package.Class
    """
    package, klass = path.rsplit('.', 1)
    module = import_module(package)
    return getattr(module, klass)

def cleaned_sites():
    """
    Create a list of tuples mapping domains from the sites table to their
    site name.  The domains will be cleaned into regexes that may be
    more permissive than the site domain is in the db.
    
    [(domain_regex, domain_name, domain_string), ...]
    """
    mappings = {}
    for site in Site.objects.all():
        # match the site domain, breaking it into several pieces
        match = re.match(r'(https?://)?(www[^\.]*\.)?([^/]+)', site.domain)
        
        if match is not None:
            http, www, domain = match.groups()
            
            # if the protocol is specified, use it, otherwise accept 80/443
            http_re = http or r'https?:\/\/'
            
            # whether or not there's a www (or www2 :x) allow it in the match
            www_re = r'(?:www[^\.]*\.)?'
            
            # build a regex of the permissive http re, the www re, and the domain
            domain_re = http_re + www_re + domain
            
            # now build a pretty string representation of the domain
            http = http or r'http://'
            www = www or ''
            normalized = http + www + domain
            
            mappings[site.pk] = (domain_re, site.name, normalized)
    return mappings
