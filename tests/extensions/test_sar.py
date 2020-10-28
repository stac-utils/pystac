"""Tests for pystac.extensions.sar."""

import datetime
from typing import List
import unittest

import pystac
from pystac.extensions import sar


def make_item() -> pystac.Item:
    asset_id = 'my/items/2011'
    start = datetime.datetime(2020, 11, 7)
    item = pystac.Item(id=asset_id, geometry=None, bbox=None, datetime=start, properties={})

    item.ext.enable(pystac.Extensions.SAR)
    return item


class SarItemExtTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.item = make_item()
        self.item.ext.enable(pystac.Extensions.SAR)

    def test_stac_extensions(self):
        self.assertEqual([pystac.Extensions.SAR], self.item.stac_extensions)

    def test_required(self):
        mode: str = 'Nonesense mode'
        frequency_band: sar.FrequencyBand = sar.FrequencyBand.P
        polarizations: List[sar.Polarization] = [sar.Polarization.HV, sar.Polarization.VH]
        product_type: str = 'Some product'
        self.item.ext.sar.apply(mode, frequency_band, polarizations, product_type)
        self.assertEqual(mode, self.item.ext.sar.instrument_mode)
        self.assertIn(sar.INSTRUMENT_MODE, self.item.properties)

        self.assertEqual(frequency_band, self.item.ext.sar.frequency_band)
        self.assertIn(sar.FREQUENCY_BAND, self.item.properties)

        self.assertEqual(polarizations, self.item.ext.sar.polarizations)
        self.assertIn(sar.POLARIZATIONS, self.item.properties)

        self.assertEqual(product_type, self.item.ext.sar.product_type)
        self.assertIn(sar.PRODUCT_TYPE, self.item.properties)

        self.item.validate()

    def test_all(self):
        mode: str = 'WV'
        frequency_band: sar.FrequencyBand = sar.FrequencyBand.KA
        polarizations: List[sar.Polarization] = [sar.Polarization.VV, sar.Polarization.HH]
        product_type: str = 'Some product'
        center_frequency: float = 1.2
        resolution_range: float = 3.1
        resolution_azimuth: float = 4.1
        pixel_spacing_range: float = 5.1
        pixel_spacing_azimuth: float = 6.1
        looks_range: int = 7
        looks_azimuth: int = 8
        looks_equivalent_number: float = 9.1
        observation_direction: sar.ObservationDirection = sar.ObservationDirection.LEFT

        self.item.ext.sar.apply(mode, frequency_band, polarizations, product_type, center_frequency,
                                resolution_range, resolution_azimuth, pixel_spacing_range,
                                pixel_spacing_azimuth, looks_range, looks_azimuth,
                                looks_equivalent_number, observation_direction)

        self.assertEqual(center_frequency, self.item.ext.sar.center_frequency)
        self.assertIn(sar.CENTER_FREQUENCY, self.item.properties)

        self.assertEqual(resolution_range, self.item.ext.sar.resolution_range)
        self.assertIn(sar.RESOLUTION_RANGE, self.item.properties)

        self.assertEqual(resolution_azimuth, self.item.ext.sar.resolution_azimuth)
        self.assertIn(sar.RESOLUTION_AZIMUTH, self.item.properties)

        self.assertEqual(pixel_spacing_range, self.item.ext.sar.pixel_spacing_range)
        self.assertIn(sar.PIXEL_SPACING_RANGE, self.item.properties)

        self.assertEqual(pixel_spacing_azimuth, self.item.ext.sar.pixel_spacing_azimuth)
        self.assertIn(sar.PIXEL_SPACING_AZIMUTH, self.item.properties)

        self.assertEqual(looks_range, self.item.ext.sar.looks_range)
        self.assertIn(sar.LOOKS_RANGE, self.item.properties)

        self.assertEqual(looks_azimuth, self.item.ext.sar.looks_azimuth)
        self.assertIn(sar.LOOKS_AZIMUTH, self.item.properties)

        self.assertEqual(looks_equivalent_number, self.item.ext.sar.looks_equivalent_number)
        self.assertIn(sar.LOOKS_EQUIVALENT_NUMBER, self.item.properties)

        self.assertEqual(observation_direction, self.item.ext.sar.observation_direction)
        self.assertIn(sar.OBSERVATION_DIRECTION, self.item.properties)

        self.item.validate()

    def test_polarization_must_be_list(self):
        mode: str = 'Nonesense mode'
        frequency_band: sar.FrequencyBand = sar.FrequencyBand.P
        # Skip type hint as we are passing in an incorrect polarization.
        polarizations = sar.Polarization.HV
        product_type: str = 'Some product'
        with self.assertRaises(pystac.STACError):
            self.item.ext.sar.apply(mode, frequency_band, polarizations, product_type)


if __name__ == '__main__':
    unittest.main()
