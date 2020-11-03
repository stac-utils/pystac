import os
from datetime import datetime
import json
import unittest
from tempfile import TemporaryDirectory

import pystac
from pystac import Asset, Item, Provider
from pystac.validation import validate_dict
from pystac.item import CommonMetadata
from pystac.utils import (str_to_datetime, is_absolute_href)
from pystac.serialization.identify import STACObjectType
from tests.utils import (TestCases, test_to_from_dict)


class ItemTest(unittest.TestCase):
    def get_example_item_dict(self):
        m = TestCases.get_path('data-files/item/sample-item.json')
        with open(m) as f:
            item_dict = json.load(f)
        return item_dict

    def test_to_from_dict(self):
        self.maxDiff = None

        item_dict = self.get_example_item_dict()

        test_to_from_dict(self, Item, item_dict)
        item = Item.from_dict(item_dict)
        self.assertEqual(
            item.get_self_href(),
            'http://cool-sat.com/catalog/CS3-20160503_132130_04/CS3-20160503_132130_04.json')

        # test asset creation additional field(s)
        self.assertEqual(item.assets['analytic'].properties['product'],
                         'http://cool-sat.com/catalog/products/analytic.json')
        self.assertEqual(len(item.assets['thumbnail'].properties), 0)

    def test_set_self_href_doesnt_break_asset_hrefs(self):
        cat = TestCases.test_case_6()
        for item in cat.get_all_items():
            for asset in item.assets.values():
                print(asset.href)
                assert not is_absolute_href(asset.href)
            item.set_self_href('http://example.com/item.json')
            for asset in item.assets.values():
                self.assertTrue(is_absolute_href(asset.href))
                self.assertTrue(os.path.exists(asset.href))

    def test_asset_absolute_href(self):
        item_dict = self.get_example_item_dict()
        item = Item.from_dict(item_dict)
        rel_asset = Asset('./data.geojson')
        rel_asset.set_owner(item)
        expected_href = 'http://cool-sat.com/catalog/CS3-20160503_132130_04/data.geojson'
        actual_href = rel_asset.get_absolute_href()
        self.assertEqual(expected_href, actual_href)

    def test_extra_fields(self):
        item = pystac.read_file(TestCases.get_path('data-files/item/sample-item.json'))

        item.extra_fields['test'] = 'extra'

        with TemporaryDirectory() as tmp_dir:
            p = os.path.join(tmp_dir, 'item.json')
            item.save_object(include_self_link=False, dest_href=p)
            with open(p) as f:
                item_json = json.load(f)
            self.assertTrue('test' in item_json)
            self.assertEqual(item_json['test'], 'extra')

            read_item = pystac.read_file(p)
            self.assertTrue('test' in read_item.extra_fields)
            self.assertEqual(read_item.extra_fields['test'], 'extra')

    def test_clearing_collection(self):
        collection = TestCases.test_case_4().get_child('acc')
        item = next(collection.get_all_items())
        self.assertEqual(item.collection_id, collection.id)
        item.set_collection(None)
        self.assertIsNone(item.collection_id)
        self.assertIsNone(item.get_collection())
        item.set_collection(collection)
        self.assertEqual(item.collection_id, collection.id)
        self.assertIs(item.get_collection(), collection)

    def test_datetime_ISO8601_format(self):
        item_dict = self.get_example_item_dict()

        item = Item.from_dict(item_dict)

        formatted_time = item.to_dict()['properties']['datetime']

        self.assertEqual('2016-05-03T13:22:30.040000Z', formatted_time)

    def test_null_datetime(self):
        item = pystac.read_file(TestCases.get_path('data-files/item/sample-item.json'))

        with self.assertRaises(pystac.STACError):
            Item('test', geometry=item.geometry, bbox=item.bbox, datetime=None, properties={})

        null_dt_item = Item('test',
                            geometry=item.geometry,
                            bbox=item.bbox,
                            datetime=None,
                            properties={
                                'start_datetime': pystac.utils.datetime_to_str(item.datetime),
                                'end_datetime': pystac.utils.datetime_to_str(item.datetime)
                            })

        null_dt_item.validate()

    def test_get_set_asset_datetime(self):
        item = pystac.read_file(
            TestCases.get_path('data-files/item/sample-item-asset-properties.json'))
        item_datetime = item.datetime

        # No property on asset
        self.assertEqual(item.get_datetime(item.assets['thumbnail']), item.datetime)

        # Property on asset
        self.assertNotEqual(item.get_datetime(item.assets['analytic']), item.datetime)
        self.assertEqual(item.get_datetime(item.assets['analytic']),
                         str_to_datetime("2017-05-03T13:22:30.040Z"))

        item.set_datetime(str_to_datetime("2018-05-03T13:22:30.040Z"), item.assets['thumbnail'])
        self.assertEqual(item.get_datetime(), item_datetime)
        self.assertEqual(item.get_datetime(item.assets['thumbnail']),
                         str_to_datetime("2018-05-03T13:22:30.040Z"))

    def test_read_eo_item_owns_asset(self):
        item = next(x for x in TestCases.test_case_1().get_all_items() if isinstance(x, Item))
        assert len(item.assets) > 0
        for asset_key in item.assets:
            self.assertEqual(item.assets[asset_key].owner, item)

    def test_self_contained_item(self):
        item_dict = self.get_example_item_dict()
        item_dict['links'] = [link for link in item_dict['links'] if link['rel'] == 'self']
        item = Item.from_dict(item_dict)
        self.assertIsInstance(item, Item)
        self.assertEqual(len(item.links), 1)

    def test_null_geometry(self):
        m = TestCases.get_path(
            'data-files/examples/1.0.0-beta.2/item-spec/examples/null-geom-item.json')
        with open(m) as f:
            item_dict = json.load(f)

        validate_dict(item_dict, STACObjectType.ITEM)

        item = Item.from_dict(item_dict)
        self.assertIsInstance(item, Item)
        item.validate()

        item_dict = item.to_dict()
        self.assertIsNone(item_dict['geometry'])
        with self.assertRaises(KeyError):
            item_dict['bbox']

    def test_0_9_item_with_no_extensions_does_not_read_collection_data(self):
        item_json = pystac.STAC_IO.read_json(
            TestCases.get_path('data-files/examples/hand-0.9.0/010100/010100.json'))
        assert item_json.get('stac_extensions') is None
        assert item_json.get('stac_version') == '0.9.0'

        did_merge = pystac.serialization.common_properties.merge_common_properties(item_json)
        self.assertFalse(did_merge)

    def test_clone_sets_asset_owner(self):
        cat = TestCases.test_case_2()
        item = next(cat.get_all_items())
        original_asset = list(item.assets.values())[0]
        assert original_asset.owner is item

        clone = item.clone()
        clone_asset = list(clone.assets.values())[0]
        self.assertIs(clone_asset.owner, clone)

    def test_make_asset_href_relative_is_noop_on_relative_hrefs(self):
        cat = TestCases.test_case_2()
        item = next(cat.get_all_items())
        asset = list(item.assets.values())[0]
        assert not is_absolute_href(asset.href)
        original_href = asset.get_absolute_href()

        item.make_asset_hrefs_relative()
        self.assertEqual(asset.get_absolute_href(), original_href)


