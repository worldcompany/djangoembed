Getting Started with OEmbed
===========================

Installation
------------

First, you need to install OEmbed.  It is available at http://github.com/worldcompany/djangoembed/

::

    git clone git://github.com/worldcompany/djangoembed/
    cd djangoembed
    python setup.py install

Adding to your Django Project
--------------------------------

After installing, adding OEmbed consumption to your projects is a snap.  First,
add it to your projects' INSTALLED_APPs and run 'syncdb'::
    
    # settings.py
    INSTALLED_APPS = [
        ...
        'oembed'
    ]

djangoembed uses a registration pattern like the admin's.  In order to be
sure all apps have been loaded, djangoembed should run autodiscover() in the
urls.py.  If you like, you can place this code right below your admin.autodiscover()
bits::
    
    # urls.py
    import oembed
    oembed.autodiscover()

Consuming Resources
-------------------

Now you're ready to start consuming OEmbed-able objects.  There are a couple of
options depending on what you want to do.  The most straightforward way to get
up-and-running is to add it to your templates::

    {% load oembed_tags %}
    
    {% oembed %}blog.content{% endoembed %}

    {# or use the filter #}
    
    {{ blog.content|oembed }}
    
    {# maybe you're working with some dimensional constraints #}
    
    {% oembed "600x600" %}blog.content{% endoembed %}
    
    {{ blog.content|oembed:"600x600" }}

You can consume oembed objects in python as well::

    import oembed
    oembed.autodiscover()
    
    # just get the metadata
    resource = oembed.site.embed('http://www.youtube.com/watch?v=nda_OSWeyn8')
    resource.get_data()
    
    {u'author_name': u'botmib',
     u'author_url': u'http://www.youtube.com/user/botmib',
     u'height': 313,
     u'html': u'<object width="384" height="313"><param name="movie" value="http://www.youtube.com/v/nda_OSWeyn8&fs=1"></param><param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param><embed src="http://www.youtube.com/v/nda_OSWeyn8&fs=1" type="application/x-shockwave-flash" width="384" height="313" allowscriptaccess="always" allowfullscreen="true"></embed></object>',
     u'provider_name': u'YouTube',
     u'provider_url': u'http://www.youtube.com/',
     u'title': u'Leprechaun in Mobile, Alabama',
     u'type': u'video',
     u'version': u'1.0',
     u'width': 384}
    
    # get the metadata and run it through a template for pretty presentation
    from oembed.consumer import OEmbedConsumer
    client = OEmbedConsumer()
    embedded = client.parse_text("http://www.youtube.com/watch?v=nda_OSWeyn8")
    
    <div class="oembed oembed-video provider-youtube">
      <object width="384" height="313">
        <param name="movie" value="http://www.youtube.com/v/nda_OSWeyn8&fs=1"></param>
        <param name="allowFullScreen" value="true"></param>
        <param name="allowscriptaccess" value="always"></param>
        <embed src="http://www.youtube.com/v/nda_OSWeyn8&fs=1" 
               type="application/x-shockwave-flash" 
               width="384" 
               height="313" 
               allowscriptaccess="always" 
               allowfullscreen="true">
        </embed>
      </object>
      <p class="credit">
        <a href="http://www.youtube.com/watch?v=nda_OSWeyn8">Leprechaun in Mobile, Alabama</a>
        by 
        <a href="http://www.youtube.com/user/botmib">botmib</a>
      </p>
    </div>'

Troubleshooting
---------------

Problem: You try the youtube embed example, but all you get is a link to the youtube video.

Solution: Djangoembed uses fixtures to load data about oembed providors like Youtube in to the database.  Try fooling around with syncdb (or migrations, if you're running South) until there are objects of type oembed.storedprovider.

If you have another problem, consider looking through the more extensive docs in the project's doc subdirectory.
