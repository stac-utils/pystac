from datetime import datetime
from typing import Any

import pytest

from pystac import CommonMetadata, Item, Provider, ProviderRole, utils
from tests.v1.utils import TestCases


@pytest.fixture
def date_time_range_item() -> Item:
    return Item.from_file(
        TestCases.get_path(
            "data-files/examples/1.0.0-beta.2/item-spec/examples/datetimerange.json"
        )
    )


@pytest.fixture
def sample_full_item() -> Item:
    return Item.from_file(
        TestCases.get_path(
            "data-files/examples/1.0.0-beta.2/item-spec/examples/sample-full.json"
        )
    )


def test_datetimes(date_time_range_item: Item) -> None:
    # save dict of original item to check that `common_metadata`
    # method doesn't mutate self.item_1
    before = date_time_range_item.clone().to_dict()
    start_datetime_str = date_time_range_item.properties["start_datetime"]
    assert isinstance(start_datetime_str, str)

    cm = date_time_range_item.common_metadata
    assert isinstance(cm, CommonMetadata)
    assert isinstance(cm.start_datetime, datetime)
    assert before == date_time_range_item.to_dict()
    assert cm.providers is None


def test_common_metadata_start_datetime(date_time_range_item: Item) -> None:
    x = date_time_range_item.clone()
    start_datetime_str = "2018-01-01T13:21:30Z"
    start_datetime_dt = utils.str_to_datetime(start_datetime_str)
    example_datetime_str = "2020-01-01T00:00:00Z"
    example_datetime_dt = utils.str_to_datetime(example_datetime_str)

    assert x.common_metadata.start_datetime == start_datetime_dt
    assert x.properties["start_datetime"] == start_datetime_str

    x.common_metadata.start_datetime = example_datetime_dt

    assert x.common_metadata.start_datetime == example_datetime_dt
    assert x.properties["start_datetime"] == example_datetime_str


def test_common_metadata_end_datetime(date_time_range_item: Item) -> None:
    x = date_time_range_item.clone()
    end_datetime_str = "2018-01-01T13:31:30Z"
    end_datetime_dt = utils.str_to_datetime(end_datetime_str)
    example_datetime_str = "2020-01-01T00:00:00Z"
    example_datetime_dt = utils.str_to_datetime(example_datetime_str)

    assert x.common_metadata.end_datetime == end_datetime_dt
    assert x.properties["end_datetime"] == end_datetime_str

    x.common_metadata.end_datetime = example_datetime_dt

    assert x.common_metadata.end_datetime == example_datetime_dt
    assert x.properties["end_datetime"] == example_datetime_str


def test_common_metadata_created(sample_full_item: Item) -> None:
    x = sample_full_item.clone()
    created_str = "2016-05-04T00:00:01Z"
    created_dt = utils.str_to_datetime(created_str)
    example_datetime_str = "2020-01-01T00:00:00Z"
    example_datetime_dt = utils.str_to_datetime(example_datetime_str)

    assert x.common_metadata.created == created_dt
    assert x.properties["created"] == created_str

    x.common_metadata.created = example_datetime_dt

    assert x.common_metadata.created == example_datetime_dt
    assert x.properties["created"] == example_datetime_str


def test_common_metadata_updated(sample_full_item: Item) -> None:
    x = sample_full_item.clone()
    updated_str = "2017-01-01T00:30:55Z"
    updated_dt = utils.str_to_datetime(updated_str)
    example_datetime_str = "2020-01-01T00:00:00Z"
    example_datetime_dt = utils.str_to_datetime(example_datetime_str)

    assert x.common_metadata.updated == updated_dt
    assert x.properties["updated"] == updated_str

    x.common_metadata.updated = example_datetime_dt

    assert x.common_metadata.updated == example_datetime_dt
    assert x.properties["updated"] == example_datetime_str


