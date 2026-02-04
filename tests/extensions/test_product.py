from __future__ import annotations

import pytest
import pystac

from pystac.extensions.product import (
    ACQUISITION_TYPE_PROP,
    TIMELINESS_CATEGORY_PROP,
    TIMELINESS_PROP,
    TYPE_PROP,
    AcquisitionType,
    ProductExtension,
    PRODUCT_EXTENSION_HOOKS,
)


def make_item() -> pystac.Item:
    return pystac.Item(
        id="i",
        geometry=None,
        bbox=None,
        datetime=None,
        properties={},
        start_datetime=None,
        end_datetime=None,
    )


def make_collection() -> pystac.Collection:
    return pystac.Collection(
        id="c",
        description="d",
        extent=pystac.Extent(
            pystac.SpatialExtent([[-180, -90, 180, 90]]),
            pystac.TemporalExtent([[None, None]]),
        ),
        license="proprietary",
    )


def test_apply_requires_timeliness_when_setting_category() -> None:
    item = make_item()
    ext = ProductExtension.ext(item, add_if_missing=True)

    with pytest.raises(ValueError):
        ext.apply(timeliness_category="NRT")  # timeliness missing and not already set

    # If timeliness is already set, setting category is allowed
    ext.timeliness = "PT3H"
    ext.apply(timeliness_category="NRT")
    assert item.properties[TIMELINESS_CATEGORY_PROP] == "NRT"


def test_item_apply_roundtrip_and_acquisition_type_enum() -> None:
    item = make_item()
    ext = ProductExtension.ext(item, add_if_missing=True)

    ext.apply(
        product_type="SLC",
        timeliness="PT3H",
        timeliness_category="NRT",
        acquisition_type=AcquisitionType.NOMINAL,
    )

    assert item.properties[TYPE_PROP] == "SLC"
    assert item.properties[TIMELINESS_PROP] == "PT3H"
    assert item.properties[TIMELINESS_CATEGORY_PROP] == "NRT"
    assert item.properties[ACQUISITION_TYPE_PROP] == "nominal"
    assert ext.acquisition_type == AcquisitionType.NOMINAL

    # Unknown strings should roundtrip as raw strings
    ext.acquisition_type = "nonstandard"
    assert item.properties[ACQUISITION_TYPE_PROP] == "nonstandard"
    assert ext.acquisition_type == "nonstandard"


def test_collection_top_level_fields() -> None:
    col = make_collection()
    ext = ProductExtension.ext(col, add_if_missing=True)

    ext.product_type = "L1C"
    assert col.extra_fields[TYPE_PROP] == "L1C"


def test_summaries_wrapper_sets_lists() -> None:
    col = make_collection()
    sext = ProductExtension.summaries(col, add_if_missing=True)

    sext.product_type = ["L1C", "L2A"]
    assert col.summaries.lists[TYPE_PROP] == ["L1C", "L2A"]


def test_extension_hooks_are_declared() -> None:
    assert PRODUCT_EXTENSION_HOOKS.schema_uri == ProductExtension.get_schema_uri()
    assert "product" in PRODUCT_EXTENSION_HOOKS.prev_extension_ids
    assert pystac.STACObjectType.COLLECTION in PRODUCT_EXTENSION_HOOKS.stac_object_types