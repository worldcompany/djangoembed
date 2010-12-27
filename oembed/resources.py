from django.utils import simplejson

from oembed.exceptions import OEmbedException

class OEmbedResource(object):
    """
    OEmbed resource, as well as a factory for creating resource instances
    from response json
    """
    _data = {}
    content_object = None
    
    def __getattr__(self, name):
        return self._data.get(name)
    
    def get_data(self):
        return self._data
        
    def load_data(self, data):
        self._data = data
    
    @property
    def json(self):
        return simplejson.dumps(self._data)
    
    @classmethod
    def create(cls, data):
        if not 'type' in data or not 'version' in data:
            raise OEmbedException('Missing required fields on OEmbed response.')

        data['width'] = data.get('width') and int(data['width']) or None
        data['height'] = data.get('height') and int(data['height']) or None
        
        filtered_data = dict([(k, v) for k, v in data.items() if v])
        
        resource = cls()
        resource.load_data(filtered_data)
        
        return resource

    @classmethod
    def create_json(cls, raw):
        data = simplejson.loads(raw)
        return cls.create(data)
