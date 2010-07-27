The OEmbed Spec
===============

The full spec is available at http://www.oembed.com - this overview will touch
on everything without going into too much detail to get you up and running with
OEmbed quickly!

What is OEmbed?
---------------

    "oEmbed is a format for allowing an embedded representation of a URL on 
    third party sites. The simple API allows a website to display embedded 
    content (such as photos or videos) when a user posts a link to that 
    resource, without having to parse the resource directly."

What problem does it solve?
---------------------------

One of the tasks we as web developers run into a lot is the need to integrate
rich third-party content into our own sites.  Numerous REST APIs exist for this 
purpose, but suppose we are only concerned with metadata?

REST APIs make it difficult to extract metadata in a generic way:
 * URL structures vary (/statuses/update.json, /users/show.json)
 * attribute names are not standardized
 * metadata provided is content-dependant (twitter returns tweets, flickr photos)
 * authentication can be a pain
 * response formats vary

OEmbed aims at solving these problems by:
 * Endpoint lives at one place, like /oembed/json/
 * attribute names are standard, including 'title', 'author', 'thumbnail_url'
 * resource types are standard, being 'video', 'photo', 'link', 'rich'
 * response format must be JSON or XML

OEmbed is not a REST API.  It is a *READ* API.  It allows you to retrieve 
metadata about the objects you're interested in, using a single endpoint.

The best part?  **All you need to provide the endpoint is the URL you want 
metadata about**.

An Example
----------

::

    curl http://www.flickr.com/services/oembed/?url=http%3A//www.flickr.com/photos/bees/2341623661/

    <?xml version="1.0" encoding="utf-8" standalone="yes"?>
    <oembed>
	    <version>1.0</version>
	    <type>photo</type>
	    <title>ZB8T0193</title>
	    <author_name>‮‭‬bees‬</author_name>
	    <author_url>http://www.flickr.com/photos/bees/</author_url>
	    <cache_age>3600</cache_age>
	    <provider_name>Flickr</provider_name>
	    <provider_url>http://www.flickr.com/</provider_url>
	    <width>500</width>
	    <height>333</height>
	    <url>http://farm4.static.flickr.com/3123/2341623661_7c99f48bbf.jpg</url>
    </oembed>

In the example above, we pass a flickr photo-detail URL to their OEmbed endpoint.
Flickr then returns a wealth of metadata about the object, including the image's
URL, width and height.

OEmbed endpoints also can accept other arguments, like a **maxwidth**, or **format**:

::

    curl http://www.flickr.com/services/oembed/?url=http%3A//www.flickr.com/photos/bees/2341623661/\&maxwidth=300\&format=json

    {
      "version":"1.0",
      "type":"photo",
      "title":"ZB8T0193",
      "author_name":"\u202e\u202d\u202cbees\u202c",
      "author_url":"http:\/\/www.flickr.com\/photos\/bees\/",
      "cache_age":3600,
      "provider_name":"Flickr",
      "provider_url":"http:\/\/www.flickr.com\/",
      "width":"240",
      "height":"160",
      "url":"http:\/\/farm4.static.flickr.com\/3123\/2341623661_7c99f48bbf_m.jpg"
    }

As you can see from the response, the returned image width is now 240.  If a
maximum width (or height) is specified, the provider must respect that.
