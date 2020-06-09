import unittest
import json

from pystac import Asset, Item, TemporalExtent, Provider
from pystac.item import CommonMetadata
from tests.utils import (TestCases, test_to_from_dict)
from datetime import datetime


class ItemTest(unittest.TestCase):
    def test_to_from_dict(self):
        self.maxDiff = None
        m = TestCases.get_path('data-files/itemcollections/sample-item-collection.json')
        with open(m) as f:
            item_dict = json.load(f)['features'][0]

        test_to_from_dict(self, Item, item_dict)
        item = Item.from_dict(item_dict)
        self.assertEqual(
            item.get_self_href(),
            'http://cool-sat.com/catalog/CS3-20160503_132130_04/CS3-20160503_132130_04.json')

        # test asset creation additional field(s)
        self.assertEqual(item.assets['analytic'].properties['product'],
                         'http://cool-sat.com/catalog/products/analytic.json')
        self.assertIsNone(item.assets['thumbnail'].properties)

    def test_asset_absolute_href(self):
        m = TestCases.get_path('data-files/itemcollections/sample-item-collection.json')
        with open(m) as f:
            item_dict = json.load(f)['features'][0]
        item = Item.from_dict(item_dict)
        rel_asset = Asset('./data.geojson')
        rel_asset.set_owner(item)
        expected_href = 'http://cool-sat.com/catalog/CS3-20160503_132130_04/data.geojson'
        actual_href = rel_asset.get_absolute_href()
        self.assertEqual(expected_href, actual_href)

    def test_datetime_ISO8601_format(self):
        m = TestCases.get_path('data-files/itemcollections/sample-item-collection.json')
        with open(m) as f:
            item_dict = json.load(f)['features'][0]

        item = Item.from_dict(item_dict)

        formatted_time = item.to_dict()['properties']['datetime']

        self.assertEqual('2016-05-03T13:22:30.040000Z', formatted_time)

    def test_read_eo_item_owns_asset(self):
        item = next(x for x in TestCases.test_case_1().get_all_items() if isinstance(x, Item))
        assert len(item.assets) > 0
        for asset_key in item.assets:
            self.assertEqual(item.assets[asset_key].owner, item)


class CommonMetadataTest(unittest.TestCase):
    def setUp(self):
        self.URI_1 = TestCases.get_path(
            'data-files/examples/0.9.0/item-spec/examples/datetimerange.json')
        self.ITEM_1 = Item.from_file(self.URI_1)

        self.URI_2 = TestCases.get_path(
            'data-files/examples/0.9.0/item-spec/examples/sample-full.json')
        self.ITEM_2 = Item.from_file(self.URI_2)

        self.EXAMPLE_CM_DICT = {
            'start_datetime':
            '2020-05-21T16:42:24.896Z',
            'platform':
            'example platform',
            'providers': [{
                'name': 'example provider',
                'roles': ['example roll'],
                'url': 'https://example-provider.com/'
            }]
        }

    def test_datetimes(self):
        # save dict of original item to check that `common_metadata`
        # method doesn't mutate self.item_1
        before = self.ITEM_1.clone().to_dict()
        start_datetime_str = self.ITEM_1.properties['start_datetime']
        end_datetime_str = self.ITEM_1.properties['end_datetime']
        self.assertIsInstance(start_datetime_str, str)

        common_metadata = self.ITEM_1.common_metadata
        self.assertIsInstance(common_metadata, CommonMetadata)
        self.assertIsInstance(common_metadata.start_datetime, datetime)

        temp_ext = common_metadata.time_range
        self.assertIsInstance(temp_ext, TemporalExtent)

        test_dict = {'interval': [[start_datetime_str, end_datetime_str]]}
        self.assertDictEqual(temp_ext.to_dict(), test_dict)

        self.assertDictEqual(before, self.ITEM_1.to_dict())

        self.assertIsNone(common_metadata.providers)

        common_metadata_dict = common_metadata.to_dict()
        common_metadata_2 = CommonMetadata.from_dict(common_metadata_dict)
        self.assertEqual(common_metadata.start_datetime, common_metadata_2.start_datetime)

    def test_set_common_metadata(self):
        common_metadata = self.ITEM_2.common_metadata

        for provider in common_metadata.providers:
            self.assertIsInstance(provider, Provider)
        self.assertEqual(common_metadata.platform, 'coolsat2')

        example_cm = CommonMetadata.from_dict(self.EXAMPLE_CM_DICT)
        self.assertIsInstance(example_cm.start_datetime, datetime)
        self.assertIsInstance(example_cm.providers[0], Provider)

        item_2_copy = self.ITEM_2.clone()
        item_2_copy.set_common_metadata(example_cm)
        self.assertNotEqual(self.EXAMPLE_CM_DICT['platform'], item_2_copy.properties['platform'])
        self.assertEqual(item_2_copy.properties['platform'], self.ITEM_2.properties['platform'])

        item_2_copy.set_common_metadata(example_cm, override=True)
        self.assertEqual(self.EXAMPLE_CM_DICT['platform'], item_2_copy.properties['platform'])
        self.assertNotEqual(item_2_copy.properties['platform'], self.ITEM_2.properties['platform'])
        self.assertIsInstance(item_2_copy.properties['start_datetime'], str)
        self.assertEqual(item_2_copy.properties['start_datetime'],
                         self.EXAMPLE_CM_DICT['start_datetime'])
        self.assertEqual(item_2_copy.properties['platform'], self.EXAMPLE_CM_DICT['platform'])
        for i, provider in enumerate(item_2_copy.properties['providers']):
            self.assertDictEqual(provider, self.EXAMPLE_CM_DICT['providers'][i])
