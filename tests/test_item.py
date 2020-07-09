import unittest
import json

from pystac import Asset, Item, Provider
from pystac.item import CommonMetadata
from pystac.utils import str_to_datetime
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
        self.assertEqual(len(item.assets['thumbnail'].properties), 0)

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

    def test_self_contained_item(self):
        m = TestCases.get_path('data-files/itemcollections/sample-item-collection.json')
        with open(m) as f:
            item_dict = json.load(f)['features'][0]
        item_dict['links'] = [link for link in item_dict['links'] if link['rel'] == 'self']
        item = Item.from_dict(item_dict)
        self.assertIsInstance(item, Item)
        self.assertEqual(len(item.links), 1)


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
        self.assertIsInstance(start_datetime_str, str)

        common_metadata = self.ITEM_1.common_metadata
        self.assertIsInstance(common_metadata, CommonMetadata)
        self.assertIsInstance(common_metadata.start_datetime, datetime)
        self.assertDictEqual(before, self.ITEM_1.to_dict())
        self.assertIsNone(common_metadata.providers)

    def test_common_metadata_start_datetime(self):
        x = self.ITEM_1.clone()
        start_datetime_str = "2018-01-01T13:21:30Z"
        start_datetime_dt = str_to_datetime(start_datetime_str)
        example_datetime_str = "2020-01-01T00:00:00"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.start_datetime, start_datetime_dt)
        self.assertEqual(x.properties['start_datetime'], start_datetime_str)

        x.common_metadata.start_datetime = example_datetime_str

        self.assertEqual(x.common_metadata.start_datetime, example_datetime_dt)
        self.assertEqual(x.properties['start_datetime'], example_datetime_str)

    def test_common_metadata_end_datetime(self):
        x = self.ITEM_1.clone()
        end_datetime_str = "2018-01-01T13:31:30Z"
        end_datetime_dt = str_to_datetime(end_datetime_str)
        example_datetime_str = "2020-01-01T00:00:00"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.end_datetime, end_datetime_dt)
        self.assertEqual(x.properties['end_datetime'], end_datetime_str)

        x.common_metadata.end_datetime = example_datetime_str

        self.assertEqual(x.common_metadata.end_datetime, example_datetime_dt)
        self.assertEqual(x.properties['end_datetime'], example_datetime_str)

    def test_common_metadata_created(self):
        x = self.ITEM_2.clone()
        created_str = "2016-05-04T00:00:01Z"
        created_dt = str_to_datetime(created_str)
        example_datetime_str = "2020-01-01T00:00:00"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.created, created_dt)
        self.assertEqual(x.properties['created'], created_str)

        x.common_metadata.created = example_datetime_str

        self.assertEqual(x.common_metadata.created, example_datetime_dt)
        self.assertEqual(x.properties['created'], example_datetime_str)

    def test_common_metadata_updated(self):
        x = self.ITEM_2.clone()
        updated_str = "2017-01-01T00:30:55Z"
        updated_dt = str_to_datetime(updated_str)
        example_datetime_str = "2020-01-01T00:00:00"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.updated, updated_dt)
        self.assertEqual(x.properties['updated'], updated_str)

        x.common_metadata.updated = example_datetime_str

        self.assertEqual(x.common_metadata.updated, example_datetime_dt)
        self.assertEqual(x.properties['updated'], example_datetime_str)

    def test_common_metadata_providers(self):
        x = self.ITEM_2.clone()

        providers_dict_list = [{
            "name": "CoolSat",
            "roles": ["producer", "licensor"],
            "url": "https://cool-sat.com/"
        }]
        providers_object_list = [Provider.from_dict(d) for d in providers_dict_list]

        example_providers_dict_list = [{
            "name": "ExampleProvider_1",
            "roles": ["example_role_1", "example_role_2"],
            "url": "https://exampleprovider1.com/"
        }, {
            "name": "ExampleProvider_2",
            "roles": ["example_role_1", "example_role_2"],
            "url": "https://exampleprovider2.com/"
        }]
        example_providers_object_list = [Provider.from_dict(d) for d in example_providers_dict_list]

        for i in range(len(x.common_metadata.providers)):
            p1 = x.common_metadata.providers[i]
            p2 = providers_object_list[i]
            self.assertIsInstance(p1, Provider)
            self.assertIsInstance(p2, Provider)
            self.assertDictEqual(p1.to_dict(), p2.to_dict())

            pd1 = x.properties['providers'][i]
            pd2 = providers_dict_list[i]
            self.assertIsInstance(pd1, dict)
            self.assertIsInstance(pd2, dict)
            self.assertDictEqual(pd1, pd2)

        x.common_metadata.providers = example_providers_dict_list

        for i in range(len(x.common_metadata.providers)):
            p1 = x.common_metadata.providers[i]
            p2 = example_providers_object_list[i]
            self.assertIsInstance(p1, Provider)
            self.assertIsInstance(p2, Provider)
            self.assertDictEqual(p1.to_dict(), p2.to_dict())

            pd1 = x.properties['providers'][i]
            pd2 = example_providers_dict_list[i]
            self.assertIsInstance(pd1, dict)
            self.assertIsInstance(pd2, dict)
            self.assertDictEqual(pd1, pd2)

    def test_common_metadata_basics(self):
        x = self.ITEM_2.clone()

        # Title
        title = "A CS3 item"
        example_title = "example title"
        self.assertEqual(x.common_metadata.title, title)
        x.common_metadata.title = example_title
        self.assertEqual(x.common_metadata.title, example_title)
        self.assertEqual(x.properties['title'], example_title)

        # Description
        example_description = "example description"
        self.assertIsNone(x.common_metadata.description)
        x.common_metadata.description = example_description
        self.assertEqual(x.common_metadata.description, example_description)
        self.assertEqual(x.properties['description'], example_description)

        # License
        license = "PDDL-1.0"
        example_license = "example license"
        self.assertEqual(x.common_metadata.license, license)
        x.common_metadata.license = example_license
        self.assertEqual(x.common_metadata.license, example_license)
        self.assertEqual(x.properties['license'], example_license)

        # Platform
        platform = "coolsat2"
        example_platform = "example_platform"
        self.assertEqual(x.common_metadata.platform, platform)
        x.common_metadata.platform = example_platform
        self.assertEqual(x.common_metadata.platform, example_platform)
        self.assertEqual(x.properties['platform'], example_platform)

        # Instruments
        instruments = ["cool_sensor_v1"]
        example_instruments = ["example instrument 1", "example instrument 2"]
        self.assertListEqual(x.common_metadata.instruments, instruments)
        x.common_metadata.instruments = example_instruments
        self.assertListEqual(x.common_metadata.instruments, example_instruments)
        self.assertListEqual(x.properties['instruments'], example_instruments)

        # Constellation
        example_constellation = "example constellation"
        self.assertIsNone(x.common_metadata.constellation)
        x.common_metadata.constellation = example_constellation
        self.assertEqual(x.common_metadata.constellation, example_constellation)
        self.assertEqual(x.properties['constellation'], example_constellation)

        # Mission
        example_mission = "example mission"
        self.assertIsNone(x.common_metadata.mission)
        x.common_metadata.mission = example_mission
        self.assertEqual(x.common_metadata.mission, example_mission)
        self.assertEqual(x.properties['mission'], example_mission)
