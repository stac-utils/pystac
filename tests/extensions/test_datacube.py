import unittest
import pystac
from pystac import ExtensionTypeError
from pystac.extensions.datacube import DatacubeExtension

from tests.utils import TestCases


class DatacubeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.example_uri = TestCases.get_path("data-files/datacube/item.json")

    def test_validate_datacube(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        item.validate()

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

    def test_should_raise_exception_when_passing_invalid_extension_object(
        self,
    ) -> None:
        self.assertRaisesRegex(
            ExtensionTypeError,
            r"^Datacube extension does not apply to type 'object'$",
            DatacubeExtension.ext,
            object(),
        )
