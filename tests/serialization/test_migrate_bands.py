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

EO_FIELDS = {
    "common_name",
    "center_wavelength",
    "full_width_half_max",
    "solar_illumination",
}
RASTER_FIELDS = {
    "sampling",
    "bits_per_sample",
    "spatial_resolution",
    "scale",
    "offset",
    "histogram",
}


def migrate_eo(d: dict[str, Any]) -> bool:
    return migrate_extension_bands(d, "eo:bands", "eo:", EO_FIELDS)


def migrate_raster(d: dict[str, Any]) -> bool:
    return migrate_extension_bands(d, "raster:bands", "raster:", RASTER_FIELDS)


def migrate(d: dict[str, Any]) -> bool:
    eo = migrate_eo(d)
    raster = migrate_raster(d)
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
    migrate_raster(raster_first)
    migrate_eo(raster_first)
    assert eo_first == raster_first


def test_item_properties_bands_on_assets_are_removed(
    item_dict: dict[str, Any],
) -> None:
    item_dict["properties"]["eo:bands"] = [
        {"name": "red", "common_name": "red"},
        {"name": "nir"},
    ]
    item_dict["assets"]["data"]["eo:bands"] = [{"name": "red", "common_name": "red"}]
    item_dict["assets"]["nir"] = {"href": "nir.tif", "bands": [{"name": "nir"}]}
    assert migrate(item_dict)
    assert "eo:bands" not in item_dict["properties"]
    assert "bands" not in item_dict["properties"]
    assert item_dict["assets"]["data"]["bands"] == [
        {"name": "red", "eo:common_name": "red"}
    ]


def test_item_properties_bands_not_on_assets_are_not_migrated(
    item_dict: dict[str, Any],
) -> None:
    item_dict["properties"]["eo:bands"] = [{"name": "red"}, {"name": "nir"}]
    item_dict["assets"]["data"]["eo:bands"] = [{"name": "red"}]
    expected = deepcopy(item_dict)
    with pytest.warns(UserWarning, match="Item properties have bands that no asset"):
        assert not migrate(item_dict)
    assert item_dict == expected


def test_item_properties_next_to_bands_are_merged(item_dict: dict[str, Any]) -> None:
    item_dict["properties"]["bands"] = [{"name": "red"}]
    item_dict["properties"]["eo:bands"] = [{"name": "red", "common_name": "red"}]
    assert migrate(item_dict)
    assert item_dict["properties"] == {
        "datetime": "2020-01-01T00:00:00Z",
        "bands": [{"name": "red", "eo:common_name": "red"}],
    }


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


def test_equal_fields_are_merged(item_dict: dict[str, Any]) -> None:
    item_dict["assets"]["data"]["bands"] = [{"name": "red", "unit": "m"}]
    item_dict["assets"]["data"]["eo:bands"] = [{"name": "red", "common_name": "red"}]
    assert migrate(item_dict)
    assert item_dict["assets"]["data"]["bands"] == [
        {"name": "red", "unit": "m", "eo:common_name": "red"}
    ]


def test_different_values_than_bands_are_not_migrated(
    item_dict: dict[str, Any],
) -> None:
    item_dict["assets"]["data"]["bands"] = [{"name": "common"}]
    item_dict["assets"]["data"]["eo:bands"] = [{"name": "eo", "common_name": "red"}]
    expected = deepcopy(item_dict)
    with pytest.warns(UserWarning, match="bands has different values for name"):
        assert not migrate(item_dict)
    assert item_dict == expected


@pytest.mark.parametrize("eo_first", [True, False])
def test_different_values_than_other_band_list_are_not_migrated(
    item_dict: dict[str, Any], eo_first: bool
) -> None:
    asset = item_dict["assets"]["data"]
    asset["eo:bands"] = [{"name": "B1", "description": "Red"}]
    asset["raster:bands"] = [{"description": "Reflectance", "scale": 2}]
    expected = deepcopy(item_dict)
    with pytest.warns(UserWarning, match="different values for description"):
        if eo_first:
            assert not migrate_eo(item_dict)
            assert not migrate_raster(item_dict)
        else:
            assert not migrate_raster(item_dict)
            assert not migrate_eo(item_dict)
    assert item_dict == expected


@pytest.mark.parametrize("eo_first", [True, False])
def test_raster_band_names_give_way(item_dict: dict[str, Any], eo_first: bool) -> None:
    asset = item_dict["assets"]["data"]
    asset["eo:bands"] = [{"name": "B1"}, {"name": "B2", "common_name": "nir"}]
    asset["raster:bands"] = [{"name": "band1", "scale": 2}, {"name": "B2"}]
    with pytest.warns(UserWarning, match="Dropping name of raster:bands"):
        if eo_first:
            assert migrate_eo(item_dict)
            assert migrate_raster(item_dict)
        else:
            assert migrate_raster(item_dict)
            assert migrate_eo(item_dict)
    assert asset["bands"] == [
        {"name": "B1", "raster:scale": 2},
        {"name": "B2", "eo:common_name": "nir"},
    ]


def test_raster_band_names_give_way_to_bands(item_dict: dict[str, Any]) -> None:
    asset = item_dict["assets"]["data"]
    asset["bands"] = [{"name": "B1"}]
    asset["raster:bands"] = [{"name": "band1", "scale": 2}]
    with pytest.warns(UserWarning, match="Dropping name of raster:bands"):
        assert migrate(item_dict)
    assert asset["bands"] == [{"name": "B1", "raster:scale": 2}]


def test_only_extension_fields_get_prefix(item_dict: dict[str, Any]) -> None:
    item_dict["assets"]["data"]["eo:bands"] = [
        {"name": "B1", "common_name": "red", "gsd": 30, "title": "Red"}
    ]
    item_dict["assets"]["data"]["raster:bands"] = [{"scale": 2, "gsd": 30}]
    assert migrate(item_dict)
    assert item_dict["assets"]["data"]["bands"] == [
        {
            "name": "B1",
            "eo:common_name": "red",
            "gsd": 30,
            "title": "Red",
            "raster:scale": 2,
        }
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
    expected = deepcopy(item_dict)
    with pytest.warns(UserWarning, match=r"bands: it has \d bands but \w+:bands has"):
        assert not migrate(item_dict)
    assert item_dict == expected


def test_different_lengths_leave_other_containers_unchanged(
    item_dict: dict[str, Any],
) -> None:
    item_dict["properties"]["raster:bands"] = [{"nodata": 0}]
    item_dict["assets"]["data"]["bands"] = [{"name": "red"}, {"name": "green"}]
    item_dict["assets"]["data"]["raster:bands"] = [{"nodata": 0}]
    expected = deepcopy(item_dict)
    with pytest.warns(UserWarning, match="raster:bands"):
        assert not migrate_raster(item_dict)
    assert item_dict == expected


def test_band_indices_are_not_migrated(item_dict: dict[str, Any]) -> None:
    item_dict["assets"]["data"]["eo:bands"] = [0, 1]
    assert not migrate(item_dict)
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
    assert not migrate(d)
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
