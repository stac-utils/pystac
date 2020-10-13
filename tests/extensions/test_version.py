"""Tests for pystac.extensions.version."""

import datetime
import unittest

import pystac
from pystac.extensions import version

URL_TEMPLATE = 'http://example.com/catalog/%s.json'


def MakeItem(year):
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
        self.item = MakeItem(2011)

        self.item.ext.enable(pystac.Extensions.VERSION)

    def tearDown(self):
        super().tearDown()
        self.item.validate()

    def testStacExtensions(self):
        self.assertEqual([pystac.Extensions.VERSION], self.item.stac_extensions)
        # Make sure the item is valid for tearDown check.
        self.item.ext.version.apply(self.version)

    def testAddVersion(self):
        self.item.ext.version.apply(self.version)
        self.assertEqual(self.version, self.item.ext.version.version)
        self.assertNotIn('deprecated', self.item.properties)
        self.assertFalse(self.item.ext.version.deprecated)

    def testVersionInProperties(self):
        self.item.ext.version.apply(self.version, deprecated=True)
        self.assertIn('version', self.item.properties)
        self.assertIn('deprecated', self.item.properties)

    def testAddNotDeprecatedVersion(self):
        self.item.ext.version.apply(self.version, deprecated=False)
        self.assertIn('deprecated', self.item.properties)
        self.assertFalse(self.item.ext.version.deprecated)

    def testAddDeprecatedVersion(self):
        self.item.ext.version.apply(self.version, deprecated=True)
        self.assertIn('deprecated', self.item.properties)
        self.assertTrue(self.item.ext.version.deprecated)

    def testLatest(self):
        year = 2013
        latest = MakeItem(year)
        self.item.ext.version.apply(self.version, latest=latest)
        latest_link = self.item.ext.version.latest_link
        self.assertEqual(version.LATEST_VERSION, latest_link.rel)

        expected_href = URL_TEMPLATE % year
        self.assertEqual(expected_href, latest_link.get_href())

    def testPredecessor(self):
        year = 2010
        predecessor = MakeItem(year)
        self.item.ext.version.apply(self.version, predecessor=predecessor)
        predecessor_link = self.item.ext.version.predecessor_link
        self.assertEqual(version.PREDECESSOR_VERSION, predecessor_link.rel)

        expected_href = URL_TEMPLATE % year
        self.assertEqual(expected_href, predecessor_link.get_href())

    def testSuccessor(self):
        year = 2012
        successor = MakeItem(year)
        self.item.ext.version.apply(self.version, successor=successor)
        successor_link = self.item.ext.version.successor_link
        self.assertEqual(version.SUCCESSOR_VERSION, successor_link.rel)

        expected_href = URL_TEMPLATE % year
        self.assertEqual(expected_href, successor_link.get_href())

    def testFailValidate(self):
        with self.assertRaises(pystac.validation.STACValidationError):
            self.item.validate()

        self.item.ext.version.apply(self.version)

    def testAllLinks(self):
        deprecated = True
        latest = MakeItem(2013)
        predecessor = MakeItem(2010)
        successor = MakeItem(2012)
        self.item.ext.version.apply(self.version, deprecated, latest, predecessor, successor)
        # Just validate in tearDown.


def MakeCollection(year):
    asset_id = 'my/collection/of/things'
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
        self.collection = MakeCollection(2011)

        self.collection.ext.enable(pystac.Extensions.VERSION)

    def tearDown(self):
        super().tearDown()
        self.collection.validate()

    def testStacExtensions(self):
        self.assertEqual([pystac.Extensions.VERSION], self.collection.stac_extensions)
        # Make sure the Collection is valid for tearDown check.
        self.collection.ext.version.apply(self.version)

    def testAddVersion(self):
        self.collection.ext.version.apply(self.version)
        self.assertEqual(self.version, self.collection.ext.version.version)
        self.assertNotIn('deprecated', self.collection.extra_fields)
        self.assertFalse(self.collection.ext.version.deprecated)

    def testVersionDeprecated(self):
        self.collection.ext.version.apply(self.version, deprecated=True)
        self.assertIn('version', self.collection.extra_fields)
        self.assertIn('deprecated', self.collection.extra_fields)

    def testAddNotDeprecatedVersion(self):
        self.collection.ext.version.apply(self.version, deprecated=False)
        self.assertIn('deprecated', self.collection.extra_fields)
        self.assertFalse(self.collection.ext.version.deprecated)

    def testAddDeprecatedVersion(self):
        self.collection.ext.version.apply(self.version, deprecated=True)
        self.assertIn('deprecated', self.collection.extra_fields)
        self.assertTrue(self.collection.ext.version.deprecated)

    def testLatest(self):
        year = 2013
        latest = MakeCollection(year)
        self.collection.ext.version.apply(self.version, latest=latest)
        latest_link = self.collection.ext.version.latest_link
        self.assertEqual(version.LATEST_VERSION, latest_link.rel)

        expected_href = URL_TEMPLATE % year
        self.assertEqual(expected_href, latest_link.get_href())

    def testPredecessor(self):
        year = 2010
        predecessor = MakeCollection(year)
        self.collection.ext.version.apply(self.version, predecessor=predecessor)
        predecessor_link = self.collection.ext.version.predecessor_link
        self.assertEqual(version.PREDECESSOR_VERSION, predecessor_link.rel)

        expected_href = URL_TEMPLATE % year
        self.assertEqual(expected_href, predecessor_link.get_href())

    def testSuccessor(self):
        year = 2012
        successor = MakeCollection(year)
        self.collection.ext.version.apply(self.version, successor=successor)
        successor_link = self.collection.ext.version.successor_link
        self.assertEqual(version.SUCCESSOR_VERSION, successor_link.rel)

        expected_href = URL_TEMPLATE % year
        self.assertEqual(expected_href, successor_link.get_href())

    def testValidateMinimum(self):
        with self.assertRaises(pystac.validation.STACValidationError):
            self.collection.validate()

        self.collection.ext.version.apply(self.version)

    def testValidateAll(self):
        deprecated = True
        latest = MakeCollection(2013)
        predecessor = MakeCollection(2010)
        successor = MakeCollection(2012)
        self.collection.ext.version.apply(self.version, deprecated, latest, predecessor, successor)


if __name__ == '__main__':
    unittest.main()
