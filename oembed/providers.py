import datetime
import httplib2
import re
import time
from urllib import urlencode

try:
    import Image
except ImportError:
    from PIL import Image
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.files import storage
from django.core.urlresolvers import get_resolver
from django.db.models.fields import DateTimeField, DateField
from django.db.models.fields.files import ImageField, ImageFieldFile
from django.template import RequestContext, Context
from django.template.loader import render_to_string, get_template
from django.utils import simplejson

from oembed.constants import OEMBED_ALLOWED_SIZES, OEMBED_THUMBNAIL_SIZE
from oembed.exceptions import OEmbedException, OEmbedHTTPException
from oembed.image_processors import image_processor
from oembed.resources import OEmbedResource
from oembed.utils import (fetch_url, get_domain, mock_request, cleaned_sites, 
    size_to_nearest, relative_to_full, scale)


resolver = get_resolver(None)


class BaseProvider(object):
    """
    Base class for OEmbed resources.
    """
    regex = None # regex this provider will match
    provides = True  # allow this provider to be accessed by third parties
    
    def request_resource(self, url, **kwargs):
        """
        Get an OEmbedResource from one of the providers configured in this 
        provider according to the resource url.
        
        Args:
            url: The url of the resource to get.
            format: Desired response format (json or xml).
            **kwargs: Optional parameters to pass in to the provider.
        
        Returns:
            OEmbedResource object.
            
        If no object returned, raises OEmbedException
        """
        raise NotImplementedError


class HTTPProvider(BaseProvider):
    """
    Provider class for HTTP providers, like YouTube - basically
    a proxy.
    """
    endpoint_url = ''
    provides = False # since this is generally a proxy to a pre-existing oembed
                     # provider, do not re-provide it
    
    # NOTE: these attributes are only required if provides = True
    # see http://oembed.com/ section 2.1 for how to define
    # but the gist is, this is a list of urls with wildcards
    # indicating what will match, instead of regex bits, i.e.
    # http://flickr.com/photos/*
    url_scheme = None
    resource_type = None # one of 'photo', 'video', 'rich' or 'link'
    
    def __init__(self):
        self._validate()
    
    def _validate(self):
        if self.provides and (not self.url_scheme or not self.resource_type):
            raise AttributeError(
                'If you want to provide %s up-stream, a url_scheme and ' \
                'resource_type must be specified' % self.__name__)
        if self.provides and self.resource_type not in ('photo', 'video', 'rich', 'link'):
            raise ValueError('resource_type must be one of "photo", "video", "rich" or "link"')
    
    def _fetch(self, url):
        """
        Fetches from a URL, respecting GZip encoding, etc.
        
        Returns an OEmbedResource instance
        """
        return fetch_url(url)
    
    def convert_to_resource(self, headers, raw_response, params):
        if 'content-type' not in headers:
            raise OEmbedException('Missing mime-type in response')
        
        content_type = headers['content-type'].split(';')[0]
        
        if content_type in ('text/javascript', 'application/json'):
            try:
                json_response = simplejson.loads(raw_response)
                resource = OEmbedResource.create(json_response)
            except ValueError:
                raise OEmbedException('Unable to parse response json')
        else:
            raise OEmbedException('Invalid mime-type - %s' % headers['content-type'])
        return resource
    
    def request_resource(self, url, **kwargs):
        """
        Request an OEmbedResource for a given url.  Some valid keyword args:
        - format
        - maxwidth
        - maxheight
        """
        params = kwargs
        
        params['url'] = url
        params['format'] = 'json'
        
        if '?' in self.endpoint_url:
            url_with_qs = '%s&%s' % (self.endpoint_url.rstrip('&'), urlencode(params))
        else:
            url_with_qs = "%s?%s" % (self.endpoint_url, urlencode(params))
        
        headers, raw_response = self._fetch(url_with_qs)
        resource = self.convert_to_resource(headers, raw_response, params)
        
        return resource


