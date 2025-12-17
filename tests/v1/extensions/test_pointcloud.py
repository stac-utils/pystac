import json
from typing import Any

import pytest
from pystac.extensions.pointcloud import (
    AssetPointcloudExtension,
    PhenomenologyType,
    PointcloudExtension,
    Schema,
    SchemaType,
    Statistic,
)
from pystac.summaries import RangeSummary

import pystac
from pystac.asset import Asset
from pystac.errors import ExtensionTypeError, RequiredPropertyMissing, STACError
from tests.v1.utils import TestCases, assert_to_from_dict

# from copy import deepcopy


@pytest.fixture
def example_uri() -> str:
    return TestCases.get_path("data-files/pointcloud/example-laz.json")


@pytest.fixture
def pc_item(example_uri: str) -> pystac.Item:
    return pystac.Item.from_file(example_uri)


@pytest.fixture
def pc_no_stats_item() -> pystac.Item:
    return pystac.Item.from_file(
        TestCases.get_path("data-files/pointcloud/example-laz-no-statistics.json")
    )


@pytest.fixture
def plain_item() -> pystac.Item:
    return pystac.Item.from_file(TestCases.get_path("data-files/item/sample-item.json"))


@pytest.fixture
def collection() -> pystac.Collection:
    return pystac.Collection.from_file(
        TestCases.get_path("data-files/collections/multi-extent.json")
    )


def test_to_from_dict(example_uri: str) -> None:
    with open(example_uri) as f:
        d = json.load(f)
    assert_to_from_dict(pystac.Item, d)


def test_apply() -> None:
    item = next(TestCases.case_2().get_items(recursive=True))

    assert not PointcloudExtension.has_extension(item)

    PointcloudExtension.add_to(item)
    PointcloudExtension.ext(item).apply(
        1000,
        PhenomenologyType.LIDAR,
        "laszip",
        [Schema({"name": "X", "size": 8, "type": "floating"})],
    )
    assert PointcloudExtension.has_extension(item)


@pytest.mark.vcr()
def test_validate_pointcloud(pc_item: pystac.Item) -> None:
    pc_item.validate()


@pytest.mark.vcr()
def test_count(pc_item: pystac.Item) -> None:
    # Get
    assert "pc:count" in pc_item.properties
    pc_count = PointcloudExtension.ext(pc_item).count
    assert pc_count == pc_item.properties["pc:count"]

    # Set
    PointcloudExtension.ext(pc_item).count = pc_count + 100
    assert pc_count + 100 == pc_item.properties["pc:count"]

    # Validate
    pc_item.validate()

    # Cannot test validation errors until the pointcloud schema.json syntax is fixed
    # Ensure setting bad count fails validation

    with pytest.raises(pystac.STACValidationError):
        PointcloudExtension.ext(pc_item).count = "not_an_int"  # type:ignore
        pc_item.validate()


@pytest.mark.vcr()
def test_type(pc_item: pystac.Item) -> None:
    # Get
    assert "pc:type" in pc_item.properties
    pc_type = PointcloudExtension.ext(pc_item).type
    assert pc_type == pc_item.properties["pc:type"]

    # Set
    PointcloudExtension.ext(pc_item).type = "sonar"
    assert "sonar" == pc_item.properties["pc:type"]

    # Validate
    pc_item.validate()


@pytest.mark.vcr()
def test_encoding(pc_item: pystac.Item) -> None:
    # Get
    assert "pc:encoding" in pc_item.properties
    pc_encoding = PointcloudExtension.ext(pc_item).encoding
    assert pc_encoding == pc_item.properties["pc:encoding"]

    # Set
    PointcloudExtension.ext(pc_item).encoding = "binary"
    assert "binary" == pc_item.properties["pc:encoding"]

    # Validate
    pc_item.validate()


@pytest.mark.vcr()
def test_schemas(pc_item: pystac.Item) -> None:
    # Get
    assert "pc:schemas" in pc_item.properties
    pc_schemas = [s.to_dict() for s in PointcloudExtension.ext(pc_item).schemas]
    assert pc_schemas == pc_item.properties["pc:schemas"]

    # Set
    schema = [Schema({"name": "X", "size": 8, "type": "floating"})]
    PointcloudExtension.ext(pc_item).schemas = schema
    assert [s.to_dict() for s in schema] == pc_item.properties["pc:schemas"]
    # Validate
    pc_item.validate()


