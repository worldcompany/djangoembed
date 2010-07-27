import oembed
from oembed.providers import DjangoDateBasedProvider, DjangoProvider
from oembed.utils import size_to_nearest

from oembed.tests.models import Blog, Category, Rich

class BlogProvider(DjangoDateBasedProvider):
    resource_type = 'link'
    
    class Meta:
        model = Blog
        named_view = 'test_blog_detail'
        fields_to_match = {'entry_slug': 'slug'}
        date_field = 'pub_date'

    def author_name(self, obj):
        return obj.author
    
    def title(self, obj):
        return obj.title

class CategoryProvider(DjangoProvider):
    resource_type = 'photo'
    
    class Meta:
        model = Category
        named_view = 'test_category_detail'
        fields_to_match = {'_0': 'pk'}
    
    def title(self, obj):
        return obj.name

class RichProvider(DjangoProvider):
    resource_type = 'rich'
    
    class Meta:
        model = Rich
        named_view = 'test_rich_detail'
        fields_to_match = {'_0': 'slug'}
    
    def title(self, obj):
        return obj.name

oembed.site.register(BlogProvider)
oembed.site.register(CategoryProvider)
oembed.site.register(RichProvider)