class DjangoProviderOptions(object):
    model = None         # required
    named_view = ''      # required: the name of this models' detail view
    fields_to_match = {} # mapping of regex_field -> model attr for lookups
    
    valid_sizes = OEMBED_ALLOWED_SIZES
    thumbnail_sizes = OEMBED_THUMBNAIL_SIZE
    image_processor = image_processor()
    force_fit = False
    
    year_part = 'year'
    month_part = 'month'
    day_part = 'day'

    context_varname = 'object'
    
    abstract = False
    
    def __init__(self, meta_options, provider_class):
        for k, v in meta_options.__dict__.items():
            if not k.startswith('_'):
                # because we are using properties, which are descriptors,
                # an AttributeError will be raised if we try to setattr()
                # to change a property (like image_field), so make changes
                # to the __dict__ instead
                self.__dict__[k] = v
        
        self.provider_class = provider_class
        
        if not self.abstract:
            self._validate()
            if not getattr(self, 'template_name', None):
                self.template_name = 'oembed/provider/%s_%s.html' % (
                    self.model._meta.app_label, self.model._meta.module_name
                )
    
    def _validate(self):
        if self.model is None:
            raise OEmbedException('Provider %s requires a model' % self.provider_class.__name__)
        if not self.named_view:
            raise OEmbedException('Provider %s requires a named_view' % self.provider_class.__name__)
    
    def _image_field(self):
        """
        Try to automatically detect an image field
        """
        for field in self.model._meta.fields:
            if isinstance(field, ImageField):
                return field.name
    image_field = property(_image_field)
    
    def _date_field(self):
        """
        Try to automatically detect an image field
        """
        for field in self.model._meta.fields:
            if isinstance(field, (DateTimeField, DateField)):
                return field.name
    date_field = property(_date_field)


class DjangoProviderMetaclass(type):
    def __new__(cls, name, bases, attrs):
        """
        Provides namespacing of Meta options
        """
        # these are any overrides defined on the incoming provider class
        meta = attrs.pop('Meta', None)
        
        provider_class = super(DjangoProviderMetaclass, cls).__new__(
            cls, name, bases, attrs)
        
        # see if the provider class is extending any class that has its own
        # set of overrides
        for b in bases:
            base_meta = getattr(b, '_meta', None)
            if not base_meta:
                continue
            
            for (k, v) in base_meta.__dict__.items():
                if not k.startswith('_') and k != 'abstract' and k not in meta.__dict__:
                    meta.__dict__[k] = v
        
        if meta:
            # instantiate the options class, passing in our provider
            _meta = DjangoProviderOptions(meta, provider_class)
            
            # bolt the options onto the new provider class
            provider_class._meta = _meta
        
        return provider_class


