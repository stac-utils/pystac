import json
import unittest

import pystac
from pystac import ExtensionTypeError
from tests.utils import TestCases, assert_to_from_dict
from pystac.extensions.file import FileExtension, ByteOrder, MappingObject


class ByteOrderTest(unittest.TestCase):
    def test_to_str(self) -> None:
        self.assertEqual(ByteOrder.LITTLE_ENDIAN.value, "little-endian")
        self.assertEqual(ByteOrder.BIG_ENDIAN.value, "big-endian")


class MappingObjectTest(unittest.TestCase):
    def test_create(self) -> None:
        values = [0, 1]
        summary = "clouds"
        m = MappingObject.create(values, summary)

        self.assertListEqual(m.values, values)
        self.assertEqual(m.summary, summary)

    def test_set_properties(self) -> None:
        values = [0, 1]
        summary = "clouds"
        m = MappingObject.create(values, summary)

        new_values = [3, 4]
        new_summary = "cloud shadow"
        m.summary = new_summary
        m.values = new_values

        self.assertListEqual(m.values, new_values)
        self.assertEqual(m.summary, new_summary)

    def test_apply(self) -> None:
        values = [0, 1]
        summary = "clouds"
        m = MappingObject.create(values, summary)

        new_values = [3, 4]
        new_summary = "cloud shadow"
        m.apply(new_values, new_summary)

        self.assertListEqual(m.values, new_values)
        self.assertEqual(m.summary, new_summary)


