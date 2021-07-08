"""Tests for pystac.extensions.version."""

import datetime
import unittest
from typing import List, Optional

import pystac
from pystac import ExtensionTypeError
from pystac.extensions import version
from pystac.extensions.version import VersionExtension, VersionRelType
from tests.utils import TestCases

URL_TEMPLATE: str = "http://example.com/catalog/%s.json"


def make_item(year: int) -> pystac.Item:
    """Create basic test items that are only slightly different."""
    asset_id = f"USGS/GAP/CONUS/{year}"
    start = datetime.datetime(year, 1, 2)

    item = pystac.Item(
        id=asset_id, geometry=None, bbox=None, datetime=start, properties={}
    )
    item.set_self_href(URL_TEMPLATE % year)

    VersionExtension.add_to(item)

    return item


class VersionExtensionTest(unittest.TestCase):
    def test_should_raise_exception_when_passing_invalid_extension_object(
        self,
    ) -> None:
        self.assertRaisesRegex(
            ExtensionTypeError,
            r"^Version extension does not apply to type 'object'$",
            VersionExtension.ext,
            object(),
        )


class ItemVersionExtensionTest(unittest.TestCase):
    version: str = "1.2.3"

    def setUp(self) -> None:
        super().setUp()
        self.item = make_item(2011)
        self.example_item_uri = TestCases.get_path("data-files/version/item.json")

    def test_rel_types(self) -> None:
        self.assertEqual(VersionRelType.LATEST.value, "latest-version")
        self.assertEqual(VersionRelType.PREDECESSOR.value, "predecessor-version")
        self.assertEqual(VersionRelType.SUCCESSOR.value, "successor-version")

    def test_stac_extensions(self) -> None:
        self.assertTrue(VersionExtension.has_extension(self.item))

    def test_add_version(self) -> None:
        VersionExtension.ext(self.item).apply(self.version)
        self.assertEqual(self.version, VersionExtension.ext(self.item).version)
        self.assertNotIn(version.DEPRECATED, self.item.properties)
        self.assertFalse(VersionExtension.ext(self.item).deprecated)
        self.item.validate()

    def test_version_in_properties(self) -> None:
        VersionExtension.ext(self.item).apply(self.version, deprecated=True)
        self.assertIn(version.VERSION, self.item.properties)
        self.assertIn(version.DEPRECATED, self.item.properties)
        self.item.validate()

    def test_add_not_deprecated_version(self) -> None:
        VersionExtension.ext(self.item).apply(self.version, deprecated=False)
        self.assertIn(version.DEPRECATED, self.item.properties)
        self.assertFalse(VersionExtension.ext(self.item).deprecated)
        self.item.validate()

    def test_add_deprecated_version(self) -> None:
        VersionExtension.ext(self.item).apply(self.version, deprecated=True)
        self.assertIn(version.DEPRECATED, self.item.properties)
        self.assertTrue(VersionExtension.ext(self.item).deprecated)
        self.item.validate()

    def test_latest(self) -> None:
        year = 2013
        latest = make_item(year)
        VersionExtension.ext(self.item).apply(self.version, latest=latest)
        latest_result = VersionExtension.ext(self.item).latest
        self.assertIs(latest, latest_result)

        expected_href = URL_TEMPLATE % year
        link = self.item.get_links(VersionRelType.LATEST)[0]
        self.assertEqual(expected_href, link.get_href())
        self.item.validate()

    def test_predecessor(self) -> None:
        year = 2010
        predecessor = make_item(year)
        VersionExtension.ext(self.item).apply(self.version, predecessor=predecessor)
        predecessor_result = VersionExtension.ext(self.item).predecessor
        self.assertIs(predecessor, predecessor_result)

        expected_href = URL_TEMPLATE % year
        link = self.item.get_links(VersionRelType.PREDECESSOR)[0]
        self.assertEqual(expected_href, link.get_href())
        self.item.validate()

    def test_successor(self) -> None:
        year = 2012
        successor = make_item(year)
        VersionExtension.ext(self.item).apply(self.version, successor=successor)
        successor_result = VersionExtension.ext(self.item).successor
        self.assertIs(successor, successor_result)

        expected_href = URL_TEMPLATE % year
        link = self.item.get_links(VersionRelType.SUCCESSOR)[0]
        self.assertEqual(expected_href, link.get_href())
        self.item.validate()

    def test_fail_validate(self) -> None:
        with self.assertRaises(pystac.STACValidationError):
            self.item.validate()

    def test_all_links(self) -> None:
        deprecated = True
        latest = make_item(2013)
        predecessor = make_item(2010)
        successor = make_item(2012)
        VersionExtension.ext(self.item).apply(
            self.version, deprecated, latest, predecessor, successor
        )
        self.item.validate()

    def test_full_copy(self) -> None:
        cat = TestCases.test_case_1()

        # Fetch two items from the catalog
        item1 = cat.get_item("area-1-1-imagery", recursive=True)
        item2 = cat.get_item("area-2-2-imagery", recursive=True)

        assert item1 is not None
        assert item2 is not None

        # Enable the version extension on each, and link them
        # as if they are different versions of the same Item
        VersionExtension.add_to(item1)
        VersionExtension.add_to(item2)

        VersionExtension.ext(item1).apply(version="2.0", predecessor=item2)
        VersionExtension.ext(item2).apply(version="1.0", successor=item1, latest=item1)

        # Make a full copy of the catalog
        cat_copy = cat.full_copy()

        # Retrieve the copied version of the items
        item1_copy = cat_copy.get_item("area-1-1-imagery", recursive=True)
        assert item1_copy is not None
        item2_copy = cat_copy.get_item("area-2-2-imagery", recursive=True)
        assert item2_copy is not None

        # Check to see if the version links point to the instances of the
        # item objects as they should.

        predecessor = item1_copy.get_single_link(VersionRelType.PREDECESSOR)
        assert predecessor is not None
        predecessor_target = predecessor.target
        successor = item2_copy.get_single_link(VersionRelType.SUCCESSOR)
        assert successor is not None
        successor_target = successor.target
        latest = item2_copy.get_single_link(VersionRelType.LATEST)
        assert latest is not None
        latest_target = latest.target

        self.assertIs(predecessor_target, item2_copy)
        self.assertIs(successor_target, item1_copy)
        self.assertIs(latest_target, item1_copy)

    def test_setting_none_clears_link(self) -> None:
        deprecated = False
        latest = make_item(2013)
        predecessor = make_item(2010)
        successor = make_item(2012)
        VersionExtension.ext(self.item).apply(
            self.version, deprecated, latest, predecessor, successor
        )

        VersionExtension.ext(self.item).latest = None
        links = self.item.get_links(VersionRelType.LATEST)
        self.assertEqual(0, len(links))
        self.assertIsNone(VersionExtension.ext(self.item).latest)

        VersionExtension.ext(self.item).predecessor = None
        links = self.item.get_links(VersionRelType.PREDECESSOR)
        self.assertEqual(0, len(links))
        self.assertIsNone(VersionExtension.ext(self.item).predecessor)

        VersionExtension.ext(self.item).successor = None
        links = self.item.get_links(VersionRelType.SUCCESSOR)
        self.assertEqual(0, len(links))
        self.assertIsNone(VersionExtension.ext(self.item).successor)

    def test_multiple_link_setting(self) -> None:
        deprecated = False
        latest1 = make_item(2013)
        predecessor1 = make_item(2010)
        successor1 = make_item(2012)
        VersionExtension.ext(self.item).apply(
            self.version, deprecated, latest1, predecessor1, successor1
        )

        year = 2015
        latest2 = make_item(year)
        expected_href = URL_TEMPLATE % year
        VersionExtension.ext(self.item).latest = latest2
        links = self.item.get_links(VersionRelType.LATEST)
        self.assertEqual(1, len(links))
        self.assertEqual(expected_href, links[0].get_href())

        year = 2009
        predecessor2 = make_item(year)
        expected_href = URL_TEMPLATE % year
        VersionExtension.ext(self.item).predecessor = predecessor2
        links = self.item.get_links(VersionRelType.PREDECESSOR)
        self.assertEqual(1, len(links))
        self.assertEqual(expected_href, links[0].get_href())

        year = 2014
        successor2 = make_item(year)
        expected_href = URL_TEMPLATE % year
        VersionExtension.ext(self.item).successor = successor2
        links = self.item.get_links(VersionRelType.SUCCESSOR)
        self.assertEqual(1, len(links))
        self.assertEqual(expected_href, links[0].get_href())

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Item does not include extension URI
        item = pystac.Item.from_file(self.example_item_uri)
        item.stac_extensions.remove(VersionExtension.get_schema_uri())

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = VersionExtension.ext(item)

    def test_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.example_item_uri)
        item.stac_extensions.remove(VersionExtension.get_schema_uri())
        self.assertNotIn(VersionExtension.get_schema_uri(), item.stac_extensions)

        _ = VersionExtension.ext(item, add_if_missing=True)

        self.assertIn(VersionExtension.get_schema_uri(), item.stac_extensions)


