from copy import deepcopy
import os
from datetime import datetime
import json
import tempfile
from typing import Any, Dict, List
import unittest

import pystac
from pystac import Asset, Item, Provider, ProviderRole
from pystac.validation import validate_dict
import pystac.serialization.common_properties
from pystac.common_metadata import CommonMetadata
from pystac.utils import datetime_to_str, get_opt, str_to_datetime, is_absolute_href
from tests.utils import TestCases, assert_to_from_dict


class ItemTest(unittest.TestCase):
    def get_example_item_dict(self) -> Dict[str, Any]:
        m = TestCases.get_path("data-files/item/sample-item.json")
        with open(m) as f:
            item_dict: Dict[str, Any] = json.load(f)
        return item_dict

    def test_to_from_dict(self) -> None:
        self.maxDiff = None

        item_dict = self.get_example_item_dict()
        param_dict = deepcopy(item_dict)

        assert_to_from_dict(self, Item, param_dict)
        item = Item.from_dict(param_dict)
        self.assertEqual(item.id, "CS3-20160503_132131_05")

        # test asset creation additional field(s)
        self.assertEqual(
            item.assets["analytic"].extra_fields["product"],
            "http://cool-sat.com/catalog/products/analytic.json",
        )
        self.assertEqual(len(item.assets["thumbnail"].extra_fields), 0)

        # test that the parameter is preserved
        self.assertEqual(param_dict, item_dict)

        # assert that the parameter is not preserved with
        # non-default parameter
        _ = Item.from_dict(param_dict, preserve_dict=False)
        self.assertNotEqual(param_dict, item_dict)

    def test_from_dict_set_root(self) -> None:
        item_dict = self.get_example_item_dict()
        catalog = pystac.Catalog(id="test", description="test desc")
        item = Item.from_dict(item_dict, root=catalog)
        self.assertIs(item.get_root(), catalog)

    def test_set_self_href_does_not_break_asset_hrefs(self) -> None:
        cat = TestCases.test_case_2()
        for item in cat.get_all_items():
            for asset in item.assets.values():
                if is_absolute_href(asset.href):
                    asset.href = f"./{os.path.basename(asset.href)}"
            item.set_self_href("http://example.com/item.json")
            for asset in item.assets.values():
                self.assertTrue(is_absolute_href(asset.href))

    def test_set_self_href_none_ignores_relative_asset_hrefs(self) -> None:
        cat = TestCases.test_case_2()
        for item in cat.get_all_items():
            for asset in item.assets.values():
                if is_absolute_href(asset.href):
                    asset.href = f"./{os.path.basename(asset.href)}"
            item.set_self_href(None)
            for asset in item.assets.values():
                self.assertFalse(is_absolute_href(asset.href))

    def test_asset_absolute_href(self) -> None:
        item_dict = self.get_example_item_dict()
        item = Item.from_dict(item_dict)
        rel_asset = Asset("./data.geojson")
        rel_asset.set_owner(item)
        expected_href = os.path.abspath("./data.geojson")
        actual_href = rel_asset.get_absolute_href()
        self.assertEqual(expected_href, actual_href)

    def test_extra_fields(self) -> None:
        item = pystac.Item.from_file(
            TestCases.get_path("data-files/item/sample-item.json")
        )

        item.extra_fields["test"] = "extra"

        with tempfile.TemporaryDirectory() as tmp_dir:
            p = os.path.join(tmp_dir, "item.json")
            item.save_object(include_self_link=False, dest_href=p)
            with open(p) as f:
                item_json = json.load(f)
            self.assertTrue("test" in item_json)
            self.assertEqual(item_json["test"], "extra")

            read_item = pystac.Item.from_file(p)
            self.assertTrue("test" in read_item.extra_fields)
            self.assertEqual(read_item.extra_fields["test"], "extra")

    def test_clearing_collection(self) -> None:
        collection = TestCases.test_case_4().get_child("acc")
        assert isinstance(collection, pystac.Collection)
        item = next(iter(collection.get_all_items()))
        self.assertEqual(item.collection_id, collection.id)
        item.set_collection(None)
        self.assertIsNone(item.collection_id)
        self.assertIsNone(item.get_collection())
        item.set_collection(collection)
        self.assertEqual(item.collection_id, collection.id)
        self.assertIs(item.get_collection(), collection)

    def test_datetime_ISO8601_format(self) -> None:
        item_dict = self.get_example_item_dict()

        item = Item.from_dict(item_dict)

        formatted_time = item.to_dict()["properties"]["datetime"]

        self.assertEqual("2016-05-03T13:22:30.040000Z", formatted_time)

    def test_null_datetime(self) -> None:
        item = pystac.Item.from_file(
            TestCases.get_path("data-files/item/sample-item.json")
        )

        with self.assertRaises(pystac.STACError):
            Item(
                "test",
                geometry=item.geometry,
                bbox=item.bbox,
                datetime=None,
                properties={},
            )

        null_dt_item = Item(
            "test",
            geometry=item.geometry,
            bbox=item.bbox,
            datetime=None,
            properties={
                "start_datetime": datetime_to_str(get_opt(item.datetime)),
                "end_datetime": datetime_to_str(get_opt(item.datetime)),
            },
        )

        null_dt_item.validate()

    def test_get_set_asset_datetime(self) -> None:
        item = pystac.Item.from_file(
            TestCases.get_path("data-files/item/sample-item-asset-properties.json")
        )
        item_datetime = item.datetime

        # No property on asset
        self.assertEqual(item.get_datetime(item.assets["thumbnail"]), item.datetime)

        # Property on asset
        self.assertNotEqual(item.get_datetime(item.assets["analytic"]), item.datetime)
        self.assertEqual(
            item.get_datetime(item.assets["analytic"]),
            str_to_datetime("2017-05-03T13:22:30.040Z"),
        )

        item.set_datetime(
            str_to_datetime("2018-05-03T13:22:30.040Z"), item.assets["thumbnail"]
        )
        self.assertEqual(item.get_datetime(), item_datetime)
        self.assertEqual(
            item.get_datetime(item.assets["thumbnail"]),
            str_to_datetime("2018-05-03T13:22:30.040Z"),
        )

    def test_read_eo_item_owns_asset(self) -> None:
        item = next(iter(TestCases.test_case_1().get_all_items()))
        assert len(item.assets) > 0
        for asset_key in item.assets:
            self.assertEqual(item.assets[asset_key].owner, item)

    def test_null_geometry(self) -> None:
        m = TestCases.get_path(
            "data-files/examples/1.0.0-beta.2/item-spec/examples/null-geom-item.json"
        )
        with open(m) as f:
            item_dict = json.load(f)

        validate_dict(item_dict, pystac.STACObjectType.ITEM)

        item = Item.from_dict(item_dict)
        self.assertIsInstance(item, Item)
        item.validate()

        item_dict = item.to_dict()
        self.assertIsNone(item_dict["geometry"])
        self.assertNotIn("bbox", item_dict)

    def test_0_9_item_with_no_extensions_does_not_read_collection_data(self) -> None:
        item_json = pystac.StacIO.default().read_json(
            TestCases.get_path("data-files/examples/hand-0.9.0/010100/010100.json")
        )
        assert item_json.get("stac_extensions") is None
        assert item_json.get("stac_version") == "0.9.0"

        did_merge = pystac.serialization.common_properties.merge_common_properties(
            item_json
        )
        self.assertFalse(did_merge)

    def test_clone_sets_asset_owner(self) -> None:
        cat = TestCases.test_case_2()
        item = next(iter(cat.get_all_items()))
        original_asset = list(item.assets.values())[0]
        assert original_asset.owner is item

        clone = item.clone()
        clone_asset = list(clone.assets.values())[0]
        self.assertIs(clone_asset.owner, clone)

    def test_make_asset_href_relative_is_noop_on_relative_hrefs(self) -> None:
        cat = TestCases.test_case_2()
        item = next(iter(cat.get_all_items()))
        asset = list(item.assets.values())[0]
        assert not is_absolute_href(asset.href)
        original_href = asset.get_absolute_href()

        item.make_asset_hrefs_relative()
        self.assertEqual(asset.get_absolute_href(), original_href)

    def test_from_invalid_dict_raises_exception(self) -> None:
        stac_io = pystac.StacIO.default()
        catalog_dict = stac_io.read_json(
            TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
        )
        with self.assertRaises(pystac.STACTypeError):
            _ = pystac.Item.from_dict(catalog_dict)