class FileTest(unittest.TestCase):
    FILE_ITEM_EXAMPLE_URI = TestCases.get_path("data-files/file/item.json")
    FILE_COLLECTION_EXAMPLE_URI = TestCases.get_path("data-files/file/collection.json")
    PLAIN_ITEM = TestCases.get_path("data-files/item/sample-item.json")

    def setUp(self) -> None:
        self.maxDiff = None

    def test_to_from_dict(self) -> None:
        with open(self.FILE_ITEM_EXAMPLE_URI) as f:
            item_dict = json.load(f)
        assert_to_from_dict(self, pystac.Item, item_dict)

    def test_validate_item(self) -> None:
        item = pystac.Item.from_file(self.FILE_ITEM_EXAMPLE_URI)
        item.validate()

    def test_validate_collection(self) -> None:
        collection = pystac.Collection.from_file(self.FILE_COLLECTION_EXAMPLE_URI)
        collection.validate()

    def test_item_asset_size(self) -> None:
        item = pystac.Item.from_file(self.FILE_ITEM_EXAMPLE_URI)
        asset = item.assets["thumbnail"]

        # Get
        self.assertEqual(146484, FileExtension.ext(asset).size)

        # Set
        new_size = 1
        FileExtension.ext(asset).size = new_size
        self.assertEqual(new_size, FileExtension.ext(asset).size)
        item.validate()

    def test_item_asset_header_size(self) -> None:
        item = pystac.Item.from_file(self.FILE_ITEM_EXAMPLE_URI)
        asset = item.assets["measurement"]

        # Get
        self.assertEqual(4096, FileExtension.ext(asset).header_size)

        # Set
        new_header_size = 8192
        FileExtension.ext(asset).header_size = new_header_size
        self.assertEqual(new_header_size, FileExtension.ext(asset).header_size)
        item.validate()

    def test_item_asset_checksum(self) -> None:
        item = pystac.Item.from_file(self.FILE_ITEM_EXAMPLE_URI)
        asset = item.assets["thumbnail"]

        # Get
        self.assertEqual(
            "90e40210f52acd32b09769d3b1871b420789456c",
            FileExtension.ext(asset).checksum,
        )

        # Set
        new_checksum = "90e40210163700a8a6501eccd00b6d3b44ddaed0"
        FileExtension.ext(asset).checksum = new_checksum
        self.assertEqual(new_checksum, FileExtension.ext(asset).checksum)
        item.validate()

    def test_item_asset_byte_order(self) -> None:
        # Get
        item = pystac.Item.from_file(self.FILE_ITEM_EXAMPLE_URI)
        asset = item.assets["thumbnail"]
        file_ext = FileExtension.ext(asset)

        self.assertEqual(ByteOrder.BIG_ENDIAN, file_ext.byte_order)

        # Set
        new_byte_order = ByteOrder.LITTLE_ENDIAN
        file_ext.byte_order = new_byte_order

        self.assertEqual(file_ext.byte_order, new_byte_order)

        item.validate()

    def test_item_asset_values(self) -> None:
        # Set/get
        item = pystac.Item.from_file(self.FILE_ITEM_EXAMPLE_URI)
        asset = item.assets["thumbnail"]
        file_ext = FileExtension.ext(asset)
        values = [MappingObject.create([0], summary="clouds")]

        file_ext.values = values

        self.assertEqual(file_ext.values, values)

    def test_item_asset_apply(self) -> None:
        item = pystac.Item.from_file(self.FILE_ITEM_EXAMPLE_URI)
        asset = item.assets["thumbnail"]
        file_ext = FileExtension.ext(asset)

        new_checksum = "90e40210163700a8a6501eccd00b6d3b44ddaed0"
        new_size = 1
        new_header_size = 8192
        new_values = [MappingObject.create([0], summary="clouds")]
        new_byte_order = ByteOrder.LITTLE_ENDIAN

        self.assertNotEqual(file_ext.checksum, new_checksum)
        self.assertNotEqual(file_ext.size, new_size)
        self.assertNotEqual(file_ext.header_size, new_header_size)
        self.assertNotEqual(file_ext.values, new_values)
        self.assertNotEqual(file_ext.byte_order, new_byte_order)

        file_ext.apply(
            byte_order=new_byte_order,
            checksum=new_checksum,
            size=new_size,
            header_size=new_header_size,
            values=new_values,
        )

        self.assertEqual(file_ext.checksum, new_checksum)
        self.assertEqual(file_ext.size, new_size)
        self.assertEqual(file_ext.header_size, new_header_size)
        self.assertEqual(file_ext.values, new_values)
        self.assertEqual(file_ext.byte_order, new_byte_order)

    def test_repr(self) -> None:
        item = pystac.Item.from_file(self.FILE_ITEM_EXAMPLE_URI)
        asset = item.assets["thumbnail"]
        file_ext = FileExtension.ext(asset)

        self.assertEqual(
            file_ext.__repr__(), f"<AssetFileExtension Asset href={asset.href}>"
        )

    def test_migrates_old_checksum(self) -> None:
        example_path = TestCases.get_path(
            "data-files/examples/1.0.0-beta.2/"
            "extensions/checksum/examples/sentinel1.json"
        )
        item = pystac.Item.from_file(example_path)

        self.assertTrue(FileExtension.has_extension(item))
        self.assertEqual(
            FileExtension.ext(item.assets["noises"]).checksum,
            "90e40210a30d1711e81a4b11ef67b28744321659",
        )

    def test_extension_type_error(self) -> None:
        item = pystac.Item.from_file(self.FILE_ITEM_EXAMPLE_URI)

        with self.assertRaises(pystac.ExtensionTypeError):
            _ = FileExtension.ext(item)  # type: ignore

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Item does not include extension URI
        item = pystac.Item.from_file(self.PLAIN_ITEM)
        asset = item.assets["thumbnail"]

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = FileExtension.ext(asset)

        # Should succeed if Asset has no owner
        ownerless_asset = pystac.Asset.from_dict(asset.to_dict())

        _ = FileExtension.ext(ownerless_asset)

    def test_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.PLAIN_ITEM)
        asset = item.assets["thumbnail"]

        self.assertNotIn(FileExtension.get_schema_uri(), item.stac_extensions)

        _ = FileExtension.ext(asset, add_if_missing=True)

        self.assertIn(FileExtension.get_schema_uri(), item.stac_extensions)

    def test_should_raise_exception_when_passing_invalid_extension_object(
        self,
    ) -> None:
        self.assertRaisesRegex(
            ExtensionTypeError,
            r"^File Info extension does not apply to type 'object'$",
            FileExtension.ext,
            object(),
        )
