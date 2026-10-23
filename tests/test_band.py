import json
from typing import Any

import pytest

from pystac import Asset, Band, Item
from pystac.common_metadata import DataType, NoDataStrings, Statistics


def test_from_dict_without_name() -> None:
    band = Band.from_dict({"description": "no name"})
    assert band.name is None
    assert band.description == "no name"


def test_from_dict_does_not_modify_input() -> None:
    d = {"name": "red", "description": "Red", "eo:common_name": "red"}
    Band.from_dict(d)
    assert d == {"name": "red", "description": "Red", "eo:common_name": "red"}


def test_to_dict_omits_unset_fields() -> None:
    assert Band(name="red").to_dict() == {"name": "red"}
    assert Band(description="Red").to_dict() == {"description": "Red"}


def test_roundtrip_with_extra_fields() -> None:
    d: dict[str, Any] = {
        "name": "B04",
        "description": "Red",
        "eo:center_wavelength": 0.665,
        "raster:scale": 0.0001,
    }
    band = Band.from_dict(d)
    assert band.extra_fields == {"eo:center_wavelength": 0.665, "raster:scale": 0.0001}
    assert band.to_dict() == d


def test_dicts_do_not_share_nested_values() -> None:
    d: dict[str, Any] = {"raster:histogram": {"buckets": [1, 2]}}
    band = Band.from_dict(d)
    d["raster:histogram"]["buckets"].append(3)
    band.to_dict()["raster:histogram"]["buckets"].append(4)
    assert band.extra_fields == {"raster:histogram": {"buckets": [1, 2]}}


def test_roundtrip_with_data_values() -> None:
    d: dict[str, Any] = {
        "name": "B04",
        "data_type": "uint16",
        "nodata": 0,
        "statistics": {"minimum": 1, "maximum": 10000, "count": 42},
        "unit": "m",
    }
    band = Band.from_dict(d)
    assert band.data_type == DataType.UINT16
    assert band.nodata == 0
    assert band.statistics == Statistics(minimum=1, maximum=10000, count=42)
    assert band.unit == "m"
    assert band.extra_fields == {}
    assert band.to_dict() == d


@pytest.mark.parametrize(
    "value, expected",
    [
        ("nan", NoDataStrings.NAN),
        ("inf", NoDataStrings.INF),
        ("-inf", NoDataStrings.NINF),
    ],
)
def test_nodata_strings(value: str, expected: NoDataStrings) -> None:
    band = Band.from_dict({"nodata": value})
    assert band.nodata is expected
    assert band.to_dict() == {"nodata": value}


@pytest.mark.parametrize("value", [0, -9999, 1.5])
def test_nodata_numbers(value: float) -> None:
    assert Band.from_dict({"nodata": value}).nodata == value


def test_unknown_enum_values_are_kept() -> None:
    band = Band.from_dict({"data_type": "uint4", "nodata": "none"})
    assert band.data_type == "uint4"
    assert not isinstance(band.data_type, DataType)
    assert band.nodata == "none"
    assert band.to_dict() == {"data_type": "uint4", "nodata": "none"}


def test_to_dict_is_json_serializable() -> None:
    band = Band(
        name="red",
        data_type=DataType.FLOAT32,
        nodata=NoDataStrings.NAN,
        statistics=Statistics(mean=0.5),
    )
    assert json.loads(json.dumps(band.to_dict())) == {
        "name": "red",
        "data_type": "float32",
        "nodata": "nan",
        "statistics": {"mean": 0.5},
    }


def test_statistics_extra_fields() -> None:
    d = {"minimum": 0, "median": 3}
    statistics = Statistics.from_dict(d)
    assert statistics.minimum == 0
    assert statistics.extra_fields == {"median": 3}
    assert statistics.to_dict() == d
    assert d == {"minimum": 0, "median": 3}


def test_statistics_dicts_do_not_share_nested_values() -> None:
    d: dict[str, Any] = {"percentiles": [1, 2]}
    statistics = Statistics.from_dict(d)
    d["percentiles"].append(3)
    statistics.to_dict()["percentiles"].append(4)
    assert statistics.extra_fields == {"percentiles": [1, 2]}


def test_statistics_empty() -> None:
    assert Statistics.from_dict({}) == Statistics()
    assert Statistics().to_dict() == {}


def test_asset_clone_deep_copies_statistics() -> None:
    asset = Asset("data.tif", bands=[Band(statistics=Statistics(minimum=0))])
    cloned = asset.clone()
    assert cloned.bands
    assert cloned.bands[0].statistics
    cloned.bands[0].statistics.minimum = 1
    assert asset.bands
    assert asset.bands[0].statistics == Statistics(minimum=0)


def test_item_roundtrip_with_data_values(sample_item: Item) -> None:
    sample_item.bands = [Band(name="red", data_type=DataType.UINT8, nodata=255)]
    item = Item.from_dict(sample_item.to_dict())
    assert item.bands == [Band(name="red", data_type=DataType.UINT8, nodata=255)]