@pytest.mark.vcr()
def test_statistics(pc_item: pystac.Item) -> None:
    # Get
    assert "pc:statistics" in pc_item.properties
    statistics = PointcloudExtension.ext(pc_item).statistics
    assert statistics is not None
    pc_statistics = [s.to_dict() for s in statistics]
    assert pc_statistics == pc_item.properties["pc:statistics"]

    # Set
    stats = [
        Statistic(
            {
                "average": 1,
                "count": 1,
                "maximum": 1,
                "minimum": 1,
                "name": "Test",
                "position": 1,
                "stddev": 1,
                "variance": 1,
            }
        )
    ]
    PointcloudExtension.ext(pc_item).statistics = stats
    assert [s.to_dict() for s in stats] == pc_item.properties["pc:statistics"]
    # Validate
    pc_item.validate()


@pytest.mark.vcr()
def test_density(pc_item: pystac.Item) -> None:
    # Get
    assert "pc:density" in pc_item.properties
    pc_density = PointcloudExtension.ext(pc_item).density
    assert pc_density == pc_item.properties["pc:density"]
    # Set
    density = 100
    PointcloudExtension.ext(pc_item).density = density
    assert density == pc_item.properties["pc:density"]
    # Validate
    pc_item.validate()


def test_pointcloud_schema() -> None:
    props: dict[str, Any] = {
        "name": "test",
        "size": 8,
        "type": "floating",
    }
    schema = Schema(props)
    assert props == schema.properties

    # test all getters and setters
    for k in props:
        if isinstance(props[k], str):
            val = props[k] + str(1)
        else:
            val = props[k] + 1
        setattr(schema, k, val)
        assert getattr(schema, k) == val

    schema = Schema.create("intensity", 16, SchemaType.UNSIGNED)
    assert schema.name == "intensity"
    assert schema.size == 16
    assert schema.type == "unsigned"

    with pytest.raises(STACError):
        schema.size = 0.5  # type: ignore

    empty_schema = Schema({})
    for required_prop in {"size", "name", "type"}:
        with pytest.raises(RequiredPropertyMissing):
            getattr(empty_schema, required_prop)


def test_pointcloud_statistics() -> None:
    props: dict[str, Any] = {
        "average": 1,
        "count": 1,
        "maximum": 1,
        "minimum": 1,
        "name": "Test",
        "position": 1,
        "stddev": 1,
        "variance": 1,
    }
    stat = Statistic(props)
    assert props == stat.properties

    # test all getters and setters
    for k in props:
        if isinstance(props[k], str):
            val = props[k] + str(1)
        else:
            val = props[k] + 1
        setattr(stat, k, val)
        assert getattr(stat, k) == val

    stat = Statistic.create("foo", 1, 2, 3, 4, 5, 6, 7)
    assert stat.name == "foo"
    assert stat.position == 1
    assert stat.average == 2
    assert stat.count == 3
    assert stat.maximum == 4
    assert stat.minimum == 5
    assert stat.stddev == 6
    assert stat.variance == 7

    stat.name = None  # type: ignore
    assert "name" not in stat.properties
    stat.position = None
    assert "position" not in stat.properties
    stat.average = None
    assert "average" not in stat.properties
    stat.count = None
    assert "count" not in stat.properties
    stat.maximum = None
    assert "maximum" not in stat.properties
    stat.minimum = None
    assert "minimum" not in stat.properties
    stat.stddev = None
    assert "stddev" not in stat.properties
    stat.variance = None
    assert "variance" not in stat.properties

    empty_stat = Statistic({})
    with pytest.raises(RequiredPropertyMissing):
        empty_stat.name


def test_statistics_accessor_when_no_stats(pc_no_stats_item: pystac.Item) -> None:
    assert PointcloudExtension.ext(pc_no_stats_item).statistics is None


