import json
from datetime import datetime
from pathlib import Path

import pystac
import pytest
from pystac import Collection, ExtensionTypeError, Item
from pystac.extensions.timestamps import TimestampsExtension
from pystac.summaries import RangeSummary
from pystac.utils import datetime_to_str, get_opt, str_to_datetime
from pytest_pystac.plugin import assert_to_from_dict

DATA_FILES = Path(__file__).resolve().parent / "data-files"
EXAMPLE_URI = str(DATA_FILES / "example-landsat8.json")
SAMPLE_DATETIME_STR = "2020-01-01T00:00:00Z"


@pytest.fixture
def item() -> Item:
    return Item.from_file(EXAMPLE_URI)


@pytest.fixture
def sample_datetime() -> datetime:
    return str_to_datetime(SAMPLE_DATETIME_STR)


def test_to_from_dict() -> None:
    with open(EXAMPLE_URI) as f:
        item_dict = json.load(f)
    assert_to_from_dict(pystac.Item, item_dict)


def test_apply() -> None:
    item = pystac.Item(
        id="test-item",
        geometry=None,
        bbox=None,
        datetime=datetime(2020, 1, 1),
        properties={},
    )
    assert not TimestampsExtension.has_extension(item)

    TimestampsExtension.add_to(item)
    assert TimestampsExtension.has_extension(item)
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
        assert isinstance(d, datetime)

    for p in ("published", "expires", "unpublished"):
        assert isinstance(item.properties[p], str)

    published_str = "2020-04-03T06:45:55Z"
    TimestampsExtension.ext(item).apply(published=str_to_datetime(published_str))
    assert isinstance(TimestampsExtension.ext(item).published, datetime)
    assert item.properties["published"] == published_str

    for d in [
        TimestampsExtension.ext(item).expires,
        TimestampsExtension.ext(item).unpublished,
    ]:
        assert d is None

    for p in ("expires", "unpublished"):
        assert p not in item.properties


@pytest.mark.vcr()
def test_validate_timestamps(item: Item) -> None:
    item.validate()


@pytest.mark.vcr()
def test_expires(item: Item, sample_datetime: datetime) -> None:
    # Get
    assert "expires" in item.properties
    timestamps_expires = TimestampsExtension.ext(item).expires
    assert isinstance(timestamps_expires, datetime)
    assert datetime_to_str(get_opt(timestamps_expires)) == item.properties["expires"]

    # Set
    TimestampsExtension.ext(item).expires = sample_datetime
    assert SAMPLE_DATETIME_STR == item.properties["expires"]

    # Get from Asset
    asset_no_prop = item.assets["red"]
    asset_prop = item.assets["blue"]
    assert (
        TimestampsExtension.ext(asset_no_prop).expires
        == TimestampsExtension.ext(item).expires
    )
    assert TimestampsExtension.ext(asset_prop).expires == str_to_datetime(
        "2018-12-02T00:00:00Z"
    )

    # # Set to Asset
    asset_value = str_to_datetime("2019-02-02T00:00:00Z")
    TimestampsExtension.ext(asset_no_prop).expires = asset_value
    assert (
        TimestampsExtension.ext(asset_no_prop).expires
        != TimestampsExtension.ext(item).expires
    )
    assert TimestampsExtension.ext(asset_no_prop).expires == asset_value

    # Validate
    item.validate()


@pytest.mark.vcr()
def test_published(item: Item, sample_datetime: datetime) -> None:
    # Get
    assert "published" in item.properties
    timestamps_published = TimestampsExtension.ext(item).published
    assert isinstance(timestamps_published, datetime)
    assert (
        datetime_to_str(get_opt(timestamps_published)) == item.properties["published"]
    )

    # Set
    TimestampsExtension.ext(item).published = sample_datetime
    assert SAMPLE_DATETIME_STR == item.properties["published"]

    # Get from Asset
    asset_no_prop = item.assets["red"]
    asset_prop = item.assets["blue"]
    assert (
        TimestampsExtension.ext(asset_no_prop).published
        == TimestampsExtension.ext(item).published
    )
    assert TimestampsExtension.ext(asset_prop).published == str_to_datetime(
        "2018-11-02T00:00:00Z"
    )

    # # Set to Asset
    asset_value = str_to_datetime("2019-02-02T00:00:00Z")
    TimestampsExtension.ext(asset_no_prop).published = asset_value
    assert (
        TimestampsExtension.ext(asset_no_prop).published
        != TimestampsExtension.ext(item).published
    )
    assert TimestampsExtension.ext(asset_no_prop).published == asset_value

    # Validate
    item.validate()


@pytest.mark.vcr()
def test_unpublished(item: Item, sample_datetime: datetime) -> None:
    # Get
    assert "unpublished" not in item.properties
    timestamps_unpublished = TimestampsExtension.ext(item).unpublished
    assert timestamps_unpublished is None

    # Set
    TimestampsExtension.ext(item).unpublished = sample_datetime
    assert SAMPLE_DATETIME_STR == item.properties["unpublished"]

    # Get from Asset
    asset_no_prop = item.assets["red"]
    asset_prop = item.assets["blue"]
    assert (
        TimestampsExtension.ext(asset_no_prop).unpublished
        == TimestampsExtension.ext(item).unpublished
    )
    assert TimestampsExtension.ext(asset_prop).unpublished == str_to_datetime(
        "2019-01-02T00:00:00Z"
    )

    # Set to Asset
    asset_value = str_to_datetime("2019-02-02T00:00:00Z")
    TimestampsExtension.ext(asset_no_prop).unpublished = asset_value
    assert (
        TimestampsExtension.ext(asset_no_prop).unpublished
        != TimestampsExtension.ext(item).unpublished
    )
    assert TimestampsExtension.ext(asset_no_prop).unpublished == asset_value

    # Validate
    item.validate()


