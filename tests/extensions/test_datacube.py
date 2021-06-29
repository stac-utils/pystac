from typing import cast
import unittest
import pystac
from pystac.extensions.datacube import (
    AdditionalDimension,
    DatacubeExtension,
    VerticalSpatialDimension,
)

from tests.utils import TestCases


class DatacubeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.example_uri = TestCases.get_path("data-files/datacube/item.json")

    def test_validate_datacube(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        item.validate()

    def test_get_set(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        item.validate()
        ext = DatacubeExtension.ext(item)
        dim = ext.dimensions["x"]

        self.assertEqual(dim.dim_type, "spatial")

        spectral = ext.dimensions["spectral"]
        spectral = cast(AdditionalDimension, spectral)

        self.assertEqual(spectral.values, ["red", "green", "blue"])

        del dim.properties["type"]

        with self.assertRaises(pystac.errors.RequiredPropertyMissing):
            dim.dim_type

        dim.dim_type = "spatial"
        dim.description = None

        self.assertNotIn("description", dim.properties)
        dim.dim_type = None  # type: ignore
        self.assertIn("type", dim.properties)

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Item does not include extension URI
        item = pystac.Item.from_file(self.example_uri)
        item.stac_extensions.remove(DatacubeExtension.get_schema_uri())

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = DatacubeExtension.ext(item)

        # Should raise exception if owning Item does not include extension URI
        asset = item.assets["data"]

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = DatacubeExtension.ext(asset)

        # Should succeed if Asset has no owner
        ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
        _ = DatacubeExtension.ext(ownerless_asset)

    def test_item_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        item.stac_extensions.remove(DatacubeExtension.get_schema_uri())
        self.assertNotIn(DatacubeExtension.get_schema_uri(), item.stac_extensions)

        _ = DatacubeExtension.ext(item, add_if_missing=True)

        self.assertIn(DatacubeExtension.get_schema_uri(), item.stac_extensions)

    def test_asset_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        item.stac_extensions.remove(DatacubeExtension.get_schema_uri())
        self.assertNotIn(DatacubeExtension.get_schema_uri(), item.stac_extensions)
        asset = item.assets["data"]

        _ = DatacubeExtension.ext(asset, add_if_missing=True)

        self.assertIn(DatacubeExtension.get_schema_uri(), item.stac_extensions)

    def test_clear_step(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        ext = DatacubeExtension.ext(item)
        dim = ext.dimensions["pressure_levels"]
        self.assertIsInstance(dim, VerticalSpatialDimension)

        dim = cast(VerticalSpatialDimension, dim)
        self.assertEqual(dim.step, 100)
        dim.step = None
        self.assertIn("step", dim.properties)
        dim.clear_step()
        self.assertNotIn("step", dim.properties)
