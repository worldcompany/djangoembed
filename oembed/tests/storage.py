import os
from urllib2 import urlparse
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.conf import settings
from django.core.files import storage


class DummyMemoryStorage(storage.Storage):
    """
    A simple in-memory storage backend for testing image storage - copied from
    djutils (http://github.com/coleifer/djutils/)
    """
    _files = {} # bampf
    
    def delete(self, name):
        if name in self._files:
            del(self._files[name])
    
    def exists(self, name):
        return name in self._files
    
    def listdir(self, path):
        files = []
        if not path.endswith('/'):
            path += '/' # make sure ends in slash for string comp below
        for k in self._files:
            if k.startswith(path) and '/' not in k.replace(path, ''):
                files.append(k.replace(path, ''))
    
    def size(self, name):
        return len(self._files[name])
    
    def url(self, name):
        return urlparse.urljoin(settings.MEDIA_URL, name)
    
    def _open(self, name, mode):
        return StringIO(self._files.get(name, ''))
    
    def _save(self, name, content):
        content.seek(0)
        self._files[name] = content.read()
        return name
    
    def get_valid_name(self, name):
        return name
    
    def get_available_name(self, name):
        if name not in self._files:
            return name
        
        base_path, ext = os.path.splitext(name)
        counter = 1
        
        while 1:
            test = '%s_%s%s' % (base_path, counter, ext)
            if test not in self._files:
                return test
            counter += 1
