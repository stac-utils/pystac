from datetime import datetime
from typing import Any, Dict, List
import unittest

from pystac import Asset, CommonMetadata, Item, Provider, ProviderRole
from pystac.utils import str_to_datetime, datetime_to_str, get_opt
from tests.utils import TestCases


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

    def test_datetime_stays_in_sync(self) -> None:
        item = self.ITEM_2.clone()
        item_cm = CommonMetadata(item.properties)

        self.assertEqual(item.datetime, item_cm.datetime)

        # Set from Item.datetime
        new_datetime_1 = str_to_datetime("2021-01-01T00:00:00Z")
        assert new_datetime_1 != item.datetime
        item.datetime = new_datetime_1

        self.assertEqual(item.properties["datetime"], datetime_to_str(new_datetime_1))
        self.assertEqual(item_cm.datetime, new_datetime_1)

        # Set from CommonMetadata
        new_datetime_2 = str_to_datetime("2022-01-01T00:00:00Z")
        item_cm.datetime = new_datetime_2

        self.assertEqual(item.properties["datetime"], datetime_to_str(new_datetime_2))
        self.assertEqual(item.datetime, new_datetime_2)

    def test_datetimes(self) -> None:
        # save dict of original item to check that `common_metadata`
        # method doesn't mutate self.item_1
        before = self.ITEM_1.clone().to_dict()
        start_datetime_str = self.ITEM_1.properties["start_datetime"]
        self.assertIsInstance(start_datetime_str, str)

        common_metadata = CommonMetadata.ext(self.ITEM_1)
        self.assertIsInstance(common_metadata, CommonMetadata)
        self.assertIsInstance(common_metadata.start_datetime, datetime)
        self.assertDictEqual(before, self.ITEM_1.to_dict())
        self.assertIsNone(common_metadata.providers)

    def test_common_metadata_start_datetime(self) -> None:
        x = self.ITEM_1.clone()
        common_metadata = CommonMetadata.ext(x)
        start_datetime_str = "2018-01-01T13:21:30Z"
        start_datetime_dt = str_to_datetime(start_datetime_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(common_metadata.start_datetime, start_datetime_dt)
        self.assertEqual(x.properties["start_datetime"], start_datetime_str)

        common_metadata.start_datetime = example_datetime_dt

        self.assertEqual(common_metadata.start_datetime, example_datetime_dt)
        self.assertEqual(x.properties["start_datetime"], example_datetime_str)

    def test_common_metadata_end_datetime(self) -> None:
        x = self.ITEM_1.clone()
        common_metadata = CommonMetadata.ext(x)
        end_datetime_str = "2018-01-01T13:31:30Z"
        end_datetime_dt = str_to_datetime(end_datetime_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(common_metadata.end_datetime, end_datetime_dt)
        self.assertEqual(x.properties["end_datetime"], end_datetime_str)

        common_metadata.end_datetime = example_datetime_dt

        self.assertEqual(common_metadata.end_datetime, example_datetime_dt)
        self.assertEqual(x.properties["end_datetime"], example_datetime_str)

    def test_common_metadata_created(self) -> None:
        x = self.ITEM_2.clone()
        common_metadata = CommonMetadata.ext(x)
        created_str = "2016-05-04T00:00:01Z"
        created_dt = str_to_datetime(created_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(common_metadata.created, created_dt)
        self.assertEqual(x.properties["created"], created_str)

        common_metadata.created = example_datetime_dt

        self.assertEqual(common_metadata.created, example_datetime_dt)
        self.assertEqual(x.properties["created"], example_datetime_str)

    def test_common_metadata_updated(self) -> None:
        x = self.ITEM_2.clone()
        common_metadata = CommonMetadata.ext(x)
        updated_str = "2017-01-01T00:30:55Z"
        updated_dt = str_to_datetime(updated_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = str_to_datetime(example_datetime_str)

        self.assertEqual(common_metadata.updated, updated_dt)
        self.assertEqual(x.properties["updated"], updated_str)

        common_metadata.updated = example_datetime_dt

        self.assertEqual(common_metadata.updated, example_datetime_dt)
        self.assertEqual(x.properties["updated"], example_datetime_str)

    def test_common_metadata_providers(self) -> None:
        x = self.ITEM_2.clone()
        common_metadata = CommonMetadata.ext(x)

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

        for i in range(len(get_opt(common_metadata.providers))):
            p1 = get_opt(common_metadata.providers)[i]
            p2 = providers_object_list[i]
            self.assertIsInstance(p1, Provider)
            self.assertIsInstance(p2, Provider)
            self.assertDictEqual(p1.to_dict(), p2.to_dict())

            pd1 = x.properties["providers"][i]
            pd2 = providers_dict_list[i]
            self.assertIsInstance(pd1, dict)
            self.assertIsInstance(pd2, dict)
            self.assertDictEqual(pd1, pd2)

        common_metadata.providers = example_providers_object_list

        for i in range(len(common_metadata.providers)):
            p1 = common_metadata.providers[i]
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
        common_metadata = CommonMetadata.ext(x)

        # Title
        title = "A CS3 item"
        example_title = "example title"
        self.assertEqual(common_metadata.title, title)
        common_metadata.title = example_title
        self.assertEqual(common_metadata.title, example_title)
        self.assertEqual(x.properties["title"], example_title)

        # Description
        example_description = "example description"
        self.assertIsNone(common_metadata.description)
        common_metadata.description = example_description
        self.assertEqual(common_metadata.description, example_description)
        self.assertEqual(x.properties["description"], example_description)

        # License
        license = "PDDL-1.0"
        example_license = "example license"
        self.assertEqual(common_metadata.license, license)
        common_metadata.license = example_license
        self.assertEqual(common_metadata.license, example_license)
        self.assertEqual(x.properties["license"], example_license)

        # Platform
        platform = "coolsat2"
        example_platform = "example_platform"
        self.assertEqual(common_metadata.platform, platform)
        common_metadata.platform = example_platform
        self.assertEqual(common_metadata.platform, example_platform)
        self.assertEqual(x.properties["platform"], example_platform)

        # Instruments
        instruments = ["cool_sensor_v1"]
        example_instruments = ["example instrument 1", "example instrument 2"]
        self.assertListEqual(common_metadata.instruments or [], instruments)
        common_metadata.instruments = example_instruments
        self.assertListEqual(common_metadata.instruments, example_instruments)
        self.assertListEqual(x.properties["instruments"], example_instruments)

        # Constellation
        example_constellation = "example constellation"
        self.assertIsNone(common_metadata.constellation)
        common_metadata.constellation = example_constellation
        self.assertEqual(common_metadata.constellation, example_constellation)
        self.assertEqual(x.properties["constellation"], example_constellation)

        # Mission
        example_mission = "example mission"
        self.assertIsNone(common_metadata.mission)
        common_metadata.mission = example_mission
        self.assertEqual(common_metadata.mission, example_mission)
        self.assertEqual(x.properties["mission"], example_mission)

        # GSD
        gsd = 0.512
        example_gsd = 0.75
        self.assertEqual(common_metadata.gsd, gsd)
        common_metadata.gsd = example_gsd
        self.assertEqual(common_metadata.gsd, example_gsd)
        self.assertEqual(x.properties["gsd"], example_gsd)


class AssetCommonMetadataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    def test_datetime(self) -> None:
        expected_datetime = "2017-05-01T13:22:30.040Z"
        asset = Asset.from_dict({"href": "test", "datetime": expected_datetime})
        asset_cm = CommonMetadata(asset.fields)

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
        asset = Asset.from_dict(
            {"href": "test", "start_datetime": expected_start_datetime}
        )
        asset_cm = CommonMetadata(asset.fields)

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
        asset = Asset.from_dict({"href": "test", "end_datetime": expected_end_datetime})
        asset_cm = CommonMetadata(asset.fields)

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
        asset = Asset.from_dict({"href": "test", "license": expected_license})
        asset_cm = CommonMetadata(asset.fields)

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
        asset = Asset.from_dict({"href": "test", "providers": expected_providers})
        asset_cm = CommonMetadata(asset.fields)

        # Get
        self.assertEqual(
            asset_cm.providers, [Provider.from_dict(p) for p in expected_providers]
        )

        # Set
        set_value = [
            Provider(
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
        asset = Asset.from_dict({"href": "test", "platform": expected_platform})
        asset_cm = CommonMetadata(asset.fields)

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
        asset = Asset.from_dict({"href": "test", "instruments": expected_instruments})
        asset_cm = CommonMetadata(asset.fields)

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
        asset = Asset.from_dict(
            {"href": "test", "constellation": expected_constellation}
        )
        asset_cm = CommonMetadata(asset.fields)

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
        asset = Asset.from_dict({"href": "test", "mission": expected_mission})
        asset_cm = CommonMetadata(asset.fields)

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
        asset = Asset.from_dict({"href": "test", "gsd": expected_gsd})
        asset_cm = CommonMetadata(asset.fields)

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
        asset = Asset.from_dict({"href": "test", "created": expected_created})
        asset_cm = CommonMetadata(asset.fields)

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
        asset = Asset.from_dict({"href": "test", "updated": expected_updated})
        asset_cm = CommonMetadata(asset.fields)

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