def test_extension_not_implemented(item: Item) -> None:
    # Should raise exception if Item does not include extension URI
    item.stac_extensions.remove(TimestampsExtension.get_schema_uri())

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = TimestampsExtension.ext(item)

    # Should raise exception if owning Item does not include extension URI
    asset = item.assets["blue"]

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = TimestampsExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = TimestampsExtension.ext(ownerless_asset)


def test_item_ext_add_to(item: Item) -> None:
    item.stac_extensions.remove(TimestampsExtension.get_schema_uri())
    assert TimestampsExtension.get_schema_uri() not in item.stac_extensions

    _ = TimestampsExtension.ext(item, add_if_missing=True)

    assert TimestampsExtension.get_schema_uri() in item.stac_extensions


def test_asset_ext_add_to(item: Item) -> None:
    item.stac_extensions.remove(TimestampsExtension.get_schema_uri())
    assert TimestampsExtension.get_schema_uri() not in item.stac_extensions
    asset = item.assets["blue"]

    _ = TimestampsExtension.ext(asset, add_if_missing=True)

    assert TimestampsExtension.get_schema_uri() in item.stac_extensions


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError,
        match=r"^TimestampsExtension does not apply to type 'object'$",
    ):
        # calling it wrong on purpose --------------v
        TimestampsExtension.ext(object())  # type: ignore


def test_item_repr(item: Item) -> None:
    assert (
        TimestampsExtension.ext(item).__repr__()
        == f"<ItemTimestampsExtension Item id={item.id}>"
    )


def test_asset_repr(item: Item) -> None:
    asset = item.assets["blue"]
    assert (
        TimestampsExtension.ext(asset).__repr__()
        == f"<AssetTimestampsExtension Asset href={asset.href}>"
    )


def test_summaries_published(multi_extent_collection: Collection) -> None:
    summaries_ext = TimestampsExtension.summaries(multi_extent_collection, True)
    published_range = RangeSummary(
        str_to_datetime("2020-01-01T00:00:00.000Z"),
        str_to_datetime("2020-01-02T00:00:00.000Z"),
    )

    summaries_ext.published = published_range

    assert summaries_ext.published == published_range

    summaries_dict = multi_extent_collection.to_dict()["summaries"]

    assert summaries_dict["published"] == {
        "minimum": datetime_to_str(published_range.minimum),
        "maximum": datetime_to_str(published_range.maximum),
    }


def test_summaries_expires(multi_extent_collection: Collection) -> None:
    summaries_ext = TimestampsExtension.summaries(multi_extent_collection, True)
    expires_range = RangeSummary(
        str_to_datetime("2020-01-01T00:00:00.000Z"),
        str_to_datetime("2020-01-02T00:00:00.000Z"),
    )

    summaries_ext.expires = expires_range

    assert summaries_ext.expires == expires_range

    summaries_dict = multi_extent_collection.to_dict()["summaries"]

    assert summaries_dict["expires"] == {
        "minimum": datetime_to_str(expires_range.minimum),
        "maximum": datetime_to_str(expires_range.maximum),
    }


def test_summaries_unpublished(multi_extent_collection: Collection) -> None:
    summaries_ext = TimestampsExtension.summaries(multi_extent_collection, True)
    unpublished_range = RangeSummary(
        str_to_datetime("2020-01-01T00:00:00.000Z"),
        str_to_datetime("2020-01-02T00:00:00.000Z"),
    )

    summaries_ext.unpublished = unpublished_range

    assert summaries_ext.unpublished == unpublished_range

    summaries_dict = multi_extent_collection.to_dict()["summaries"]

    assert summaries_dict["unpublished"] == {
        "minimum": datetime_to_str(unpublished_range.minimum),
        "maximum": datetime_to_str(unpublished_range.maximum),
    }


def test_summaries_adds_uri(multi_extent_collection: Collection) -> None:
    multi_extent_collection.stac_extensions = []
    with pytest.raises(
        pystac.ExtensionNotImplemented,
        match="Extension 'timestamps' is not implemented",
    ):
        TimestampsExtension.summaries(multi_extent_collection, add_if_missing=False)

    _ = TimestampsExtension.summaries(multi_extent_collection, True)

    assert (
        TimestampsExtension.get_schema_uri() in multi_extent_collection.stac_extensions
    )

    TimestampsExtension.remove_from(multi_extent_collection)
    assert (
        TimestampsExtension.get_schema_uri()
        not in multi_extent_collection.stac_extensions
    )


@pytest.mark.parametrize(
    "schema_uri",
    ("https://stac-extensions.github.io/timestamps/v1.0.0/schema.json",),
)
def test_migrate(schema_uri: str, item: Item) -> None:
    item_dict = item.to_dict(include_self_link=False, transform_hrefs=False)
    item_dict["stac_extensions"] = [schema_uri]
    item = Item.from_dict(item_dict, migrate=True)
    assert item.stac_extensions == [
        "https://stac-extensions.github.io/timestamps/v1.1.0/schema.json"
    ]
