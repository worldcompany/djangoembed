import Image
import os

class PIL_Resizer(object):
    def resize(self, image_field, new_width, new_height):
        img_file, img_ext = os.path.splitext(image_field.path)
        img_url, img_ext = os.path.splitext(image_field.url)
        
        append = '_%sx%s%s' % (new_width, new_height, img_ext)
        new_url = img_url + append
        if not os.path.isfile(img_file + append):
            img = Image.open(image_field.path)
            img = img.resize((new_width, new_height), Image.ANTIALIAS)
            img.save(img_file + append)
        
        return (new_url, new_width, new_height)
