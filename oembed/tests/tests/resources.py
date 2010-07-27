import oembed

from oembed.tests.tests.base import BaseOEmbedTestCase
from oembed.resources import OEmbedResource


class ResourceTestCase(BaseOEmbedTestCase):
    def test_json_handling(self):
        resource = oembed.site.embed(self.category_url)

        json = resource.json
        another_resource = OEmbedResource.create_json(json)

        self.assertEqual(resource.get_data(), another_resource.get_data())
