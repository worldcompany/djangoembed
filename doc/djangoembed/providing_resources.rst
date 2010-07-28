Providing Resources
===================

Suppose you would like your own content to be OEmbed-able.  Making your own site
a provider also allows you to consume your own content in a uniform fashion.
Say you have a blog app and occasionally link to your own articles.  By defining
a provider for your blog entries, you can consume them transparently!

django-oembed comes with base classes you can extend to write your own providers
depending on what you want to embed.

BaseProvider
------------

Taking a look at BaseProvider, we see that it defines two attributes and one
method::

    class BaseProvider(object):
        """
        Base class for OEmbed resources.
        """
        regex = r''
        provides = True  # allow this provider to be accessed by third parties
            
        def request_resource(self, url, **kwargs):
            """
            Get an OEmbedResource from one of the providers configured in this 
            provider according to the resource url.
            
            Args:
                url: The url of the resource to get.
                **kwargs: Optional parameters to pass in to the provider.
            
            Returns:
                OEmbedResource object.
                
            If no object returned, raises OEmbedException
            """
            raise NotImplementedError

When the consumer processes a URL, it checks to see if it's URL matches any of
the regexes provided by registered OEmbedProviders.  When a match is found, that
provider's ``endpoint()`` method is called, with the URL and any arguments
passed in, such as 'format', 'maxwidth', or 'maxheight'.  The ``endpoint()``
method returns a valid OEmbedResource or raises an ``OEmbedException``.


HTTPProvider
------------

Many popular content sites already provide OEmbed endpoints.  The ``HTTPProvider``
acts as a proxy layer that handles fetching resources and validating them.

Looking in ``oembed_providers.py``, there are numerous providers already set-up
for you.  Here is what the Flickr provider looks like::

    class FlickrProvider(HTTPProvider):
        endpoint_url = 'http://www.flickr.com/services/oembed/'
        regex = 'http://(?:www\.)?flickr\.com/photos/\S+?/(?:sets/)?\d+/?'


DjangoProvider
--------------

The ``DjangoProvider`` class is intended to make writing providers for your 
Django models super easy.  It knows how to introspect your models for 
ImageFields, it can intelligently resize your objects based on user-specified 
dimensions, and it allows you to return HTML rendered through your own templates 
for rich content like videos.

Let's look at a basic example you might use for a Blog::

    # assume the following is our Blog model
    from django.db import models
    from django.core.urlresolvers import reverse
    
    class Entry(models.Model):
        title = models.CharField(max_length=255)
        slug = models.SlugField()
        body = models.TextField()
        author = models.ForeignKey(User)
        published = models.BooleanField()
        pub_date = models.DateTimeField(auto_now_add=True)
    
        def get_absolute_url(self):
            return reverse('blog_detail', args=[self.slug])

The ``urls.py`` defines a list and detail view::

    from django.conf.urls.defaults import *

    urlpatterns = patterns('blog.views',
        url(r'^(?P<entry_slug>[-a-z0-9]+)/$',
            view='blog_detail',
            name='blog_detail'),
        url(r'^$',
            view='blog_list',
            name='blog_index'),
    )
    
Now let's write a provider for it.  This lives in an ``oembed_providers.py`` 
file in your blog app's directory::

    import oembed
    from blog.models import Entry
    from oembed.providers import DjangoProvider
    
    class EntryProvider(DjangoProvider):
        resource_type = 'link' # this is required
        
        class Meta:
            queryset = Entry.objects.filter(published=True)
            named_view = 'blog_detail'
            fields_to_match = {'entry_slug': 'slug'} # map url field to model field
        
        def author_name(self, obj):
            return obj.author.username
        
        def author_url(self, obj):
            return obj.author.get_absolute_url()
        
        def title(self, obj):
            return obj.title

    # don't forget to register your provider
    oembed.site.register(EntryProvider)

You should now be able to hit your API endpoint (by default /oembed/json/) with
a published entry URL and get a JSON response!

One caveat: django provider URLs build their regexes using site domains from the
sites app.  If your site is ``http://www.mysite.com`` and you are running locally,
using ``127.0.0.1:8000``, you will want to give your endpoint URLs as they would
appear on your live site, so:

    http://www.mysite.com/blog/this-is-a-great-entry/
    
    instead of
    
    http://127.0.0.1/blog/this-is-a-great-entry/


DjangoDateBasedProvider
-----------------------

Oftentimes, your content may live a date-based URL.  Writing providers for these
models is simplified by using the ``DjangoDateBasedProvider`` class.  Returning
to the Blog example from above, let's assume the detail view looks like this::

    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{1,2})/(?P<entry_slug>[\w-]+)/$',
        view='blog_detail',
        name='blog_detail'),

The only modification we will make to our ``EntryProvider`` will be to subclass
the date-based provider class::

    from oembed.providers import DjangoDateBasedProvider
    
    class EntryProvider(DjangoDateBasedProvider):
        ...

The date-based provider introspects your model and uses the first DateField or
DateTimeField.  If you have multiple fields of this type, you can explicitly
define a date field::

    from oembed.providers import DjangoDateBasedProvider
    
    class EntryProvider(DjangoDateBasedProvider):
        ...
        class Meta:
            ...
            date_field = 'pub_date'


How are images handled?
-----------------------

By default djangoembed uses PIL to resize images within the dimensional
constraints requested.  The built-in DjangoProvider has a resize_photo() method
and a thumbnail() method that take as their parameters an object and some
dimensions.  These methods call a general-purpose resize() method which
hooks into the image processing backend (by default PIL, but you can write 
your own!) and resizes the photo, returning the url of the resized image and
the new dimensions.
