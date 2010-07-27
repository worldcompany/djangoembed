from django.contrib import admin

from oembed.tests.models import Blog, Category

admin.site.register(Blog)
admin.site.register(Category)
