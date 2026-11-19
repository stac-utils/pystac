"""Tests for pystac.extensions.sar."""

from datetime import datetime, timezone
from random import choice
from string import ascii_letters

import pytest

import pystac
from pystac import ExtensionTypeError
from pystac.extensions import processing
from pystac.extensions.processing import (
    ProcessingExtension,
    ProcessingLevel,
)
from tests.utils import TestCases


@pytest.fixture
def item() -> pystac.Item:
    asset_id = "my/items/2011"
    start = datetime(2020, 11, 7)
    item = pystac.Item(
        id=asset_id, geometry=None, bbox=None, datetime=start, properties={}
    )
    ProcessingExtension.add_to(item)
    return item


@pytest.fixture
def sentinel_item() -> pystac.Item:
    return pystac.Item.from_file(TestCases.get_path("data-files/processing/item.json"))


@pytest.fixture
def collection() -> pystac.Collection:
    return pystac.Collection.from_file(
        TestCases.get_path("data-files/processing/collection.json")
    )


def test_stac_extensions(item: pystac.Item) -> None:
    assert ProcessingExtension.has_extension(item)


@pytest.mark.vcr()
def test_required(item: pystac.Item) -> None:
    # None of the properties are required

    ProcessingExtension.ext(item).apply()
    item.validate()


@pytest.mark.vcr()
def test_all(item: pystac.Item) -> None:
    processing_level = ProcessingLevel.L1
    processing_datetime = datetime.now(timezone.utc)
    processing_expression = "b1+b2"
    processing_lineage = "GRD Post Processing"
    processing_facility = "Copernicus S1 Core Ground Segment - DPA"
    processing_version = "002.71"
    processing_software = {"Sentinel-1 IPF": "002.71"}

    ProcessingExtension.ext(item).apply(
        processing_level,
        processing_datetime,
        processing_expression,
        processing_lineage,
        processing_facility,
        processing_version,
        processing_software,
    )

    assert processing_level == ProcessingExtension.ext(item).level
    assert processing.LEVEL_PROP in item.properties

    assert processing_datetime == ProcessingExtension.ext(item).datetime
    assert processing.DATETIME_PROP in item.properties

    assert (
        processing_expression == ProcessingExtension.ext(item).expression["expression"]
    )
    assert "string" == ProcessingExtension.ext(item).expression["format"]
    assert processing.EXPRESSION_PROP in item.properties

    assert processing_lineage == ProcessingExtension.ext(item).lineage
    assert processing.LINEAGE_PROP in item.properties

    assert processing_software == ProcessingExtension.ext(item).software
    assert processing.SOFTWARE_PROP in item.properties

    assert processing_facility == ProcessingExtension.ext(item).facility
    assert processing.FACILITY_PROP in item.properties

    assert processing_version == ProcessingExtension.ext(item).version
    assert processing.VERSION_PROP in item.properties

    item.validate()


def test_should_return_none_when_nothing_is_set(
    item: pystac.Item,
) -> None:
    extension = ProcessingExtension.ext(item)
    extension.apply()

    assert extension.level is None
    assert extension.datetime is None
    assert extension.expression is None
    assert extension.software is None
    assert extension.facility is None
    assert extension.version is None


def test_extension_not_implemented(sentinel_item: pystac.Item) -> None:
    # Should raise exception if Item does not include extension URI
    sentinel_item.stac_extensions.remove(ProcessingExtension.get_schema_uri())

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = ProcessingExtension.ext(sentinel_item)

    # Should raise exception if owning Item does not include extension URI
    asset = sentinel_item.assets["quick-look"]

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = ProcessingExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = ProcessingExtension.ext(ownerless_asset)


def test_item_ext_add_to(sentinel_item: pystac.Item) -> None:
    sentinel_item.stac_extensions.remove(ProcessingExtension.get_schema_uri())
    assert ProcessingExtension.get_schema_uri() not in sentinel_item.stac_extensions

    _ = ProcessingExtension.ext(sentinel_item, add_if_missing=True)

    assert ProcessingExtension.get_schema_uri() in sentinel_item.stac_extensions


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError,
        match=r"^ProcessingExtension does not apply to type 'object'$",
    ):
        ProcessingExtension.ext(object())  # type: ignore
