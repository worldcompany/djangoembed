from django import VERSION
from django.conf import settings
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import simplejson

from oembed.constants import RESOURCE_CHOICES
from oembed.providers import HTTPProvider


if VERSION < (1, 2):
    db_engine = settings.DATABASE_ENGINE
else:
    db_engine = settings.DATABASES['default']['ENGINE']


class StoredOEmbed(models.Model):
    match = models.TextField()
    response_json = models.TextField()
    resource_type = models.CharField(choices=RESOURCE_CHOICES, editable=False, max_length=8)
    date_added = models.DateTimeField(auto_now_add=True)
    date_expires = models.DateTimeField(blank=True, null=True)
    maxwidth = models.IntegerField(blank=True, null=True)
    maxheight = models.IntegerField(blank=True, null=True)

    # generic bits
    object_id = models.IntegerField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True,
            related_name="related_%(class)s")
    content_object = GenericForeignKey()

    class Meta:
        ordering = ('-date_added',)
        verbose_name = 'stored OEmbed'
        verbose_name_plural = 'stored OEmbeds'
        if 'mysql' not in db_engine:
            unique_together = ('match', 'maxwidth', 'maxheight')

    def __unicode__(self):
        return self.match
    
    @property
    def response(self):
        return simplejson.loads(self.response_json)


class StoredProviderManager(models.Manager):
    def active(self):
        return self.filter(active=True)

class StoredProvider(models.Model, HTTPProvider):
    """
    Essentially, a stored proxy provider that mimics the interface of a python
    HTTPProvider - used for autodiscovery
    """
    endpoint_url = models.CharField(max_length=255)
    regex = models.CharField(max_length=255)
    wildcard_regex = models.CharField(max_length=255, blank=True,
        help_text='Wild-card version of regex')
    resource_type = models.CharField(choices=RESOURCE_CHOICES, max_length=8)
    active = models.BooleanField(default=False)
    provides = models.BooleanField(default=False, help_text='Provide upstream')
    scheme_url = models.CharField(max_length=255, blank=True)

    objects = StoredProviderManager()

    class Meta:
        ordering = ('endpoint_url', 'resource_type', 'wildcard_regex')

    def __unicode__(self):
        return self.wildcard_regex

    def save(self, *args, **kwargs):
        if not self.regex:
            # convert wildcard to non-greedy 'match anything' regex
            self.regex = self.wildcard_regex.replace('*', '.+?')
        super(StoredProvider, self).save(*args, **kwargs)

    @property
    def url_scheme(self):
        if self.provides and self.wildcard_regex:
            return self.wildcard_regex


class AggregateMediaDescriptor(property):
    def contribute_to_class(self, cls, name):
        self.name = name
        setattr(cls, self.name, self)
        
    def __get__(self, instance, cls=None):
        if instance.content_object:
            return instance.content_object
        try:
            import oembed
            resource = oembed.site.embed(instance.url)
            if resource.content_object:
                instance.content_object = resource.content_object
                instance.save()
                return instance.content_object
            else:
                stored_oembed = StoredOEmbed.objects.filter(
                        match=instance.url)[0]
                return stored_oembed
        except:
            pass

    def __set__(self, instance, value):
        raise NotImplementedError('%s is read-only' % self.name)


class AggregateMedia(models.Model):
    url = models.TextField()
    object_id = models.IntegerField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True,
            related_name="aggregate_media")
    content_object = GenericForeignKey()
    
    media = AggregateMediaDescriptor()
    
    def __unicode__(self):
        return self.url
    
    def get_absolute_url(self):
        if self.content_object and hasattr(self.content_object, 'get_absolute_url'):
            return self.content_object.get_absolute_url()
        return self.url


from oembed.listeners import start_listening
start_listening()
