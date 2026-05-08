"""Tests for pystac.extensions.sentinel2."""

from datetime import datetime
from typing import Any

import pytest

import pystac
from pystac import Collection, ExtensionTypeError, Item
from pystac.extensions import sentinel2
from pystac.extensions.sentinel2 import (
    SCHEMA_URI,
    Sentinel2Extension,
    SummariesSentinel2Extension,
)
from pystac.summaries import RangeSummary
from pystac.utils import str_to_datetime
from tests.utils import TestCases


@pytest.fixture
def item() -> Item:
    item = pystac.Item(
        id="sentinel2-item",
        geometry=None,
        bbox=None,
        datetime=datetime(2020, 1, 1),
        properties={},
    )
    Sentinel2Extension.add_to(item)
    return item


@pytest.fixture
def collection() -> Collection:
    return Collection.from_file(
        TestCases.get_path("data-files/collections/multi-extent.json")
    )


def test_stac_extensions(item: Item) -> None:
    assert Sentinel2Extension.has_extension(item)


def test_item_repr(item: Item) -> None:
    assert (
        Sentinel2Extension.ext(item).__repr__()
        == f"<ItemSentinel2Extension Item id={item.id}>"
    )


@pytest.mark.vcr()
def test_no_args_validate(item: Item) -> None:
    Sentinel2Extension.ext(item).apply()
    item.validate()


@pytest.mark.vcr()
def test_apply_and_validate(item: Item) -> None:
    generation_time = str_to_datetime("2020-01-02T03:04:05Z")

    Sentinel2Extension.ext(item).apply(
        tile_id="S2B_OPER_MSI_L2A_TL_SGS__20200102T030405_A012345_T32TQM_N02.09",
        datatake_id="GS2B_20200102T030405_012345_N02.09",
        product_uri="S2B_MSIL2A_20200101T103029_N0213_R108_T32TQM_20200101T132423.SAFE",
        datastrip_id="S2B_OPER_MSI_L2A_DS_SGS__20200102T030405_S20200101T103029_N02.09",
        datatake_type="INS-NOBS",
        generation_time=generation_time,
        processing_baseline="02.13",
        water_percentage=1.5,
        snow_ice_percentage=0.2,
        vegetation_percentage=34.7,
        reflectance_conversion_factor=1.032,
        mgrs_tile="32TQM",
    )

    ext = Sentinel2Extension.ext(item)
    assert ext.tile_id == (
        "S2B_OPER_MSI_L2A_TL_SGS__20200102T030405_A012345_T32TQM_N02.09"
    )
    assert ext.datatake_id == "GS2B_20200102T030405_012345_N02.09"
    assert (
        ext.product_uri
        == "S2B_MSIL2A_20200101T103029_N0213_R108_T32TQM_20200101T132423.SAFE"
    )
    assert (
        ext.datastrip_id
        == "S2B_OPER_MSI_L2A_DS_SGS__20200102T030405_S20200101T103029_N02.09"
    )
    assert ext.datatake_type == "INS-NOBS"
    assert ext.generation_time == generation_time
    assert ext.processing_baseline == "02.13"
    assert ext.water_percentage == 1.5
    assert ext.snow_ice_percentage == 0.2
    assert ext.vegetation_percentage == 34.7
    assert ext.reflectance_conversion_factor == 1.032
    assert ext.mgrs_tile == "32TQM"

    item.validate()


def test_processing_baseline_validation(item: Item) -> None:
    with pytest.raises(ValueError, match=r"must match NN.NN"):
        Sentinel2Extension.ext(item).processing_baseline = "2.13"


def test_percentage_validation(item: Item) -> None:
    with pytest.raises(ValueError, match=r"water_percentage"):
        Sentinel2Extension.ext(item).water_percentage = 101


