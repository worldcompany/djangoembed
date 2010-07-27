from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify

from oembed.fields import EmbeddedMediaField

class Blog(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    content = models.TextField()
    author = models.CharField(max_length=255)
    pub_date = models.DateTimeField()

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Blog, self).save(*args, **kwargs)

    def get_absolute_url(self):
        year = self.pub_date.year
        month = self.pub_date.strftime('%b').lower()
        day = self.pub_date.day
        return reverse('test_blog_detail', args=[year, month, day, self.slug])

class Category(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='images')
    width = models.IntegerField(blank=True, null=True, editable=False)
    height = models.IntegerField(blank=True, null=True, editable=False)

    def get_absolute_url(self):
        return reverse('test_category_detail', args=[self.pk])

class Rich(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    content = models.TextField()

    media = EmbeddedMediaField(['photo', 'video'], related_name='rich_media')
    photos = EmbeddedMediaField('photo', related_name='rich_photos')
    videos = EmbeddedMediaField('video', related_name='rich_videos')

    def get_absolute_url(self):
        return reverse('test_rich_detail', args=[self.slug])