def test_common_metadata_providers(sample_full_item: Item) -> None:
    x = sample_full_item.clone()

    providers_dict_list: list[dict[str, Any]] = [
        {
            "name": "CoolSat",
            "roles": ["producer", "licensor"],
            "url": "https://cool-sat.com/",
        }
    ]
    providers_object_list = [Provider.from_dict(d) for d in providers_dict_list]

    example_providers_dict_list: list[dict[str, Any]] = [
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
        assert isinstance(p1, Provider)
        assert isinstance(p2, Provider)
        assert p1.to_dict() == p2.to_dict()

        pd1 = x.properties["providers"][i]
        pd2 = providers_dict_list[i]
        assert isinstance(pd1, dict)
        assert isinstance(pd2, dict)
        assert pd1 == pd2

    x.common_metadata.providers = example_providers_object_list

    for i in range(len(x.common_metadata.providers)):
        p1 = x.common_metadata.providers[i]
        p2 = example_providers_object_list[i]
        assert isinstance(p1, Provider)
        assert isinstance(p2, Provider)
        assert p1.to_dict() == p2.to_dict()

        pd1 = x.properties["providers"][i]
        pd2 = example_providers_dict_list[i]
        assert isinstance(pd1, dict)
        assert isinstance(pd2, dict)
        assert pd1 == pd2


def test_common_metadata_basics(sample_full_item: Item) -> None:
    x = sample_full_item.clone()

    # Title
    title = "A CS3 item"
    example_title = "example title"
    assert x.common_metadata.title == title
    x.common_metadata.title = example_title
    assert x.common_metadata.title == example_title
    assert x.properties["title"] == example_title

    # Description
    example_description = "example description"
    assert x.common_metadata.description is None
    x.common_metadata.description = example_description
    assert x.common_metadata.description == example_description
    assert x.properties["description"] == example_description
    with pytest.raises(ValueError):
        x.common_metadata.description = ""

    # License
    license = "PDDL-1.0"
    example_license = "example license"
    assert x.common_metadata.license == license
    x.common_metadata.license = example_license
    assert x.common_metadata.license == example_license
    assert x.properties["license"] == example_license

    # Platform
    platform = "coolsat2"
    example_platform = "example_platform"
    assert x.common_metadata.platform == platform
    x.common_metadata.platform = example_platform
    assert x.common_metadata.platform == example_platform
    assert x.properties["platform"] == example_platform

    # Instruments
    instruments = ["cool_sensor_v1"]
    example_instruments = ["example instrument 1", "example instrument 2"]
    assert (x.common_metadata.instruments or []) == instruments
    x.common_metadata.instruments = example_instruments
    assert x.common_metadata.instruments == example_instruments
    assert x.properties["instruments"] == example_instruments

    # Constellation
    example_constellation = "example constellation"
    assert x.common_metadata.constellation is None
    x.common_metadata.constellation = example_constellation
    assert x.common_metadata.constellation == example_constellation
    assert x.properties["constellation"] == example_constellation

    # Mission
    example_mission = "example mission"
    assert x.common_metadata.mission is None
    x.common_metadata.mission = example_mission
    assert x.common_metadata.mission == example_mission
    assert x.properties["mission"] == example_mission

    # GSD
    gsd = 0.512
    example_gsd = 0.75
    assert x.common_metadata.gsd == gsd
    x.common_metadata.gsd = example_gsd
    assert x.common_metadata.gsd == example_gsd
    assert x.properties["gsd"] == example_gsd


class TestAssetCommonMetadata:
    @pytest.fixture
    def item(self) -> Item:
        return Item.from_file(
            TestCases.get_path("data-files/item/sample-item-asset-properties.json")
        )

    def test_title(self, item: Item) -> None:
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.title
        a2_known_value = "Thumbnail"

        # Get
        assert thumbnail_cm.title != item_value
        assert thumbnail_cm.title == a2_known_value

        # Set
        set_value = "Just Another Asset"
        analytic_cm.title = set_value

        assert analytic_cm.title == set_value
        assert analytic.to_dict()["title"] == set_value

    def test_description(self, item: Item) -> None:
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.description
        a2_known_value = "Thumbnail of the item"

        # Get
        assert thumbnail_cm.description != item_value
        assert thumbnail_cm.description == a2_known_value

        # Set
        set_value = "Yet another description."
        analytic_cm.description = set_value

        assert analytic_cm.description == set_value
        assert analytic.to_dict()["description"] == set_value

    def test_start_datetime(self, item: Item) -> None:
        item_cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = item_cm.start_datetime
        a2_known_value = utils.str_to_datetime("2017-05-01T13:22:30.040Z")

        # Get
        assert thumbnail_cm.start_datetime != item_value
        assert thumbnail_cm.start_datetime == a2_known_value

        # Set
        set_value = utils.str_to_datetime("2014-05-01T13:22:30.040Z")
        analytic_cm.start_datetime = set_value

        assert analytic_cm.start_datetime == set_value
        assert analytic.to_dict()["start_datetime"] == utils.datetime_to_str(set_value)

    def test_end_datetime(self, item: Item) -> None:
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.end_datetime
        a2_known_value = utils.str_to_datetime("2017-05-02T13:22:30.040Z")

        # Get
        assert thumbnail_cm.end_datetime != item_value
        assert thumbnail_cm.end_datetime == a2_known_value

        # Set
        set_value = utils.str_to_datetime("2014-05-01T13:22:30.040Z")
        analytic_cm.end_datetime = set_value

        assert analytic_cm.end_datetime == set_value
        assert analytic.to_dict()["end_datetime"] == utils.datetime_to_str(set_value)

    def test_license(self, item: Item) -> None:
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.license
        a2_known_value = "CC-BY-4.0"

        # Get
        assert thumbnail_cm.license != item_value
        assert thumbnail_cm.license == a2_known_value

        # Set
        set_value = "various"
        analytic_cm.license = set_value

        assert analytic_cm.license == set_value
        assert analytic.to_dict()["license"] == set_value

    def test_providers(self, item: Item) -> None:
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
        assert thumbnail_cm.providers != item_value
        assert thumbnail_cm.providers == a2_known_value

        # Set
        set_value = [
            Provider(
                name="John Snow",
                url="https://cholera.com/",
                roles=[ProviderRole.PRODUCER],
            )
        ]
        analytic_cm.providers = set_value

        assert analytic_cm.providers == set_value
        assert analytic.to_dict()["providers"] == [p.to_dict() for p in set_value]

    def test_platform(self, item: Item) -> None:
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.platform
        a2_known_value = "shoes"

        # Get
        assert thumbnail_cm.platform != item_value
        assert thumbnail_cm.platform == a2_known_value

        # Set
        set_value = "brick"
        analytic_cm.platform = set_value

        assert analytic_cm.platform == set_value
        assert analytic.to_dict()["platform"] == set_value

    def test_instruments(self, item: Item) -> None:
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.instruments
        a2_known_value = ["caliper"]

        # Get
        assert thumbnail_cm.instruments != item_value
        assert thumbnail_cm.instruments == a2_known_value

        # Set
        set_value = ["horns"]
        analytic_cm.instruments = set_value

        assert analytic_cm.instruments == set_value
        assert analytic.to_dict()["instruments"] == set_value

    def test_constellation(self, item: Item) -> None:
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.constellation
        a2_known_value = "little dipper"

        # Get
        assert thumbnail_cm.constellation != item_value
        assert thumbnail_cm.constellation == a2_known_value

        # Set
        set_value = "orion"
        analytic_cm.constellation = set_value

        assert analytic_cm.constellation == set_value
        assert analytic.to_dict()["constellation"] == set_value

    def test_mission(self, item: Item) -> None:
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.mission
        a2_known_value = "possible"

        # Get
        assert thumbnail_cm.mission != item_value
        assert thumbnail_cm.mission == a2_known_value

        # Set
        set_value = "critical"
        analytic_cm.mission = set_value

        assert analytic_cm.mission == set_value
        assert analytic.to_dict()["mission"] == set_value

    def test_gsd(self, item: Item) -> None:
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.gsd
        a2_known_value = 40

        # Get
        assert thumbnail_cm.gsd != item_value
        assert thumbnail_cm.gsd == a2_known_value

        # Set
        set_value = 100
        analytic_cm.gsd = set_value

        assert analytic_cm.gsd == set_value
        assert analytic.to_dict()["gsd"] == set_value

    def test_created(self, item: Item) -> None:
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.created
        a2_known_value = utils.str_to_datetime("2017-05-17T13:22:30.040Z")

        # Get
        assert thumbnail_cm.created != item_value
        assert thumbnail_cm.created == a2_known_value

        # Set
        set_value = utils.str_to_datetime("2014-05-17T13:22:30.040Z")
        analytic_cm.created = set_value

        assert analytic_cm.created == set_value
        assert analytic.to_dict()["created"] == utils.datetime_to_str(set_value)

    def test_updated(self, item: Item) -> None:
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.updated
        a2_known_value = utils.str_to_datetime("2017-05-18T13:22:30.040Z")

        # Get
        assert thumbnail_cm.updated != item_value
        assert thumbnail_cm.updated == a2_known_value

        # Set
        set_value = utils.str_to_datetime("2014-05-18T13:22:30.040Z")
        analytic_cm.updated = set_value

        assert analytic_cm.updated == set_value
        assert analytic.to_dict()["updated"] == utils.datetime_to_str(set_value)

    def test_keywords(self, item: Item) -> None:
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.keywords
        a2_known_value = ["keyword_a"]

        # Get
        assert thumbnail_cm.keywords != item_value
        assert thumbnail_cm.keywords == a2_known_value

        # Set
        set_value = ["keyword_b"]
        analytic_cm.keywords = set_value

        assert analytic_cm.keywords == set_value
        assert analytic.to_dict()["keywords"] == set_value

    def test_roles(self, item: Item) -> None:
        cm = item.common_metadata
        analytic = item.assets["analytic"]
        analytic_cm = CommonMetadata(analytic)
        thumbnail = item.assets["thumbnail"]
        thumbnail_cm = CommonMetadata(thumbnail)

        item_value = cm.roles
        a2_known_value = ["a_role"]

        # Get
        assert thumbnail_cm.roles != item_value
        assert thumbnail_cm.roles == a2_known_value

        # Set
        set_value = ["another_role"]
        analytic_cm.roles = set_value

        assert analytic_cm.roles == set_value
        assert analytic.to_dict()["roles"] == set_value
