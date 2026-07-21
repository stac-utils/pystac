from __future__ import annotations

from datetime import datetime
from typing import Any, cast

import pytest

import pystac
from pystac.extensions.earthquake import (
    DEPTH_PROP,
    EARTHQUAKE_EXTENSION_HOOKS,
    FELT_PROP,
    MAGNITUDE_PROP,
    MAGNITUDE_TYPE_PROP,
    SOURCES_PROP,
    STATUS_PROP,
    TSUNAMI_PROP,
    EarthquakeExtension,
    EarthquakeSource,
)


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def make_item() -> pystac.Item:
    return pystac.Item(
        id="eq-item",
        geometry=None,
        bbox=None,
        datetime=_dt("2020-01-01T00:00:00Z"),
        properties={},
        start_datetime=None,
        end_datetime=None,
    )


def test_item_apply_roundtrip() -> None:
    item = make_item()
    ext = EarthquakeExtension.ext(item, add_if_missing=True)

    sources: list[EarthquakeSource] = [{"name": "usgs", "code": "ak021"}]
    ext.apply(
        magnitude=6.1,
        sources=sources,
        magnitude_type="mww",
        felt=12,
        status="reviewed",
        tsunami=False,
        depth=8.4,
    )

    assert item.properties[MAGNITUDE_PROP] == 6.1
    assert item.properties[SOURCES_PROP] == sources
    assert item.properties[MAGNITUDE_TYPE_PROP] == "mww"
    assert item.properties[FELT_PROP] == 12
    assert item.properties[STATUS_PROP] == "reviewed"
    assert item.properties[TSUNAMI_PROP] is False
    assert item.properties[DEPTH_PROP] == 8.4

    assert ext.magnitude == 6.1
    assert ext.sources == sources
    assert ext.magnitude_type == "mww"
    assert ext.status == "reviewed"


def test_validation_errors() -> None:
    item = make_item()
    ext = EarthquakeExtension.ext(item, add_if_missing=True)

    with pytest.raises(ValueError):
        ext.magnitude = 25.0

    with pytest.raises(ValueError):
        ext.felt = -1

    with pytest.raises(ValueError):
        ext.sources = []

    with pytest.raises(ValueError):
        ext.sources = cast(Any, [{"name": "usgs"}])


def test_asset_reads_from_owner_and_writes_to_asset() -> None:
    item = make_item()
    iext = EarthquakeExtension.ext(item, add_if_missing=True)
    iext.magnitude = 5.0

    asset = pystac.Asset(href="s3://bucket/quake.json")
    item.add_asset("quake", asset)

    aext = EarthquakeExtension.ext(asset)
    assert aext.magnitude == 5.0

    aext.depth = 7.5
    assert asset.extra_fields[DEPTH_PROP] == 7.5


def test_extension_hooks_are_declared() -> None:
    assert EARTHQUAKE_EXTENSION_HOOKS.schema_uri == EarthquakeExtension.get_schema_uri()
    assert "eq" in EARTHQUAKE_EXTENSION_HOOKS.prev_extension_ids
    assert pystac.STACObjectType.ITEM in EARTHQUAKE_EXTENSION_HOOKS.stac_object_types
