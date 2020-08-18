import json
import unittest
from datetime import datetime

from pystac import Item, STACError
from pystac.utils import str_to_datetime
from tests.utils import TestCases, test_to_from_dict


class TimestampsTest(unittest.TestCase):
    LANDSAT_EXAMPLE_URI = TestCases.get_path('data-files/timestamps/example-landsat8.json')

    def setUp(self):
        self.maxDiff = None

    def test_to_from_dict(self):
        with open(self.LANDSAT_EXAMPLE_URI) as f:
            item_dict = json.load(f)

        test_to_from_dict(self, Item, item_dict)
        item = Item.from_dict(item_dict)
        self.assertIsInstance(item.properties['published'], str)
        self.assertTrue(item.ext.implements('timestamps'))

        self.assertIsInstance(item.ext.timestamps.expires, datetime)
        self.assertIsInstance(item.ext.timestamps.published, datetime)
        self.assertIsNone(item.ext.timestamps.unpublished, datetime)

        unpublished_timestamp = "2019-10-03T06:45:55Z"
        item.ext.timestamps.unpublished = str_to_datetime(unpublished_timestamp)
        self.assertIsInstance(item.ext.timestamps.unpublished, datetime)
        self.assertEqual(item.properties['unpublished'], unpublished_timestamp)

        item_copy = item.clone()
        with self.assertRaises(STACError):
            item_copy.ext.timestamps.apply()

        exp_timestamp = str_to_datetime("2020-10-03T06:45:55Z")
        item_copy.ext.timestamps.apply(expires=exp_timestamp)
        self.assertEqual(item_copy.ext.timestamps.expires, exp_timestamp)
        self.assertIsNone(item_copy.ext.timestamps.published)
        self.assertIsNone(item_copy.ext.timestamps.unpublished)
