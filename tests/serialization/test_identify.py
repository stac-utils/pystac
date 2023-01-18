import unittest

import pytest

import pystac
from pystac.cache import CollectionCache
from pystac.serialization import (
    identify_stac_object,
    identify_stac_object_type,
    merge_common_properties,
)
from pystac.serialization.identify import STACVersionID, STACVersionRange
from tests.utils import TestCases
from tests.utils.test_cases import ExampleInfo


class TestIdentify:
    @pytest.mark.parametrize("example", TestCases.get_examples_info())
    def test_identify(self, example: ExampleInfo) -> None:
        collection_cache = CollectionCache()
        path = example.path
        d = pystac.StacIO.default().read_json(path)
        if identify_stac_object_type(d) == pystac.STACObjectType.ITEM:
            merge_common_properties(
                d, json_href=path, collection_cache=collection_cache
            )

        actual = identify_stac_object(d)
        # Explicitly cover __repr__ functions in tests
        str_info = str(actual)
        assert isinstance(str_info, str)

        msg = "Failed {}:".format(path)

        assert actual.object_type == example.object_type, msg
        version_contained_in_range = actual.version_range.contains(example.stac_version)
        assert version_contained_in_range, msg
        assert set(actual.extensions) == set(example.extensions), msg

    def test_identify_non_stac_type(self) -> None:
        plain_feature_dict = {
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "Point", "coordinates": [0, 0]},
        }

        assert identify_stac_object_type(plain_feature_dict) is None

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

        with pytest.raises(pystac.STACTypeError) as ctx:
            identify_stac_object(invalid_dict)

        assert "JSON does not represent a STAC object" in str(ctx.value.args[0])

    def test_identify_non_stac_raises_error(self) -> None:
        plain_feature_dict = {
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "Point", "coordinates": [0, 0]},
        }

        with pytest.raises(pystac.STACTypeError) as ctx:
            identify_stac_object(plain_feature_dict)

        assert "JSON does not represent a STAC object" in str(ctx.value.args[0])

    def test_identify_invalid_with_stac_version(self) -> None:
        not_stac = {"stac_version": "0.9.0", "type": "Custom"}

        assert identify_stac_object_type(not_stac) is None


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
