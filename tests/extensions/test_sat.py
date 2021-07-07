"""Tests for pystac.extensions.sat."""

import datetime
from pystac.summaries import RangeSummary
from typing import Any, Dict
import unittest

import pystac
from pystac.utils import str_to_datetime, datetime_to_str
from pystac import ExtensionTypeError
from pystac.extensions import sat
from pystac.extensions.sat import OrbitState, SatExtension
from tests.utils import TestCases


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
    def setUp(self) -> None:
        super().setUp()
        self.item = make_item()
        self.sentinel_example_uri = TestCases.get_path("data-files/sat/sentinel-1.json")

    def test_stac_extensions(self) -> None:
        self.assertTrue(SatExtension.has_extension(self.item))

    def test_item_repr(self) -> None:
        sat_item_ext = SatExtension.ext(self.item)
        self.assertEqual(
            f"<ItemSatExtension Item id={self.item.id}>", sat_item_ext.__repr__()
        )

    def test_asset_repr(self) -> None:
        item = pystac.Item.from_file(self.sentinel_example_uri)
        asset = item.assets["measurement_iw1_vh"]
        sat_asset_ext = SatExtension.ext(asset)

        self.assertEqual(
            f"<AssetSatExtension Asset href={asset.href}>", sat_asset_ext.__repr__()
        )

    def test_no_args_fails(self) -> None:
        SatExtension.ext(self.item).apply()
        with self.assertRaises(pystac.STACValidationError):
            self.item.validate()

    def test_orbit_state(self) -> None:
        orbit_state = sat.OrbitState.ASCENDING
        SatExtension.ext(self.item).apply(orbit_state)
        self.assertEqual(orbit_state, SatExtension.ext(self.item).orbit_state)
        self.assertNotIn(sat.RELATIVE_ORBIT_PROP, self.item.properties)
        self.assertIsNone(SatExtension.ext(self.item).relative_orbit)
        self.item.validate()

    def test_relative_orbit(self) -> None:
        relative_orbit = 1234
        SatExtension.ext(self.item).apply(None, relative_orbit)
        self.assertEqual(relative_orbit, SatExtension.ext(self.item).relative_orbit)
        self.assertNotIn(sat.ORBIT_STATE_PROP, self.item.properties)
        self.assertIsNone(SatExtension.ext(self.item).orbit_state)
        self.item.validate()

    def test_absolute_orbit(self) -> None:
        absolute_orbit = 1234
        SatExtension.ext(self.item).apply(absolute_orbit=absolute_orbit)
        self.assertEqual(absolute_orbit, SatExtension.ext(self.item).absolute_orbit)
        self.assertNotIn(sat.RELATIVE_ORBIT_PROP, self.item.properties)
        self.assertIsNone(SatExtension.ext(self.item).relative_orbit)
        self.item.validate()

    def test_anx_datetime(self) -> None:
        anx_datetime = str_to_datetime("2020-01-01T00:00:00Z")
        SatExtension.ext(self.item).apply(anx_datetime=anx_datetime)
        self.assertEqual(anx_datetime, SatExtension.ext(self.item).anx_datetime)
        self.assertNotIn(sat.RELATIVE_ORBIT_PROP, self.item.properties)
        self.assertIsNone(SatExtension.ext(self.item).relative_orbit)
        self.item.validate()

    def test_platform_international_designator(self) -> None:
        platform_international_designator = "2018-080A"
        SatExtension.ext(self.item).apply(
            platform_international_designator=platform_international_designator
        )
        self.assertEqual(
            platform_international_designator,
            SatExtension.ext(self.item).platform_international_designator,
        )
        self.assertNotIn(sat.ORBIT_STATE_PROP, self.item.properties)
        self.assertIsNone(SatExtension.ext(self.item).orbit_state)
        self.item.validate()

    def test_relative_orbit_no_negative(self) -> None:
        negative_relative_orbit = -2
        SatExtension.ext(self.item).apply(None, negative_relative_orbit)
        with self.assertRaises(pystac.STACValidationError):
            self.item.validate()

    def test_both(self) -> None:
        orbit_state = sat.OrbitState.DESCENDING
        relative_orbit = 4321
        SatExtension.ext(self.item).apply(orbit_state, relative_orbit)
        self.assertEqual(orbit_state, SatExtension.ext(self.item).orbit_state)
        self.assertEqual(relative_orbit, SatExtension.ext(self.item).relative_orbit)
        self.item.validate()

    def test_modify(self) -> None:
        SatExtension.ext(self.item).apply(sat.OrbitState.DESCENDING, 999)

        orbit_state = sat.OrbitState.GEOSTATIONARY
        SatExtension.ext(self.item).orbit_state = orbit_state
        relative_orbit = 1000
        SatExtension.ext(self.item).relative_orbit = relative_orbit
        self.assertEqual(orbit_state, SatExtension.ext(self.item).orbit_state)
        self.assertEqual(relative_orbit, SatExtension.ext(self.item).relative_orbit)
        self.item.validate()

    def test_from_dict(self) -> None:
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
            "stac_extensions": [SatExtension.get_schema_uri()],
        }
        item = pystac.Item.from_dict(d)
        self.assertEqual(orbit_state, SatExtension.ext(item).orbit_state)
        self.assertEqual(relative_orbit, SatExtension.ext(item).relative_orbit)

    def test_to_from_dict(self) -> None:
        orbit_state = sat.OrbitState.GEOSTATIONARY
        relative_orbit = 1002
        SatExtension.ext(self.item).apply(orbit_state, relative_orbit)
        d = self.item.to_dict()
        self.assertEqual(orbit_state.value, d["properties"][sat.ORBIT_STATE_PROP])
        self.assertEqual(relative_orbit, d["properties"][sat.RELATIVE_ORBIT_PROP])

        item = pystac.Item.from_dict(d)
        self.assertEqual(orbit_state, SatExtension.ext(item).orbit_state)
        self.assertEqual(relative_orbit, SatExtension.ext(item).relative_orbit)

    def test_clear_orbit_state(self) -> None:
        SatExtension.ext(self.item).apply(sat.OrbitState.DESCENDING, 999)

        SatExtension.ext(self.item).orbit_state = None
        self.assertIsNone(SatExtension.ext(self.item).orbit_state)
        self.item.validate()

    def test_clear_relative_orbit(self) -> None:
        SatExtension.ext(self.item).apply(sat.OrbitState.DESCENDING, 999)

        SatExtension.ext(self.item).relative_orbit = None
        self.assertIsNone(SatExtension.ext(self.item).relative_orbit)
        self.item.validate()

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Item does not include extension URI
        item = pystac.Item.from_file(self.sentinel_example_uri)
        item.stac_extensions.remove(SatExtension.get_schema_uri())

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = SatExtension.ext(item)

        # Should raise exception if owning Item does not include extension URI
        asset = item.assets["measurement_iw1_vh"]

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = SatExtension.ext(asset)

        # Should succeed if Asset has no owner
        ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
        _ = SatExtension.ext(ownerless_asset)

    def test_item_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.sentinel_example_uri)
        item.stac_extensions.remove(SatExtension.get_schema_uri())
        self.assertNotIn(SatExtension.get_schema_uri(), item.stac_extensions)

        _ = SatExtension.ext(item, add_if_missing=True)

        self.assertIn(SatExtension.get_schema_uri(), item.stac_extensions)

    def test_asset_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.sentinel_example_uri)
        item.stac_extensions.remove(SatExtension.get_schema_uri())
        self.assertNotIn(SatExtension.get_schema_uri(), item.stac_extensions)
        asset = item.assets["measurement_iw1_vh"]

        _ = SatExtension.ext(asset, add_if_missing=True)

        self.assertIn(SatExtension.get_schema_uri(), item.stac_extensions)

    def test_should_raise_exception_when_passing_invalid_extension_object(
        self,
    ) -> None:
        self.assertRaisesRegex(
            ExtensionTypeError,
            r"^Satellite extension does not apply to type 'object'$",
            SatExtension.ext,
            object(),
        )


class SatSummariesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    @staticmethod
    def collection() -> pystac.Collection:
        return pystac.Collection.from_file(
            TestCases.get_path("data-files/collections/multi-extent.json")
        )

    def test_platform_international_designation(self) -> None:
        collection = self.collection()
        summaries_ext = SatExtension.summaries(collection)
        platform_international_designator_list = ["2018-080A"]

        summaries_ext.platform_international_designator = ["2018-080A"]

        self.assertEqual(
            summaries_ext.platform_international_designator,
            platform_international_designator_list,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sat:platform_international_designator"],
            platform_international_designator_list,
        )

    def test_orbit_state(self) -> None:
        collection = self.collection()
        summaries_ext = SatExtension.summaries(collection)
        orbit_state_list = [OrbitState.ASCENDING]

        summaries_ext.orbit_state = orbit_state_list

        self.assertEqual(
            summaries_ext.orbit_state,
            orbit_state_list,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sat:orbit_state"],
            orbit_state_list,
        )

    def test_absolute_orbit(self) -> None:
        collection = self.collection()
        summaries_ext = SatExtension.summaries(collection)
        absolute_orbit_range = RangeSummary(2000, 3000)

        summaries_ext.absolute_orbit = absolute_orbit_range

        self.assertEqual(
            summaries_ext.absolute_orbit,
            absolute_orbit_range,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sat:absolute_orbit"],
            absolute_orbit_range.to_dict(),
        )

    def test_relative_orbit(self) -> None:
        collection = self.collection()
        summaries_ext = SatExtension.summaries(collection)
        relative_orbit_range = RangeSummary(50, 100)

        summaries_ext.relative_orbit = relative_orbit_range

        self.assertEqual(
            summaries_ext.relative_orbit,
            relative_orbit_range,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["sat:relative_orbit"],
            relative_orbit_range.to_dict(),
        )

    def test_anx_datetime(self) -> None:
        collection = self.collection()
        summaries_ext = SatExtension.summaries(collection)
        anx_datetime_range = RangeSummary(
            str_to_datetime("2020-01-01T00:00:00.000Z"),
            str_to_datetime("2020-01-02T00:00:00.000Z"),
        )

        summaries_ext.anx_datetime = anx_datetime_range

        self.assertEqual(
            summaries_ext.anx_datetime,
            anx_datetime_range,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertDictEqual(
            summaries_dict["sat:anx_datetime"],
            {
                "minimum": datetime_to_str(anx_datetime_range.minimum),
                "maximum": datetime_to_str(anx_datetime_range.maximum),
            },
        )