class DjangoProvider(BaseProvider):
    """
    Provider class for Django apps
    
    Examples:
    
    class PhotoProvider(DjangoProvider):
        class Meta:
            model = Photo
            named_view = 'photo_detail'
            fields_to_match = {'object_id': 'id'}
        
        def author_name(self, obj):
            return obj.user.username
        
        def title(self, obj):
            return obj.title
    
    class VideoProvider(DjangoDateBasedProvider):
        class Meta:
            model = Video
            named_view = 'video_detail'
            fields_to_match = {'slug': 'slug'}
        
            valid_sizes = ((400, 300), (600, 450)) # embed will automatically resize
            force_fit = True # don't scale dimensions, force fit
        
        def html(self, obj):
            return self.render_html(
                obj,
                context=Context({'width': self.width, 'height': self.height}), 
                context_varname='video')
        
        ...
    """
    __metaclass__ = DjangoProviderMetaclass
    
    resource_type = None # photo, link, video or rich
    
    def __init__(self):
        self._validate()
    
    def _validate(self):
        if self.resource_type not in ('photo', 'video', 'rich', 'link'):
            raise ValueError('resource_type must be one of "photo", "video", "rich" or "link"')
    
    def _build_regex(self):
        """
        Performs a reverse lookup on a named view and generates
        a list of regexes that match that object.  It generates
        regexes with the domain name included, using sites provided
        by the get_sites() method.
        
        >>> regex = provider.regex
        >>> regex.pattern
        'http://(www2.kusports.com|www2.ljworld.com|www.lawrence.com)/photos/(?P<year>\\d{4})/(?P<month>\\w{3})/(?P<day>\\d{1,2})/(?P<object_id>\\d+)/$'
        """
        # get the regexes from the urlconf
        url_patterns = resolver.reverse_dict.get(self._meta.named_view)
        
        try:
            regex = url_patterns[1]
        except TypeError:
            raise OEmbedException('Error looking up %s' % self._meta.named_view)
        
        # get a list of normalized domains
        cleaned_sites = self.get_cleaned_sites()
        
        site_regexes = []
        
        for site in self.get_sites():
            site_regexes.append(cleaned_sites[site.pk][0])
        
        # join the sites together with the regex 'or'
        sites = '|'.join(site_regexes)
        
        # create URL-matching regexes for sites
        regex = re.compile('(%s)/%s' % (sites, regex))
        
        return regex
    regex = property(_build_regex)
    
    def get_sites(self):
        """
        Return sites whose domains should be checked against
        """
        return Site.objects.all()
    
    def get_cleaned_sites(self):
        """
        Attribute-caches the sites/regexes returned by
        `oembed.utils.cleaned_sites`
        """
        if not getattr(self, '_clean_sites', None):
            self._clean_sites = cleaned_sites()
        return self._clean_sites
    
    def provider_from_url(self, url):
        """
        Given a URL for any of our sites, try and match it to one, returning
        the domain & name of the match.  If no match is found, return current.
        
        Returns a tuple of domain, site name -- used to determine 'provider'
        """
        domain = get_domain(url)
        site_tuples = self.get_cleaned_sites().values()
        for domain_re, name, normalized_domain in site_tuples:
            if re.match(domain_re, domain):
                return normalized_domain, name
        site = Site.objects.get_current()
        return site.domain, site.name
    
    def get_params(self, url):
        """
        Extract the named parameters from a url regex.  If the url regex does not contain
        named parameters, they will be keyed _0, _1, ...
        
        * Named parameters
        Regex:
        /photos/^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{1,2})/(?P<object_id>\d+)/
        
        URL:
        http://www2.ljworld.com/photos/2009/oct/11/12345/
        
        Return Value:
        {u'day': '11', u'month': 'oct', u'object_id': '12345', u'year': '2009'}
        
        * Unnamed parameters
        Regex:
        /blah/([\w-]+)/(\d+)/
        
        URL:
        http://www.example.com/blah/hello/123/
        
        Return Value:
        {u'_0': 'hello', u'_1': '123'}
        """
        match = re.match(self.regex, url)
        if match is not None:
            params = match.groupdict()
            if not params:
                params = {}
                for i, group in enumerate(match.groups()[1:]):
                    params['_%s' % i] = group
            return params
        
        raise OEmbedException('No regex matched the url %s' % (url))
    
    def get_queryset(self):
        return self._meta.model._default_manager.all()
    
    def get_object(self, url):
        """
        Fields to match is a mapping of url params to fields, so for
        the photos example above, it would be:
        
        fields_to_match = { 'object_id': 'id' }
        
        This procedure parses out named params from a URL and then uses
        the fields_to_match dictionary to generate a query.
        """
        params = self.get_params(url)
        query = {}
        for key, value in self._meta.fields_to_match.iteritems():
            try:
                query[value] = params[key]
            except KeyError:
                raise OEmbedException('%s was not found in the urlpattern parameters.  Valid names are: %s' % (key, ', '.join(params.keys())))
        
        try:
            obj = self.get_queryset().get(**query)
        except self._meta.model.DoesNotExist:
            raise OEmbedException('Requested object not found')
        
        return obj
    
    def render_html(self, obj, context=None):
        """
        Generate the 'html' attribute of an oembed resource using a template.
        Sort of a corollary to the parser's render_oembed method.  By default,
        the current mapping will be passed in as the context.
        
        OEmbed templates are stored in:
        
        oembed/provider/[app_label]_[model].html
        
        -- or --
        
        oembed/provider/media_video.html
        """        
        provided_context = context or Context()
        context = RequestContext(mock_request())
        context.update(provided_context)
        
        context.push()
        context[self._meta.context_varname] = obj
        rendered = render_to_string(self._meta.template_name, context)
        context.pop()
        return rendered
    
    def map_attr(self, mapping, attr, obj):
        """
        A kind of cheesy method that allows for callables or attributes to
        be used interchangably
        """
        if attr not in mapping and hasattr(self, attr):
            if not callable(getattr(self, attr)):
                mapping[attr] = getattr(self, attr)
            else:
                mapping[attr] = getattr(self, attr)(obj)
    
    def get_image(self, obj):
        """
        Return an ImageFileField instance
        """
        if self._meta.image_field:
            return getattr(obj, self._meta.image_field)
    
    def resize(self, image_field, new_width=None, new_height=None):
        """
        Resize an image to the 'best fit' width & height, maintaining
        the scale of the image, so a 500x500 image sized to 300x400
        will actually be scaled to 300x300.
        
        Params:
        image: ImageFieldFile to be resized (i.e. model.image_field)
        new_width & new_height: desired maximums for resizing
        
        Returns:
        the url to the new image and the new width & height
        (http://path-to-new-image, 300, 300)
        """
        if isinstance(image_field, ImageFieldFile) and \
           image_field.field.width_field and \
           image_field.field.height_field:
            # use model fields
            current_width = getattr(image_field.instance, image_field.field.width_field)
            current_height = getattr(image_field.instance, image_field.field.height_field)
        else:
            # use PIL
            try:
                file_obj = storage.default_storage.open(image_field.name, 'rb')
                img_obj = Image.open(file_obj)
                current_width, current_height = img_obj.size
            except IOError:
                return (image_field.url, 0, 0) 
        
        # determine if resizing needs to be done (will not scale up)
        if current_width < new_width:
            if not new_height or current_height < new_height:
                return (image_field.url, current_width, current_height)
        
        # calculate ratios
        new_width, new_height = scale(current_width, current_height, new_width, new_height)
        
        # use the image_processor defined in the settings, or PIL by default
        return self._meta.image_processor.resize(image_field, new_width, new_height)
    
    def resize_photo(self, obj, mapping, maxwidth=None, maxheight=None):
        url, width, height = self.resize(
            self.get_image(obj), 
            *size_to_nearest(maxwidth, maxheight, self._meta.valid_sizes))
        mapping.update(url=url, width=width, height=height)
        
    def thumbnail(self, obj, mapping):
        url, width, height = self.resize(
            self.get_image(obj), 
            *size_to_nearest(allowed_sizes=self._meta.thumbnail_sizes))
        mapping.update(thumbnail_url=url, thumbnail_width=width, 
                       thumbnail_height=height)
    
    def preprocess(self, obj, mapping, **kwargs):
        """
        Pre-processing hook.  Called by map_to_dictionary()
        """
        pass
    
    def postprocess(self, obj, mapping, **kwargs):
        """
        Post-processing hook.  Called by map_to_dictionary()
        """
        pass
    
    def map_to_dictionary(self, url, obj, **kwargs):
        """
        Build a dictionary of metadata for the requested object.
        """
        maxwidth = kwargs.get('maxwidth', None)
        maxheight = kwargs.get('maxheight', None)
        
        provider_url, provider_name = self.provider_from_url(url)
        
        mapping = {
            'version': '1.0',
            'url': url,
            'provider_name': provider_name,
            'provider_url': provider_url,
            'type': self.resource_type
        }
        
        # a hook
        self.preprocess(obj, mapping, **kwargs)
        
        # resize image if we have a photo, otherwise use the given maximums
        if self.resource_type == 'photo' and self.get_image(obj):
            self.resize_photo(obj, mapping, maxwidth, maxheight)
        elif self.resource_type in ('video', 'rich', 'photo'):
            width, height = size_to_nearest(
                maxwidth,
                maxheight,
                self._meta.valid_sizes,
                self._meta.force_fit
            )
            mapping.update(width=width, height=height)
        
        # create a thumbnail
        if self.get_image(obj):
            self.thumbnail(obj, mapping)
        
        # map attributes to the mapping dictionary.  if the attribute is
        # a callable, it must have an argument signature of
        # (self, obj)
        for attr in ('title', 'author_name', 'author_url', 'html'):
            self.map_attr(mapping, attr, obj)
        
        # fix any urls
        if 'url' in mapping:
            mapping['url'] = relative_to_full(mapping['url'], url)
        
        if 'thumbnail_url' in mapping:
            mapping['thumbnail_url'] = relative_to_full(mapping['thumbnail_url'], url)
        
        if 'html' not in mapping and mapping['type'] in ('video', 'rich'):
            mapping['html'] = self.render_html(obj, context=Context(mapping))
        
        # a hook
        self.postprocess(obj, mapping, **kwargs)
        
        return mapping
    
    def request_resource(self, url, **kwargs):
        """
        Request an OEmbedResource for a given url.  Some valid keyword args:
        - format
        - maxwidth
        - maxheight
        """
        obj = self.get_object(url)
        
        mapping = self.map_to_dictionary(url, obj, **kwargs)
        
        resource = OEmbedResource.create(mapping)
        resource.content_object = obj
        
        return resource

