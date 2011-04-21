import Image
import os
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.core.files import File
from django.core.files.storage import default_storage


class PIL_Resizer(object):
    def resize(self, image_field, new_width, new_height):
        img_url, img_ext = os.path.splitext(image_field.url)
        img_path, img_ext = os.path.splitext(image_field.name)
        
        append = '_%sx%s%s' % (new_width, new_height, img_ext)

        new_url = img_url + append
        new_path = img_path + append

        if not default_storage.exists(new_path):
            # load a file-like object at the image path
            source_file = default_storage.open(img_path)

            # load up the image using PIL and retrieve format
            img = Image.open(image_field.path)
            format = img.format
            
            # perform resize
            img = img.resize((new_width, new_height), Image.ANTIALIAS)

            # create a file-like object to store resized data
            img_buffer = StringIO()
            img.MAXBLOCK = 1024*1024
            img.save(img_buffer, format=format)

            # save data
            default_storage.save(new_path, File(img_buffer))
        
        return (new_url, new_width, new_height)
