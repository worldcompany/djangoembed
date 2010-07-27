from django.db.models.signals import post_save

import oembed
from oembed.models import StoredProvider

def provider_site_invalidate(sender, instance, created, **kwargs):
    oembed.site.invalidate_providers()

def start_listening():
    post_save.connect(provider_site_invalidate, sender=StoredProvider)
