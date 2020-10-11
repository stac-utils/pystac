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


class VersionTest(unittest.TestCase):
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

    def testVersionInProperties(self):
        self.item.ext.version.apply(self.version, deprecated=True)
        self.assertIn('version', self.item.properties)
        self.assertIn('deprecated', self.item.properties)

    def testAddVersion(self):
        self.item.ext.version.apply(self.version)
        self.assertEqual(self.version, self.item.ext.version.version)
        self.assertNotIn('deprecated', self.item.properties)
        self.assertFalse(self.item.ext.version.deprecated)

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

    def testAllLinks(self):
        deprecated = True
        latest = MakeItem(2013)
        predecessor = MakeItem(2010)
        successor = MakeItem(2012)
        self.item.ext.version.apply(self.version, deprecated, latest, predecessor, successor)
        # Just validate in tearDown.


if __name__ == '__main__':
    unittest.main()
