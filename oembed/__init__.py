#     .--.  
#    /( @ >    ,-.   DJANGOEMBED
#   / ' .'--._/  /
#   :   ,    , .'
#   '. (___.'_/
#    ((-((-'' 
VERSION = (0, 1, 1)

from oembed.sites import site


def autodiscover():
    """
    Automatically build the provider index.
    """
    import imp
    from django.conf import settings
    
    for app in settings.INSTALLED_APPS:
        try:
            app_path = __import__(app, {}, {}, [app.split('.')[-1]]).__path__
        except AttributeError:
            continue
        
        try:
            imp.find_module('oembed_providers', app_path)
        except ImportError:
            continue
        
        __import__("%s.oembed_providers" % app)
