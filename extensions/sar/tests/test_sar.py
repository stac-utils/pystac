"""Tests for pystac.extensions.sar."""

from datetime import datetime
from pathlib import Path
from random import choice
from string import ascii_letters

import pystac
import pytest
from pystac import ExtensionTypeError
from pystac.extensions import sar
from pystac.extensions.sar import (
    FrequencyBand,
    ObservationDirection,
    Polarization,
    SarExtension,
)
from pystac.summaries import RangeSummary

DATA_FILES = Path(__file__).resolve().parent / "data-files"


@pytest.fixture
def item() -> pystac.Item:
    asset_id = "my/items/2011"
    start = datetime(2020, 11, 7)
    item = pystac.Item(
        id=asset_id, geometry=None, bbox=None, datetime=start, properties={}
    )
    SarExtension.add_to(item)
    return item


@pytest.fixture
def sentinel_item() -> pystac.Item:
    return pystac.Item.from_file(str(DATA_FILES / "sentinel-1.json"))


@pytest.fixture
def collection() -> pystac.Collection:
    return pystac.Collection.from_file(
        str(DATA_FILES / "collections/multi-extent.json")
    )


def test_stac_extensions(item: pystac.Item) -> None:
    assert SarExtension.has_extension(item)


@pytest.mark.vcr()
def test_required(item: pystac.Item) -> None:
    mode: str = "Nonsense mode"
    frequency_band: sar.FrequencyBand = sar.FrequencyBand.P
    polarizations: list[sar.Polarization] = [
        sar.Polarization.HV,
        sar.Polarization.VH,
    ]
    product_type: str = "Some product"

    SarExtension.ext(item).apply(mode, frequency_band, polarizations, product_type)
    assert mode == SarExtension.ext(item).instrument_mode
    assert sar.INSTRUMENT_MODE_PROP in item.properties

    assert frequency_band == SarExtension.ext(item).frequency_band
    assert sar.FREQUENCY_BAND_PROP in item.properties

    assert polarizations == SarExtension.ext(item).polarizations
    assert sar.POLARIZATIONS_PROP in item.properties

    assert product_type == SarExtension.ext(item).product_type
    assert sar.PRODUCT_TYPE_PROP in item.properties

    item.validate()


@pytest.mark.vcr()
def test_all(item: pystac.Item) -> None:
    mode: str = "WV"
    frequency_band: sar.FrequencyBand = sar.FrequencyBand.KA
    polarizations: list[sar.Polarization] = [
        sar.Polarization.VV,
        sar.Polarization.HH,
    ]
    product_type: str = "Some product"
    center_frequency: float = 1.2
    resolution_range: float = 3.1
    resolution_azimuth: float = 4.1
    pixel_spacing_range: float = 5.1
    pixel_spacing_azimuth: float = 6.1
    looks_range: int = 7
    looks_azimuth: int = 8
    looks_equivalent_number: float = 9.1
    observation_direction: sar.ObservationDirection = sar.ObservationDirection.LEFT

    SarExtension.ext(item).apply(
        mode,
        frequency_band,
        polarizations,
        product_type,
        center_frequency,
        resolution_range,
        resolution_azimuth,
        pixel_spacing_range,
        pixel_spacing_azimuth,
        looks_range,
        looks_azimuth,
        looks_equivalent_number,
        observation_direction,
    )

    assert center_frequency == SarExtension.ext(item).center_frequency
    assert sar.CENTER_FREQUENCY_PROP in item.properties

    assert resolution_range == SarExtension.ext(item).resolution_range
    assert sar.RESOLUTION_RANGE_PROP in item.properties

    assert resolution_azimuth == SarExtension.ext(item).resolution_azimuth
    assert sar.RESOLUTION_AZIMUTH_PROP in item.properties

    assert pixel_spacing_range == SarExtension.ext(item).pixel_spacing_range
    assert sar.PIXEL_SPACING_RANGE_PROP in item.properties

    assert pixel_spacing_azimuth == SarExtension.ext(item).pixel_spacing_azimuth
    assert sar.PIXEL_SPACING_AZIMUTH_PROP in item.properties

    assert looks_range == SarExtension.ext(item).looks_range
    assert sar.LOOKS_RANGE_PROP in item.properties

    assert looks_azimuth == SarExtension.ext(item).looks_azimuth
    assert sar.LOOKS_AZIMUTH_PROP in item.properties

    assert looks_equivalent_number == SarExtension.ext(item).looks_equivalent_number
    assert sar.LOOKS_EQUIVALENT_NUMBER_PROP in item.properties

    assert observation_direction == SarExtension.ext(item).observation_direction
    assert sar.OBSERVATION_DIRECTION_PROP in item.properties

    item.validate()


