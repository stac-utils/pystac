from __future__ import annotations

from datetime import datetime
from typing import Any, TypeAlias, cast

import pytest

import pystac
from pystac.errors import RequiredPropertyMissing
from pystac.extensions.order import (
    DATE_PROP,
    EXPIRATION_DATE_PROP,
    ID_PROP,
    STATUS_PROP,
    AssetOrderExtension,
    OrderExtension,
    OrderStatus,
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


def test_item_status_is_required() -> None:
    item = make_item()
    OrderExtension.ext(item, add_if_missing=True)

    # status missing -> get_required should raise
    ext = OrderExtension.ext(item)
    with pytest.raises(RequiredPropertyMissing):
        _ = ext.status


def test_item_apply_roundtrip() -> None:
    item = make_item()
    ext = OrderExtension.ext(item, add_if_missing=True)

    d = _dt("2024-01-01T10:00:00Z")
    ext.apply(status=OrderStatus.ORDERED, order_id="123", date=d)

    assert item.properties[STATUS_PROP] == "ordered"
    assert item.properties[ID_PROP] == "123"
    assert item.properties[DATE_PROP].endswith("Z")
    assert ext.status == OrderStatus.ORDERED
    assert ext.order_id == "123"
    assert ext.date == d

    # pop_if_none on optional fields
    ext.order_id = None
    assert ID_PROP not in item.properties


def test_collection_top_level_fields() -> None:
    col = make_collection()
    ext = OrderExtension.ext(col, add_if_missing=True)

    ext.status = OrderStatus.PENDING
    ext.order_id = "abc"

    assert col.extra_fields[STATUS_PROP] == "pending"
    assert col.extra_fields[ID_PROP] == "abc"


def test_asset_owner_type_validation() -> None:
    # Asset with no owner is allowed when add_if_missing is False.
    asset = pystac.Asset(href="s3://bucket/a.tif")
    ext = OrderExtension.ext(asset, add_if_missing=False)
    assert isinstance(ext, AssetOrderExtension)
    assert ext.asset_href == "s3://bucket/a.tif"

    # Make it owned by something invalid (not Item/Collection)
    cat = pystac.Catalog(id="cat", description="d")
    bad_asset = pystac.Asset(href="s3://bucket/b.tif")
    bad_asset.owner = cast(Any, cat)

    with pytest.raises(pystac.ExtensionTypeError):
        OrderExtension.ext(bad_asset, add_if_missing=True)


def test_expiration_date_is_deprecated_and_roundtrips() -> None:
    item = make_item()
    ext = OrderExtension.ext(item, add_if_missing=True)

    exp = _dt("2024-02-01T00:00:00Z")
    with pytest.warns(DeprecationWarning):
        ext.expiration_date = exp

    assert item.properties[EXPIRATION_DATE_PROP].endswith("Z")

    with pytest.warns(DeprecationWarning):
        got = ext.expiration_date
    assert got == exp


def test_summaries_wrapper_sets_lists() -> None:
    col = make_collection()
    sext = OrderExtension.summaries(col, add_if_missing=True)

    sext.status = [OrderStatus.ORDERABLE, OrderStatus.ORDERED]

    assert col.summaries.lists[STATUS_PROP] == [
        OrderStatus.ORDERABLE,
        OrderStatus.ORDERED,
    ]