class ItemCommonMetadataTest(unittest.TestCase):
    def setUp(self) -> None:
        # TODO: Update these to use 1.0.0 examples
        self.URI_1 = TestCases.get_path(
            "data-files/examples/1.0.0-beta.2/item-spec/examples/datetimerange.json"
        )
        self.ITEM_1 = Item.from_file(self.URI_1)

        self.URI_2 = TestCases.get_path(
            "data-files/examples/1.0.0-beta.2/item-spec/examples/sample-full.json"
        )
        self.ITEM_2 = Item.from_file(self.URI_2)

        self.EXAMPLE_CM_DICT: Dict[str, Any] = {
            "start_datetime": "2020-05-21T16:42:24.896Z",
            "platform": "example platform",
            "providers": [
                {
                    "name": "example provider",
                    "roles": ["example roll"],
                    "url": "https://example-provider.com/",
                }
            ],
        }

    def test_datetimes(self) -> None:
        # save dict of original item to check that `common_metadata`
        # method doesn't mutate self.item_1
        before = self.ITEM_1.clone().to_dict()
        start_datetime_str = self.ITEM_1.properties["start_datetime"]
        self.assertIsInstance(start_datetime_str, str)

        common_metadata = self.ITEM_1.common_metadata
        self.assertIsInstance(common_metadata, CommonMetadata)
        self.assertIsInstance(common_metadata.start_datetime, datetime)
        self.assertDictEqual(before, self.ITEM_1.to_dict())
        self.assertIsNone(common_metadata.providers)

    def test_common_metadata_start_datetime(self) -> None:
        x = self.ITEM_1.clone()
        start_datetime_str = "2018-01-01T13:21:30Z"
        start_datetime_dt = str_to_datetime(start_datetime_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.start_datetime, start_datetime_dt)
        self.assertEqual(x.properties["start_datetime"], start_datetime_str)

        x.common_metadata.start_datetime = example_datetime_dt

        self.assertEqual(x.common_metadata.start_datetime, example_datetime_dt)
        self.assertEqual(x.properties["start_datetime"], example_datetime_str)

    def test_common_metadata_end_datetime(self) -> None:
        x = self.ITEM_1.clone()
        end_datetime_str = "2018-01-01T13:31:30Z"
        end_datetime_dt = str_to_datetime(end_datetime_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.end_datetime, end_datetime_dt)
        self.assertEqual(x.properties["end_datetime"], end_datetime_str)

        x.common_metadata.end_datetime = example_datetime_dt

        self.assertEqual(x.common_metadata.end_datetime, example_datetime_dt)
        self.assertEqual(x.properties["end_datetime"], example_datetime_str)

    def test_common_metadata_created(self) -> None:
        x = self.ITEM_2.clone()
        created_str = "2016-05-04T00:00:01Z"
        created_dt = str_to_datetime(created_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.created, created_dt)
        self.assertEqual(x.properties["created"], created_str)

        x.common_metadata.created = example_datetime_dt

        self.assertEqual(x.common_metadata.created, example_datetime_dt)
        self.assertEqual(x.properties["created"], example_datetime_str)

    def test_common_metadata_updated(self) -> None:
        x = self.ITEM_2.clone()
        updated_str = "2017-01-01T00:30:55Z"
        updated_dt = str_to_datetime(updated_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.updated, updated_dt)
        self.assertEqual(x.properties["updated"], updated_str)

        x.common_metadata.updated = example_datetime_dt

        self.assertEqual(x.common_metadata.updated, example_datetime_dt)
        self.assertEqual(x.properties["updated"], example_datetime_str)

    def test_common_metadata_providers(self) -> None:
        x = self.ITEM_2.clone()

        providers_dict_list: List[Dict[str, Any]] = [
            {
                "name": "CoolSat",
                "roles": ["producer", "licensor"],
                "url": "https://cool-sat.com/",
            }
        ]
        providers_object_list = [Provider.from_dict(d) for d in providers_dict_list]

        example_providers_dict_list: List[Dict[str, Any]] = [
            {
                "name": "ExampleProvider_1",
                "roles": ["example_role_1", "example_role_2"],
                "url": "https://exampleprovider1.com/",
            },
            {
                "name": "ExampleProvider_2",
                "roles": ["example_role_1", "example_role_2"],
                "url": "https://exampleprovider2.com/",
            },
        ]
        example_providers_object_list = [
            Provider.from_dict(d) for d in example_providers_dict_list
        ]

        for i in range(len(get_opt(x.common_metadata.providers))):
            p1 = get_opt(x.common_metadata.providers)[i]
            p2 = providers_object_list[i]
            self.assertIsInstance(p1, Provider)
            self.assertIsInstance(p2, Provider)
            self.assertDictEqual(p1.to_dict(), p2.to_dict())

            pd1 = x.properties["providers"][i]
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

            pd1 = x.properties["providers"][i]
            pd2 = example_providers_dict_list[i]
            self.assertIsInstance(pd1, dict)
            self.assertIsInstance(pd2, dict)
            self.assertDictEqual(pd1, pd2)

    def test_common_metadata_basics(self) -> None:
        x = self.ITEM_2.clone()

        # Title
        title = "A CS3 item"
        example_title = "example title"
        self.assertEqual(x.common_metadata.title, title)
        x.common_metadata.title = example_title
        self.assertEqual(x.common_metadata.title, example_title)
        self.assertEqual(x.properties["title"], example_title)

        # Description
        example_description = "example description"
        self.assertIsNone(x.common_metadata.description)
        x.common_metadata.description = example_description
        self.assertEqual(x.common_metadata.description, example_description)
        self.assertEqual(x.properties["description"], example_description)

        # License
        license = "PDDL-1.0"
        example_license = "example license"
        self.assertEqual(x.common_metadata.license, license)
        x.common_metadata.license = example_license
        self.assertEqual(x.common_metadata.license, example_license)
        self.assertEqual(x.properties["license"], example_license)

        # Platform
        platform = "coolsat2"
        example_platform = "example_platform"
        self.assertEqual(x.common_metadata.platform, platform)
        x.common_metadata.platform = example_platform
        self.assertEqual(x.common_metadata.platform, example_platform)
        self.assertEqual(x.properties["platform"], example_platform)

        # Instruments
        instruments = ["cool_sensor_v1"]
        example_instruments = ["example instrument 1", "example instrument 2"]
        self.assertListEqual(x.common_metadata.instruments or [], instruments)
        x.common_metadata.instruments = example_instruments
        self.assertListEqual(x.common_metadata.instruments, example_instruments)
        self.assertListEqual(x.properties["instruments"], example_instruments)

        # Constellation
        example_constellation = "example constellation"
        self.assertIsNone(x.common_metadata.constellation)
        x.common_metadata.constellation = example_constellation
        self.assertEqual(x.common_metadata.constellation, example_constellation)
        self.assertEqual(x.properties["constellation"], example_constellation)

        # Mission
        example_mission = "example mission"
        self.assertIsNone(x.common_metadata.mission)
        x.common_metadata.mission = example_mission
        self.assertEqual(x.common_metadata.mission, example_mission)
        self.assertEqual(x.properties["mission"], example_mission)

        # GSD
        gsd = 0.512
        example_gsd = 0.75
        self.assertEqual(x.common_metadata.gsd, gsd)
        x.common_metadata.gsd = example_gsd
        self.assertEqual(x.common_metadata.gsd, example_gsd)
        self.assertEqual(x.properties["gsd"], example_gsd)


class AssetCommonMetadataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    def test_datetime(self) -> None:
        expected_datetime = "2017-05-01T13:22:30.040Z"
        asset = pystac.Asset.from_dict({"href": "test", "datetime": expected_datetime})
        asset_cm = CommonMetadata(asset.extra_fields)

        # Get
        self.assertEqual(asset_cm.datetime, str_to_datetime(expected_datetime))

        # Set
        set_value = str_to_datetime("2014-05-02T13:22:30.040Z")
        asset_cm.datetime = set_value

        self.assertEqual(asset_cm.datetime, set_value)
        self.assertEqual(asset.to_dict()["datetime"], datetime_to_str(set_value))

        # Does not pop
        asset_cm.datetime = None
        self.assertIn("datetime", asset.to_dict())
        self.assertIsNone(asset.to_dict()["datetime"])

    def test_start_datetime(self) -> None:
        expected_start_datetime = "2017-05-01T13:22:30.040Z"
        asset = pystac.Asset.from_dict(
            {"href": "test", "start_datetime": expected_start_datetime}
        )
        asset_cm = CommonMetadata(asset.extra_fields)

        # Get
        self.assertEqual(
            asset_cm.start_datetime, str_to_datetime(expected_start_datetime)
        )

        # Set
        set_value = str_to_datetime("2014-05-02T13:22:30.040Z")
        asset_cm.start_datetime = set_value

        self.assertEqual(asset_cm.start_datetime, set_value)
        self.assertEqual(asset.to_dict()["start_datetime"], datetime_to_str(set_value))

        # Pop
        asset_cm.start_datetime = None
        self.assertNotIn("start_datetime", asset.to_dict())

    def test_end_datetime(self) -> None:
        expected_end_datetime = "2017-05-02T13:22:30.040Z"
        asset = pystac.Asset.from_dict(
            {"href": "test", "end_datetime": expected_end_datetime}
        )
        asset_cm = CommonMetadata(asset.extra_fields)

        # Get
        self.assertEqual(asset_cm.end_datetime, str_to_datetime(expected_end_datetime))

        # Set
        set_value = str_to_datetime("2014-05-01T13:22:30.040Z")
        asset_cm.end_datetime = set_value

        self.assertEqual(asset_cm.end_datetime, set_value)
        self.assertEqual(asset.to_dict()["end_datetime"], datetime_to_str(set_value))

        # Pop
        asset_cm.end_datetime = None
        self.assertNotIn("end_datetime", asset.to_dict())

    def test_license(self) -> None:
        expected_license = "CC-BY-4.0"
        asset = pystac.Asset.from_dict({"href": "test", "license": expected_license})
        asset_cm = CommonMetadata(asset.extra_fields)

        # Get
        self.assertEqual(asset_cm.license, expected_license)

        # Set
        set_value = "various"
        asset_cm.license = set_value

        self.assertEqual(asset_cm.license, set_value)
        self.assertEqual(asset.to_dict()["license"], set_value)

        # Pop
        asset_cm.license = None
        self.assertNotIn("license", asset.to_dict())

    def test_providers(self) -> None:
        expected_providers = [
            {
                "name": "USGS",
                "url": "https://landsat.usgs.gov/",
                "roles": [ProviderRole.PRODUCER, ProviderRole.LICENSOR],
            }
        ]
        asset = pystac.Asset.from_dict(
            {"href": "test", "providers": expected_providers}
        )
        asset_cm = CommonMetadata(asset.extra_fields)

        # Get
        self.assertEqual(
            asset_cm.providers, [Provider.from_dict(p) for p in expected_providers]
        )

        # Set
        set_value = [
            pystac.Provider(
                name="John Snow",
                url="https://cholera.com/",
                roles=[ProviderRole.PRODUCER],
            )
        ]
        asset_cm.providers = set_value

        self.assertEqual(asset_cm.providers, set_value)
        self.assertEqual(asset.to_dict()["providers"], [p.to_dict() for p in set_value])

        # Pop
        asset_cm.providers = None
        self.assertNotIn("providers", asset.to_dict())

    def test_platform(self) -> None:
        expected_platform = "shoes"
        asset = pystac.Asset.from_dict({"href": "test", "platform": expected_platform})
        asset_cm = CommonMetadata(asset.extra_fields)

        # Get
        self.assertEqual(asset_cm.platform, expected_platform)

        # Set
        set_value = "brick"
        asset_cm.platform = set_value

        self.assertEqual(asset_cm.platform, set_value)
        self.assertEqual(asset.to_dict()["platform"], set_value)

        # Pop
        asset_cm.platform = None
        self.assertNotIn("platform", asset.to_dict())

    def test_instruments(self) -> None:
        expected_instruments = ["caliper"]
        asset = pystac.Asset.from_dict(
            {"href": "test", "instruments": expected_instruments}
        )
        asset_cm = CommonMetadata(asset.extra_fields)

        # Get
        self.assertEqual(asset_cm.instruments, expected_instruments)

        # Set
        set_value = ["horns"]
        asset_cm.instruments = set_value

        self.assertEqual(asset_cm.instruments, set_value)
        self.assertEqual(asset.to_dict()["instruments"], set_value)

        # Pop
        asset_cm.instruments = None
        self.assertNotIn("instruments", asset.to_dict())

    def test_constellation(self) -> None:
        expected_constellation = "little dipper"
        asset = pystac.Asset.from_dict(
            {"href": "test", "constellation": expected_constellation}
        )
        asset_cm = CommonMetadata(asset.extra_fields)

        # Get
        self.assertEqual(asset_cm.constellation, expected_constellation)

        # Set
        set_value = "orion"
        asset_cm.constellation = set_value

        self.assertEqual(asset_cm.constellation, set_value)
        self.assertEqual(asset.to_dict()["constellation"], set_value)

        # Pop
        asset_cm.constellation = None
        self.assertNotIn("constellation", asset.to_dict())

    def test_mission(self) -> None:
        expected_mission = "possible"
        asset = pystac.Asset.from_dict({"href": "test", "mission": expected_mission})
        asset_cm = CommonMetadata(asset.extra_fields)

        # Get
        self.assertEqual(asset_cm.mission, expected_mission)

        # Set
        set_value = "critical"
        asset_cm.mission = set_value

        self.assertEqual(asset_cm.mission, set_value)
        self.assertEqual(asset.to_dict()["mission"], set_value)

        # Pop
        asset_cm.mission = None
        self.assertNotIn("mission", asset.to_dict())

    def test_gsd(self) -> None:
        expected_gsd = 40
        asset = pystac.Asset.from_dict({"href": "test", "gsd": expected_gsd})
        asset_cm = CommonMetadata(asset.extra_fields)

        # Get
        self.assertEqual(asset_cm.gsd, expected_gsd)

        # Set
        set_value = 100
        asset_cm.gsd = set_value

        self.assertEqual(asset_cm.gsd, set_value)
        self.assertEqual(asset.to_dict()["gsd"], set_value)

        # Pop
        asset_cm.gsd = None
        self.assertNotIn("gsd", asset.to_dict())

    def test_created(self) -> None:
        expected_created = "2017-05-18T13:22:30.040000Z"
        asset = pystac.Asset.from_dict({"href": "test", "created": expected_created})
        asset_cm = CommonMetadata(asset.extra_fields)

        # Get
        self.assertEqual(asset_cm.created, str_to_datetime(expected_created))

        # Set
        set_value = str_to_datetime("2017-06-18T13:22:30.040Z")
        asset_cm.created = set_value

        self.assertEqual(asset_cm.created, set_value)
        self.assertEqual(asset.to_dict()["created"], datetime_to_str(set_value))

        # Pop
        asset_cm.created = None
        self.assertNotIn("created", asset.to_dict())

    def test_updated(self) -> None:
        expected_updated = "2017-05-18T13:22:30.040000Z"
        asset = pystac.Asset.from_dict({"href": "test", "updated": expected_updated})
        asset_cm = CommonMetadata(asset.extra_fields)

        # Get
        self.assertEqual(asset_cm.updated, str_to_datetime(expected_updated))

        # Set
        set_value = str_to_datetime("2017-06-18T13:22:30.040Z")
        asset_cm.updated = set_value

        self.assertEqual(asset_cm.updated, set_value)
        self.assertEqual(asset.to_dict()["updated"], datetime_to_str(set_value))

        # Pop
        asset_cm.created = None
        self.assertNotIn("created", asset.to_dict())


