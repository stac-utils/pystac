import unittest

import pystac
from pystac.cache import CollectionCache
from pystac.serialization import (
    identify_stac_object,
    identify_stac_object_type,
    merge_common_properties,
)
from pystac.serialization.identify import STACVersionRange, STACVersionID

from tests.utils import TestCases


class IdentifyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.examples = TestCases.get_examples_info()

    def test_identify(self) -> None:
        collection_cache = CollectionCache()
        for example in self.examples:
            with self.subTest(example.path):
                path = example.path
                d = pystac.StacIO.default().read_json(path)
                if identify_stac_object_type(d) == pystac.STACObjectType.ITEM:
                    merge_common_properties(
                        d, json_href=path, collection_cache=collection_cache
                    )

                actual = identify_stac_object(d)
                # Explicitly cover __repr__ functions in tests
                str_info = str(actual)
                self.assertIsInstance(str_info, str)

                msg = "Failed {}:".format(path)

                self.assertEqual(actual.object_type, example.object_type, msg=msg)
                version_contained_in_range = actual.version_range.contains(
                    example.stac_version
                )
                self.assertTrue(version_contained_in_range, msg=msg)
                self.assertEqual(
                    set(actual.extensions), set(example.extensions), msg=msg
                )

    def test_identify_non_stac_type(self) -> None:
        plain_feature_dict = {
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "Point", "coordinates": [0, 0]},
        }

        self.assertIsNone(identify_stac_object_type(plain_feature_dict))

    def test_identify_invalid_stac_object_with_version(self) -> None:
        # Has stac_version but is not a valid STAC object
        invalid_dict = {
            "id": "concepts",
            "title": "Concepts catalogs",
            "links": [
                {
                    "rel": "self",
                    "type": "application/json",
                    "href": "https://tamn.snapplanet.io/catalogs/concepts",
                },
                {
                    "rel": "root",
                    "type": "application/json",
                    "href": "https://tamn.snapplanet.io",
                },
            ],
            "stac_version": "1.0.0",
        }

        with self.assertRaises(pystac.STACTypeError) as ctx:
            identify_stac_object(invalid_dict)

        self.assertIn("JSON does not represent a STAC object", str(ctx.exception))

    def test_identify_non_stac_raises_error(self) -> None:
        plain_feature_dict = {
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "Point", "coordinates": [0, 0]},
        }

        with self.assertRaises(pystac.STACTypeError) as ctx:
            identify_stac_object(plain_feature_dict)

        self.assertIn("JSON does not represent a STAC object", str(ctx.exception))

    def test_identify_invalid_with_stac_version(self) -> None:
        not_stac = {"stac_version": "0.9.0", "type": "Custom"}

        self.assertIsNone(identify_stac_object_type(not_stac))


class VersionTest(unittest.TestCase):
    def test_version_ordering(self) -> None:
        self.assertEqual(STACVersionID("0.9.0"), STACVersionID("0.9.0"))
        self.assertFalse(STACVersionID("0.9.0") < STACVersionID("0.9.0"))
        self.assertFalse(STACVersionID("0.9.0") != STACVersionID("0.9.0"))
        self.assertFalse(STACVersionID("0.9.0") > STACVersionID("0.9.0"))
        self.assertTrue(STACVersionID("1.0.0-beta.2") < "1.0.0")
        self.assertTrue(STACVersionID("0.9.1") > "0.9.0")
        self.assertFalse(STACVersionID("0.9.0") > "0.9.0")
        self.assertTrue(STACVersionID("0.9.0") <= "0.9.0")
        self.assertTrue(STACVersionID("1.0.0-beta.1") <= STACVersionID("1.0.0-beta.2"))
        self.assertFalse(STACVersionID("1.0.0") < STACVersionID("1.0.0-beta.2"))

    def test_version_range_ordering(self) -> None:
        version_range = STACVersionRange("0.9.0", "1.0.0-beta.2")
        self.assertIsInstance(str(version_range), str)
        self.assertTrue(version_range.contains("1.0.0-beta.1"))
        self.assertFalse(version_range.contains("1.0.0"))
        self.assertTrue(version_range.is_later_than("0.8.9"))

        version_range = STACVersionRange("0.9.0", "1.0.0-beta.1")
        self.assertFalse(version_range.contains("1.0.0-beta.2"))

        version_range = STACVersionRange(min_version="0.6.0-rc1", max_version="0.9.0")
        self.assertTrue(version_range.contains("0.9.0"))
