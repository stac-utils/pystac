import unittest

from pystac import (STAC_IO, STAC_VERSION, STACObject)
from pystac.cache import CollectionCache
from pystac.serialization import (identify_stac_object, identify_stac_object_type,
                                  merge_common_properties, migrate_to_latest, STACObjectType)

from tests.utils import TestCases


class MigrateTest(unittest.TestCase):
    def setUp(self):
        self.examples = [
            e for e in TestCases.get_examples_info() if e['stac_version'] < STAC_VERSION
        ]

    def test_migrate(self):
        collection_cache = CollectionCache()
        for example in self.examples:
            path = example['path']
            d = STAC_IO.read_json(path)
            if identify_stac_object_type(d) == STACObjectType.ITEM:
                merge_common_properties(d, json_href=path, collection_cache=collection_cache)

            info = identify_stac_object(d)

            migrated_d = migrate_to_latest(d, info)

            migrated_info = identify_stac_object(migrated_d)

            self.assertEqual(migrated_info.object_type, info.object_type)
            self.assertEqual(migrated_info.version_range.latest_valid_version(), STAC_VERSION)
            self.assertEqual(set(migrated_info.common_extensions), set(info.common_extensions))
            self.assertEqual(set(migrated_info.custom_extensions), set(info.custom_extensions))

            # Test that PySTAC can read it without errors.
            self.assertIsInstance(STAC_IO.stac_object_from_dict(migrated_d, href=path), STACObject)
