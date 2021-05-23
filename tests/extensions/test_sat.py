"""Tests for pystac.extensions.sat."""

import datetime
from typing import Any, Dict
import unittest

import pystac
from pystac.extensions import sat
from pystac.extensions.sat import SatExtension


def make_item() -> pystac.Item:
    """Create basic test items that are only slightly different."""
    asset_id = "an/asset"
    start = datetime.datetime(2018, 1, 2)
    item = pystac.Item(
        id=asset_id, geometry=None, bbox=None, datetime=start, properties={}
    )

    SatExtension.add_to(item)
    return item


class SatTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.item = make_item()

    def test_stac_extensions(self):
        self.assertTrue(SatExtension.has_extension(self.item))

    def test_no_args_fails(self):
        SatExtension.ext(self.item).apply()
        with self.assertRaises(pystac.STACValidationError):
            self.item.validate()

    def test_orbit_state(self):
        orbit_state = sat.OrbitState.ASCENDING
        SatExtension.ext(self.item).apply(orbit_state)
        self.assertEqual(orbit_state, SatExtension.ext(self.item).orbit_state)
        self.assertNotIn(sat.RELATIVE_ORBIT, self.item.properties)
        self.assertFalse(SatExtension.ext(self.item).relative_orbit)
        self.item.validate()

    def test_relative_orbit(self):
        relative_orbit = 1234
        SatExtension.ext(self.item).apply(None, relative_orbit)
        self.assertEqual(relative_orbit, SatExtension.ext(self.item).relative_orbit)
        self.assertNotIn(sat.ORBIT_STATE, self.item.properties)
        self.assertFalse(SatExtension.ext(self.item).orbit_state)
        self.item.validate()

    def test_relative_orbit_no_negative(self):
        negative_relative_orbit = -2
        SatExtension.ext(self.item).apply(None, negative_relative_orbit)
        with self.assertRaises(pystac.STACValidationError):
            self.item.validate()

    def test_both(self):
        orbit_state = sat.OrbitState.DESCENDING
        relative_orbit = 4321
        SatExtension.ext(self.item).apply(orbit_state, relative_orbit)
        self.assertEqual(orbit_state, SatExtension.ext(self.item).orbit_state)
        self.assertEqual(relative_orbit, SatExtension.ext(self.item).relative_orbit)
        self.item.validate()

    def test_modify(self):
        SatExtension.ext(self.item).apply(sat.OrbitState.DESCENDING, 999)

        orbit_state = sat.OrbitState.GEOSTATIONARY
        SatExtension.ext(self.item).orbit_state = orbit_state
        relative_orbit = 1000
        SatExtension.ext(self.item).relative_orbit = relative_orbit
        self.assertEqual(orbit_state, SatExtension.ext(self.item).orbit_state)
        self.assertEqual(relative_orbit, SatExtension.ext(self.item).relative_orbit)
        self.item.validate()

    def test_from_dict(self):
        orbit_state = sat.OrbitState.GEOSTATIONARY
        relative_orbit = 1001
        d: Dict[str, Any] = {
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
            "stac_extensions": ["sat"],
        }
        item = pystac.Item.from_dict(d)
        self.assertEqual(orbit_state, SatExtension.ext(item).orbit_state)
        self.assertEqual(relative_orbit, SatExtension.ext(item).relative_orbit)

    def test_to_from_dict(self):
        orbit_state = sat.OrbitState.GEOSTATIONARY
        relative_orbit = 1002
        SatExtension.ext(self.item).apply(orbit_state, relative_orbit)
        d = self.item.to_dict()
        self.assertEqual(orbit_state.value, d["properties"][sat.ORBIT_STATE])
        self.assertEqual(relative_orbit, d["properties"][sat.RELATIVE_ORBIT])

        item = pystac.Item.from_dict(d)
        self.assertEqual(orbit_state, SatExtension.ext(item).orbit_state)
        self.assertEqual(relative_orbit, SatExtension.ext(item).relative_orbit)

    def test_clear_orbit_state(self):
        SatExtension.ext(self.item).apply(sat.OrbitState.DESCENDING, 999)

        SatExtension.ext(self.item).orbit_state = None
        self.assertIsNone(SatExtension.ext(self.item).orbit_state)
        self.item.validate()

    def test_clear_relative_orbit(self):
        SatExtension.ext(self.item).apply(sat.OrbitState.DESCENDING, 999)

        SatExtension.ext(self.item).relative_orbit = None
        self.assertIsNone(SatExtension.ext(self.item).relative_orbit)
        self.item.validate()
