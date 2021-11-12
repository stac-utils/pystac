import unittest
import pystac
from pystac import ExtensionTypeError
from pystac.extensions.table import TableExtension

from tests.utils import TestCases


class TableTest(unittest.TestCase):
    def setUp(self) -> None:
        self.example_uri = TestCases.get_path("data-files/table/item.json")

    def test_validate(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        item.validate()

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if item does not include extension URI
        item = pystac.Item.from_file(self.example_uri)
        item.stac_extensions.remove(TableExtension.get_schema_uri())

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = TableExtension.ext(item)

        # Should raise exception if owning item does not include extension URI
        asset = item.assets["data"]

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = TableExtension.ext(asset)

        # Should succeed if Asset has no owner
        ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
        _ = TableExtension.ext(ownerless_asset)

    def test_item_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        item.stac_extensions.remove(TableExtension.get_schema_uri())

        _ = TableExtension.ext(item, add_if_missing=True)

        self.assertIn(TableExtension.get_schema_uri(), item.stac_extensions)

    def test_asset_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        item.stac_extensions.remove(TableExtension.get_schema_uri())

        self.assertNotIn(TableExtension.get_schema_uri(), item.stac_extensions)
        asset = item.assets["data"]

        _ = TableExtension.ext(asset, add_if_missing=True)
        self.assertIn(TableExtension.get_schema_uri(), item.stac_extensions)

    def test_should_raise_exception_when_passing_invalid_extension_object(
        self,
    ) -> None:
        self.assertRaisesRegex(
            ExtensionTypeError,
            r"^Table extension does not apply to type 'object'$",
            TableExtension.ext,
            object(),
        )