def test_asset_extension(pc_no_stats_item: pystac.Item) -> None:
    asset = Asset(
        "https://github.com/PDAL/PDAL/blob"
        "/a6c986f68458e92414a66c664408bee4737bbb08/test/data/laz"
        "/autzen_trim.laz",
        "laz file",
        "The laz data",
        "application/octet-stream",
        ["data"],
        {"foo": "bar"},
    )
    pc_no_stats_item.add_asset("data", asset)
    ext = AssetPointcloudExtension(asset)
    assert ext.asset_href == asset.href
    assert ext.properties == asset.extra_fields
    assert ext.additional_read_properties == [pc_no_stats_item.properties]


def test_ext(pc_no_stats_item: pystac.Item) -> None:
    PointcloudExtension.ext(pc_no_stats_item)
    asset = Asset(
        "https://github.com/PDAL/PDAL/blob"
        "/a6c986f68458e92414a66c664408bee4737bbb08/test/data/laz"
        "/autzen_trim.laz",
        "laz file",
        "The laz data",
        "application/octet-stream",
        ["data"],
        {"foo": "bar"},
    )
    PointcloudExtension.ext(asset)

    class RandomObject:
        pass

    with pytest.raises(
        ExtensionTypeError,
        match=r"^PointcloudExtension does not apply to type 'RandomObject'$",
    ):
        # calling it wrong on purpose so -----------------v
        PointcloudExtension.ext(RandomObject())  # type: ignore


def test_extension_not_implemented(plain_item: pystac.Item) -> None:
    # Should raise exception if Item does not include extension URI
    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = PointcloudExtension.ext(plain_item)

    # Should raise exception if owning Item does not include extension URI
    asset = plain_item.assets["thumbnail"]

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = PointcloudExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = PointcloudExtension.ext(ownerless_asset)


def test_item_ext_add_to(plain_item: pystac.Item) -> None:
    assert PointcloudExtension.get_schema_uri() not in plain_item.stac_extensions

    _ = PointcloudExtension.ext(plain_item, add_if_missing=True)

    assert PointcloudExtension.get_schema_uri() in plain_item.stac_extensions


def test_asset_ext_add_to(plain_item: pystac.Item) -> None:
    assert PointcloudExtension.get_schema_uri() not in plain_item.stac_extensions
    asset = plain_item.assets["thumbnail"]

    _ = PointcloudExtension.ext(asset, add_if_missing=True)

    assert PointcloudExtension.get_schema_uri() in plain_item.stac_extensions


def test_summaries_count(collection: pystac.Collection) -> None:
    summaries_ext = PointcloudExtension.summaries(collection, True)
    count_range = RangeSummary(1000, 10000)

    summaries_ext.count = count_range

    assert summaries_ext.count == count_range

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["pc:count"] == count_range.to_dict()


def test_summaries_type(collection: pystac.Collection) -> None:
    summaries_ext = PointcloudExtension.summaries(collection, True)
    type_list = [PhenomenologyType.LIDAR, "something"]

    summaries_ext.type = type_list

    assert summaries_ext.type == type_list

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["pc:type"] == type_list


def test_summaries_encoding(collection: pystac.Collection) -> None:
    summaries_ext = PointcloudExtension.summaries(collection, True)
    encoding_list = ["LASzip"]

    summaries_ext.encoding = encoding_list

    assert summaries_ext.encoding == encoding_list

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["pc:encoding"] == encoding_list


def test_summaries_density(collection: pystac.Collection) -> None:
    summaries_ext = PointcloudExtension.summaries(collection, True)
    density_range = RangeSummary(500.0, 1000.0)

    summaries_ext.density = density_range

    assert summaries_ext.density == density_range

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["pc:density"] == density_range.to_dict()


def test_summaries_statistics(collection: pystac.Collection) -> None:
    summaries_ext = PointcloudExtension.summaries(collection, True)
    statistics_list = [
        Statistic(
            {
                "average": 637294.1783,
                "count": 10653336,
                "maximum": 639003.73,
                "minimum": 635577.79,
                "name": "X",
                "position": 0,
                "stddev": 967.9329805,
                "variance": 936894.2548,
            }
        )
    ]

    summaries_ext.statistics = statistics_list

    assert summaries_ext.statistics == statistics_list

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["pc:statistics"] == [s.to_dict() for s in statistics_list]
