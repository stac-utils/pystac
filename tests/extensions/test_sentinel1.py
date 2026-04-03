"""Tests for pystac.extensions.sentinel1."""

from datetime import datetime
from typing import Any

import pytest

import pystac
from pystac import Collection, ExtensionTypeError, Item
from pystac.extensions import sentinel1
from pystac.extensions.sentinel1 import (
    SCHEMA_URI,
    Sentinel1Extension,
    SummariesSentinel1Extension,
)
from pystac.summaries import RangeSummary
from pystac.utils import str_to_datetime
from tests.utils import TestCases


@pytest.fixture
def item() -> Item:
    item = pystac.Item(
        id="sentinel1-item",
        geometry=None,
        bbox=None,
        datetime=datetime(2020, 1, 1),
        properties={},
    )
    Sentinel1Extension.add_to(item)
    return item


@pytest.fixture
def collection() -> Collection:
    return Collection.from_file(
        TestCases.get_path("data-files/collections/multi-extent.json")
    )


def test_stac_extensions(item: Item) -> None:
    assert Sentinel1Extension.has_extension(item)


def test_item_repr(item: Item) -> None:
    assert (
        Sentinel1Extension.ext(item).__repr__()
        == f"<ItemSentinel1Extension Item id={item.id}>"
    )


@pytest.mark.vcr()
def test_no_args_fails(item: Item) -> None:
    Sentinel1Extension.ext(item).apply()
    with pytest.raises(pystac.STACValidationError):
        item.validate()


@pytest.mark.vcr()
def test_apply_and_validate(item: Item) -> None:
    processing_datetime = str_to_datetime("2020-01-02T03:04:05Z")

    Sentinel1Extension.ext(item).apply(
        datatake_id="123456",
        instrument_configuration_id="9",
        orbit_source="RESORB",
        processing_datetime=processing_datetime,
        product_identifier="S1A_IW_GRDH_1SDV_20200101T000000",
        product_timeliness="Fast-24h",
        resolution="H",
        slice_number="2",
        total_slices="9",
        processing_level="LEVEL1",
        shape=[10980, 10980],
    )

    ext = Sentinel1Extension.ext(item)
    assert ext.datatake_id == "123456"
    assert ext.instrument_configuration_id == "9"
    assert ext.orbit_source == "RESORB"
    assert ext.processing_datetime == processing_datetime
    assert ext.product_identifier == "S1A_IW_GRDH_1SDV_20200101T000000"
    assert ext.product_timeliness == "Fast-24h"
    assert ext.resolution == "H"
    assert ext.slice_number == "2"
    assert ext.total_slices == "9"
    assert ext.processing_level == "LEVEL1"
    assert ext.shape == [10980, 10980]

    item.validate()


def test_shape_must_have_two_values(item: Item) -> None:
    with pytest.raises(ValueError, match=r"must contain at least two integers"):
        Sentinel1Extension.ext(item).shape = [10980]


def test_from_dict() -> None:
    d: dict[str, Any] = {
        "type": "Feature",
        "stac_version": "1.0.0",
        "id": "sentinel1-item",
        "properties": {
            "datetime": "2020-01-01T00:00:00Z",
            "s1:datatake_id": "123456",
            "s1:shape": [10980, 10980],
        },
        "geometry": None,
        "links": [],
        "assets": {},
        "stac_extensions": [SCHEMA_URI],
    }
    item = pystac.Item.from_dict(d)

    ext = Sentinel1Extension.ext(item)
    assert ext.datatake_id == "123456"
    assert ext.shape == [10980, 10980]


def test_to_from_dict(item: Item) -> None:
    processing_datetime = str_to_datetime("2020-01-02T03:04:05Z")
    Sentinel1Extension.ext(item).apply(
        datatake_id="123456",
        processing_datetime=processing_datetime,
        shape=[100, 200],
    )

    d = item.to_dict()
    assert d["properties"][sentinel1.DATATAKE_ID_PROP] == "123456"
    assert d["properties"][sentinel1.PROCESSING_DATETIME_PROP] == "2020-01-02T03:04:05Z"
    assert d["properties"][sentinel1.SHAPE_PROP] == [100, 200]

    item = pystac.Item.from_dict(d)
    ext = Sentinel1Extension.ext(item)
    assert ext.datatake_id == "123456"
    assert ext.processing_datetime == processing_datetime
    assert ext.shape == [100, 200]


def test_extension_not_implemented(item: Item) -> None:
    item.stac_extensions.remove(Sentinel1Extension.get_schema_uri())

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = Sentinel1Extension.ext(item)


def test_item_ext_add_to(item: Item) -> None:
    item.stac_extensions.remove(Sentinel1Extension.get_schema_uri())
    assert Sentinel1Extension.get_schema_uri() not in item.stac_extensions

    _ = Sentinel1Extension.ext(item, add_if_missing=True)

    assert Sentinel1Extension.get_schema_uri() in item.stac_extensions


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError,
        match=r"^Sentinel1Extension does not apply to type 'object'$",
    ):
        Sentinel1Extension.ext(object())  # type: ignore


def test_summaries(collection: Collection) -> None:
    summaries_ext = Sentinel1Extension.summaries(collection, True)
    processing_datetime = RangeSummary(
        str_to_datetime("2020-01-01T00:00:00Z"),
        str_to_datetime("2020-01-02T00:00:00Z"),
    )

    summaries_ext.datatake_id = ["123456", "654321"]
    summaries_ext.processing_datetime = processing_datetime
    summaries_ext.shape = [[10980, 10980]]

    assert summaries_ext.datatake_id == ["123456", "654321"]
    assert summaries_ext.processing_datetime == processing_datetime
    assert summaries_ext.shape == [[10980, 10980]]

    summaries_dict = collection.to_dict()["summaries"]
    assert summaries_dict["s1:datatake_id"] == ["123456", "654321"]
    assert summaries_dict["s1:processing_datetime"] == {
        "minimum": "2020-01-01T00:00:00Z",
        "maximum": "2020-01-02T00:00:00Z",
    }
    assert summaries_dict["s1:shape"] == [[10980, 10980]]


def test_collection_hint(collection: Collection) -> None:
    with pytest.raises(
        ExtensionTypeError,
        match=r"Hint: Did you mean to use `Sentinel1Extension.summaries` instead\\?",
    ):
        Sentinel1Extension.ext(collection)  # type: ignore[arg-type]


def test_summaries_ext_add_to(collection: Collection) -> None:
    if Sentinel1Extension.get_schema_uri() in collection.stac_extensions:
        collection.stac_extensions.remove(Sentinel1Extension.get_schema_uri())

    summaries_ext = Sentinel1Extension.summaries(collection, add_if_missing=True)

    assert isinstance(summaries_ext, SummariesSentinel1Extension)
    assert Sentinel1Extension.get_schema_uri() in collection.stac_extensions
