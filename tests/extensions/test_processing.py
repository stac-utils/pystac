from __future__ import annotations

from datetime import datetime
from typing import TypeAlias

import pystac
from pystac.extensions.processing import (
    DATETIME_PROP,
    EXPRESSION_PROP,
    FACILITY_PROP,
    LEVEL_PROP,
    LINEAGE_PROP,
    SOFTWARE_PROP,
    VERSION_PROP,
    ProcessingExpression,
    ProcessingExtension,
)

TemporalIntervals: TypeAlias = list[list[datetime | None]]


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def make_item() -> pystac.Item:
    return pystac.Item(
        id="i",
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


def test_processing_expression_create_and_to_dict() -> None:
    pe = ProcessingExpression.create(format="cwl", expression={"a": 1})
    assert pe.format == "cwl"
    assert pe.expression == {"a": 1}
    assert pe.to_dict() == {"format": "cwl", "expression": {"a": 1}}
    assert "ProcessingExpression" in repr(pe)


def test_item_apply_roundtrip() -> None:
    item = make_item()
    ext = ProcessingExtension.ext(item, add_if_missing=True)

    pe = ProcessingExpression.create(format="cwl", expression={"steps": []})
    dt = _dt("2024-01-01T12:00:00Z")
    ext.apply(
        expression=pe,
        lineage="L2 from L1",
        level="L2A",
        facility="ESA",
        software={"snap": "9.0"},
        version="1.0",
        processing_datetime=dt,
    )

    assert item.properties[EXPRESSION_PROP] == {
        "format": "cwl",
        "expression": {"steps": []},
    }
    assert item.properties[LINEAGE_PROP] == "L2 from L1"
    assert item.properties[LEVEL_PROP] == "L2A"
    assert item.properties[FACILITY_PROP] == "ESA"
    assert item.properties[SOFTWARE_PROP] == {"snap": "9.0"}
    assert item.properties[VERSION_PROP] == "1.0"
    assert item.properties[DATETIME_PROP].endswith("Z")

    assert ext.expression is not None
    assert ext.expression.format == "cwl"
    assert ext.processing_datetime == dt


def test_asset_read_falls_back_to_owner_item_properties() -> None:
    item = make_item()
    iext = ProcessingExtension.ext(item, add_if_missing=True)
    iext.level = "L2B"

    asset = pystac.Asset(href="s3://bucket/a.tif")
    item.add_asset("data", asset)

    aext = ProcessingExtension.ext(asset, add_if_missing=True)
    # Not set on asset, but should be readable via additional_read_properties fallback
    assert aext.level == "L2B"

    aext.level = "L2C"
    assert asset.extra_fields[LEVEL_PROP] == "L2C"
    assert aext.level == "L2C"


def test_summaries_wrapper_sets_lists_and_schema() -> None:
    col = make_collection()
    sext = ProcessingExtension.summaries(col, add_if_missing=True)

    sext.level = ["L1", "L2"]
    sext.software = {"snap": {"type": "string"}}

    assert col.summaries.lists[LEVEL_PROP] == ["L1", "L2"]
    assert col.summaries.schemas[SOFTWARE_PROP] == {"snap": {"type": "string"}}


def test_provider_wrapper_sets_extra_fields() -> None:
    provider = pystac.Provider(
        name="ACME",
        roles=[pystac.ProviderRole.PROCESSOR],
        url="https://example.com",
    )
    pext = ProcessingExtension.provider(provider)

    pext.level = "L3"
    assert provider.extra_fields[LEVEL_PROP] == "L3"
