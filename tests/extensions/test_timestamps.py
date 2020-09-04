import json
import pystac
import unittest
from datetime import datetime

from pystac import (Extensions, Item)
from pystac.extensions import ExtensionError
from pystac.utils import (str_to_datetime, datetime_to_str)
from tests.utils import (TestCases, test_to_from_dict)


class TimestampsTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.example_uri = TestCases.get_path('data-files/timestamps/example-landsat8.json')
        with open(self.example_uri) as f:
            self.item_dict = json.load(f)
        self.sample_datetime_str = "2020-01-01T00:00:00Z"
        self.sample_datetime = str_to_datetime(self.sample_datetime_str)

    def test_to_from_dict(self):
        test_to_from_dict(self, Item, self.item_dict)

    def test_apply(self):
        item = next(TestCases.test_case_2().get_all_items())
        with self.assertRaises(ExtensionError):
            item.ext.timestamps

        item.ext.enable(Extensions.TIMESTAMPS)
        self.assertIn(Extensions.TIMESTAMPS, item.stac_extensions)
        item.ext.timestamps.apply(published=str_to_datetime("2020-01-03T06:45:55Z"),
                                  expires=str_to_datetime("2020-02-03T06:45:55Z"),
                                  unpublished=str_to_datetime("2020-03-03T06:45:55Z"))

        for d in [
                item.ext.timestamps.published, item.ext.timestamps.expires,
                item.ext.timestamps.unpublished
        ]:
            self.assertIsInstance(d, datetime)

        for p in ('published', 'expires', 'unpublished'):
            self.assertIsInstance(item.properties[p], str)

        published_str = "2020-04-03T06:45:55Z"
        item.ext.timestamps.apply(published=str_to_datetime(published_str))
        self.assertIsInstance(item.ext.timestamps.published, datetime)
        self.assertEqual(item.properties['published'], published_str)

        for d in [item.ext.timestamps.expires, item.ext.timestamps.unpublished]:
            self.assertIsNone(d)

        for p in ('expires', 'unpublished'):
            self.assertIsNone(item.properties[p])

    def test_validate_timestamps(self):
        item = pystac.read_file(self.example_uri)
        item.validate()

    def test_expires(self):
        timestamps_item = pystac.read_file(self.example_uri)

        # Get
        self.assertIn("expires", timestamps_item.properties)
        timestamps_expires = timestamps_item.ext.timestamps.expires
        self.assertIsInstance(timestamps_expires, datetime)
        self.assertEqual(datetime_to_str(timestamps_expires), timestamps_item.properties['expires'])

        # Set
        timestamps_item.ext.timestamps.expires = self.sample_datetime
        self.assertEqual(self.sample_datetime_str, timestamps_item.properties['expires'])

        # Get from Asset
        asset_no_prop = timestamps_item.assets['red']
        asset_prop = timestamps_item.assets['blue']
        self.assertEqual(timestamps_item.ext.timestamps.get_expires(asset_no_prop),
                         timestamps_item.ext.timestamps.get_expires())
        self.assertEqual(timestamps_item.ext.timestamps.get_expires(asset_prop),
                         str_to_datetime("2018-12-02T00:00:00Z"))

        # # Set to Asset
        asset_value = str_to_datetime("2019-02-02T00:00:00Z")
        timestamps_item.ext.timestamps.set_expires(asset_value, asset_no_prop)
        self.assertNotEqual(timestamps_item.ext.timestamps.get_expires(asset_no_prop),
                            timestamps_item.ext.timestamps.get_expires())
        self.assertEqual(timestamps_item.ext.timestamps.get_expires(asset_no_prop), asset_value)

        # Validate
        timestamps_item.validate()

    def test_published(self):
        timestamps_item = pystac.read_file(self.example_uri)

        # Get
        self.assertIn("published", timestamps_item.properties)
        timestamps_published = timestamps_item.ext.timestamps.published
        self.assertIsInstance(timestamps_published, datetime)
        self.assertEqual(datetime_to_str(timestamps_published),
                         timestamps_item.properties['published'])

        # Set
        timestamps_item.ext.timestamps.published = self.sample_datetime
        self.assertEqual(self.sample_datetime_str, timestamps_item.properties['published'])

        # Get from Asset
        asset_no_prop = timestamps_item.assets['red']
        asset_prop = timestamps_item.assets['blue']
        self.assertEqual(timestamps_item.ext.timestamps.get_published(asset_no_prop),
                         timestamps_item.ext.timestamps.get_published())
        self.assertEqual(timestamps_item.ext.timestamps.get_published(asset_prop),
                         str_to_datetime("2018-11-02T00:00:00Z"))

        # # Set to Asset
        asset_value = str_to_datetime("2019-02-02T00:00:00Z")
        timestamps_item.ext.timestamps.set_published(asset_value, asset_no_prop)
        self.assertNotEqual(timestamps_item.ext.timestamps.get_published(asset_no_prop),
                            timestamps_item.ext.timestamps.get_published())
        self.assertEqual(timestamps_item.ext.timestamps.get_published(asset_no_prop), asset_value)

        # Validate
        timestamps_item.validate()

    def test_unpublished(self):
        timestamps_item = pystac.read_file(self.example_uri)

        # Get
        self.assertNotIn("unpublished", timestamps_item.properties)
        timestamps_unpublished = timestamps_item.ext.timestamps.unpublished
        self.assertIsNone(timestamps_unpublished, datetime)

        # Set
        timestamps_item.ext.timestamps.unpublished = self.sample_datetime
        self.assertEqual(self.sample_datetime_str, timestamps_item.properties['unpublished'])

        # Get from Asset
        asset_no_prop = timestamps_item.assets['red']
        asset_prop = timestamps_item.assets['blue']
        self.assertEqual(timestamps_item.ext.timestamps.get_unpublished(asset_no_prop),
                         timestamps_item.ext.timestamps.get_unpublished())
        self.assertEqual(timestamps_item.ext.timestamps.get_unpublished(asset_prop),
                         str_to_datetime("2019-01-02T00:00:00Z"))

        # Set to Asset
        asset_value = str_to_datetime("2019-02-02T00:00:00Z")
        timestamps_item.ext.timestamps.set_unpublished(asset_value, asset_no_prop)
        self.assertNotEqual(timestamps_item.ext.timestamps.get_unpublished(asset_no_prop),
                            timestamps_item.ext.timestamps.get_unpublished())
        self.assertEqual(timestamps_item.ext.timestamps.get_unpublished(asset_no_prop), asset_value)

        # Validate
        timestamps_item.validate()
