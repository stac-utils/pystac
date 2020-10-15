"""Tests for pystac.extensions.version."""

import datetime
from tests.utils import TestCases
import unittest

import pystac
from pystac.extensions import version

URL_TEMPLATE = 'http://example.com/catalog/%s.json'


def make_item(year):
    """Create basic test items that are only slightly different."""
    asset_id = f'USGS/GAP/CONUS/{year}'
    start = datetime.datetime(year, 1, 2)

    item = pystac.Item(id=asset_id, geometry=None, bbox=None, datetime=start, properties={})
    item.set_self_href(URL_TEMPLATE % year)

    item.ext.enable(pystac.Extensions.VERSION)

    return item


class VersionItemExtTest(unittest.TestCase):
    version = '1.2.3'

    def setUp(self):
        super().setUp()
        self.item = make_item(2011)

        self.item.ext.enable(pystac.Extensions.VERSION)

    def test_stac_extensions(self):
        self.assertEqual([pystac.Extensions.VERSION], self.item.stac_extensions)

    def test_add_version(self):
        self.item.ext.version.apply(self.version)
        self.assertEqual(self.version, self.item.ext.version.version)
        self.assertNotIn('deprecated', self.item.properties)
        self.assertFalse(self.item.ext.version.deprecated)
        self.item.validate()

    def test_version_in_properties(self):
        self.item.ext.version.apply(self.version, deprecated=True)
        self.assertIn('version', self.item.properties)
        self.assertIn('deprecated', self.item.properties)
        self.item.validate()

    def test_add_not_deprecated_version(self):
        self.item.ext.version.apply(self.version, deprecated=False)
        self.assertIn('deprecated', self.item.properties)
        self.assertFalse(self.item.ext.version.deprecated)
        self.item.validate()

    def test_add_deprecated_version(self):
        self.item.ext.version.apply(self.version, deprecated=True)
        self.assertIn('deprecated', self.item.properties)
        self.assertTrue(self.item.ext.version.deprecated)
        self.item.validate()

    def test_latest(self):
        year = 2013
        latest = make_item(year)
        self.item.ext.version.apply(self.version, latest=latest)
        latest_result = self.item.ext.version.latest
        self.assertIs(latest, latest_result)

        expected_href = URL_TEMPLATE % year
        link = self.item.get_links(version.LATEST)[0]
        self.assertEqual(expected_href, link.get_href())
        self.item.validate()

    def test_predecessor(self):
        year = 2010
        predecessor = make_item(year)
        self.item.ext.version.apply(self.version, predecessor=predecessor)
        predecessor_result = self.item.ext.version.predecessor
        self.assertIs(predecessor, predecessor_result)

        expected_href = URL_TEMPLATE % year
        link = self.item.get_links(version.PREDECESSOR)[0]
        self.assertEqual(expected_href, link.get_href())
        self.item.validate()

    def test_successor(self):
        year = 2012
        successor = make_item(year)
        self.item.ext.version.apply(self.version, successor=successor)
        successor_result = self.item.ext.version.successor
        self.assertIs(successor, successor_result)

        expected_href = URL_TEMPLATE % year
        link = self.item.get_links(version.SUCCESSOR)[0]
        self.assertEqual(expected_href, link.get_href())
        self.item.validate()

    def test_fail_validate(self):
        with self.assertRaises(pystac.validation.STACValidationError):
            self.item.validate()

    def test_all_links(self):
        deprecated = True
        latest = make_item(2013)
        predecessor = make_item(2010)
        successor = make_item(2012)
        self.item.ext.version.apply(self.version, deprecated, latest, predecessor, successor)
        self.item.validate()

    def test_full_copy(self):
        cat = TestCases.test_case_1()

        # Fetch two items from the catalog
        item1 = cat.get_item('area-1-1-imagery', recursive=True)
        item2 = cat.get_item('area-2-2-imagery', recursive=True)

        # Enable the version extension on each, and link them
        # as if they are different versions of the same Item
        item1.ext.enable(pystac.Extensions.VERSION)
        item2.ext.enable(pystac.Extensions.VERSION)

        item1.ext.version.apply(version='2.0', predecessor=item2)
        item2.ext.version.apply(version='1.0', successor=item1, latest=item1)

        # Make a full copy of the catalog
        cat_copy = cat.full_copy()

        # Retrieve the copied version of the items
        item1_copy = cat_copy.get_item('area-1-1-imagery', recursive=True)
        item2_copy = cat_copy.get_item('area-2-2-imagery', recursive=True)

        # Check to see if the version links point to the instances of the
        # item objects as they should.
        predecessor = item1_copy.get_single_link(version.PREDECESSOR).target
        successor = item2_copy.get_single_link(version.SUCCESSOR).target
        latest = item2_copy.get_single_link(version.LATEST).target

        self.assertIs(predecessor, item2_copy)
        self.assertIs(successor, item1_copy)
        self.assertIs(latest, item1_copy)


