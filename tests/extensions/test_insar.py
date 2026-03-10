from __future__ import annotations

from datetime import datetime
from typing import Any, TypeAlias, cast

import pytest

import pystac
from pystac.extensions.insar import (
    GEOC_DEM_PROP,
    HOA_PROP,
    PERP_BASELINE_PROP,
    PROC_DEM_PROP,
    REF_DT_PROP,
    SEC_DT_PROP,
    TEMP_BASELINE_PROP,
    InsarExtension,
)

TemporalIntervals: TypeAlias = list[list[datetime | None]]


def _dt(s: str) -> datetime:
    # Accept RFC3339 "Z" and return tz-aware datetime
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def make_item() -> pystac.Item:
    return pystac.Item(
        id="test",
        geometry=None,
        bbox=None,
        datetime=_dt("2020-01-01T00:00:00Z"),
        properties={},
        start_datetime=None,
        end_datetime=None,
    )


def make_collection() -> pystac.Collection:
    temporal_intervals: TemporalIntervals = [[None, None]]
    return pystac.Collection(
        id="c",
        description="d",
        extent=pystac.Extent(
            pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
            pystac.TemporalExtent(temporal_intervals),
        ),
        license="proprietary",
    )


def test_item_ext_adds_extension_when_requested() -> None:
    item = make_item()
    assert InsarExtension.get_schema_uri() not in item.stac_extensions

    ext = InsarExtension.ext(item, add_if_missing=True)
    assert InsarExtension.get_schema_uri() in item.stac_extensions
    assert ext.perpendicular_baseline is None


def test_item_apply_roundtrip_and_serialization() -> None:
    item = make_item()
    ext = InsarExtension.ext(item, add_if_missing=True)

    ref = _dt("2023-02-01T00:00:00Z")
    sec = _dt("2023-02-28T23:59:59Z")

    ext.apply(
        perpendicular_baseline=123.4,
        temporal_baseline=12,
        height_of_ambiguity=42,
        reference_datetime=ref,
        secondary_datetime=sec,
        processing_dem="s3://bucket/dem1.tif",
        geocoding_dem="s3://bucket/dem2.tif",
    )

    assert item.properties[PERP_BASELINE_PROP] == 123.4
    assert item.properties[TEMP_BASELINE_PROP] == 12.0
    assert item.properties[HOA_PROP] == 42.0
    assert item.properties[REF_DT_PROP].endswith("Z")
    assert item.properties[SEC_DT_PROP].endswith("Z")
    assert item.properties[PROC_DEM_PROP] == "s3://bucket/dem1.tif"
    assert item.properties[GEOC_DEM_PROP] == "s3://bucket/dem2.tif"

    # getters
    assert ext.perpendicular_baseline == 123.4
    assert ext.temporal_baseline == 12.0
    assert ext.height_of_ambiguity == 42.0
    assert ext.reference_datetime == ref
    assert ext.secondary_datetime == sec
    assert ext.processing_dem == "s3://bucket/dem1.tif"
    assert ext.geocoding_dem == "s3://bucket/dem2.tif"

    # pop_if_none behavior
    ext.processing_dem = None
    assert PROC_DEM_PROP not in item.properties


def test_validations_raise_value_error() -> None:
    item = make_item()
    ext = InsarExtension.ext(item, add_if_missing=True)

    with pytest.raises(ValueError):
        ext.perpendicular_baseline = True  # bool is not a number

    with pytest.raises(ValueError):
        ext.processing_dem = 123  # type: ignore[assignment]


def test_asset_ext_adds_extension_to_owner() -> None:
    item = make_item()
    asset = pystac.Asset(href="s3://bucket/a.tif")
    item.add_asset("data", asset)

    assert InsarExtension.get_schema_uri() not in item.stac_extensions
    aext = InsarExtension.ext(asset, add_if_missing=True)
    assert InsarExtension.get_schema_uri() in item.stac_extensions

    aext.temporal_baseline = 3
    assert asset.extra_fields[TEMP_BASELINE_PROP] == 3.0


def test_collection_ext_is_not_supported() -> None:
    col = make_collection()
    with pytest.raises(pystac.ExtensionTypeError):
        InsarExtension.ext(cast(Any, col))


def test_collection_summaries_singleton_storage_and_removal() -> None:
    col = make_collection()
    sext = InsarExtension.summaries(col, add_if_missing=True)

    ref = _dt("2023-02-01T00:00:00Z")
    sext.apply(reference_datetime=ref, processing_dem="demA", geocoding_dem="demB")

    # Stored as singleton lists
    assert col.summaries.lists[REF_DT_PROP] == ["2023-02-01T00:00:00Z"]
    assert col.summaries.lists[PROC_DEM_PROP] == ["demA"]
    assert col.summaries.lists[GEOC_DEM_PROP] == ["demB"]

    assert sext.reference_datetime == ref
    assert sext.processing_dem == "demA"
    assert sext.geocoding_dem == "demB"

    # Removal
    sext.processing_dem = None
    assert PROC_DEM_PROP not in col.summaries.lists
