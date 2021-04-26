import json
import unittest

import pystac as ps
from tests.utils import (TestCases, test_to_from_dict)
from pystac.extensions import file_ext
from pystac.extensions.file import FileDataType


class FileTest(unittest.TestCase):
    FILE_EXAMPLE_URI = TestCases.get_path('data-files/file/file-example.json')

    def setUp(self):
        self.maxDiff = None

    def test_to_from_dict(self):
        with open(self.FILE_EXAMPLE_URI) as f:
            item_dict = json.load(f)
        test_to_from_dict(self, ps.Item, item_dict)

    def test_validate_file(self):
        item = ps.Item.from_file(self.FILE_EXAMPLE_URI)
        item.validate()

    def test_asset_size(self):
        item = ps.Item.from_file(self.FILE_EXAMPLE_URI)
        asset = item.assets["thumbnail"]

        # Get
        self.assertEqual(146484, file_ext(asset).size)

        # Set
        new_size = 1
        file_ext(asset).size = new_size
        self.assertEqual(new_size, file_ext(asset).size)
        item.validate()

    def test_asset_checksum(self):
        item = ps.Item.from_file(self.FILE_EXAMPLE_URI)
        asset = item.assets["thumbnail"]

        # Get
        self.assertEqual("90e40210f52acd32b09769d3b1871b420789456c",
                         file_ext(asset).checksum)

        # Set
        new_checksum = "90e40210163700a8a6501eccd00b6d3b44ddaed0"
        file_ext(asset).checksum = new_checksum
        self.assertEqual(new_checksum, file_ext(asset).checksum)
        item.validate()

    def test_asset_data_type(self):
        item = ps.Item.from_file(self.FILE_EXAMPLE_URI)
        asset = item.assets["thumbnail"]

        # Get
        self.assertEqual(FileDataType.UINT8, file_ext(asset).data_type)

        # Set
        new_data_type = FileDataType.UINT16
        file_ext(asset).data_type = new_data_type
        self.assertEqual(new_data_type, file_ext(asset).data_type)
        item.validate()

    def test_asset_nodata(self):
        item = ps.Item.from_file(self.FILE_EXAMPLE_URI)
        asset = item.assets["thumbnail"]

        # Get
        self.assertEqual([], file_ext(asset).nodata)

        # Set
        new_nodata = [-1]
        file_ext(asset).nodata = new_nodata
        self.assertEqual(new_nodata, file_ext(asset).nodata)
        item.validate()
