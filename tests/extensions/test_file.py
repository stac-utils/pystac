import json
import unittest

import pystac
from tests.utils import TestCases, test_to_from_dict
from pystac.extensions.file import FileExtension, FileDataType


class FileTest(unittest.TestCase):
    FILE_EXAMPLE_URI = TestCases.get_path("data-files/file/file-example.json")

    def setUp(self):
        self.maxDiff = None

    def test_to_from_dict(self):
        with open(self.FILE_EXAMPLE_URI) as f:
            item_dict = json.load(f)
        test_to_from_dict(self, pystac.Item, item_dict)

    def test_validate_file(self):
        item = pystac.Item.from_file(self.FILE_EXAMPLE_URI)
        item.validate()

    def test_asset_size(self):
        item = pystac.Item.from_file(self.FILE_EXAMPLE_URI)
        asset = item.assets["thumbnail"]

        # Get
        self.assertEqual(146484, FileExtension.ext(asset).size)

        # Set
        new_size = 1
        FileExtension.ext(asset).size = new_size
        self.assertEqual(new_size, FileExtension.ext(asset).size)
        item.validate()

    def test_asset_checksum(self):
        item = pystac.Item.from_file(self.FILE_EXAMPLE_URI)
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

    def test_asset_data_type(self):
        item = pystac.Item.from_file(self.FILE_EXAMPLE_URI)
        asset = item.assets["thumbnail"]

        # Get
        self.assertEqual(FileDataType.UINT8, FileExtension.ext(asset).data_type)

        # Set
        new_data_type = FileDataType.UINT16
        FileExtension.ext(asset).data_type = new_data_type
        self.assertEqual(new_data_type, FileExtension.ext(asset).data_type)
        item.validate()

    def test_asset_nodata(self):
        item = pystac.Item.from_file(self.FILE_EXAMPLE_URI)
        asset = item.assets["thumbnail"]

        # Get
        self.assertEqual([], FileExtension.ext(asset).nodata)

        # Set
        new_nodata = [-1]
        FileExtension.ext(asset).nodata = new_nodata
        self.assertEqual(new_nodata, FileExtension.ext(asset).nodata)
        item.validate()

    def test_migrates_old_checksum(self):
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
