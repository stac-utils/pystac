import unittest

import pystac
from pystac import (STAC_IO, STACObject)
from pystac.cache import CollectionCache
from pystac.serialization import (identify_stac_object, identify_stac_object_type,
                                  merge_common_properties, migrate_to_latest, STACObjectType)
from pystac.utils import str_to_datetime

from tests.utils import TestCases


class MigrateTest(unittest.TestCase):
    def setUp(self):
        self.examples = [e for e in TestCases.get_examples_info()]

    def test_migrate(self):
        collection_cache = CollectionCache()
        for example in self.examples:
            with self.subTest(example['path']):
                path = example['path']

                d = STAC_IO.read_json(path)
                if identify_stac_object_type(d) == STACObjectType.ITEM:
                    merge_common_properties(d, json_href=path, collection_cache=collection_cache)

                info = identify_stac_object(d)

                migrated_d, info = migrate_to_latest(d, info)

                migrated_info = identify_stac_object(migrated_d)

                self.assertEqual(migrated_info.object_type, info.object_type)
                self.assertEqual(migrated_info.version_range.latest_valid_version(),
                                 pystac.get_stac_version())
                self.assertEqual(set(migrated_info.common_extensions), set(info.common_extensions))
                self.assertEqual(set(migrated_info.custom_extensions), set(info.custom_extensions))

                # Test that PySTAC can read it without errors.
                if info.object_type != STACObjectType.ITEMCOLLECTION:
                    self.assertIsInstance(STAC_IO.stac_object_from_dict(migrated_d, href=path),
                                          STACObject)

    def test_migrates_removed_extension(self):
        item = pystac.read_file(
            TestCases.get_path('data-files/examples/0.7.0/extensions/sar/'
                               'examples/sentinel1.json'))
        self.assertFalse('dtr' in item.stac_extensions)
        self.assertEqual(item.common_metadata.start_datetime,
                         str_to_datetime("2018-11-03T23:58:55.121559Z"))

    def test_migrates_added_extension(self):
        item = pystac.read_file(
            TestCases.get_path('data-files/examples/0.8.1/item-spec/'
                               'examples/planet-sample.json'))
        self.assertTrue('view' in item.stac_extensions)
        self.assertEqual(item.ext.view.sun_azimuth, 101.8)
        self.assertEqual(item.ext.view.sun_elevation, 58.8)
        self.assertEqual(item.ext.view.off_nadir, 1)

    def test_migrates_renamed_extension(self):
        collection = pystac.read_file(
            TestCases.get_path('data-files/examples/0.9.0/extensions/asset/'
                               'examples/example-landsat8.json'))

        self.assertIn('item-assets', collection.stac_extensions)
        self.assertIn('item_assets', collection.extra_fields)
