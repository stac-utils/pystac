import json
import unittest
from datetime import datetime

import pystac
from pystac.extensions.timestamps import TimestampsExtension
from pystac.utils import get_opt, str_to_datetime, datetime_to_str
from tests.utils import TestCases, test_to_from_dict


class TimestampsTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.example_uri = TestCases.get_path(
            "data-files/timestamps/example-landsat8.json"
        )
        with open(self.example_uri) as f:
            self.item_dict = json.load(f)
        self.sample_datetime_str = "2020-01-01T00:00:00Z"
        self.sample_datetime = str_to_datetime(self.sample_datetime_str)

    def test_to_from_dict(self):
        test_to_from_dict(self, pystac.Item, self.item_dict)

    def test_apply(self):
        item = next(iter(TestCases.test_case_2().get_all_items()))
        self.assertFalse(TimestampsExtension.has_extension(item))

        TimestampsExtension.add_to(item)
        self.assertTrue(TimestampsExtension.has_extension(item))
        TimestampsExtension.ext(item).apply(
            published=str_to_datetime("2020-01-03T06:45:55Z"),
            expires=str_to_datetime("2020-02-03T06:45:55Z"),
            unpublished=str_to_datetime("2020-03-03T06:45:55Z"),
        )

        for d in [
            TimestampsExtension.ext(item).published,
            TimestampsExtension.ext(item).expires,
            TimestampsExtension.ext(item).unpublished,
        ]:
            self.assertIsInstance(d, datetime)

        for p in ("published", "expires", "unpublished"):
            self.assertIsInstance(item.properties[p], str)

        published_str = "2020-04-03T06:45:55Z"
        TimestampsExtension.ext(item).apply(published=str_to_datetime(published_str))
        self.assertIsInstance(TimestampsExtension.ext(item).published, datetime)
        self.assertEqual(item.properties["published"], published_str)

        for d in [
            TimestampsExtension.ext(item).expires,
            TimestampsExtension.ext(item).unpublished,
        ]:
            self.assertIsNone(d)

        for p in ("expires", "unpublished"):
            self.assertNotIn(p, item.properties)

    def test_validate_timestamps(self):
        item = pystac.read_file(self.example_uri)
        item.validate()

    def test_expires(self):
        timestamps_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("expires", timestamps_item.properties)
        timestamps_expires = TimestampsExtension.ext(timestamps_item).expires
        self.assertIsInstance(timestamps_expires, datetime)
        self.assertEqual(
            datetime_to_str(get_opt(timestamps_expires)),
            timestamps_item.properties["expires"],
        )

        # Set
        TimestampsExtension.ext(timestamps_item).expires = self.sample_datetime
        self.assertEqual(
            self.sample_datetime_str, timestamps_item.properties["expires"]
        )

        # Get from Asset
        asset_no_prop = timestamps_item.assets["red"]
        asset_prop = timestamps_item.assets["blue"]
        self.assertEqual(
            TimestampsExtension.ext(asset_no_prop).expires,
            TimestampsExtension.ext(timestamps_item).expires,
        )
        self.assertEqual(
            TimestampsExtension.ext(asset_prop).expires,
            str_to_datetime("2018-12-02T00:00:00Z"),
        )

        # # Set to Asset
        asset_value = str_to_datetime("2019-02-02T00:00:00Z")
        TimestampsExtension.ext(asset_no_prop).expires = asset_value
        self.assertNotEqual(
            TimestampsExtension.ext(asset_no_prop).expires,
            TimestampsExtension.ext(timestamps_item).expires,
        )
        self.assertEqual(TimestampsExtension.ext(asset_no_prop).expires, asset_value)

        # Validate
        timestamps_item.validate()

    def test_published(self):
        timestamps_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("published", timestamps_item.properties)
        timestamps_published = TimestampsExtension.ext(timestamps_item).published
        self.assertIsInstance(timestamps_published, datetime)
        self.assertEqual(
            datetime_to_str(get_opt(timestamps_published)),
            timestamps_item.properties["published"],
        )

        # Set
        TimestampsExtension.ext(timestamps_item).published = self.sample_datetime
        self.assertEqual(
            self.sample_datetime_str, timestamps_item.properties["published"]
        )

        # Get from Asset
        asset_no_prop = timestamps_item.assets["red"]
        asset_prop = timestamps_item.assets["blue"]
        self.assertEqual(
            TimestampsExtension.ext(asset_no_prop).published,
            TimestampsExtension.ext(timestamps_item).published,
        )
        self.assertEqual(
            TimestampsExtension.ext(asset_prop).published,
            str_to_datetime("2018-11-02T00:00:00Z"),
        )

        # # Set to Asset
        asset_value = str_to_datetime("2019-02-02T00:00:00Z")
        TimestampsExtension.ext(asset_no_prop).published = asset_value
        self.assertNotEqual(
            TimestampsExtension.ext(asset_no_prop).published,
            TimestampsExtension.ext(timestamps_item).published,
        )
        self.assertEqual(TimestampsExtension.ext(asset_no_prop).published, asset_value)

        # Validate
        timestamps_item.validate()

    def test_unpublished(self):
        timestamps_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertNotIn("unpublished", timestamps_item.properties)
        timestamps_unpublished = TimestampsExtension.ext(timestamps_item).unpublished
        self.assertIsNone(timestamps_unpublished, datetime)

        # Set
        TimestampsExtension.ext(timestamps_item).unpublished = self.sample_datetime
        self.assertEqual(
            self.sample_datetime_str, timestamps_item.properties["unpublished"]
        )

        # Get from Asset
        asset_no_prop = timestamps_item.assets["red"]
        asset_prop = timestamps_item.assets["blue"]
        self.assertEqual(
            TimestampsExtension.ext(asset_no_prop).unpublished,
            TimestampsExtension.ext(timestamps_item).unpublished,
        )
        self.assertEqual(
            TimestampsExtension.ext(asset_prop).unpublished,
            str_to_datetime("2019-01-02T00:00:00Z"),
        )

        # Set to Asset
        asset_value = str_to_datetime("2019-02-02T00:00:00Z")
        TimestampsExtension.ext(asset_no_prop).unpublished = asset_value
        self.assertNotEqual(
            TimestampsExtension.ext(asset_no_prop).unpublished,
            TimestampsExtension.ext(timestamps_item).unpublished,
        )
        self.assertEqual(
            TimestampsExtension.ext(asset_no_prop).unpublished, asset_value
        )

        # Validate
        timestamps_item.validate()
