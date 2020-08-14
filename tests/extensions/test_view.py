import json
import unittest

import pystac
from pystac.extensions import ExtensionError
from pystac import (Item, Extensions)
from tests.utils import (TestCases, test_to_from_dict)


class ViewTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.example_uri = TestCases.get_path('data-files/view/example-landsat8.json')

    def test_to_from_dict(self):
        with open(self.example_uri) as f:
            d = json.load(f)
        test_to_from_dict(self, Item, d)

    def test_apply(self):
        item = next(TestCases.test_case_2().get_all_items())
        with self.assertRaises(ExtensionError):
            item.ext.view

        item.ext.enable(Extensions.VIEW)
        item.ext.view.apply(off_nadir=1.0,
                            incidence_angle=2.0,
                            azimuth=3.0,
                            sun_azimuth=2.0,
                            sun_elevation=1.0)

    def test_validate_view(self):
        item = pystac.read_file(self.example_uri)
        item.validate()

    def test_off_nadir(self):
        view_item = pystac.read_file(self.example_uri)

        # Get
        self.assertIn("view:off_nadir", view_item.properties)
        view_off_nadir = view_item.ext.view.off_nadir
        self.assertEqual(view_off_nadir, view_item.properties['view:off_nadir'])

        # Set
        view_item.ext.view.off_nadir = view_off_nadir + 10
        self.assertEqual(view_off_nadir + 10, view_item.properties['view:off_nadir'])

        # Get from Asset
        asset_no_prop = view_item.assets['blue']
        asset_prop = view_item.assets['red']
        self.assertEqual(view_item.ext.view.get_off_nadir(asset_no_prop),
                         view_item.ext.view.get_off_nadir())
        self.assertEqual(view_item.ext.view.get_off_nadir(asset_prop), 3.0)

        # Set to Asset
        asset_value = 13.0
        view_item.ext.view.set_off_nadir(asset_value, asset_no_prop)
        self.assertNotEqual(view_item.ext.view.get_off_nadir(asset_no_prop),
                            view_item.ext.view.get_off_nadir())
        self.assertEqual(view_item.ext.view.get_off_nadir(asset_no_prop), asset_value)

        # Validate
        view_item.validate()

    def test_incidence_angle(self):
        view_item = pystac.read_file(self.example_uri)

        # Get
        self.assertIn("view:incidence_angle", view_item.properties)
        view_incidence_angle = view_item.ext.view.incidence_angle
        self.assertEqual(view_incidence_angle, view_item.properties['view:incidence_angle'])

        # Set
        view_item.ext.view.incidence_angle = view_incidence_angle + 10
        self.assertEqual(view_incidence_angle + 10, view_item.properties['view:incidence_angle'])

        # Get from Asset
        asset_no_prop = view_item.assets['blue']
        asset_prop = view_item.assets['red']
        self.assertEqual(view_item.ext.view.get_incidence_angle(asset_no_prop),
                         view_item.ext.view.get_incidence_angle())
        self.assertEqual(view_item.ext.view.get_incidence_angle(asset_prop), 4.0)

        # Set to Asset
        asset_value = 14.0
        view_item.ext.view.set_incidence_angle(asset_value, asset_no_prop)
        self.assertNotEqual(view_item.ext.view.get_incidence_angle(asset_no_prop),
                            view_item.ext.view.get_incidence_angle())
        self.assertEqual(view_item.ext.view.get_incidence_angle(asset_no_prop), asset_value)

        # Validate
        view_item.validate()

    def test_azimuth(self):
        view_item = pystac.read_file(self.example_uri)

        # Get
        self.assertIn("view:azimuth", view_item.properties)
        view_azimuth = view_item.ext.view.azimuth
        self.assertEqual(view_azimuth, view_item.properties['view:azimuth'])

        # Set
        view_item.ext.view.azimuth = view_azimuth + 100
        self.assertEqual(view_azimuth + 100, view_item.properties['view:azimuth'])

        # Get from Asset
        asset_no_prop = view_item.assets['blue']
        asset_prop = view_item.assets['red']
        self.assertEqual(view_item.ext.view.get_azimuth(asset_no_prop),
                         view_item.ext.view.get_azimuth())
        self.assertEqual(view_item.ext.view.get_azimuth(asset_prop), 5.0)

        # Set to Asset
        asset_value = 15.0
        view_item.ext.view.set_azimuth(asset_value, asset_no_prop)
        self.assertNotEqual(view_item.ext.view.get_azimuth(asset_no_prop),
                            view_item.ext.view.get_azimuth())
        self.assertEqual(view_item.ext.view.get_azimuth(asset_no_prop), asset_value)

        # Validate
        view_item.validate()

    def test_sun_azimuth(self):
        view_item = pystac.read_file(self.example_uri)

        # Get
        self.assertIn("view:sun_azimuth", view_item.properties)
        view_sun_azimuth = view_item.ext.view.sun_azimuth
        self.assertEqual(view_sun_azimuth, view_item.properties['view:sun_azimuth'])

        # Set
        view_item.ext.view.sun_azimuth = view_sun_azimuth + 100
        self.assertEqual(view_sun_azimuth + 100, view_item.properties['view:sun_azimuth'])

        # Get from Asset
        asset_no_prop = view_item.assets['blue']
        asset_prop = view_item.assets['red']
        self.assertEqual(view_item.ext.view.get_sun_azimuth(asset_no_prop),
                         view_item.ext.view.get_sun_azimuth())
        self.assertEqual(view_item.ext.view.get_sun_azimuth(asset_prop), 1.0)

        # Set to Asset
        asset_value = 11.0
        view_item.ext.view.set_sun_azimuth(asset_value, asset_no_prop)
        self.assertNotEqual(view_item.ext.view.get_sun_azimuth(asset_no_prop),
                            view_item.ext.view.get_sun_azimuth())
        self.assertEqual(view_item.ext.view.get_sun_azimuth(asset_no_prop), asset_value)

        # Validate
        view_item.validate()

    def test_sun_elevation(self):
        view_item = pystac.read_file(self.example_uri)

        # Get
        self.assertIn("view:sun_elevation", view_item.properties)
        view_sun_elevation = view_item.ext.view.sun_elevation
        self.assertEqual(view_sun_elevation, view_item.properties['view:sun_elevation'])

        # Set
        view_item.ext.view.sun_elevation = view_sun_elevation + 10
        self.assertEqual(view_sun_elevation + 10, view_item.properties['view:sun_elevation'])

        # Get from Asset
        asset_no_prop = view_item.assets['blue']
        asset_prop = view_item.assets['red']
        self.assertEqual(view_item.ext.view.get_sun_elevation(asset_no_prop),
                         view_item.ext.view.get_sun_elevation())
        self.assertEqual(view_item.ext.view.get_sun_elevation(asset_prop), 2.0)

        # Set to Asset
        asset_value = 12.0
        view_item.ext.view.set_sun_elevation(asset_value, asset_no_prop)
        self.assertNotEqual(view_item.ext.view.get_sun_elevation(asset_no_prop),
                            view_item.ext.view.get_sun_elevation())
        self.assertEqual(view_item.ext.view.get_sun_elevation(asset_no_prop), asset_value)

        # Validate
        view_item.validate()
