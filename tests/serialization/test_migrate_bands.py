from copy import deepcopy
from typing import Any

import pytest

import pystac
from pystac import Collection
from pystac.serialization.migrate import (
    has_extension_fields,
    migrate_extension_bands,
)
from tests.utils import TestCases


def migrate(d: dict[str, Any]) -> bool:
    eo = migrate_extension_bands(d, "eo:bands", "eo:")
    raster = migrate_extension_bands(d, "raster:bands", "raster:")
    return eo and raster


@pytest.fixture
def sentinel2_dict() -> dict[str, Any]:
    return pystac.StacIO.default().read_json(
        TestCases.get_path("data-files/examples/1.0.0/example-sentinel2.json")
    )


@pytest.fixture
def item_dict() -> dict[str, Any]:
    return {
        "type": "Feature",
        "stac_version": "1.0.0",
        "id": "item",
        "geometry": None,
        "properties": {"datetime": "2020-01-01T00:00:00Z"},
        "links": [],
        "assets": {"data": {"href": "data.tif"}},
    }


def test_sentinel2_asset(sentinel2_dict: dict[str, Any]) -> None:
    assert migrate(sentinel2_dict)
    asset = sentinel2_dict["assets"]["red"]
    assert "eo:bands" not in asset
    assert "raster:bands" not in asset
    assert asset["bands"] == [
        {
            "name": "red",
            "eo:common_name": "red",
            "description": "Red (band 4)",
            "eo:center_wavelength": 0.665,
            "eo:full_width_half_max": 0.038,
            "nodata": 0,
            "data_type": "uint16",
            "raster:bits_per_sample": 15,
            "raster:spatial_resolution": 10,
            "unit": "none",
            "raster:scale": 0.0001,
            "raster:offset": 0,
        }
    ]


def test_sentinel2_eo_only_asset(sentinel2_dict: dict[str, Any]) -> None:
    migrate(sentinel2_dict)
    bands = sentinel2_dict["assets"]["visual"]["bands"]
    assert [band["name"] for band in bands] == ["red", "green", "blue"]
    assert bands[0]["eo:common_name"] == "red"


def test_merge_order_does_not_matter(sentinel2_dict: dict[str, Any]) -> None:
    eo_first = deepcopy(sentinel2_dict)
    migrate(eo_first)
    raster_first = sentinel2_dict
    migrate_extension_bands(raster_first, "raster:bands", "raster:")
    migrate_extension_bands(raster_first, "eo:bands", "eo:")
    assert eo_first == raster_first


def test_item_properties(item_dict: dict[str, Any]) -> None:
    item_dict["properties"]["eo:bands"] = [{"name": "red"}]
    assert migrate(item_dict)
    assert item_dict["properties"]["bands"] == [{"name": "red"}]
    assert "eo:bands" not in item_dict["properties"]


def test_raster_only(item_dict: dict[str, Any]) -> None:
    item_dict["assets"]["data"]["raster:bands"] = [
        {"nodata": "nan", "statistics": {"minimum": 0}, "histogram": {"count": 1}}
    ]
    assert migrate(item_dict)
    assert item_dict["assets"]["data"]["bands"] == [
        {
            "nodata": "nan",
            "statistics": {"minimum": 0},
            "raster:histogram": {"count": 1},
        }
    ]


def test_existing_fields_are_kept(item_dict: dict[str, Any]) -> None:
    item_dict["assets"]["data"]["bands"] = [{"name": "common"}]
    item_dict["assets"]["data"]["eo:bands"] = [{"name": "eo", "common_name": "red"}]
    assert migrate(item_dict)
    assert item_dict["assets"]["data"]["bands"] == [
        {"name": "common", "eo:common_name": "red"}
    ]


def test_prefixed_fields_are_not_prefixed_again(item_dict: dict[str, Any]) -> None:
    item_dict["assets"]["data"]["raster:bands"] = [
        {"raster:scale": 2, "classification:classes": [{"value": 1}]}
    ]
    assert migrate(item_dict)
    assert item_dict["assets"]["data"]["bands"] == [
        {"raster:scale": 2, "classification:classes": [{"value": 1}]}
    ]


def test_different_lengths_are_not_migrated(item_dict: dict[str, Any]) -> None:
    asset = item_dict["assets"]["data"]
    asset["eo:bands"] = [{"name": "red"}, {"name": "green"}]
    asset["raster:bands"] = [{"nodata": 0}]
    with pytest.warns(
        UserWarning, match="raster:bands: it has 1 bands but bands has 2"
    ):
        assert not migrate(item_dict)
    assert asset == {
        "href": "data.tif",
        "bands": [{"name": "red"}, {"name": "green"}],
        "raster:bands": [{"nodata": 0}],
    }


