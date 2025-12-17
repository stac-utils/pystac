"""Tests for pystac.extensions.sat."""

from datetime import datetime
from typing import Any

import pytest
from pystac.extensions.sat import OrbitState, SatExtension, SummariesSatExtension
from pystac.summaries import RangeSummary

import pystac
from pystac import Collection, ExtensionTypeError, Item
from pystac.extensions import sat
from pystac.utils import datetime_to_str, str_to_datetime
from tests.v1.utils import TestCases


@pytest.fixture
def item() -> Item:
    """Create basic test items that are only slightly different."""
    asset_id = "an/asset"
    start = datetime(2018, 1, 2)
    item = pystac.Item(
        id=asset_id, geometry=None, bbox=None, datetime=start, properties={}
    )

    SatExtension.add_to(item)
    return item


@pytest.fixture
def sentinel_item() -> Item:
    sentinel_example_uri = TestCases.get_path("data-files/sat/sentinel-1.json")
    return pystac.Item.from_file(sentinel_example_uri)


def test_stac_extensions(item: Item) -> None:
    assert SatExtension.has_extension(item)


def test_item_repr(item: Item) -> None:
    sat_item_ext = SatExtension.ext(item)
    assert f"<ItemSatExtension Item id={item.id}>" == sat_item_ext.__repr__()


def test_asset_repr(sentinel_item: Item) -> None:
    asset = sentinel_item.assets["measurement_iw1_vh"]
    sat_asset_ext = SatExtension.ext(asset)

    assert f"<AssetSatExtension Asset href={asset.href}>" == sat_asset_ext.__repr__()


@pytest.mark.vcr()
def test_no_args_fails(item: Item) -> None:
    SatExtension.ext(item).apply()
    with pytest.raises(pystac.STACValidationError):
        item.validate()


@pytest.mark.vcr()
def test_orbit_state(item: Item) -> None:
    orbit_state = sat.OrbitState.ASCENDING
    SatExtension.ext(item).apply(orbit_state)
    assert orbit_state == SatExtension.ext(item).orbit_state
    assert sat.RELATIVE_ORBIT_PROP not in item.properties
    assert SatExtension.ext(item).relative_orbit is None
    item.validate()


@pytest.mark.vcr()
def test_relative_orbit(item: Item) -> None:
    relative_orbit = 1234
    SatExtension.ext(item).apply(None, relative_orbit)
    assert relative_orbit == SatExtension.ext(item).relative_orbit
    assert sat.ORBIT_STATE_PROP not in item.properties
    assert SatExtension.ext(item).orbit_state is None
    item.validate()


@pytest.mark.vcr()
def test_absolute_orbit(item: Item) -> None:
    absolute_orbit = 1234
    SatExtension.ext(item).apply(absolute_orbit=absolute_orbit)
    assert absolute_orbit == SatExtension.ext(item).absolute_orbit
    assert sat.RELATIVE_ORBIT_PROP not in item.properties
    assert SatExtension.ext(item).relative_orbit is None
    item.validate()


@pytest.mark.vcr()
def test_anx_datetime(item: Item) -> None:
    anx_datetime = str_to_datetime("2020-01-01T00:00:00Z")
    SatExtension.ext(item).apply(anx_datetime=anx_datetime)
    assert anx_datetime == SatExtension.ext(item).anx_datetime
    assert sat.RELATIVE_ORBIT_PROP not in item.properties
    assert SatExtension.ext(item).relative_orbit is None
    item.validate()


@pytest.mark.vcr()
def test_platform_international_designator(item: Item) -> None:
    platform_international_designator = "2018-080A"
    SatExtension.ext(item).apply(
        platform_international_designator=platform_international_designator
    )
    assert (
        platform_international_designator
        == SatExtension.ext(item).platform_international_designator
    )
    assert sat.ORBIT_STATE_PROP not in item.properties
    assert SatExtension.ext(item).orbit_state is None
    item.validate()


@pytest.mark.vcr()
def test_relative_orbit_no_negative(item: Item) -> None:
    negative_relative_orbit = -2
    SatExtension.ext(item).apply(None, negative_relative_orbit)
    with pytest.raises(pystac.STACValidationError):
        item.validate()


@pytest.mark.vcr()
def test_both(item: Item) -> None:
    orbit_state = sat.OrbitState.DESCENDING
    relative_orbit = 4321
    SatExtension.ext(item).apply(orbit_state, relative_orbit)
    assert orbit_state == SatExtension.ext(item).orbit_state
    assert relative_orbit == SatExtension.ext(item).relative_orbit
    item.validate()


@pytest.mark.vcr()
def test_modify(item: Item) -> None:
    SatExtension.ext(item).apply(sat.OrbitState.DESCENDING, 999)

    orbit_state = sat.OrbitState.GEOSTATIONARY
    SatExtension.ext(item).orbit_state = orbit_state
    relative_orbit = 1000
    SatExtension.ext(item).relative_orbit = relative_orbit
    assert orbit_state == SatExtension.ext(item).orbit_state
    assert relative_orbit == SatExtension.ext(item).relative_orbit
    item.validate()


def test_from_dict() -> None:
    orbit_state = sat.OrbitState.GEOSTATIONARY
    relative_orbit = 1001
    d: dict[str, Any] = {
        "type": "Feature",
        "stac_version": "1.0.0-beta.2",
        "id": "an/asset",
        "properties": {
            "sat:orbit_state": orbit_state.value,
            "sat:relative_orbit": relative_orbit,
            "datetime": "2018-01-02T00:00:00Z",
        },
        "geometry": None,
        "links": [],
        "assets": {},
        "stac_extensions": [SatExtension.get_schema_uri()],
    }
    item = pystac.Item.from_dict(d)
    assert orbit_state == SatExtension.ext(item).orbit_state
    assert relative_orbit == SatExtension.ext(item).relative_orbit


