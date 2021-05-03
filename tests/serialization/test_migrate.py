from pystac.extensions.item_assets import ItemAssetsExtension
from pystac.extensions.view import ViewExtension
import unittest

import pystac
from pystac.cache import CollectionCache
from pystac.serialization import (
    identify_stac_object,
    identify_stac_object_type,
    merge_common_properties,
    migrate_to_latest,
)
from pystac.utils import str_to_datetime

from tests.utils import TestCases


class MigrateTest(unittest.TestCase):
    def setUp(self):
        self.examples = [e for e in TestCases.get_examples_info()]

    def test_migrate(self):
        collection_cache = CollectionCache()
        for example in self.examples:
            with self.subTest(example.path):
                path = example.path

                d = pystac.StacIO.default().read_json(path)
                if identify_stac_object_type(d) == pystac.STACObjectType.ITEM:
                    merge_common_properties(
                        d, json_href=path, collection_cache=collection_cache
                    )

                info = identify_stac_object(d)

                migrated_d = migrate_to_latest(d, info)

                migrated_info = identify_stac_object(migrated_d)

                self.assertEqual(migrated_info.object_type, info.object_type)
                self.assertEqual(
                    migrated_info.version_range.latest_valid_version(),
                    pystac.get_stac_version(),
                )

                # Ensure all stac_extensions are schema URIs
                for e_id in migrated_d["stac_extensions"]:
                    self.assertTrue(
                        e_id.endswith(".json"), f"{e_id} is not a JSON schema URI"
                    )

                # Test that PySTAC can read it without errors.
                if info.object_type != pystac.STACObjectType.ITEMCOLLECTION:
                    self.assertIsInstance(
                        pystac.read_dict(migrated_d, href=path), pystac.STACObject
                    )

    def test_migrates_removed_extension(self):
        item = pystac.Item.from_file(
            TestCases.get_path(
                "data-files/examples/0.7.0/extensions/sar/" "examples/sentinel1.json"
            )
        )
        self.assertFalse("dtr" in item.stac_extensions)
        self.assertEqual(
            item.common_metadata.start_datetime,
            str_to_datetime("2018-11-03T23:58:55.121559Z"),
        )

    def test_migrates_added_extension(self):
        item = pystac.Item.from_file(
            TestCases.get_path(
                "data-files/examples/0.8.1/item-spec/" "examples/planet-sample.json"
            )
        )
        self.assertTrue(ViewExtension.has_extension(item))
        view_ext = ViewExtension.ext(item)
        self.assertEqual(view_ext.sun_azimuth, 101.8)
        self.assertEqual(view_ext.sun_elevation, 58.8)
        self.assertEqual(view_ext.off_nadir, 1)

    def test_migrates_renamed_extension(self):
        collection = pystac.Collection.from_file(
            TestCases.get_path(
                "data-files/examples/0.9.0/extensions/asset/"
                "examples/example-landsat8.json"
            )
        )

        self.assertTrue(ItemAssetsExtension.has_extension(collection))
        self.assertIn("item_assets", collection.extra_fields)
