import unittest
from datetime import datetime
from typing import Any, Dict, List

from pystac import CommonMetadata, Provider, ProviderRole, Item
from pystac import utils

from tests.utils import TestCases


class CommonMetadataTest(unittest.TestCase):
    def setUp(self) -> None:
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

        cm = self.ITEM_1.common_metadata
        self.assertIsInstance(cm, CommonMetadata)
        self.assertIsInstance(cm.start_datetime, datetime)
        self.assertDictEqual(before, self.ITEM_1.to_dict())
        self.assertIsNone(cm.providers)

    def test_common_metadata_start_datetime(self) -> None:
        x = self.ITEM_1.clone()
        start_datetime_str = "2018-01-01T13:21:30Z"
        start_datetime_dt = utils.str_to_datetime(start_datetime_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = utils.str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.start_datetime, start_datetime_dt)
        self.assertEqual(x.properties["start_datetime"], start_datetime_str)

        x.common_metadata.start_datetime = example_datetime_dt

        self.assertEqual(x.common_metadata.start_datetime, example_datetime_dt)
        self.assertEqual(x.properties["start_datetime"], example_datetime_str)

    def test_common_metadata_end_datetime(self) -> None:
        x = self.ITEM_1.clone()
        end_datetime_str = "2018-01-01T13:31:30Z"
        end_datetime_dt = utils.str_to_datetime(end_datetime_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = utils.str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.end_datetime, end_datetime_dt)
        self.assertEqual(x.properties["end_datetime"], end_datetime_str)

        x.common_metadata.end_datetime = example_datetime_dt

        self.assertEqual(x.common_metadata.end_datetime, example_datetime_dt)
        self.assertEqual(x.properties["end_datetime"], example_datetime_str)

    def test_common_metadata_created(self) -> None:
        x = self.ITEM_2.clone()
        created_str = "2016-05-04T00:00:01Z"
        created_dt = utils.str_to_datetime(created_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = utils.str_to_datetime(example_datetime_str)

        self.assertEqual(x.common_metadata.created, created_dt)
        self.assertEqual(x.properties["created"], created_str)

        x.common_metadata.created = example_datetime_dt

        self.assertEqual(x.common_metadata.created, example_datetime_dt)
        self.assertEqual(x.properties["created"], example_datetime_str)

    def test_common_metadata_updated(self) -> None:
        x = self.ITEM_2.clone()
        updated_str = "2017-01-01T00:30:55Z"
        updated_dt = utils.str_to_datetime(updated_str)
        example_datetime_str = "2020-01-01T00:00:00Z"
        example_datetime_dt = utils.str_to_datetime(example_datetime_str)

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

        for i in range(len(utils.get_opt(x.common_metadata.providers))):
            p1 = utils.get_opt(x.common_metadata.providers)[i]
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
        self.item = Item.from_file(
            TestCases.get_path("data-files/item/sample-item-asset-properties.json")
        )

    def test_title(self) -> None:
        item = self.item.clone()
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.title
        a2_known_value = "Thumbnail"

        # Get
        self.assertNotEqual(thumbnail_cm.title, item_value)
        self.assertEqual(thumbnail_cm.title, a2_known_value)

        # Set
        set_value = "Just Another Asset"
        analytic_cm.title = set_value

        self.assertEqual(analytic_cm.title, set_value)
        self.assertEqual(analytic.to_dict()["title"], set_value)

    def test_description(self) -> None:
        item = self.item.clone()
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.description
        a2_known_value = "Thumbnail of the item"

        # Get
        self.assertNotEqual(thumbnail_cm.description, item_value)
        self.assertEqual(thumbnail_cm.description, a2_known_value)

        # Set
        set_value = "Yet another description."
        analytic_cm.description = set_value

        self.assertEqual(analytic_cm.description, set_value)
        self.assertEqual(analytic.to_dict()["description"], set_value)

    def test_start_datetime(self) -> None:
        item = self.item.clone()
        item_cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = item_cm.start_datetime
        a2_known_value = utils.str_to_datetime("2017-05-01T13:22:30.040Z")

        # Get
        self.assertNotEqual(thumbnail_cm.start_datetime, item_value)
        self.assertEqual(thumbnail_cm.start_datetime, a2_known_value)

        # Set
        set_value = utils.str_to_datetime("2014-05-01T13:22:30.040Z")
        analytic_cm.start_datetime = set_value

        self.assertEqual(analytic_cm.start_datetime, set_value)
        self.assertEqual(
            analytic.to_dict()["start_datetime"], utils.datetime_to_str(set_value)
        )

    def test_end_datetime(self) -> None:
        item = self.item.clone()
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.end_datetime
        a2_known_value = utils.str_to_datetime("2017-05-02T13:22:30.040Z")

        # Get
        self.assertNotEqual(thumbnail_cm.end_datetime, item_value)
        self.assertEqual(thumbnail_cm.end_datetime, a2_known_value)

        # Set
        set_value = utils.str_to_datetime("2014-05-01T13:22:30.040Z")
        analytic_cm.end_datetime = set_value

        self.assertEqual(analytic_cm.end_datetime, set_value)
        self.assertEqual(
            analytic.to_dict()["end_datetime"], utils.datetime_to_str(set_value)
        )

    def test_license(self) -> None:
        item = self.item.clone()
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.license
        a2_known_value = "CC-BY-4.0"

        # Get
        self.assertNotEqual(thumbnail_cm.license, item_value)
        self.assertEqual(thumbnail_cm.license, a2_known_value)

        # Set
        set_value = "various"
        analytic_cm.license = set_value

        self.assertEqual(analytic_cm.license, set_value)
        self.assertEqual(analytic.to_dict()["license"], set_value)

    def test_providers(self) -> None:
        item = self.item.clone()
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.providers
        a2_known_value = [
            Provider(
                name="USGS",
                url="https://landsat.usgs.gov/",
                roles=[ProviderRole.PRODUCER, ProviderRole.LICENSOR],
            )
        ]

        # Get
        self.assertNotEqual(thumbnail_cm.providers, item_value)
        self.assertEqual(thumbnail_cm.providers, a2_known_value)

        # Set
        set_value = [
            Provider(
                name="John Snow",
                url="https://cholera.com/",
                roles=[ProviderRole.PRODUCER],
            )
        ]
        analytic_cm.providers = set_value

        self.assertEqual(analytic_cm.providers, set_value)
        self.assertEqual(
            analytic.to_dict()["providers"], [p.to_dict() for p in set_value]
        )

    def test_platform(self) -> None:
        item = self.item.clone()
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.platform
        a2_known_value = "shoes"

        # Get
        self.assertNotEqual(thumbnail_cm.platform, item_value)
        self.assertEqual(thumbnail_cm.platform, a2_known_value)

        # Set
        set_value = "brick"
        analytic_cm.platform = set_value

        self.assertEqual(analytic_cm.platform, set_value)
        self.assertEqual(analytic.to_dict()["platform"], set_value)

    def test_instruments(self) -> None:
        item = self.item.clone()
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.instruments
        a2_known_value = ["caliper"]

        # Get
        self.assertNotEqual(thumbnail_cm.instruments, item_value)
        self.assertEqual(thumbnail_cm.instruments, a2_known_value)

        # Set
        set_value = ["horns"]
        analytic_cm.instruments = set_value

        self.assertEqual(analytic_cm.instruments, set_value)
        self.assertEqual(analytic.to_dict()["instruments"], set_value)

    def test_constellation(self) -> None:
        item = self.item.clone()
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.constellation
        a2_known_value = "little dipper"

        # Get
        self.assertNotEqual(thumbnail_cm.constellation, item_value)
        self.assertEqual(thumbnail_cm.constellation, a2_known_value)

        # Set
        set_value = "orion"
        analytic_cm.constellation = set_value

        self.assertEqual(analytic_cm.constellation, set_value)
        self.assertEqual(analytic.to_dict()["constellation"], set_value)

    def test_mission(self) -> None:
        item = self.item.clone()
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.mission
        a2_known_value = "possible"

        # Get
        self.assertNotEqual(thumbnail_cm.mission, item_value)
        self.assertEqual(thumbnail_cm.mission, a2_known_value)

        # Set
        set_value = "critical"
        analytic_cm.mission = set_value

        self.assertEqual(analytic_cm.mission, set_value)
        self.assertEqual(analytic.to_dict()["mission"], set_value)

    def test_gsd(self) -> None:
        item = self.item.clone()
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.gsd
        a2_known_value = 40

        # Get
        self.assertNotEqual(thumbnail_cm.gsd, item_value)
        self.assertEqual(thumbnail_cm.gsd, a2_known_value)

        # Set
        set_value = 100
        analytic_cm.gsd = set_value

        self.assertEqual(analytic_cm.gsd, set_value)
        self.assertEqual(analytic.to_dict()["gsd"], set_value)

    def test_created(self) -> None:
        item = self.item.clone()
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.created
        a2_known_value = utils.str_to_datetime("2017-05-17T13:22:30.040Z")

        # Get
        self.assertNotEqual(thumbnail_cm.created, item_value)
        self.assertEqual(thumbnail_cm.created, a2_known_value)

        # Set
        set_value = utils.str_to_datetime("2014-05-17T13:22:30.040Z")
        analytic_cm.created = set_value

        self.assertEqual(analytic_cm.created, set_value)
        self.assertEqual(
            analytic.to_dict()["created"], utils.datetime_to_str(set_value)
        )

    def test_updated(self) -> None:
        item = self.item.clone()
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.updated
        a2_known_value = utils.str_to_datetime("2017-05-18T13:22:30.040Z")

        # Get
        self.assertNotEqual(thumbnail_cm.updated, item_value)
        self.assertEqual(thumbnail_cm.updated, a2_known_value)

        # Set
        set_value = utils.str_to_datetime("2014-05-18T13:22:30.040Z")
        analytic_cm.updated = set_value

        self.assertEqual(analytic_cm.updated, set_value)
        self.assertEqual(
            analytic.to_dict()["updated"], utils.datetime_to_str(set_value)
        )