def test_polarization_must_be_list(item: pystac.Item) -> None:
    mode: str = "Nonsense mode"
    frequency_band: sar.FrequencyBand = sar.FrequencyBand.P
    # Skip type hint as we are passing in an incorrect polarization.
    polarizations = sar.Polarization.HV
    product_type: str = "Some product"
    with pytest.raises(pystac.STACError):
        SarExtension.ext(item).apply(
            mode,
            frequency_band,
            polarizations,  # type:ignore
            product_type,
        )


def test_should_return_none_when_observation_direction_is_not_set(
    item: pystac.Item,
) -> None:
    extension = SarExtension.ext(item)
    extension.apply(
        choice(ascii_letters),
        choice(list(sar.FrequencyBand)),
        [],
        choice(ascii_letters),
    )
    assert extension.observation_direction is None


def test_extension_not_implemented(sentinel_item: pystac.Item) -> None:
    # Should raise exception if Item does not include extension URI
    sentinel_item.stac_extensions.remove(SarExtension.get_schema_uri())

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = SarExtension.ext(sentinel_item)

    # Should raise exception if owning Item does not include extension URI
    asset = sentinel_item.assets["measurement"]

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = SarExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = SarExtension.ext(ownerless_asset)


def test_item_ext_add_to(sentinel_item: pystac.Item) -> None:
    sentinel_item.stac_extensions.remove(SarExtension.get_schema_uri())
    assert SarExtension.get_schema_uri() not in sentinel_item.stac_extensions

    _ = SarExtension.ext(sentinel_item, add_if_missing=True)

    assert SarExtension.get_schema_uri() in sentinel_item.stac_extensions


def test_asset_ext_add_to(sentinel_item: pystac.Item) -> None:
    sentinel_item.stac_extensions.remove(SarExtension.get_schema_uri())
    assert SarExtension.get_schema_uri() not in sentinel_item.stac_extensions
    asset = sentinel_item.assets["measurement"]

    _ = SarExtension.ext(asset, add_if_missing=True)

    assert SarExtension.get_schema_uri() in sentinel_item.stac_extensions


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError,
        match=r"^SarExtension does not apply to type 'object'$",
    ):
        SarExtension.ext(object())  # type: ignore


def test_summaries_instrument_mode(collection: pystac.Collection) -> None:
    summaries_ext = SarExtension.summaries(collection, True)
    instrument_mode_list = ["WV"]

    summaries_ext.instrument_mode = instrument_mode_list

    assert summaries_ext.instrument_mode == instrument_mode_list
    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["sar:instrument_mode"] == instrument_mode_list


def test_summaries_frequency_band(collection: pystac.Collection) -> None:
    summaries_ext = SarExtension.summaries(collection, True)
    frequency_band_list = [FrequencyBand.P, FrequencyBand.L]

    summaries_ext.frequency_band = frequency_band_list

    assert summaries_ext.frequency_band == frequency_band_list
    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["sar:frequency_band"] == frequency_band_list


def test_summaries_polarizations(collection: pystac.Collection) -> None:
    summaries_ext = SarExtension.summaries(collection, True)
    polarizations_list = [Polarization.HH]

    summaries_ext.polarizations = polarizations_list

    assert summaries_ext.polarizations == polarizations_list

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["sar:polarizations"] == polarizations_list


def test_summaries_product_type(collection: pystac.Collection) -> None:
    summaries_ext = SarExtension.summaries(collection, True)
    product_type_list = ["SSC"]

    summaries_ext.product_type = product_type_list

    assert summaries_ext.product_type == product_type_list

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["sar:product_type"] == product_type_list


