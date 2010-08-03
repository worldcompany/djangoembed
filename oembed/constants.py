import re

from django.conf import settings


# the oembed consumer can work with different parsers!
OEMBED_TEXT_PARSER = getattr(settings, 'OEMBED_TEXT_PARSER', 'oembed.parsers.text.TextParser')
OEMBED_HTML_PARSER = getattr(settings, 'OEMBED_HTML_PARSER', 'oembed.parsers.html.HTMLParser')


# the oembed image processor supports different backends!
OEMBED_IMAGE_PROCESSOR = getattr(settings, 'OEMBED_IMAGE_PROCESSOR', 'oembed.image_processors.pil.PIL_Resizer')


# oembed-ed objects can specify a TTL, after which they should be re-fetched
# from the providing site.  these settings allow you to control both the
# minimum amount of time to store an oembed and a default in the event that
# the provider does not supply a TTL
DEFAULT_OEMBED_TTL = getattr(settings, 'DEFAULT_OEMBED_TTL', 604800) # 7 days
MIN_OEMBED_TTL = getattr(settings, 'MIN_OEMBED_TTL', 86400) # 1 day


# the oembed spec defines 4 resource types
RESOURCE_PHOTO = 'photo'
RESOURCE_VIDEO = 'video'
RESOURCE_RICH = 'rich'
RESOURCE_LINK = 'link'
RESOURCE_TYPES = (
    RESOURCE_PHOTO,
    RESOURCE_VIDEO,
    RESOURCE_RICH,
    RESOURCE_LINK,
)
RESOURCE_CHOICES = (
    (RESOURCE_PHOTO, 'Photo'),
    (RESOURCE_VIDEO, 'Video'),
    (RESOURCE_RICH, 'Rich'),
    (RESOURCE_LINK, 'Link'),
)


# url for matching inline urls, which is a fairly tricky business
URL_PATTERN = '(https?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_|])'
URL_RE = re.compile(URL_PATTERN)
STANDALONE_URL_RE = re.compile('^\s*' + URL_PATTERN + '\s*$')


# oembed can parse HTML!
OEMBED_DEFAULT_PARSE_HTML = getattr(settings, 'OEMBED_DEFAULT_PARSE_HTML', True)
CONSUMER_URLIZE_ALL = getattr(settings, 'CONSUMER_URLIZE_ALL', True)


OEMBED_BLOCK_ELEMENTS = [
    'address', 'blockquote', 'center', 'dir', 'div', 'dl', 'fieldset', 'form', 
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'isindex', 'menu', 'noframes', 
    'noscript', 'ol', 'p', 'pre', 'table', 'ul', 'dd', 'dt', 'frameset', 'li', 
    'tbody', 'td', 'tfoot', 'th', 'thead', 'tr', 'button', 'del', 'iframe',
    'ins', 'map', 'object', 'script', '[document]'
]


# some default sizes to use for scaling
OEMBED_ALLOWED_SIZES = getattr(settings, 'OEMBED_ALLOWED_SIZES', [(x, x) for x in xrange(100, 900, 100)])
OEMBED_THUMBNAIL_SIZE = getattr(settings, 'OEMBED_THUMBNAIL_SIZE', ((200, 200),))

SOCKET_TIMEOUT = getattr(settings, 'SOCKET_TIMEOUT', 5)


# regex for extracting domain names
DOMAIN_RE = re.compile('((https?://)[^/]+)*')
