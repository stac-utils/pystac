# tests/extensions/test_order.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import pystac

# The Terradue branch defines this in pystac/extensions/order.py
from pystac.extensions.order import OrderExtension, OrderEvent, OrderEventType


def _utc(dt: datetime) -> datetime:
    """Force-aware UTC datetimes for stable serialization expectations."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def test_order_ext_adds_schema_and_sets_required_id(item: pystac.Item) -> None:
    # Arrange
    order_id = "ORDER-123"

    # Act
    ext = OrderExtension.ext(item, add_if_missing=True)
    ext.apply(order_id=order_id, history=None)

    # Assert: schema URI was added to stac_extensions
    assert any("image-order" in uri or "order" in uri for uri in item.stac_extensions), (
        "Expected Order extension schema URI to be present in item.stac_extensions"
    )

    # Assert: required property written
    assert item.properties.get("order:id") == order_id

    # Assert: optional property absent when None (implementation typically pops)
    assert "order:history" not in item.properties or item.properties["order:history"] is None


def test_order_ext_history_roundtrip(item: pystac.Item) -> None:
    # Arrange
    t0 = _utc(datetime(2024, 1, 1, 12, 0, 0))
    t1 = _utc(t0 + timedelta(hours=6))

    history = [
        OrderEvent.create(OrderEventType.SUBMITTED, t0),
        OrderEvent.create(OrderEventType.STARTED_PROCESSING, t1),
    ]

    # Act
    ext = OrderExtension.ext(item, add_if_missing=True)
    ext.apply(order_id="ORDER-456", history=history)

    # Assert: stored as list[dict] in properties
    raw = item.properties.get("order:history")
    assert isinstance(raw, list)
    assert raw[0]["type"] == "submitted"
    assert "timestamp" in raw[0]

    # Assert: getter returns OrderEvent objects with correct typing
    got = ext.history
    assert got is not None
    assert len(got) == 2
    assert got[0].event_type == OrderEventType.SUBMITTED
    assert got[1].event_type == OrderEventType.STARTED_PROCESSING

    # Ensure timestamps are parsed back to datetime
    assert isinstance(got[0].timestamp, datetime)
    assert isinstance(got[1].timestamp, datetime)


def test_order_id_is_required_on_read(item: pystac.Item) -> None:
    # Arrange: ensure extension is present but property is missing
    ext = OrderExtension.ext(item, add_if_missing=True)
    if "order:id" in item.properties:
        item.properties.pop("order:id")

    # Act / Assert: accessing order_id should error (get_required(...) path)
    with pytest.raises(Exception):
        _ = ext.order_id


def test_order_ext_type_error_on_wrong_object() -> None:
    # The extension should not apply to non-Item objects.
    cat = pystac.Catalog(id="c", description="d")

    with pytest.raises(pystac.ExtensionTypeError):
        OrderExtension.ext(cat, add_if_missing=False)  # type: ignore[arg-type]
