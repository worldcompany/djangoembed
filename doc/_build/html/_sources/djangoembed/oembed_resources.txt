OEmbed Resources
================

Resources are the objects returned by an OEmbed endpoint.  The OEmbed spec
defines 4 resource types:

* Video
* Photo
* Rich
* Link


Basic Metadata
--------------

Regardless of which resource type you are dealing with, the same metadata may be
provided:

* type (required)
    The resource type. Valid values, along with value-specific parameters, are described below.
* version (required)
    The oEmbed version number. This must be 1.0.
* title (optional)
    A text title, describing the resource.
* author_name (optional)
    The name of the author/owner of the resource.
* author_url (optional)
    A URL for the author/owner of the resource.
* provider_name (optional)
    The name of the resource provider.
* provider_url (optional)
    The url of the resource provider.
* cache_age (optional)
    The suggested cache lifetime for this resource, in seconds. Consumers may choose to use this value or not.
* thumbnail_url (optional)
    A URL to a thumbnail image representing the resource. The thumbnail must respect any maxwidth and maxheight parameters. If this paramater is present, thumbnail_width and thumbnail_height must also be present.
* thumbnail_width (optional)
    The width of the optional thumbnail. If this paramater is present, thumbnail_url and thumbnail_height must also be present.
* thumbnail_height (optional)
    The height of the optional thumbnail. If this paramater is present, thumbnail_url and thumbnail_width must also be present. 


Video Resources
---------------

Video resources are embeddable video players, and are returned by providers like
YouTube and Vimeo.  Every video resource **must** provide the following
metadata:

* html (required)
    The HTML required to embed a video player. The HTML should have no padding 
    or margins. Consumers may wish to load the HTML in an off-domain iframe to 
    avoid XSS vulnerabilities.
* width (required)
    The width in pixels required to display the HTML.
* height (required)
    The height in pixels required to display the HTML.

Responses of this type must obey the maxwidth and maxheight request parameters. 
If a provider wishes the consumer to just provide a thumbnail, rather than an 
embeddable player, they should instead return a photo response type.


Photo Resources
---------------

Photo resources are static photos. The following parameters are defined:

* url (required)
    The source URL of the image. Consumers should be able to insert this URL 
    into an <img> element. Only HTTP and HTTPS URLs are valid.
* width (required)
    The width in pixels of the image specified in the url parameter.
* height (required)
    The height in pixels of the image specified in the url parameter.

Responses of this type must obey the maxwidth and maxheight request parameters.


Rich Resources
--------------

This type is used for rich HTML content that does not fall under one of the 
other categories. The following parameters are defined:

* html (required)
    The HTML required to display the resource. The HTML should have no padding 
    or margins. Consumers may wish to load the HTML in an off-domain iframe to 
    avoid XSS vulnerabilities. The markup should be valid XHTML 1.0 Basic.
* width (required)
    The width in pixels required to display the HTML.
* height (required)
    The height in pixels required to display the HTML.

Responses of this type must obey the maxwidth and maxheight request parameters.


Link Resources
--------------

Responses of this type allow a provider to return any generic embed data 
(such as title and author_name), without providing either the url or html 
parameters. The consumer may then link to the resource, using the URL specified 
in the original request.


Resource Validation
-------------------

djangoembed validates resources for you!