def test_different_lengths_leave_other_containers_unchanged(
    item_dict: dict[str, Any],
) -> None:
    item_dict["properties"]["raster:bands"] = [{"nodata": 0}]
    item_dict["assets"]["data"]["bands"] = [{"name": "red"}, {"name": "green"}]
    item_dict["assets"]["data"]["raster:bands"] = [{"nodata": 0}]
    expected = deepcopy(item_dict)
    with pytest.warns(UserWarning, match="raster:bands"):
        assert not migrate_extension_bands(item_dict, "raster:bands", "raster:")
    assert item_dict == expected


def test_band_indices_are_not_migrated(item_dict: dict[str, Any]) -> None:
    item_dict["assets"]["data"]["eo:bands"] = [0, 1]
    assert migrate(item_dict)
    assert item_dict["assets"]["data"] == {"href": "data.tif", "eo:bands": [0, 1]}


def test_empty_band_list_is_removed(item_dict: dict[str, Any]) -> None:
    item_dict["assets"]["data"]["eo:bands"] = []
    assert migrate(item_dict)
    assert item_dict["assets"]["data"] == {"href": "data.tif"}


def test_nothing_to_migrate(item_dict: dict[str, Any]) -> None:
    expected = deepcopy(item_dict)
    assert migrate(item_dict)
    assert item_dict == expected


def test_catalog_is_ignored() -> None:
    d = {"type": "Catalog", "eo:bands": [{"name": "red"}]}
    assert migrate(d)
    assert d == {"type": "Catalog", "eo:bands": [{"name": "red"}]}


def test_collection_assets_and_item_assets(collection: Collection) -> None:
    d = collection.to_dict(include_self_link=False)
    d["assets"] = {"thumbnail": {"href": "t.png", "raster:bands": [{"nodata": 0}]}}
    d["item_assets"] = {
        "data": {"eo:bands": [{"name": "red"}], "raster:bands": [{"scale": 2}]}
    }
    assert migrate(d)
    assert d["assets"]["thumbnail"]["bands"] == [{"nodata": 0}]
    assert d["item_assets"]["data"]["bands"] == [{"name": "red", "raster:scale": 2}]


def test_collection_summaries(collection: Collection) -> None:
    d = collection.to_dict(include_self_link=False)
    d["summaries"] = {
        "eo:bands": [{"name": "B01", "common_name": "coastal"}],
        "raster:bands": [{"data_type": "uint8", "nodata": 255}],
        "eo:cloud_cover": {"minimum": 0, "maximum": 100},
    }
    assert migrate(d)
    assert d["summaries"] == {
        "bands": [
            {
                "name": "B01",
                "eo:common_name": "coastal",
                "data_type": "uint8",
                "nodata": 255,
            }
        ],
        "eo:cloud_cover": {"minimum": 0, "maximum": 100},
    }


def test_collection_summaries_schema_is_not_migrated(collection: Collection) -> None:
    d = collection.to_dict(include_self_link=False)
    d["summaries"] = {"eo:bands": {"type": "array"}}
    assert migrate(d)
    assert d["summaries"] == {"eo:bands": {"type": "array"}}


@pytest.mark.parametrize(
    "properties, asset",
    [
        ({"eo:cloud_cover": 1}, {}),
        ({"bands": [{"eo:common_name": "red"}]}, {}),
        ({}, {"eo:snow_cover": 1}),
        ({}, {"bands": [{"name": "red"}, {"eo:center_wavelength": 0.6}]}),
    ],
)
def test_item_has_extension_fields(
    item_dict: dict[str, Any], properties: dict[str, Any], asset: dict[str, Any]
) -> None:
    item_dict["properties"].update(properties)
    item_dict["assets"]["data"].update(asset)
    assert has_extension_fields(item_dict, "eo:")


def test_item_has_no_extension_fields(item_dict: dict[str, Any]) -> None:
    item_dict["properties"]["bands"] = [{"name": "red", "raster:scale": 2}]
    item_dict["assets"]["data"]["bands"] = [{"name": "red"}]
    assert not has_extension_fields(item_dict, "eo:")


@pytest.mark.parametrize(
    "field, value",
    [
        ("bands", [{"eo:common_name": "red"}]),
        ("assets", {"data": {"href": "d.tif", "eo:cloud_cover": 1}}),
        ("item_assets", {"data": {"bands": [{"eo:common_name": "red"}]}}),
        ("summaries", {"eo:cloud_cover": {"minimum": 0, "maximum": 1}}),
        ("summaries", {"bands": [{"eo:common_name": "red"}]}),
    ],
)
def test_collection_has_extension_fields(
    collection: Collection, field: str, value: Any
) -> None:
    d = collection.to_dict(include_self_link=False)
    d[field] = value
    assert has_extension_fields(d, "eo:")


def test_collection_has_no_extension_fields(collection: Collection) -> None:
    d = collection.to_dict(include_self_link=False)
    d["summaries"] = {"bands": [{"name": "B01"}]}
    assert not has_extension_fields(d, "eo:")
