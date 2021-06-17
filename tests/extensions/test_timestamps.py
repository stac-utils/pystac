import json
import unittest
from datetime import datetime

import pystac
from pystac.extensions.timestamps import TimestampsExtension
from pystac.utils import get_opt, str_to_datetime, datetime_to_str
from tests.utils import TestCases, assert_to_from_dict


class TimestampsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.example_uri = TestCases.get_path(
            "data-files/timestamps/example-landsat8.json"
        )
        with open(self.example_uri) as f:
            self.item_dict = json.load(f)
        self.sample_datetime_str = "2020-01-01T00:00:00Z"
        self.sample_datetime = str_to_datetime(self.sample_datetime_str)

    def test_to_from_dict(self) -> None:
        assert_to_from_dict(self, pystac.Item, self.item_dict)

    def test_apply(self) -> None:
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

    def test_validate_timestamps(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        item.validate()

    def test_expires(self) -> None:
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

    def test_published(self) -> None:
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

    def test_unpublished(self) -> None:
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

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Item does not include extension URI
        item = pystac.Item.from_file(self.example_uri)
        item.stac_extensions.remove(TimestampsExtension.get_schema_uri())

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = TimestampsExtension.ext(item)

        # Should raise exception if owning Item does not include extension URI
        asset = item.assets["blue"]

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = TimestampsExtension.ext(asset)

        # Should succeed if Asset has no owner
        ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
        _ = TimestampsExtension.ext(ownerless_asset)

    def test_item_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        item.stac_extensions.remove(TimestampsExtension.get_schema_uri())
        self.assertNotIn(TimestampsExtension.get_schema_uri(), item.stac_extensions)

        _ = TimestampsExtension.ext(item, add_if_missing=True)

        self.assertIn(TimestampsExtension.get_schema_uri(), item.stac_extensions)

    def test_asset_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        item.stac_extensions.remove(TimestampsExtension.get_schema_uri())
        self.assertNotIn(TimestampsExtension.get_schema_uri(), item.stac_extensions)
        asset = item.assets["blue"]

        _ = TimestampsExtension.ext(asset, add_if_missing=True)

        self.assertIn(TimestampsExtension.get_schema_uri(), item.stac_extensions)
