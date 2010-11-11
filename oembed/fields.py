import re

from django.db import models
from django.db.models import signals, Max
from django.db.models.fields import TextField

import oembed
from oembed.constants import URL_RE
from oembed.exceptions import OEmbedMissingEndpoint
from oembed.models import AggregateMedia


class FieldRegistry(object):
    """
    FieldRegistry -> modified Borg pattern from Marty Alchin's Pro Django
    """
    _registry = {}
    
    @classmethod
    def add_field(cls, model, field):
        reg = cls._registry.setdefault(model, [])
        reg.append(field)
    
    @classmethod
    def get_fields(cls, model):
        return cls._registry.get(model, [])
    
    @classmethod
    def __contains__(cls, model):
        return model in cls._registry


class EmbeddedSignalCreator(object):
    def __init__(self, field):
        self.field = field
        self.name = '_%s' % self.field.name
    
    def contribute_to_class(self, cls, name):
        register_field(cls, self.field)


class EmbeddedMediaField(models.ManyToManyField):
    def __init__(self, media_type=None, to=None, **kwargs):
        if media_type and not isinstance(media_type, (basestring, list)):
            raise TypeError('media_type must be either a list or string')
        elif isinstance(media_type, basestring):
            media_type = [media_type]
        self.media_type = media_type
        
        super(EmbeddedMediaField, self).__init__(AggregateMedia, **kwargs)
    
    def contribute_to_class(self, cls, name):
        """
        I need a way to ensure that this signal gets created for all child
        models, and since model inheritance doesn't have a 'contrubite_to_class'
        style hook, I am creating a fake virtual field which will be added to
        all subclasses and handles creating the signal
        """
        super(EmbeddedMediaField, self).contribute_to_class(cls, name)
        register_field(cls, self)
        
        # add a virtual field that will create signals on any/all subclasses
        cls._meta.add_virtual_field(EmbeddedSignalCreator(self))


def register_field(cls, field):
    """
    Handles registering the fields with the FieldRegistry and creating a 
    post-save signal for the model.
    """
    FieldRegistry.add_field(cls, field)
    
    signals.post_save.connect(handle_save_embeds, sender=cls,
            dispatch_uid='%s.%s.%s' % \
            (cls._meta.app_label, cls._meta.module_name, field.name))
    

def handle_save_embeds(sender, instance, **kwargs):
    embedded_media_fields = FieldRegistry.get_fields(sender)
    if not embedded_media_fields:
        return
    
    urls = []
    for field in instance._meta.fields:
        if isinstance(field, TextField):
            urls.extend(re.findall(URL_RE, getattr(instance, field.name)))

    urls = set(urls)
    for embedded_field in embedded_media_fields:
        m2m = getattr(instance, embedded_field.name)
        m2m.clear()
        for url in urls:
            try:
                provider = oembed.site.provider_for_url(url)
            except OEmbedMissingEndpoint:
                pass
            else:
                if not embedded_field.media_type or \
                        provider.resource_type in embedded_field.media_type:
                    media_obj, created = AggregateMedia.objects.get_or_create(url=url)
                    m2m.add(media_obj)

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([
        (
            [EmbeddedMediaField], # Class(es) these apply to
            [],         # Positional arguments (not used)
            {           # Keyword argument
                "media_type": ["media_type", {}],
            },
        ),
    ], ["^oembed\.fields\.EmbeddedMediaField"])

except ImportError:
    pass