def test_to_from_dict(item: Item) -> None:
    orbit_state = sat.OrbitState.GEOSTATIONARY
    relative_orbit = 1002
    SatExtension.ext(item).apply(orbit_state, relative_orbit)
    d = item.to_dict()
    assert orbit_state.value == d["properties"][sat.ORBIT_STATE_PROP]
    assert relative_orbit == d["properties"][sat.RELATIVE_ORBIT_PROP]

    item = pystac.Item.from_dict(d)
    assert orbit_state == SatExtension.ext(item).orbit_state
    assert relative_orbit == SatExtension.ext(item).relative_orbit


@pytest.mark.vcr()
def test_clear_orbit_state(item: Item) -> None:
    SatExtension.ext(item).apply(sat.OrbitState.DESCENDING, 999)

    SatExtension.ext(item).orbit_state = None
    assert SatExtension.ext(item).orbit_state is None
    item.validate()


@pytest.mark.vcr()
def test_clear_relative_orbit(item: Item) -> None:
    SatExtension.ext(item).apply(sat.OrbitState.DESCENDING, 999)

    SatExtension.ext(item).relative_orbit = None
    assert SatExtension.ext(item).relative_orbit is None
    item.validate()


def test_extension_not_implemented(sentinel_item: Item) -> None:
    # Should raise exception if Item does not include extension URI
    sentinel_item.stac_extensions.remove(SatExtension.get_schema_uri())

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = SatExtension.ext(sentinel_item)

    # Should raise exception if owning Item does not include extension URI
    asset = sentinel_item.assets["measurement_iw1_vh"]

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = SatExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = SatExtension.ext(ownerless_asset)


def test_item_ext_add_to(sentinel_item: Item) -> None:
    sentinel_item.stac_extensions.remove(SatExtension.get_schema_uri())
    assert SatExtension.get_schema_uri() not in sentinel_item.stac_extensions

    _ = SatExtension.ext(sentinel_item, add_if_missing=True)

    assert SatExtension.get_schema_uri() in sentinel_item.stac_extensions


def test_asset_ext_add_to(sentinel_item: Item) -> None:
    sentinel_item.stac_extensions.remove(SatExtension.get_schema_uri())
    assert SatExtension.get_schema_uri() not in sentinel_item.stac_extensions
    asset = sentinel_item.assets["measurement_iw1_vh"]

    _ = SatExtension.ext(asset, add_if_missing=True)

    assert SatExtension.get_schema_uri() in sentinel_item.stac_extensions


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError, match=r"^SatExtension does not apply to type 'object'$"
    ):
        # calling this wrong on purpose so ---v
        SatExtension.ext(object())  # type: ignore


@pytest.fixture
def collection() -> Collection:
    return Collection.from_file(
        TestCases.get_path("data-files/collections/multi-extent.json")
    )


@pytest.fixture
def summaries_ext(collection: Collection) -> SummariesSatExtension:
    return SatExtension.summaries(collection, True)


def test_summaries_platform_international_designation(
    collection: Collection, summaries_ext: SummariesSatExtension
) -> None:
    platform_international_designator_list = ["2018-080A"]

    summaries_ext.platform_international_designator = ["2018-080A"]

    assert (
        summaries_ext.platform_international_designator
        == platform_international_designator_list
    )

    summaries_dict = collection.to_dict()["summaries"]

    assert (
        summaries_dict["sat:platform_international_designator"]
        == platform_international_designator_list
    )


def test_summaries_orbit_state(
    collection: Collection, summaries_ext: SummariesSatExtension
) -> None:
    orbit_state_list = [OrbitState.ASCENDING]

    summaries_ext.orbit_state = orbit_state_list

    assert summaries_ext.orbit_state == orbit_state_list

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["sat:orbit_state"] == orbit_state_list


def test_summaries_absolute_orbit(
    collection: Collection, summaries_ext: SummariesSatExtension
) -> None:
    absolute_orbit_range = RangeSummary(2000, 3000)

    summaries_ext.absolute_orbit = absolute_orbit_range

    assert summaries_ext.absolute_orbit == absolute_orbit_range

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["sat:absolute_orbit"] == absolute_orbit_range.to_dict()


def test_summaries_relative_orbit(
    collection: Collection, summaries_ext: SummariesSatExtension
) -> None:
    relative_orbit_range = RangeSummary(50, 100)

    summaries_ext.relative_orbit = relative_orbit_range

    assert summaries_ext.relative_orbit == relative_orbit_range

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["sat:relative_orbit"] == relative_orbit_range.to_dict()


def test_summaries_anx_datetime(
    collection: Collection, summaries_ext: SummariesSatExtension
) -> None:
    anx_datetime_range = RangeSummary(
        str_to_datetime("2020-01-01T00:00:00.000Z"),
        str_to_datetime("2020-01-02T00:00:00.000Z"),
    )

    summaries_ext.anx_datetime = anx_datetime_range

    assert summaries_ext.anx_datetime == anx_datetime_range

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["sat:anx_datetime"] == {
        "minimum": datetime_to_str(anx_datetime_range.minimum),
        "maximum": datetime_to_str(anx_datetime_range.maximum),
    }


def test_summaries_adds_uri(collection: Collection) -> None:
    collection.stac_extensions = []
    with pytest.raises(
        pystac.ExtensionNotImplemented,
        match="Extension 'sat' is not implemented",
    ):
        SatExtension.summaries(collection, add_if_missing=False)

    _ = SatExtension.summaries(collection, True)

    assert SatExtension.get_schema_uri() in collection.stac_extensions

    SatExtension.remove_from(collection)
    assert SatExtension.get_schema_uri() not in collection.stac_extensions