def make_collection(year):
    asset_id = f'my/collection/of/things/{year}'
    start = datetime.datetime(2014, 8, 10)
    end = datetime.datetime(year, 1, 3, 4, 5)
    bboxes = [[-180, -90, 180, 90]]
    spatial_extent = pystac.SpatialExtent(bboxes)
    temporal_extent = pystac.TemporalExtent([[start, end]])
    extent = pystac.Extent(spatial_extent, temporal_extent)

    collection = pystac.Collection(asset_id, 'desc', extent)
    collection.set_self_href(URL_TEMPLATE % year)

    collection.ext.enable(pystac.Extensions.VERSION)

    return collection


class VersionCollectionExtTest(unittest.TestCase):
    version = '1.2.3'

    def setUp(self):
        super().setUp()
        self.collection = make_collection(2011)

    def test_stac_extensions(self):
        self.assertEqual([pystac.Extensions.VERSION], self.collection.stac_extensions)

    def test_add_version(self):
        self.collection.ext.version.apply(self.version)
        self.assertEqual(self.version, self.collection.ext.version.version)
        self.assertNotIn('deprecated', self.collection.extra_fields)
        self.assertFalse(self.collection.ext.version.deprecated)
        self.collection.validate()

    def test_version_deprecated(self):
        self.collection.ext.version.apply(self.version, deprecated=True)
        self.assertIn('version', self.collection.extra_fields)
        self.assertIn('deprecated', self.collection.extra_fields)
        self.collection.validate()

    def test_add_not_deprecated_version(self):
        self.collection.ext.version.apply(self.version, deprecated=False)
        self.assertIn('deprecated', self.collection.extra_fields)
        self.assertFalse(self.collection.ext.version.deprecated)
        self.collection.validate()

    def test_add_deprecated_version(self):
        self.collection.ext.version.apply(self.version, deprecated=True)
        self.assertIn('deprecated', self.collection.extra_fields)
        self.assertTrue(self.collection.ext.version.deprecated)
        self.collection.validate()

    def test_latest(self):
        year = 2013
        latest = make_collection(year)
        self.collection.ext.version.apply(self.version, latest=latest)
        latest_result = self.collection.ext.version.latest
        self.assertIs(latest, latest_result)

        expected_href = URL_TEMPLATE % year
        link = self.collection.get_links(version.LATEST)[0]
        self.assertEqual(expected_href, link.get_href())
        self.collection.validate()

    def test_predecessor(self):
        year = 2010
        predecessor = make_collection(year)
        self.collection.ext.version.apply(self.version, predecessor=predecessor)
        predecessor_result = self.collection.ext.version.predecessor
        self.assertIs(predecessor, predecessor_result)

        expected_href = URL_TEMPLATE % year
        link = self.collection.get_links(version.PREDECESSOR)[0]
        self.assertEqual(expected_href, link.get_href())
        self.collection.validate()

    def test_successor(self):
        year = 2012
        successor = make_collection(year)
        self.collection.ext.version.apply(self.version, successor=successor)
        successor_result = self.collection.ext.version.successor
        self.assertIs(successor, successor_result)

        expected_href = URL_TEMPLATE % year
        link = self.collection.get_links(version.SUCCESSOR)[0]
        self.assertEqual(expected_href, link.get_href())
        self.collection.validate()

    def test_fail_validate(self):
        with self.assertRaises(pystac.validation.STACValidationError):
            self.collection.validate()

    def test_validate_all(self):
        deprecated = True
        latest = make_collection(2013)
        predecessor = make_collection(2010)
        successor = make_collection(2012)
        self.collection.ext.version.apply(self.version, deprecated, latest, predecessor, successor)
        self.collection.validate()

    def test_full_copy(self):
        cat = TestCases.test_case_1()

        # Fetch two collections from the catalog
        col1 = cat.get_child('area-1-1', recursive=True)
        col2 = cat.get_child('area-2-2', recursive=True)

        # Enable the version extension on each, and link them
        # as if they are different versions of the same Collection
        col1.ext.enable(pystac.Extensions.VERSION)
        col2.ext.enable(pystac.Extensions.VERSION)

        col1.ext.version.apply(version='2.0', predecessor=col2)
        col2.ext.version.apply(version='1.0', successor=col1, latest=col1)

        # Make a full copy of the catalog
        cat_copy = cat.full_copy()

        # Retrieve the copied version of the items
        col1_copy = cat_copy.get_child('area-1-1', recursive=True)
        col2_copy = cat_copy.get_child('area-2-2', recursive=True)

        # Check to see if the version links point to the instances of the
        # col objects as they should.
        predecessor = col1_copy.get_single_link(version.PREDECESSOR).target
        successor = col2_copy.get_single_link(version.SUCCESSOR).target
        latest = col2_copy.get_single_link(version.LATEST).target

        self.assertIs(predecessor, col2_copy)
        self.assertIs(successor, col1_copy)
        self.assertIs(latest, col1_copy)


if __name__ == '__main__':
    unittest.main()