class ItemSubClassTest(unittest.TestCase):
    """This tests cases related to creating classes inheriting from pystac.Catalog to
    ensure that inheritance, class methods, etc. function as expected."""

    SAMPLE_ITEM = TestCases.get_path("data-files/item/sample-item.json")

    class BasicCustomItem(pystac.Item):
        pass

    def setUp(self) -> None:
        self.stac_io = pystac.StacIO.default()

    def test_from_dict_returns_subclass(self) -> None:
        item_dict = self.stac_io.read_json(self.SAMPLE_ITEM)
        custom_item = self.BasicCustomItem.from_dict(item_dict)

        self.assertIsInstance(custom_item, self.BasicCustomItem)

    def test_from_file_returns_subclass(self) -> None:
        custom_item = self.BasicCustomItem.from_file(self.SAMPLE_ITEM)

        self.assertIsInstance(custom_item, self.BasicCustomItem)

    def test_clone(self) -> None:
        custom_item = self.BasicCustomItem.from_file(self.SAMPLE_ITEM)
        cloned_item = custom_item.clone()

        self.assertIsInstance(cloned_item, self.BasicCustomItem)


class AssetSubClassTest(unittest.TestCase):
    class CustomAsset(Asset):
        pass

    def setUp(self) -> None:
        self.maxDiff = None
        with open(TestCases.get_path("data-files/item/sample-item.json")) as src:
            item_dict = json.load(src)

        self.asset_dict = item_dict["assets"]["analytic"]

    def test_from_dict(self) -> None:
        asset = self.CustomAsset.from_dict(self.asset_dict)

        self.assertIsInstance(asset, self.CustomAsset)

    def test_clone(self) -> None:
        asset = self.CustomAsset.from_dict(self.asset_dict)
        cloned_asset = asset.clone()

        self.assertIsInstance(cloned_asset, self.CustomAsset)
