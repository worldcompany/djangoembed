from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

def null_view(*args, **kwargs):
    pass

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oembed/', include('oembed.urls')),
    url(r'^testapp/blog/(?P<year>\d+)/(?P<month>\w+)/(?P<day>\d+)/(?P<entry_slug>[\w-]+)/$', null_view, name='test_blog_detail'),
    url(r'^testapp/rich/([a-z-]+)/$', null_view, name='test_rich_detail'),
    url(r'^testapp/category/(\d+)/$', null_view, name='test_category_detail'),
)
