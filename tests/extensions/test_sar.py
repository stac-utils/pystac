"""Tests for pystac.extensions.sar."""

import datetime
from random import choice
from typing import List
import unittest

from string import ascii_letters

import pystac
from pystac import ExtensionTypeError
from pystac.extensions import sar
from pystac.extensions.sar import (
    FrequencyBand,
    ObservationDirection,
    Polarization,
    SarExtension,
)
from pystac.summaries import RangeSummary
from tests.utils import TestCases


def make_item() -> pystac.Item:
    asset_id = "my/items/2011"
    start = datetime.datetime(2020, 11, 7)
    item = pystac.Item(
        id=asset_id, geometry=None, bbox=None, datetime=start, properties={}
    )

    SarExtension.add_to(item)
    return item


class SarItemExtTest(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.item = make_item()
        self.sentinel_example_uri = TestCases.get_path("data-files/sar/sentinel-1.json")

    def test_stac_extensions(self) -> None:
        self.assertTrue(SarExtension.has_extension(self.item))

    def test_required(self) -> None:
        mode: str = "Nonesense mode"
        frequency_band: sar.FrequencyBand = sar.FrequencyBand.P
        polarizations: List[sar.Polarization] = [
            sar.Polarization.HV,
            sar.Polarization.VH,
        ]
        product_type: str = "Some product"

        SarExtension.ext(self.item).apply(
            mode, frequency_band, polarizations, product_type
        )
        self.assertEqual(mode, SarExtension.ext(self.item).instrument_mode)
        self.assertIn(sar.INSTRUMENT_MODE_PROP, self.item.properties)

        self.assertEqual(frequency_band, SarExtension.ext(self.item).frequency_band)
        self.assertIn(sar.FREQUENCY_BAND_PROP, self.item.properties)

        self.assertEqual(polarizations, SarExtension.ext(self.item).polarizations)
        self.assertIn(sar.POLARIZATIONS_PROP, self.item.properties)

        self.assertEqual(product_type, SarExtension.ext(self.item).product_type)
        self.assertIn(sar.PRODUCT_TYPE_PROP, self.item.properties)

        self.item.validate()

    def test_all(self) -> None:
        mode: str = "WV"
        frequency_band: sar.FrequencyBand = sar.FrequencyBand.KA
        polarizations: List[sar.Polarization] = [
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

        SarExtension.ext(self.item).apply(
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

        self.assertEqual(center_frequency, SarExtension.ext(self.item).center_frequency)
        self.assertIn(sar.CENTER_FREQUENCY_PROP, self.item.properties)

        self.assertEqual(resolution_range, SarExtension.ext(self.item).resolution_range)
        self.assertIn(sar.RESOLUTION_RANGE_PROP, self.item.properties)

        self.assertEqual(
            resolution_azimuth, SarExtension.ext(self.item).resolution_azimuth
        )
        self.assertIn(sar.RESOLUTION_AZIMUTH_PROP, self.item.properties)

        self.assertEqual(
            pixel_spacing_range, SarExtension.ext(self.item).pixel_spacing_range
        )
        self.assertIn(sar.PIXEL_SPACING_RANGE_PROP, self.item.properties)

        self.assertEqual(
            pixel_spacing_azimuth, SarExtension.ext(self.item).pixel_spacing_azimuth
        )
        self.assertIn(sar.PIXEL_SPACING_AZIMUTH_PROP, self.item.properties)

        self.assertEqual(looks_range, SarExtension.ext(self.item).looks_range)
        self.assertIn(sar.LOOKS_RANGE_PROP, self.item.properties)

        self.assertEqual(looks_azimuth, SarExtension.ext(self.item).looks_azimuth)
        self.assertIn(sar.LOOKS_AZIMUTH_PROP, self.item.properties)

        self.assertEqual(
            looks_equivalent_number, SarExtension.ext(self.item).looks_equivalent_number
        )
        self.assertIn(sar.LOOKS_EQUIVALENT_NUMBER_PROP, self.item.properties)

        self.assertEqual(
            observation_direction, SarExtension.ext(self.item).observation_direction
        )
        self.assertIn(sar.OBSERVATION_DIRECTION_PROP, self.item.properties)

        self.item.validate()

    def test_polarization_must_be_list(self) -> None:
        mode: str = "Nonesense mode"
        frequency_band: sar.FrequencyBand = sar.FrequencyBand.P
        # Skip type hint as we are passing in an incorrect polarization.
        polarizations = sar.Polarization.HV
        product_type: str = "Some product"
        with self.assertRaises(pystac.STACError):
            SarExtension.ext(self.item).apply(
                mode,
                frequency_band,
                polarizations,  # type:ignore
                product_type,
            )

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Item does not include extension URI
        item = pystac.Item.from_file(self.sentinel_example_uri)
        item.stac_extensions.remove(SarExtension.get_schema_uri())

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = SarExtension.ext(item)

        # Should raise exception if owning Item does not include extension URI
        asset = item.assets["measurement"]

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = SarExtension.ext(asset)

        # Should succeed if Asset has no owner
        ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
        _ = SarExtension.ext(ownerless_asset)

    def test_item_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.sentinel_example_uri)
        item.stac_extensions.remove(SarExtension.get_schema_uri())
        self.assertNotIn(SarExtension.get_schema_uri(), item.stac_extensions)

        _ = SarExtension.ext(item, add_if_missing=True)

        self.assertIn(SarExtension.get_schema_uri(), item.stac_extensions)

    def test_asset_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.sentinel_example_uri)
        item.stac_extensions.remove(SarExtension.get_schema_uri())
        self.assertNotIn(SarExtension.get_schema_uri(), item.stac_extensions)
        asset = item.assets["measurement"]

        _ = SarExtension.ext(asset, add_if_missing=True)

        self.assertIn(SarExtension.get_schema_uri(), item.stac_extensions)

    def test_should_return_none_when_observation_direction_is_not_set(self) -> None:
        extension = SarExtension.ext(self.item)
        extension.apply(
            choice(ascii_letters),
            choice(list(sar.FrequencyBand)),
            [],
            choice(ascii_letters),
        )
        self.assertIsNone(extension.observation_direction)

    def test_should_raise_exception_when_passing_invalid_extension_object(
        self,
    ) -> None:
        self.assertRaisesRegex(
            ExtensionTypeError,
            r"^SAR extension does not apply to type 'object'$",
            SarExtension.ext,
            object(),
        )


class SarSummariesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.collection = pystac.Collection.from_file(
            TestCases.get_path("data-files/collections/multi-extent.json")
        )

    def test_instrument_mode(self) -> None:
        collection = self.collection.clone()
        summaries_ext = SarExtension.summaries(collection, True)
        instrument_mode_list = ["WV"]

        summaries_ext.instrument_mode = instrument_mode_list

        self.assertEqual(
            summaries_ext.instrument_mode,
            instrument_mode_list,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sar:instrument_mode"],
            instrument_mode_list,
        )

    def test_frequency_band(self) -> None:
        collection = self.collection.clone()
        summaries_ext = SarExtension.summaries(collection, True)
        frequency_band_list = [FrequencyBand.P, FrequencyBand.L]

        summaries_ext.frequency_band = frequency_band_list

        self.assertEqual(
            summaries_ext.frequency_band,
            frequency_band_list,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sar:frequency_band"],
            frequency_band_list,
        )

    def test_polarizations(self) -> None:
        collection = self.collection.clone()
        summaries_ext = SarExtension.summaries(collection, True)
        polarizations_list = [Polarization.HH]

        summaries_ext.polarizations = polarizations_list

        self.assertEqual(
            summaries_ext.polarizations,
            polarizations_list,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sar:polarizations"],
            polarizations_list,
        )

    def test_product_type(self) -> None:
        collection = self.collection.clone()
        summaries_ext = SarExtension.summaries(collection, True)
        product_type_list = ["SSC"]

        summaries_ext.product_type = product_type_list

        self.assertEqual(
            summaries_ext.product_type,
            product_type_list,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sar:product_type"],
            product_type_list,
        )

    def test_center_frequency(self) -> None:
        collection = self.collection.clone()
        summaries_ext = SarExtension.summaries(collection, True)
        center_frequency_range = RangeSummary(4.405, 6.405)

        summaries_ext.center_frequency = center_frequency_range

        self.assertEqual(
            summaries_ext.center_frequency,
            center_frequency_range,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sar:center_frequency"],
            center_frequency_range.to_dict(),
        )

    def test_resolution_range(self) -> None:
        collection = self.collection.clone()
        summaries_ext = SarExtension.summaries(collection, True)
        resolution_range_range = RangeSummary(800.0, 1200.0)

        summaries_ext.resolution_range = resolution_range_range

        self.assertEqual(
            summaries_ext.resolution_range,
            resolution_range_range,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sar:resolution_range"],
            resolution_range_range.to_dict(),
        )

    def test_resolution_azimuth(self) -> None:
        collection = self.collection.clone()
        summaries_ext = SarExtension.summaries(collection, True)
        resolution_azimuth_range = RangeSummary(800.0, 1200.0)

        summaries_ext.resolution_azimuth = resolution_azimuth_range

        self.assertEqual(
            summaries_ext.resolution_azimuth,
            resolution_azimuth_range,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sar:resolution_azimuth"],
            resolution_azimuth_range.to_dict(),
        )

    def test_pixel_spacing_range(self) -> None:
        collection = self.collection.clone()
        summaries_ext = SarExtension.summaries(collection, True)
        pixel_spacing_range_range = RangeSummary(400.0, 600.0)

        summaries_ext.pixel_spacing_range = pixel_spacing_range_range

        self.assertEqual(
            summaries_ext.pixel_spacing_range,
            pixel_spacing_range_range,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sar:pixel_spacing_range"],
            pixel_spacing_range_range.to_dict(),
        )

    def test_pixel_spacing_azimuth(self) -> None:
        collection = self.collection.clone()
        summaries_ext = SarExtension.summaries(collection, True)
        pixel_spacing_azimuth_range = RangeSummary(400.0, 600.0)

        summaries_ext.pixel_spacing_azimuth = pixel_spacing_azimuth_range

        self.assertEqual(
            summaries_ext.pixel_spacing_azimuth,
            pixel_spacing_azimuth_range,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sar:pixel_spacing_azimuth"],
            pixel_spacing_azimuth_range.to_dict(),
        )

    def test_looks_range(self) -> None:
        collection = self.collection.clone()
        summaries_ext = SarExtension.summaries(collection, True)
        looks_range_range = RangeSummary(400, 600)

        summaries_ext.looks_range = looks_range_range

        self.assertEqual(
            summaries_ext.looks_range,
            looks_range_range,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sar:looks_range"],
            looks_range_range.to_dict(),
        )

    def test_looks_azimuth(self) -> None:
        collection = self.collection.clone()
        summaries_ext = SarExtension.summaries(collection, True)
        looks_azimuth_range = RangeSummary(400, 600)

        summaries_ext.looks_azimuth = looks_azimuth_range

        self.assertEqual(
            summaries_ext.looks_azimuth,
            looks_azimuth_range,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sar:looks_azimuth"],
            looks_azimuth_range.to_dict(),
        )

    def test_looks_equivalent_number(self) -> None:
        collection = self.collection.clone()
        summaries_ext = SarExtension.summaries(collection, True)
        looks_equivalent_number_range = RangeSummary(400.0, 600.0)

        summaries_ext.looks_equivalent_number = looks_equivalent_number_range

        self.assertEqual(
            summaries_ext.looks_equivalent_number,
            looks_equivalent_number_range,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sar:looks_equivalent_number"],
            looks_equivalent_number_range.to_dict(),
        )

    def test_observation_direction(self) -> None:
        collection = self.collection.clone()
        summaries_ext = SarExtension.summaries(collection, True)
        observation_direction_list = [ObservationDirection.LEFT]

        summaries_ext.observation_direction = observation_direction_list

        self.assertEqual(
            summaries_ext.observation_direction,
            observation_direction_list,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sar:observation_direction"],
            observation_direction_list,
        )
