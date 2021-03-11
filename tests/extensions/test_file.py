import json
import unittest

import pystac
from pystac import Item
from tests.utils import (TestCases, test_to_from_dict)
from pystac.extensions.file import FileDataType


class FileTest(unittest.TestCase):
    FILE_EXAMPLE_URI = TestCases.get_path('data-files/file/file-example.json')

    def setUp(self):
        self.maxDiff = None

    def test_to_from_dict(self):
        with open(self.FILE_EXAMPLE_URI) as f:
            item_dict = json.load(f)
        test_to_from_dict(self, Item, item_dict)

    def test_validate_file(self):
        item = pystac.read_file(self.FILE_EXAMPLE_URI)
        item.validate()

    def test_asset_size(self):
        item = pystac.read_file(self.FILE_EXAMPLE_URI)
        asset = item.assets["thumbnail"]

        # Get
        self.assertEqual(146484, item.ext.file.get_size(asset))

        # Set
        new_size = 1
        item.ext.file.set_size(new_size, asset)
        self.assertEqual(new_size, item.ext.file.get_size(asset))
        item.validate()

    def test_asset_checksum(self):
        item = pystac.read_file(self.FILE_EXAMPLE_URI)
        asset = item.assets["thumbnail"]

        # Get
        self.assertEqual("90e40210f52acd32b09769d3b1871b420789456c",
                         item.ext.file.get_checksum(asset))

        # Set
        new_checksum = "90e40210163700a8a6501eccd00b6d3b44ddaed0"
        item.ext.file.set_checksum(new_checksum, asset)
        self.assertEqual(new_checksum, item.ext.file.get_checksum(asset))
        item.validate()

    def test_asset_data_type(self):
        item = pystac.read_file(self.FILE_EXAMPLE_URI)
        asset = item.assets["thumbnail"]

        # Get
        self.assertEqual(FileDataType.UINT8, item.ext.file.get_data_type(asset))

        # Set
        new_data_type = FileDataType.UINT16
        item.ext.file.set_data_type(new_data_type, asset)
        self.assertEqual(new_data_type, item.ext.file.get_data_type(asset))
        item.validate()

    def test_asset_nodata(self):
        item = pystac.read_file(self.FILE_EXAMPLE_URI)
        asset = item.assets["thumbnail"]

        # Get
        self.assertEqual([], item.ext.file.get_nodata(asset))

        # Set
        new_nodata = [-1]
        item.ext.file.set_nodata(new_nodata, asset)
        self.assertEqual(new_nodata, item.ext.file.get_nodata(asset))
        item.validate()
