import datetime
import re

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import signals
from django.utils import simplejson as json

from oembed.constants import DEFAULT_OEMBED_TTL, MIN_OEMBED_TTL, RESOURCE_TYPES
from oembed.exceptions import AlreadyRegistered, NotRegistered, OEmbedMissingEndpoint, OEmbedException
from oembed.models import StoredOEmbed, StoredProvider
from oembed.providers import BaseProvider, DjangoProvider
from oembed.resources import OEmbedResource
from oembed.utils import fetch_url, relative_to_full


class ProviderSite(object):
    def __init__(self):
        self.clear()
    
    def invalidate_providers(self):
        self._populated = False
    
    def clear(self):
        self._registry = {}
        self._registered_providers = []
        self.invalidate_providers()
    
    def register(self, provider_class):
        """
        Registers a provider with the site.
        """
        if not issubclass(provider_class, BaseProvider):
            raise TypeError('%s is not a subclass of BaseProvider' % provider_class.__name__)
        
        if provider_class in self._registered_providers:
            raise AlreadyRegistered('%s is already registered' % provider_class.__name__)
        
        if issubclass(provider_class, DjangoProvider):
            # set up signal handler for cache invalidation
            signals.post_save.connect(
                self.invalidate_stored_oembeds,
                sender=provider_class._meta.model
            )
        
        # don't build the regex yet - if not all urlconfs have been loaded
        # and processed at this point, the DjangoProvider instances will fail
        # when attempting to reverse urlpatterns that haven't been created.
        # Rather, the regex-list will be populated once, on-demand.
        self._registered_providers.append(provider_class)
        
        # flag for re-population
        self.invalidate_providers()
    
    def unregister(self, provider_class):
        """
        Unregisters a provider from the site.
        """
        if not issubclass(provider_class, BaseProvider):
            raise TypeError('%s must be a subclass of BaseProvider' % provider_class.__name__)
        
        if provider_class not in self._registered_providers:
            raise NotRegistered('%s is not registered' % provider_class.__name__)
        
        self._registered_providers.remove(provider_class)
        
        # flag for repopulation
        self.invalidate_providers()
    
    def populate(self):
        """
        Populate the internal registry's dictionary with the regexes for each
        provider instance
        """
        self._registry = {}
        
        for provider_class in self._registered_providers:
            instance = provider_class()
            self._registry[instance] = instance.regex
        
        for stored_provider in StoredProvider.objects.active():
            self._registry[stored_provider] = stored_provider.regex
        
        self._populated = True
    
    def ensure_populated(self):
        """
        Ensure not only that the internal registry of Python-class providers is
        populated, but also make sure the cached queryset of database-providers
        is up-to-date
        """
        if not self._populated:
            self.populate()
    
    def get_registry(self):
        """
        Return a dictionary of {provider_instance: regex}
        """
        self.ensure_populated()
        return self._registry

    def get_providers(self):
        """Provide a list of all oembed providers that are being used."""
        return self.get_registry().keys()
    
    def provider_for_url(self, url):
        """
        Find the right provider for a URL
        """
        for provider, regex in self.get_registry().items():
            if re.match(regex, url) is not None:
                return provider
        
        raise OEmbedMissingEndpoint('No endpoint matches URL: %s' % url)
    
    def invalidate_stored_oembeds(self, sender, instance, created, **kwargs):
        """
        A hook for django-based oembed providers to delete any stored oembeds
        """
        ctype = ContentType.objects.get_for_model(instance)
        StoredOEmbed.objects.filter(
            object_id=instance.pk,
            content_type=ctype).delete()
    
    def embed(self, url, **kwargs):
        """
        The heart of the matter
        """
        try:
            # first figure out the provider
            provider = self.provider_for_url(url)
        except OEmbedMissingEndpoint:
            raise
        else:
            try:
                # check the database for a cached response, because of certain
                # race conditions that exist with get_or_create(), do a filter
                # lookup and just grab the first item
                stored_match = StoredOEmbed.objects.filter(
                    match=url, 
                    maxwidth=kwargs.get('maxwidth', None), 
                    maxheight=kwargs.get('maxheight', None),
                    date_expires__gte=datetime.datetime.now())[0]
                return OEmbedResource.create_json(stored_match.response_json)
            except IndexError:
                # query the endpoint and cache response in db
                # prevent None from being passed in as a GET param
                params = dict([(k, v) for k, v in kwargs.items() if v])
                
                # request an oembed resource for the url
                resource = provider.request_resource(url, **params)
                
                try:
                    cache_age = int(resource.cache_age)
                    if cache_age < MIN_OEMBED_TTL:
                        cache_age = MIN_OEMBED_TTL
                except:
                    cache_age = DEFAULT_OEMBED_TTL
                
                date_expires = datetime.datetime.now() + datetime.timedelta(seconds=cache_age)
                
                stored_oembed, created = StoredOEmbed.objects.get_or_create(
                    match=url,
                    maxwidth=kwargs.get('maxwidth', None),
                    maxheight=kwargs.get('maxheight', None))
                
                stored_oembed.response_json = resource.json
                stored_oembed.resource_type = resource.type
                stored_oembed.date_expires = date_expires
                
                if resource.content_object:
                    stored_oembed.content_object = resource.content_object
                
                stored_oembed.save()
                return resource
    
    def autodiscover(self, url):
        """
        Load up StoredProviders from url if it is an oembed scheme
        """
        headers, response = fetch_url(url)
        if headers['content-type'].split(';')[0] in ('application/json', 'text/javascript'):
            provider_data = json.loads(response)
            return self.store_providers(provider_data)
    
    def store_providers(self, provider_data):
        """
        Iterate over the returned json and try to sort out any new providers
        """
        if not hasattr(provider_data, '__iter__'):
            raise OEmbedException('Autodiscovered response not iterable')
        
        provider_pks = []
        
        for provider in provider_data:
            if 'endpoint' not in provider or \
               'matches' not in provider:
                continue
            
            resource_type = provider.get('type')
            if resource_type not in RESOURCE_TYPES:
                continue
            
            stored_provider, created = StoredProvider.objects.get_or_create(
                wildcard_regex=provider['matches']
            )
            
            if created:
                stored_provider.endpoint_url = relative_to_full(    
                    provider['endpoint'],
                    provider['matches']
                )
                stored_provider.resource_type = resource_type
                stored_provider.save()
            
            provider_pks.append(stored_provider.pk)
        
        return StoredProvider.objects.filter(pk__in=provider_pks)     

# just like django admin
site = ProviderSite()