def test_from_dict() -> None:
    d: dict[str, Any] = {
        "type": "Feature",
        "stac_version": "1.0.0",
        "id": "sentinel2-item",
        "properties": {
            "datetime": "2020-01-01T00:00:00Z",
            "s2:tile_id": (
                "S2A_OPER_MSI_L1C_TL_SGS__20200101T000000_A012345_T32TQM_N02.09"
            ),
            "s2:reflectance_conversion_factor": 1.032,
        },
        "geometry": None,
        "links": [],
        "assets": {},
        "stac_extensions": [SCHEMA_URI],
    }
    item = pystac.Item.from_dict(d)

    ext = Sentinel2Extension.ext(item)
    assert (
        ext.tile_id
        == "S2A_OPER_MSI_L1C_TL_SGS__20200101T000000_A012345_T32TQM_N02.09"
    )
    assert ext.reflectance_conversion_factor == 1.032


def test_to_from_dict(item: Item) -> None:
    generation_time = str_to_datetime("2020-01-02T03:04:05Z")
    Sentinel2Extension.ext(item).apply(
        tile_id="S2A_OPER_MSI_L1C_TL_SGS__20200101T000000_A012345_T32TQM_N02.09",
        generation_time=generation_time,
        water_percentage=1.5,
    )

    d = item.to_dict()
    assert d["properties"][sentinel2.TILE_ID_PROP].startswith("S2A_OPER_MSI_L1C_TL")
    assert d["properties"][sentinel2.GENERATION_TIME_PROP] == "2020-01-02T03:04:05Z"
    assert d["properties"][sentinel2.WATER_PERCENTAGE_PROP] == 1.5

    item = pystac.Item.from_dict(d)
    ext = Sentinel2Extension.ext(item)
    assert ext.generation_time == generation_time
    assert ext.water_percentage == 1.5


def test_extension_not_implemented(item: Item) -> None:
    item.stac_extensions.remove(Sentinel2Extension.get_schema_uri())

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = Sentinel2Extension.ext(item)


def test_item_ext_add_to(item: Item) -> None:
    item.stac_extensions.remove(Sentinel2Extension.get_schema_uri())
    assert Sentinel2Extension.get_schema_uri() not in item.stac_extensions

    _ = Sentinel2Extension.ext(item, add_if_missing=True)

    assert Sentinel2Extension.get_schema_uri() in item.stac_extensions


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError,
        match=r"^Sentinel2Extension does not apply to type 'object'$",
    ):
        Sentinel2Extension.ext(object())  # type: ignore


def test_summaries(collection: Collection) -> None:
    summaries_ext = Sentinel2Extension.summaries(collection, True)
    generation_time = RangeSummary(
        str_to_datetime("2020-01-01T00:00:00Z"),
        str_to_datetime("2020-01-02T00:00:00Z"),
    )
    water_percentage = RangeSummary(0.0, 10.0)

    summaries_ext.tile_id = ["32TQM", "32TQL"]
    summaries_ext.generation_time = generation_time
    summaries_ext.water_percentage = water_percentage

    assert summaries_ext.tile_id == ["32TQM", "32TQL"]
    assert summaries_ext.generation_time == generation_time
    assert summaries_ext.water_percentage == water_percentage

    summaries_dict = collection.to_dict()["summaries"]
    assert summaries_dict["s2:tile_id"] == ["32TQM", "32TQL"]
    assert summaries_dict["s2:generation_time"] == {
        "minimum": "2020-01-01T00:00:00Z",
        "maximum": "2020-01-02T00:00:00Z",
    }
    assert summaries_dict["s2:water_percentage"] == {
        "minimum": 0.0,
        "maximum": 10.0,
    }


def test_collection_hint(collection: Collection) -> None:
    with pytest.raises(
        ExtensionTypeError,
        match=r"Hint: Did you mean to use `Sentinel2Extension.summaries` instead\\?",
    ):
        Sentinel2Extension.ext(collection)  # type: ignore[arg-type]


def test_summaries_ext_add_to(collection: Collection) -> None:
    if Sentinel2Extension.get_schema_uri() in collection.stac_extensions:
        collection.stac_extensions.remove(Sentinel2Extension.get_schema_uri())

    summaries_ext = Sentinel2Extension.summaries(collection, add_if_missing=True)

    assert isinstance(summaries_ext, SummariesSentinel2Extension)
    assert Sentinel2Extension.get_schema_uri() in collection.stac_extensions
