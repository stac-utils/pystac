"""Tests for pystac.extensions.sat."""

import datetime
import unittest

import pystac
from pystac.extensions import sat


def make_item() -> pystac.Item:
    """Create basic test items that are only slightly different."""
    asset_id = 'an/asset'
    start = datetime.datetime(2018, 1, 2)
    item = pystac.Item(id=asset_id, geometry=None, bbox=None, datetime=start, properties={})

    item.ext.enable(pystac.Extensions.SAT)
    return item


class SatTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.item = make_item()

    def test_stac_extensions(self):
        self.assertEqual([pystac.Extensions.SAT], self.item.stac_extensions)

    def test_no_args_fails(self):
        with self.assertRaises(pystac.STACError):
            self.item.ext.sat.apply()

    def test_orbit_state(self):
        orbit_state = sat.OrbitState.ASCENDING
        self.item.ext.sat.apply(orbit_state)
        self.assertEqual(orbit_state, self.item.ext.sat.orbit_state)
        self.assertNotIn(sat.RELATIVE_ORBIT, self.item.properties)
        self.assertFalse(self.item.ext.sat.relative_orbit)
        self.item.validate()

    def test_relative_orbit(self):
        relative_orbit = 1234
        self.item.ext.sat.apply(None, relative_orbit)
        self.assertEqual(relative_orbit, self.item.ext.sat.relative_orbit)
        self.assertNotIn(sat.ORBIT_STATE, self.item.properties)
        self.assertFalse(self.item.ext.sat.orbit_state)
        self.item.validate()

    def test_relative_orbit_no_negative(self):
        negative_relative_orbit = -2
        with self.assertRaises(pystac.STACError):
            self.item.ext.sat.apply(None, negative_relative_orbit)

        self.item.ext.sat.apply(None, 123)
        with self.assertRaises(pystac.STACError):
            self.item.ext.sat.relative_orbit = negative_relative_orbit

    def test_both(self):
        orbit_state = sat.OrbitState.DESCENDING
        relative_orbit = 4321
        self.item.ext.sat.apply(orbit_state, relative_orbit)
        self.assertEqual(orbit_state, self.item.ext.sat.orbit_state)
        self.assertEqual(relative_orbit, self.item.ext.sat.relative_orbit)
        self.item.validate()

    def test_modify(self):
        self.item.ext.sat.apply(sat.OrbitState.DESCENDING, 999)

        orbit_state = sat.OrbitState.GEOSTATIONARY
        self.item.ext.sat.orbit_state = orbit_state
        relative_orbit = 1000
        self.item.ext.sat.relative_orbit = relative_orbit
        self.assertEqual(orbit_state, self.item.ext.sat.orbit_state)
        self.assertEqual(relative_orbit, self.item.ext.sat.relative_orbit)
        self.item.validate()

    def test_from_dict(self):
        orbit_state = sat.OrbitState.GEOSTATIONARY
        relative_orbit = 1001
        d = {
            'type': 'Feature',
            'stac_version': '1.0.0-beta.2',
            'id': 'an/asset',
            'properties': {
                'sat:orbit_state': orbit_state.value,
                'sat:relative_orbit': relative_orbit,
                'datetime': '2018-01-02T00:00:00Z'
            },
            'geometry': None,
            'links': [],
            'assets': {},
            'stac_extensions': ['sat']
        }
        item = pystac.Item.from_dict(d)
        self.assertEqual(orbit_state, item.ext.sat.orbit_state)
        self.assertEqual(relative_orbit, item.ext.sat.relative_orbit)

    def test_to_from_dict(self):
        orbit_state = sat.OrbitState.GEOSTATIONARY
        relative_orbit = 1002
        self.item.ext.sat.apply(orbit_state, relative_orbit)
        d = self.item.to_dict()
        self.assertEqual(orbit_state.value, d['properties'][sat.ORBIT_STATE])
        self.assertEqual(relative_orbit, d['properties'][sat.RELATIVE_ORBIT])

        item = pystac.Item.from_dict(d)
        self.assertEqual(orbit_state, item.ext.sat.orbit_state)
        self.assertEqual(relative_orbit, item.ext.sat.relative_orbit)

    def test_clear_orbit_state(self):
        self.item.ext.sat.apply(sat.OrbitState.DESCENDING, 999)

        self.item.ext.sat.orbit_state = None
        self.assertIsNone(self.item.ext.sat.orbit_state)
        self.item.validate()

    def test_clear_relative_orbit(self):
        self.item.ext.sat.apply(sat.OrbitState.DESCENDING, 999)

        self.item.ext.sat.relative_orbit = None
        self.assertIsNone(self.item.ext.sat.relative_orbit)
        self.item.validate()

    def test_clear_orbit_state_fail(self):
        self.item.ext.sat.apply(sat.OrbitState.DESCENDING)
        with self.assertRaises(pystac.STACError):
            self.item.ext.sat.orbit_state = None

    def test_clear_orbit_relative_orbit(self):
        self.item.ext.sat.apply(None, 1)
        with self.assertRaises(pystac.STACError):
            self.item.ext.sat.relative_orbit = None
