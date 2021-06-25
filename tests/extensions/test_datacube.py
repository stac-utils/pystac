from typing import cast
import unittest
import pystac
from pystac.extensions.datacube import AdditionalDimension, DatacubeExtension

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

        assert dim.dim_type == "spatial"

        spectral = ext.dimensions["spectral"]
        spectral = cast(AdditionalDimension, spectral)

        assert spectral.values == ["red", "green", "blue"]

        del dim.properties["type"]

        with self.assertRaises(pystac.errors.RequiredPropertyMissing):
            dim.dim_type

        dim.dim_type = "spatial"
        dim.description = None

        assert "description" not in dim.properties
        dim.dim_type = None  # type: ignore
        assert "type" in dim.properties

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
        assert isinstance(dim, AdditionalDimension)

        assert dim.step == 100
        dim.step = None
        assert "step" in dim.properties
        dim.clear_step()
        assert "step" not in dim.properties
