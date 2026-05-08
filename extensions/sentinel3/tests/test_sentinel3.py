"""Tests for pystac.extensions.sentinel3."""

from datetime import datetime
from typing import Any

import pytest

import pystac
from pystac import Collection, ExtensionTypeError, Item
from pystac.extensions import sentinel3
from pystac.extensions.sentinel3 import (
    SCHEMA_URI,
    AltimetryBand,
    Sentinel3Extension,
    SummariesSentinel3Extension,
)
from pystac.summaries import RangeSummary
from tests.utils import TestCases


@pytest.fixture
def item() -> Item:
    item = pystac.Item(
        id="sentinel3-item",
        geometry=None,
        bbox=None,
        datetime=datetime(2020, 1, 1),
        properties={},
    )
    item.add_asset("measurement", pystac.Asset(href="https://example.com/measurement.nc"))
    Sentinel3Extension.add_to(item)
    return item


@pytest.fixture
def collection() -> Collection:
    return Collection.from_file(
        TestCases.get_path("data-files/collections/multi-extent.json")
    )


def test_stac_extensions(item: Item) -> None:
    assert Sentinel3Extension.has_extension(item)


def test_item_repr(item: Item) -> None:
    assert (
        Sentinel3Extension.ext(item).__repr__()
        == f"<ItemSentinel3Extension Item id={item.id}>"
    )


def test_asset_repr(item: Item) -> None:
    asset = item.assets["measurement"]
    assert (
        Sentinel3Extension.ext(asset).__repr__()
        == f"<AssetSentinel3Extension Asset href={asset.href}>"
    )


@pytest.mark.vcr()
def test_no_args_fails(item: Item) -> None:
    Sentinel3Extension.ext(item).apply()
    with pytest.raises(pystac.STACValidationError):
        item.validate()


@pytest.mark.vcr()
def test_apply_and_validate(item: Item) -> None:
    altimetry_bands: list[AltimetryBand] = [
        {
            "band_width": 320.0,
            "description": "Ku band",
            "frequency_band": "Ku",
            "center_frequency": 13.575,
        }
    ]

    Sentinel3Extension.ext(item).apply(
        product_type="OL_1_EFR___",
        product_name="S3A_OL_1_EFR____20200101T000000_20200101T000300_20200102T120000",
        processing_timeliness="NT",
        gsd={"OLCI": 300, "SLSTR": {"S1-S6": 500, "S7-S9 and F1-F2": 1000}},
        bright=1.0,
    )
    Sentinel3Extension.ext(item.assets["measurement"]).apply(
        shape=[4091, 4865],
        spatial_resolution=[300, 300],
        altimetry_bands=altimetry_bands,
    )

    ext = Sentinel3Extension.ext(item)
    assert ext.product_type == "OL_1_EFR___"
    assert ext.processing_timeliness == "NT"
    assert ext.bright == 1.0
    assert ext.gsd == {
        "OLCI": 300,
        "SLSTR": {"S1-S6": 500, "S7-S9 and F1-F2": 1000},
    }

    asset_ext = Sentinel3Extension.ext(item.assets["measurement"])
    assert asset_ext.shape == [4091, 4865]
    assert asset_ext.spatial_resolution == [300, 300]
    assert asset_ext.altimetry_bands == altimetry_bands

    item.validate()


def test_shape_must_be_ints(item: Item) -> None:
    with pytest.raises(ValueError, match=r"must contain only integers"):
        Sentinel3Extension.ext(item.assets["measurement"]).shape = [1, "2"]  # type: ignore[list-item]


def test_from_dict() -> None:
    d: dict[str, Any] = {
        "type": "Feature",
        "stac_version": "1.0.0",
        "id": "sentinel3-item",
        "properties": {
            "datetime": "2020-01-01T00:00:00Z",
            "s3:bright": 1.0,
            "s3:product_type": "OL_1_EFR___",
        },
        "geometry": None,
        "links": [],
        "assets": {
            "measurement": {
                "href": "https://example.com/measurement.nc",
                "s3:shape": [4091, 4865],
            }
        },
        "stac_extensions": [SCHEMA_URI],
    }
    item = pystac.Item.from_dict(d)

    assert Sentinel3Extension.ext(item).bright == 1.0
    assert Sentinel3Extension.ext(item.assets["measurement"]).shape == [4091, 4865]


def test_to_from_dict(item: Item) -> None:
    Sentinel3Extension.ext(item).apply(bright=1.0, product_type="OL_1_EFR___")
    Sentinel3Extension.ext(item.assets["measurement"]).apply(shape=[100, 200])

    d = item.to_dict()
    assert d["properties"][sentinel3.BRIGHT_PROP] == 1.0
    assert d["properties"][sentinel3.PRODUCT_TYPE_PROP] == "OL_1_EFR___"
    assert d["assets"]["measurement"][sentinel3.SHAPE_PROP] == [100, 200]

    item = pystac.Item.from_dict(d)
    assert Sentinel3Extension.ext(item).bright == 1.0
    assert Sentinel3Extension.ext(item.assets["measurement"]).shape == [100, 200]


def test_extension_not_implemented(item: Item) -> None:
    item.stac_extensions.remove(Sentinel3Extension.get_schema_uri())

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = Sentinel3Extension.ext(item)

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = Sentinel3Extension.ext(item.assets["measurement"])


def test_item_ext_add_to(item: Item) -> None:
    item.stac_extensions.remove(Sentinel3Extension.get_schema_uri())
    _ = Sentinel3Extension.ext(item, add_if_missing=True)
    assert Sentinel3Extension.get_schema_uri() in item.stac_extensions


def test_asset_ext_add_to(item: Item) -> None:
    item.stac_extensions.remove(Sentinel3Extension.get_schema_uri())
    _ = Sentinel3Extension.ext(item.assets["measurement"], add_if_missing=True)
    assert Sentinel3Extension.get_schema_uri() in item.stac_extensions


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError,
        match=r"^Sentinel3Extension does not apply to type 'object'$",
    ):
        Sentinel3Extension.ext(object())  # type: ignore


def test_summaries(collection: Collection) -> None:
    summaries_ext = Sentinel3Extension.summaries(collection, True)
    summaries_ext.product_type = ["OL_1_EFR___"]
    summaries_ext.bright = RangeSummary(0.0, 1.0)

    assert summaries_ext.product_type == ["OL_1_EFR___"]
    assert summaries_ext.bright == RangeSummary(0.0, 1.0)

    summaries_dict = collection.to_dict()["summaries"]
    assert summaries_dict["s3:product_type"] == ["OL_1_EFR___"]
    assert summaries_dict["s3:bright"] == {"minimum": 0.0, "maximum": 1.0}


def test_collection_hint(collection: Collection) -> None:
    with pytest.raises(
        ExtensionTypeError,
        match=r"Hint: Did you mean to use `Sentinel3Extension.summaries` instead\\?",
    ):
        Sentinel3Extension.ext(collection)  # type: ignore[arg-type]


def test_summaries_ext_add_to(collection: Collection) -> None:
    if Sentinel3Extension.get_schema_uri() in collection.stac_extensions:
        collection.stac_extensions.remove(Sentinel3Extension.get_schema_uri())

    summaries_ext = Sentinel3Extension.summaries(collection, add_if_missing=True)

    assert isinstance(summaries_ext, SummariesSentinel3Extension)
    assert Sentinel3Extension.get_schema_uri() in collection.stac_extensions