def test_summaries_center_frequency(collection: pystac.Collection) -> None:
    summaries_ext = SarExtension.summaries(collection, True)
    center_frequency_range = RangeSummary(4.405, 6.405)

    summaries_ext.center_frequency = center_frequency_range

    assert summaries_ext.center_frequency == center_frequency_range

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["sar:center_frequency"] == center_frequency_range.to_dict()


def test_summaries_resolution_range(collection: pystac.Collection) -> None:
    summaries_ext = SarExtension.summaries(collection, True)
    resolution_range_range = RangeSummary(800.0, 1200.0)

    summaries_ext.resolution_range = resolution_range_range

    assert summaries_ext.resolution_range == resolution_range_range

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["sar:resolution_range"] == resolution_range_range.to_dict()


def test_summaries_resolution_azimuth(collection: pystac.Collection) -> None:
    summaries_ext = SarExtension.summaries(collection, True)
    resolution_azimuth_range = RangeSummary(800.0, 1200.0)

    summaries_ext.resolution_azimuth = resolution_azimuth_range

    assert summaries_ext.resolution_azimuth == resolution_azimuth_range

    summaries_dict = collection.to_dict()["summaries"]

    assert (
        summaries_dict["sar:resolution_azimuth"] == resolution_azimuth_range.to_dict()
    )


def test_summaries_pixel_spacing_range(collection: pystac.Collection) -> None:
    summaries_ext = SarExtension.summaries(collection, True)
    pixel_spacing_range_range = RangeSummary(400.0, 600.0)

    summaries_ext.pixel_spacing_range = pixel_spacing_range_range

    assert summaries_ext.pixel_spacing_range == pixel_spacing_range_range

    summaries_dict = collection.to_dict()["summaries"]

    assert (
        summaries_dict["sar:pixel_spacing_range"] == pixel_spacing_range_range.to_dict()
    )


def test_summaries_pixel_spacing_azimuth(collection: pystac.Collection) -> None:
    summaries_ext = SarExtension.summaries(collection, True)
    pixel_spacing_azimuth_range = RangeSummary(400.0, 600.0)

    summaries_ext.pixel_spacing_azimuth = pixel_spacing_azimuth_range

    assert summaries_ext.pixel_spacing_azimuth == pixel_spacing_azimuth_range

    summaries_dict = collection.to_dict()["summaries"]

    assert (
        summaries_dict["sar:pixel_spacing_azimuth"]
        == pixel_spacing_azimuth_range.to_dict()
    )


def test_summaries_looks_range(collection: pystac.Collection) -> None:
    summaries_ext = SarExtension.summaries(collection, True)
    looks_range_range = RangeSummary(400, 600)

    summaries_ext.looks_range = looks_range_range

    assert summaries_ext.looks_range == looks_range_range

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["sar:looks_range"] == looks_range_range.to_dict()


def test_summaries_looks_azimuth(collection: pystac.Collection) -> None:
    summaries_ext = SarExtension.summaries(collection, True)
    looks_azimuth_range = RangeSummary(400, 600)

    summaries_ext.looks_azimuth = looks_azimuth_range

    assert summaries_ext.looks_azimuth == looks_azimuth_range

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["sar:looks_azimuth"] == looks_azimuth_range.to_dict()


def test_summaries_looks_equivalent_number(collection: pystac.Collection) -> None:
    summaries_ext = SarExtension.summaries(collection, True)
    looks_equivalent_number_range = RangeSummary(400.0, 600.0)

    summaries_ext.looks_equivalent_number = looks_equivalent_number_range

    assert summaries_ext.looks_equivalent_number == looks_equivalent_number_range

    summaries_dict = collection.to_dict()["summaries"]

    assert (
        summaries_dict["sar:looks_equivalent_number"]
        == looks_equivalent_number_range.to_dict()
    )


def test_summaries_observation_direction(collection: pystac.Collection) -> None:
    summaries_ext = SarExtension.summaries(collection, True)
    observation_direction_list = [ObservationDirection.LEFT]

    summaries_ext.observation_direction = observation_direction_list

    assert summaries_ext.observation_direction == observation_direction_list

    summaries_dict = collection.to_dict()["summaries"]

    assert summaries_dict["sar:observation_direction"] == observation_direction_list
