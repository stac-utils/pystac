import json

from pystac import ExtensionTypeError
from pystac.collection import Collection
import unittest

import pystac
from pystac.summaries import RangeSummary
from pystac.extensions.view import ViewExtension
from tests.utils import TestCases, assert_to_from_dict


class ViewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.example_uri = TestCases.get_path("data-files/view/example-landsat8.json")

    def test_to_from_dict(self) -> None:
        with open(self.example_uri) as f:
            d = json.load(f)
        assert_to_from_dict(self, pystac.Item, d)

    def test_apply(self) -> None:
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

    def test_validate_view(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        self.assertTrue(ViewExtension.has_extension(item))
        item.validate()

    def test_off_nadir(self) -> None:
        view_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("view:off_nadir", view_item.properties)
        view_off_nadir = ViewExtension.ext(view_item).off_nadir
        assert view_off_nadir is not None
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

    def test_incidence_angle(self) -> None:
        view_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("view:incidence_angle", view_item.properties)
        view_incidence_angle = ViewExtension.ext(view_item).incidence_angle
        assert view_incidence_angle is not None
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

    def test_azimuth(self) -> None:
        view_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("view:azimuth", view_item.properties)
        view_azimuth = ViewExtension.ext(view_item).azimuth
        assert view_azimuth is not None
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

    def test_sun_azimuth(self) -> None:
        view_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("view:sun_azimuth", view_item.properties)
        view_sun_azimuth = ViewExtension.ext(view_item).sun_azimuth
        assert view_sun_azimuth is not None
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

    def test_sun_elevation(self) -> None:
        view_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("view:sun_elevation", view_item.properties)
        view_sun_elevation = ViewExtension.ext(view_item).sun_elevation
        assert view_sun_elevation is not None
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

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Item does not include extension URI
        item = pystac.Item.from_file(self.example_uri)
        item.stac_extensions.remove(ViewExtension.get_schema_uri())

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = ViewExtension.ext(item)

        # Should raise exception if owning Item does not include extension URI
        asset = item.assets["blue"]

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = ViewExtension.ext(asset)

        # Should succeed if Asset has no owner
        ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
        _ = ViewExtension.ext(ownerless_asset)

    def test_item_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        item.stac_extensions.remove(ViewExtension.get_schema_uri())
        self.assertNotIn(ViewExtension.get_schema_uri(), item.stac_extensions)

        _ = ViewExtension.ext(item, add_if_missing=True)

        self.assertIn(ViewExtension.get_schema_uri(), item.stac_extensions)

    def test_asset_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        item.stac_extensions.remove(ViewExtension.get_schema_uri())
        self.assertNotIn(ViewExtension.get_schema_uri(), item.stac_extensions)
        asset = item.assets["blue"]

        _ = ViewExtension.ext(asset, add_if_missing=True)

        self.assertIn(ViewExtension.get_schema_uri(), item.stac_extensions)

    def test_should_raise_exception_when_passing_invalid_extension_object(
        self,
    ) -> None:
        self.assertRaisesRegex(
            ExtensionTypeError,
            r"^View extension does not apply to type 'object'$",
            ViewExtension.ext,
            object(),
        )


class ViewSummariesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        example_uri = TestCases.get_path(
            "data-files/view/collection-with-summaries.json"
        )
        self.collection = Collection.from_file(example_uri)

    def test_get_off_nadir_summaries(self) -> None:
        off_nadirs = ViewExtension.summaries(self.collection).off_nadir

        assert off_nadirs is not None

        self.assertDictEqual({"minimum": 0.5, "maximum": 7.3}, off_nadirs.to_dict())

    def test_get_incidence_angle_summaries(self) -> None:
        incidence_angles = ViewExtension.summaries(self.collection).incidence_angle

        assert incidence_angles is not None

        self.assertDictEqual({"minimum": 23, "maximum": 35}, incidence_angles.to_dict())

    def test_get_azimuth_summaries(self) -> None:
        azimuths = ViewExtension.summaries(self.collection).azimuth

        assert azimuths is not None

        self.assertDictEqual({"minimum": 20, "maximum": 186}, azimuths.to_dict())

    def test_get_sun_azimuth_summaries(self) -> None:
        sun_azimuths = ViewExtension.summaries(self.collection).sun_azimuth

        assert sun_azimuths is not None

        self.assertDictEqual({"minimum": 48, "maximum": 78}, sun_azimuths.to_dict())

    def test_get_sun_elevation_summaries(self) -> None:
        sun_elevations = ViewExtension.summaries(self.collection).sun_elevation

        assert sun_elevations is not None

        self.assertDictEqual({"minimum": 10, "maximum": 45}, sun_elevations.to_dict())

    def test_set_off_nadir_summaries(self) -> None:
        collection = self.collection.clone()
        view_summaries = ViewExtension.summaries(collection)

        view_summaries.off_nadir = RangeSummary(0, 10)
        self.assertDictEqual(
            {"minimum": 0, "maximum": 10}, view_summaries.off_nadir.to_dict()
        )

    def test_set_incidence_angle_summaries(self) -> None:
        collection = self.collection.clone()
        view_summaries = ViewExtension.summaries(collection)

        view_summaries.incidence_angle = RangeSummary(5, 15)
        self.assertDictEqual(
            {"minimum": 5, "maximum": 15}, view_summaries.incidence_angle.to_dict()
        )

    def test_set_azimuth_summaries(self) -> None:
        collection = self.collection.clone()
        view_summaries = ViewExtension.summaries(collection)

        view_summaries.azimuth = None
        self.assertIsNone(view_summaries.azimuth)

    def test_set_sun_azimuth_summaries(self) -> None:
        collection = self.collection.clone()
        view_summaries = ViewExtension.summaries(collection)

        view_summaries.sun_azimuth = RangeSummary(210, 275)
        self.assertDictEqual(
            {"minimum": 210, "maximum": 275}, view_summaries.sun_azimuth.to_dict()
        )

    def test_set_sun_elevation_summaries(self) -> None:
        collection = self.collection.clone()
        view_summaries = ViewExtension.summaries(collection)

        view_summaries.sun_elevation = RangeSummary(-10, 38)
        self.assertDictEqual(
            {"minimum": -10, "maximum": 38}, view_summaries.sun_elevation.to_dict()
        )