class DjangoDateBasedProvider(DjangoProvider):
    """
    Provider for Django models that use date-based urls
    """
    def _validate(self):
        super(DjangoDateBasedProvider, self)._validate()
        if not self._meta.date_field:
            raise OEmbedException('date_field not found for %s' % self.__class__.__name__)
    
    def get_object(self, url, month_format='%b', day_format='%d'):
        """
        Parses the date from a url and uses it in the query.  For objects which
        are unique for date.
        """
        params = self.get_params(url)
        try:
            year = params[self._meta.year_part]
            month = params[self._meta.month_part]
            day = params[self._meta.day_part]
        except KeyError:
            try:
                # named lookups failed, so try to get the date using the first
                # three parameters
                year, month, day = params['_0'], params['_1'], params['_2']
            except KeyError:
                raise OEmbedException('Error extracting date from url parameters')
        
        try:
            tt = time.strptime('%s-%s-%s' % (year, month, day),
                               '%s-%s-%s' % ('%Y', month_format, day_format))
            date = datetime.date(*tt[:3])
        except ValueError:
            raise OEmbedException('Error parsing date from: %s' % url)

        # apply the date-specific lookups
        if isinstance(self._meta.model._meta.get_field(self._meta.date_field), DateTimeField):
            min_date = datetime.datetime.combine(date, datetime.time.min)
            max_date = datetime.datetime.combine(date, datetime.time.max)
            query = {'%s__range' % self._meta.date_field: (min_date, max_date)}
        else:
            query = {self._meta.date_field: date}
        
        # apply the regular search lookups
        for key, value in self._meta.fields_to_match.iteritems():
            try:
                query[value] = params[key]
            except KeyError:
                raise OEmbedException('%s was not found in the urlpattern parameters.  Valid names are: %s' % (key, ', '.join(params.keys())))
        
        try:
            obj = self.get_queryset().get(**query)
        except self._meta.model.DoesNotExist:
            raise OEmbedException('Requested object not found')
        
        return obj
