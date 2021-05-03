import json
import unittest

import pystac
from pystac.extensions.view import ViewExtension
from tests.utils import TestCases, test_to_from_dict


class ViewTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.example_uri = TestCases.get_path("data-files/view/example-landsat8.json")

    def test_to_from_dict(self):
        with open(self.example_uri) as f:
            d = json.load(f)
        test_to_from_dict(self, pystac.Item, d)

    def test_apply(self):
        item = next(iter(TestCases.test_case_2().get_all_items()))
        self.assertFalse(ViewExtension.has_extension(item))

        ViewExtension.add_to(item)
        ViewExtension.ext(item).apply(
            off_nadir=1.0,
            incidence_angle=2.0,
            azimuth=3.0,
            sun_azimuth=4.0,
            sun_elevation=5.0,
        )

        self.assertEqual(ViewExtension.ext(item).off_nadir, 1.0)
        self.assertEqual(ViewExtension.ext(item).incidence_angle, 2.0)
        self.assertEqual(ViewExtension.ext(item).azimuth, 3.0)
        self.assertEqual(ViewExtension.ext(item).sun_azimuth, 4.0)
        self.assertEqual(ViewExtension.ext(item).sun_elevation, 5.0)

    def test_validate_view(self):
        item = pystac.Item.from_file(self.example_uri)
        self.assertTrue(ViewExtension.has_extension(item))
        item.validate()

    def test_off_nadir(self):
        view_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("view:off_nadir", view_item.properties)
        view_off_nadir = ViewExtension.ext(view_item).off_nadir
        self.assertEqual(view_off_nadir, view_item.properties["view:off_nadir"])

        # Set
        ViewExtension.ext(view_item).off_nadir = view_off_nadir + 10
        self.assertEqual(view_off_nadir + 10, view_item.properties["view:off_nadir"])

        # Get from Asset
        asset_no_prop = view_item.assets["blue"]
        asset_prop = view_item.assets["red"]
        self.assertEqual(
            ViewExtension.ext(asset_no_prop).off_nadir,
            ViewExtension.ext(view_item).off_nadir,
        )
        self.assertEqual(ViewExtension.ext(asset_prop).off_nadir, 3.0)

        # Set to Asset
        asset_value = 13.0
        ViewExtension.ext(asset_no_prop).off_nadir = asset_value
        self.assertNotEqual(
            ViewExtension.ext(asset_no_prop).off_nadir,
            ViewExtension.ext(view_item).off_nadir,
        )
        self.assertEqual(ViewExtension.ext(asset_no_prop).off_nadir, asset_value)

        # Validate
        view_item.validate()

    def test_incidence_angle(self):
        view_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("view:incidence_angle", view_item.properties)
        view_incidence_angle = ViewExtension.ext(view_item).incidence_angle
        self.assertEqual(
            view_incidence_angle, view_item.properties["view:incidence_angle"]
        )

        # Set
        ViewExtension.ext(view_item).incidence_angle = view_incidence_angle + 10
        self.assertEqual(
            view_incidence_angle + 10, view_item.properties["view:incidence_angle"]
        )

        # Get from Asset
        asset_no_prop = view_item.assets["blue"]
        asset_prop = view_item.assets["red"]
        self.assertEqual(
            ViewExtension.ext(asset_no_prop).incidence_angle,
            ViewExtension.ext(view_item).incidence_angle,
        )
        self.assertEqual(ViewExtension.ext(asset_prop).incidence_angle, 4.0)

        # Set to Asset
        asset_value = 14.0
        ViewExtension.ext(asset_no_prop).incidence_angle = asset_value
        self.assertNotEqual(
            ViewExtension.ext(asset_no_prop).incidence_angle,
            ViewExtension.ext(view_item).incidence_angle,
        )
        self.assertEqual(ViewExtension.ext(asset_no_prop).incidence_angle, asset_value)

        # Validate
        view_item.validate()

    def test_azimuth(self):
        view_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("view:azimuth", view_item.properties)
        view_azimuth = ViewExtension.ext(view_item).azimuth
        self.assertEqual(view_azimuth, view_item.properties["view:azimuth"])

        # Set
        ViewExtension.ext(view_item).azimuth = view_azimuth + 100
        self.assertEqual(view_azimuth + 100, view_item.properties["view:azimuth"])

        # Get from Asset
        asset_no_prop = view_item.assets["blue"]
        asset_prop = view_item.assets["red"]
        self.assertEqual(
            ViewExtension.ext(asset_no_prop).azimuth,
            ViewExtension.ext(view_item).azimuth,
        )
        self.assertEqual(ViewExtension.ext(asset_prop).azimuth, 5.0)

        # Set to Asset
        asset_value = 15.0
        ViewExtension.ext(asset_no_prop).azimuth = asset_value
        self.assertNotEqual(
            ViewExtension.ext(asset_no_prop).azimuth,
            ViewExtension.ext(view_item).azimuth,
        )
        self.assertEqual(ViewExtension.ext(asset_no_prop).azimuth, asset_value)

        # Validate
        view_item.validate()

    def test_sun_azimuth(self):
        view_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("view:sun_azimuth", view_item.properties)
        view_sun_azimuth = ViewExtension.ext(view_item).sun_azimuth
        self.assertEqual(view_sun_azimuth, view_item.properties["view:sun_azimuth"])

        # Set
        ViewExtension.ext(view_item).sun_azimuth = view_sun_azimuth + 100
        self.assertEqual(
            view_sun_azimuth + 100, view_item.properties["view:sun_azimuth"]
        )

        # Get from Asset
        asset_no_prop = view_item.assets["blue"]
        asset_prop = view_item.assets["red"]
        self.assertEqual(
            ViewExtension.ext(asset_no_prop).sun_azimuth,
            ViewExtension.ext(view_item).sun_azimuth,
        )
        self.assertEqual(ViewExtension.ext(asset_prop).sun_azimuth, 1.0)

        # Set to Asset
        asset_value = 11.0
        ViewExtension.ext(asset_no_prop).sun_azimuth = asset_value
        self.assertNotEqual(
            ViewExtension.ext(asset_no_prop).sun_azimuth,
            ViewExtension.ext(view_item).sun_azimuth,
        )
        self.assertEqual(ViewExtension.ext(asset_no_prop).sun_azimuth, asset_value)

        # Validate
        view_item.validate()

    def test_sun_elevation(self):
        view_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("view:sun_elevation", view_item.properties)
        view_sun_elevation = ViewExtension.ext(view_item).sun_elevation
        self.assertEqual(view_sun_elevation, view_item.properties["view:sun_elevation"])

        # Set
        ViewExtension.ext(view_item).sun_elevation = view_sun_elevation + 10
        self.assertEqual(
            view_sun_elevation + 10, view_item.properties["view:sun_elevation"]
        )

        # Get from Asset
        asset_no_prop = view_item.assets["blue"]
        asset_prop = view_item.assets["red"]
        self.assertEqual(
            ViewExtension.ext(asset_no_prop).sun_elevation,
            ViewExtension.ext(view_item).sun_elevation,
        )
        self.assertEqual(ViewExtension.ext(asset_prop).sun_elevation, 2.0)

        # Set to Asset
        asset_value = 12.0
        ViewExtension.ext(asset_no_prop).sun_elevation = asset_value
        self.assertNotEqual(
            ViewExtension.ext(asset_no_prop).sun_elevation,
            ViewExtension.ext(view_item).sun_elevation,
        )
        self.assertEqual(ViewExtension.ext(asset_no_prop).sun_elevation, asset_value)

        # Validate
        view_item.validate()
