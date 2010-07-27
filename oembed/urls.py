from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('oembed.views',
    url(r'^$', 'oembed_schema', name='oembed_schema'),
    url(r'^json/$', 'json', name='oembed_json'),
    url(r'^consume/json/$', 'consume_json', name='oembed_consume_json'),
)