def make_collection(year: int) -> pystac.Collection:
    asset_id = f"my/collection/of/things/{year}"
    start = datetime.datetime(2014, 8, 10)
    end = datetime.datetime(year, 1, 3, 4, 5)
    bboxes = [[-180.0, -90.0, 180.0, 90.0]]
    spatial_extent = pystac.SpatialExtent(bboxes)
    intervals: List[List[Optional[datetime.datetime]]] = [[start, end]]
    temporal_extent = pystac.TemporalExtent(intervals)
    extent = pystac.Extent(spatial_extent, temporal_extent)

    collection = pystac.Collection(asset_id, "desc", extent)
    collection.set_self_href(URL_TEMPLATE % year)

    VersionExtension.add_to(collection)

    return collection


class CollectionVersionExtensionTest(unittest.TestCase):
    version: str = "1.2.3"

    def setUp(self) -> None:
        super().setUp()
        self.collection = make_collection(2011)
        self.example_collection_uri = TestCases.get_path(
            "data-files/version/collection.json"
        )

    def test_stac_extensions(self) -> None:
        self.assertTrue(VersionExtension.has_extension(self.collection))

    def test_add_version(self) -> None:
        VersionExtension.ext(self.collection).apply(self.version)
        self.assertEqual(self.version, VersionExtension.ext(self.collection).version)
        self.assertNotIn(version.DEPRECATED, self.collection.extra_fields)
        self.assertFalse(VersionExtension.ext(self.collection).deprecated)
        self.collection.validate()

    def test_version_deprecated(self) -> None:
        VersionExtension.ext(self.collection).apply(self.version, deprecated=True)
        self.assertIn(version.VERSION, self.collection.extra_fields)
        self.assertIn(version.DEPRECATED, self.collection.extra_fields)
        self.collection.validate()

    def test_add_not_deprecated_version(self) -> None:
        VersionExtension.ext(self.collection).apply(self.version, deprecated=False)
        self.assertIn(version.DEPRECATED, self.collection.extra_fields)
        self.assertFalse(VersionExtension.ext(self.collection).deprecated)
        self.collection.validate()

    def test_add_deprecated_version(self) -> None:
        VersionExtension.ext(self.collection).apply(self.version, deprecated=True)
        self.assertIn(version.DEPRECATED, self.collection.extra_fields)
        self.assertTrue(VersionExtension.ext(self.collection).deprecated)
        self.collection.validate()

    def test_latest(self) -> None:
        year = 2013
        latest = make_collection(year)
        VersionExtension.ext(self.collection).apply(self.version, latest=latest)
        latest_result = VersionExtension.ext(self.collection).latest
        self.assertIs(latest, latest_result)

        expected_href = URL_TEMPLATE % year
        link = self.collection.get_links(VersionRelType.LATEST)[0]
        self.assertEqual(expected_href, link.get_href())
        self.collection.validate()

    def test_predecessor(self) -> None:
        year = 2010
        predecessor = make_collection(year)
        VersionExtension.ext(self.collection).apply(
            self.version, predecessor=predecessor
        )
        predecessor_result = VersionExtension.ext(self.collection).predecessor
        self.assertIs(predecessor, predecessor_result)

        expected_href = URL_TEMPLATE % year
        link = self.collection.get_links(VersionRelType.PREDECESSOR)[0]
        self.assertEqual(expected_href, link.get_href())
        self.collection.validate()

    def test_successor(self) -> None:
        year = 2012
        successor = make_collection(year)
        VersionExtension.ext(self.collection).apply(self.version, successor=successor)
        successor_result = VersionExtension.ext(self.collection).successor
        self.assertIs(successor, successor_result)

        expected_href = URL_TEMPLATE % year
        link = self.collection.get_links(VersionRelType.SUCCESSOR)[0]
        self.assertEqual(expected_href, link.get_href())
        self.collection.validate()

    def test_fail_validate(self) -> None:
        with self.assertRaises(pystac.STACValidationError):
            self.collection.validate()

    def test_validate_all(self) -> None:
        deprecated = True
        latest = make_collection(2013)
        predecessor = make_collection(2010)
        successor = make_collection(2012)
        VersionExtension.ext(self.collection).apply(
            self.version, deprecated, latest, predecessor, successor
        )
        self.collection.validate()

    def test_full_copy(self) -> None:
        cat = TestCases.test_case_1()

        # Fetch two collections from the catalog
        col1 = cat.get_child("area-1-1", recursive=True)
        assert isinstance(col1, pystac.Collection)
        col2 = cat.get_child("area-2-2", recursive=True)
        assert isinstance(col2, pystac.Collection)

        # Enable the version extension on each, and link them
        # as if they are different versions of the same Collection
        VersionExtension.add_to(col1)
        VersionExtension.add_to(col2)

        VersionExtension.ext(col1).apply(version="2.0", predecessor=col2)
        VersionExtension.ext(col2).apply(version="1.0", successor=col1, latest=col1)

        # Make a full copy of the catalog
        cat_copy = cat.full_copy()

        # Retrieve the copied version of the items
        col1_copy = cat_copy.get_child("area-1-1", recursive=True)
        assert col1_copy is not None
        col2_copy = cat_copy.get_child("area-2-2", recursive=True)
        assert col2_copy is not None

        # Check to see if the version links point to the instances of the
        # col objects as they should.
        predecessor = col1_copy.get_single_link(VersionRelType.PREDECESSOR)
        assert predecessor is not None
        predecessor_target = predecessor.target
        successor = col2_copy.get_single_link(VersionRelType.SUCCESSOR)
        assert successor is not None
        successor_target = successor.target
        latest = col2_copy.get_single_link(VersionRelType.LATEST)
        assert latest is not None
        latest_target = latest.target

        self.assertIs(predecessor_target, col2_copy)
        self.assertIs(successor_target, col1_copy)
        self.assertIs(latest_target, col1_copy)

    def test_setting_none_clears_link(self) -> None:
        deprecated = False
        latest = make_collection(2013)
        predecessor = make_collection(2010)
        successor = make_collection(2012)
        VersionExtension.ext(self.collection).apply(
            self.version, deprecated, latest, predecessor, successor
        )

        VersionExtension.ext(self.collection).latest = None
        links = self.collection.get_links(VersionRelType.LATEST)
        self.assertEqual(0, len(links))
        self.assertIsNone(VersionExtension.ext(self.collection).latest)

        VersionExtension.ext(self.collection).predecessor = None
        links = self.collection.get_links(VersionRelType.PREDECESSOR)
        self.assertEqual(0, len(links))
        self.assertIsNone(VersionExtension.ext(self.collection).predecessor)

        VersionExtension.ext(self.collection).successor = None
        links = self.collection.get_links(VersionRelType.SUCCESSOR)
        self.assertEqual(0, len(links))
        self.assertIsNone(VersionExtension.ext(self.collection).successor)

    def test_multiple_link_setting(self) -> None:
        deprecated = False
        latest1 = make_collection(2013)
        predecessor1 = make_collection(2010)
        successor1 = make_collection(2012)
        VersionExtension.ext(self.collection).apply(
            self.version, deprecated, latest1, predecessor1, successor1
        )

        year = 2015
        latest2 = make_collection(year)
        expected_href = URL_TEMPLATE % year
        VersionExtension.ext(self.collection).latest = latest2
        links = self.collection.get_links(VersionRelType.LATEST)
        self.assertEqual(1, len(links))
        self.assertEqual(expected_href, links[0].get_href())

        year = 2009
        predecessor2 = make_collection(year)
        expected_href = URL_TEMPLATE % year
        VersionExtension.ext(self.collection).predecessor = predecessor2
        links = self.collection.get_links(VersionRelType.PREDECESSOR)
        self.assertEqual(1, len(links))
        self.assertEqual(expected_href, links[0].get_href())

        year = 2014
        successor2 = make_collection(year)
        expected_href = URL_TEMPLATE % year
        VersionExtension.ext(self.collection).successor = successor2
        links = self.collection.get_links(VersionRelType.SUCCESSOR)
        self.assertEqual(1, len(links))
        self.assertEqual(expected_href, links[0].get_href())

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Collection does not include extension URI
        collection = pystac.Collection.from_file(self.example_collection_uri)
        collection.stac_extensions.remove(VersionExtension.get_schema_uri())

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = VersionExtension.ext(collection)

    def test_ext_add_to(self) -> None:
        collection = pystac.Collection.from_file(self.example_collection_uri)
        collection.stac_extensions.remove(VersionExtension.get_schema_uri())
        self.assertNotIn(VersionExtension.get_schema_uri(), collection.stac_extensions)

        _ = VersionExtension.ext(collection, add_if_missing=True)

        self.assertIn(VersionExtension.get_schema_uri(), collection.stac_extensions)
