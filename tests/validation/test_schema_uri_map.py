import unittest

import pystac
from pystac.validation.schema_uri_map import DefaultSchemaUriMap


class SchemaUriMapTest(unittest.TestCase):
    def test_gets_extension_for_old_version(self):
        d = DefaultSchemaUriMap()
        uri = d.get_extension_schema_uri('asset', pystac.STACObjectType.COLLECTION, '0.8.0')

        self.assertEqual(
            uri, 'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.8.0/'
            'extensions/asset/json-schema/schema.json')
