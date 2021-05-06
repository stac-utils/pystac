"""Tests for pystac.extensions.sar."""

import datetime
from typing import List
import unittest

import pystac
from pystac.extensions import sar
from pystac.extensions.sar import SarExtension


def make_item() -> pystac.Item:
    asset_id = "my/items/2011"
    start = datetime.datetime(2020, 11, 7)
    item = pystac.Item(
        id=asset_id, geometry=None, bbox=None, datetime=start, properties={}
    )

    SarExtension.add_to(item)
    return item


class SarItemExtTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.item = make_item()

    def test_stac_extensions(self):
        self.assertTrue(SarExtension.has_extension(self.item))

    def test_required(self):
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
        self.assertIn(sar.INSTRUMENT_MODE, self.item.properties)

        self.assertEqual(frequency_band, SarExtension.ext(self.item).frequency_band)
        self.assertIn(sar.FREQUENCY_BAND, self.item.properties)

        self.assertEqual(polarizations, SarExtension.ext(self.item).polarizations)
        self.assertIn(sar.POLARIZATIONS, self.item.properties)

        self.assertEqual(product_type, SarExtension.ext(self.item).product_type)
        self.assertIn(sar.PRODUCT_TYPE, self.item.properties)

        self.item.validate()

    def test_all(self):
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
        self.assertIn(sar.CENTER_FREQUENCY, self.item.properties)

        self.assertEqual(resolution_range, SarExtension.ext(self.item).resolution_range)
        self.assertIn(sar.RESOLUTION_RANGE, self.item.properties)

        self.assertEqual(
            resolution_azimuth, SarExtension.ext(self.item).resolution_azimuth
        )
        self.assertIn(sar.RESOLUTION_AZIMUTH, self.item.properties)

        self.assertEqual(
            pixel_spacing_range, SarExtension.ext(self.item).pixel_spacing_range
        )
        self.assertIn(sar.PIXEL_SPACING_RANGE, self.item.properties)

        self.assertEqual(
            pixel_spacing_azimuth, SarExtension.ext(self.item).pixel_spacing_azimuth
        )
        self.assertIn(sar.PIXEL_SPACING_AZIMUTH, self.item.properties)

        self.assertEqual(looks_range, SarExtension.ext(self.item).looks_range)
        self.assertIn(sar.LOOKS_RANGE, self.item.properties)

        self.assertEqual(looks_azimuth, SarExtension.ext(self.item).looks_azimuth)
        self.assertIn(sar.LOOKS_AZIMUTH, self.item.properties)

        self.assertEqual(
            looks_equivalent_number, SarExtension.ext(self.item).looks_equivalent_number
        )
        self.assertIn(sar.LOOKS_EQUIVALENT_NUMBER, self.item.properties)

        self.assertEqual(
            observation_direction, SarExtension.ext(self.item).observation_direction
        )
        self.assertIn(sar.OBSERVATION_DIRECTION, self.item.properties)

        self.item.validate()

    def test_polarization_must_be_list(self):
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


if __name__ == "__main__":
    unittest.main()