class CommonMetadataTest(unittest.TestCase):
    def setUp(self):
        self.URI_1 = TestCases.get_path(
            'data-files/examples/1.0.0-beta.2/item-spec/examples/datetimerange.json')
        self.ITEM_1 = Item.from_file(self.URI_1)

        self.URI_2 = TestCases.get_path(
            'data-files/examples/1.0.0-beta.2/item-spec/examples/sample-full.json')
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
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.start_datetime, start_datetime_dt)
        self.assertEqual(x.properties['start_datetime'], start_datetime_str)

        x.common_metadata.start_datetime = example_datetime_dt

        self.assertEqual(x.common_metadata.start_datetime, example_datetime_dt)
        self.assertEqual(x.properties['start_datetime'], example_datetime_str)

    def test_common_metadata_end_datetime(self):
        x = self.ITEM_1.clone()
        end_datetime_str = "2018-01-01T13:31:30Z"
        end_datetime_dt = str_to_datetime(end_datetime_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.end_datetime, end_datetime_dt)
        self.assertEqual(x.properties['end_datetime'], end_datetime_str)

        x.common_metadata.end_datetime = example_datetime_dt

        self.assertEqual(x.common_metadata.end_datetime, example_datetime_dt)
        self.assertEqual(x.properties['end_datetime'], example_datetime_str)

    def test_common_metadata_created(self):
        x = self.ITEM_2.clone()
        created_str = "2016-05-04T00:00:01Z"
        created_dt = str_to_datetime(created_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.created, created_dt)
        self.assertEqual(x.properties['created'], created_str)

        x.common_metadata.created = example_datetime_dt

        self.assertEqual(x.common_metadata.created, example_datetime_dt)
        self.assertEqual(x.properties['created'], example_datetime_str)

    def test_common_metadata_updated(self):
        x = self.ITEM_2.clone()
        updated_str = "2017-01-01T00:30:55Z"
        updated_dt = str_to_datetime(updated_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.updated, updated_dt)
        self.assertEqual(x.properties['updated'], updated_str)

        x.common_metadata.updated = example_datetime_dt

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

        x.common_metadata.providers = example_providers_object_list

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

        # GSD
        gsd = 0.512
        example_gsd = 0.75
        self.assertEqual(x.common_metadata.gsd, gsd)
        x.common_metadata.gsd = example_gsd
        self.assertEqual(x.common_metadata.gsd, example_gsd)
        self.assertEqual(x.properties['gsd'], example_gsd)

    def test_asset_start_datetime(self):
        item = pystac.read_file(
            TestCases.get_path('data-files/item/sample-item-asset-properties.json'))
        cm = item.common_metadata

        item_value = cm.start_datetime
        a2_known_value = str_to_datetime("2017-05-01T13:22:30.040Z")

        # Get
        a1_value = cm.get_start_datetime(item.assets['analytic'])
        a2_value = cm.get_start_datetime(item.assets['thumbnail'])
        self.assertEqual(a1_value, item_value)
        self.assertNotEqual(a2_value, item_value)
        self.assertEqual(a2_value, a2_known_value)

        # Set
        set_value = str_to_datetime("2014-05-01T13:22:30.040Z")
        cm.set_start_datetime(set_value, item.assets['analytic'])
        new_a1_value = cm.get_start_datetime(item.assets['analytic'])
        self.assertEqual(new_a1_value, set_value)
        self.assertEqual(cm.start_datetime, item_value)

    def test_asset_end_datetime(self):
        item = pystac.read_file(
            TestCases.get_path('data-files/item/sample-item-asset-properties.json'))
        cm = item.common_metadata

        item_value = cm.end_datetime
        a2_known_value = str_to_datetime("2017-05-02T13:22:30.040Z")

        # Get
        a1_value = cm.get_end_datetime(item.assets['analytic'])
        a2_value = cm.get_end_datetime(item.assets['thumbnail'])
        self.assertEqual(a1_value, item_value)
        self.assertNotEqual(a2_value, item_value)
        self.assertEqual(a2_value, a2_known_value)

        # Set
        set_value = str_to_datetime("2014-05-01T13:22:30.040Z")
        cm.set_end_datetime(set_value, item.assets['analytic'])
        new_a1_value = cm.get_end_datetime(item.assets['analytic'])
        self.assertEqual(new_a1_value, set_value)
        self.assertEqual(cm.end_datetime, item_value)

    def test_asset_license(self):
        item = pystac.read_file(
            TestCases.get_path('data-files/item/sample-item-asset-properties.json'))
        cm = item.common_metadata

        item_value = cm.license
        a2_known_value = 'CC-BY-4.0'

        # Get
        a1_value = cm.get_license(item.assets['analytic'])
        a2_value = cm.get_license(item.assets['thumbnail'])
        self.assertEqual(a1_value, item_value)
        self.assertNotEqual(a2_value, item_value)
        self.assertEqual(a2_value, a2_known_value)

        # Set
        set_value = 'various'
        cm.set_license(set_value, item.assets['analytic'])
        new_a1_value = cm.get_license(item.assets['analytic'])
        self.assertEqual(new_a1_value, set_value)
        self.assertEqual(cm.license, item_value)

    def test_asset_providers(self):
        item = pystac.read_file(
            TestCases.get_path('data-files/item/sample-item-asset-properties.json'))
        cm = item.common_metadata

        item_value = cm.providers
        a2_known_value = [
            pystac.Provider(name="USGS",
                            url="https://landsat.usgs.gov/",
                            roles=["producer", "licensor"])
        ]

        # Get
        a1_value = cm.get_providers(item.assets['analytic'])
        a2_value = cm.get_providers(item.assets['thumbnail'])
        self.assertEqual(a1_value[0].to_dict(), item_value[0].to_dict())
        self.assertNotEqual(a2_value[0].to_dict(), item_value[0].to_dict())
        self.assertEqual(a2_value[0].to_dict(), a2_known_value[0].to_dict())

        # Set
        set_value = [
            pystac.Provider(name="John Snow", url="https://cholera.com/", roles=["producer"])
        ]
        cm.set_providers(set_value, item.assets['analytic'])
        new_a1_value = cm.get_providers(item.assets['analytic'])
        self.assertEqual(new_a1_value[0].to_dict(), set_value[0].to_dict())
        self.assertEqual(cm.providers[0].to_dict(), item_value[0].to_dict())

    def test_asset_platform(self):
        item = pystac.read_file(
            TestCases.get_path('data-files/item/sample-item-asset-properties.json'))
        cm = item.common_metadata

        item_value = cm.platform
        a2_known_value = 'shoes'

        # Get
        a1_value = cm.get_platform(item.assets['analytic'])
        a2_value = cm.get_platform(item.assets['thumbnail'])
        self.assertEqual(a1_value, item_value)
        self.assertNotEqual(a2_value, item_value)
        self.assertEqual(a2_value, a2_known_value)

        # Set
        set_value = 'brick'
        cm.set_platform(set_value, item.assets['analytic'])
        new_a1_value = cm.get_platform(item.assets['analytic'])
        self.assertEqual(new_a1_value, set_value)
        self.assertEqual(cm.platform, item_value)

    def test_asset_instruments(self):
        item = pystac.read_file(
            TestCases.get_path('data-files/item/sample-item-asset-properties.json'))
        cm = item.common_metadata

        item_value = cm.instruments
        a2_known_value = ["caliper"]

        # Get
        a1_value = cm.get_instruments(item.assets['analytic'])
        a2_value = cm.get_instruments(item.assets['thumbnail'])
        self.assertEqual(a1_value, item_value)
        self.assertNotEqual(a2_value, item_value)
        self.assertEqual(a2_value, a2_known_value)

        # Set
        set_value = ["horns"]
        cm.set_instruments(set_value, item.assets['analytic'])
        new_a1_value = cm.get_instruments(item.assets['analytic'])
        self.assertEqual(new_a1_value, set_value)
        self.assertEqual(cm.instruments, item_value)

    def test_asset_constellation(self):
        item = pystac.read_file(
            TestCases.get_path('data-files/item/sample-item-asset-properties.json'))
        cm = item.common_metadata

        item_value = cm.constellation
        a2_known_value = 'little dipper'

        # Get
        a1_value = cm.get_constellation(item.assets['analytic'])
        a2_value = cm.get_constellation(item.assets['thumbnail'])
        self.assertEqual(a1_value, item_value)
        self.assertNotEqual(a2_value, item_value)
        self.assertEqual(a2_value, a2_known_value)

        # Set
        set_value = 'orion'
        cm.set_constellation(set_value, item.assets['analytic'])
        new_a1_value = cm.get_constellation(item.assets['analytic'])
        self.assertEqual(new_a1_value, set_value)
        self.assertEqual(cm.constellation, item_value)

    def test_asset_mission(self):
        item = pystac.read_file(
            TestCases.get_path('data-files/item/sample-item-asset-properties.json'))
        cm = item.common_metadata

        item_value = cm.mission
        a2_known_value = 'possible'

        # Get
        a1_value = cm.get_mission(item.assets['analytic'])
        a2_value = cm.get_mission(item.assets['thumbnail'])
        self.assertEqual(a1_value, item_value)
        self.assertNotEqual(a2_value, item_value)
        self.assertEqual(a2_value, a2_known_value)

        # Set
        set_value = 'critical'
        cm.set_mission(set_value, item.assets['analytic'])
        new_a1_value = cm.get_mission(item.assets['analytic'])
        self.assertEqual(new_a1_value, set_value)
        self.assertEqual(cm.mission, item_value)

    def test_asset_gsd(self):
        item = pystac.read_file(
            TestCases.get_path('data-files/item/sample-item-asset-properties.json'))
        cm = item.common_metadata

        item_value = cm.gsd
        a2_known_value = 40

        # Get
        a1_value = cm.get_gsd(item.assets['analytic'])
        a2_value = cm.get_gsd(item.assets['thumbnail'])
        self.assertEqual(a1_value, item_value)
        self.assertNotEqual(a2_value, item_value)
        self.assertEqual(a2_value, a2_known_value)

        # Set
        set_value = 100
        cm.set_gsd(set_value, item.assets['analytic'])
        new_a1_value = cm.get_gsd(item.assets['analytic'])
        self.assertEqual(new_a1_value, set_value)
        self.assertEqual(cm.gsd, item_value)

    def test_asset_created(self):
        item = pystac.read_file(
            TestCases.get_path('data-files/item/sample-item-asset-properties.json'))
        cm = item.common_metadata

        item_value = cm.created
        a2_known_value = str_to_datetime("2017-05-17T13:22:30.040Z")

        # Get
        a1_value = cm.get_created(item.assets['analytic'])
        a2_value = cm.get_created(item.assets['thumbnail'])
        self.assertEqual(a1_value, item_value)
        self.assertNotEqual(a2_value, item_value)
        self.assertEqual(a2_value, a2_known_value)

        # Set
        set_value = str_to_datetime("2014-05-17T13:22:30.040Z")
        cm.set_created(set_value, item.assets['analytic'])
        new_a1_value = cm.get_created(item.assets['analytic'])
        self.assertEqual(new_a1_value, set_value)
        self.assertEqual(cm.created, item_value)

    def test_asset_updated(self):
        item = pystac.read_file(
            TestCases.get_path('data-files/item/sample-item-asset-properties.json'))
        cm = item.common_metadata

        item_value = cm.updated
        a2_known_value = str_to_datetime("2017-05-18T13:22:30.040Z")

        # Get
        a1_value = cm.get_updated(item.assets['analytic'])
        a2_value = cm.get_updated(item.assets['thumbnail'])
        self.assertEqual(a1_value, item_value)
        self.assertNotEqual(a2_value, item_value)
        self.assertEqual(a2_value, a2_known_value)

        # Set
        set_value = str_to_datetime("2014-05-18T13:22:30.040Z")
        cm.set_updated(set_value, item.assets['analytic'])
        new_a1_value = cm.get_updated(item.assets['analytic'])
        self.assertEqual(new_a1_value, set_value)
        self.assertEqual(cm.updated, item_value)
