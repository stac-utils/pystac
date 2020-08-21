import json
import unittest
# from copy import deepcopy

import pystac
from pystac import (Item, Extensions)
from pystac.extensions import ExtensionError
from tests.utils import (TestCases, test_to_from_dict)


class PointcloudTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.example_uri = TestCases.get_path('data-files/pointcloud/example-laz.json')

    def test_to_from_dict(self):
        with open(self.example_uri) as f:
            d = json.load(f)
        test_to_from_dict(self, Item, d)

    def test_apply(self):
        item = next(TestCases.test_case_2().get_all_items())
        with self.assertRaises(ExtensionError):
            item.ext.pointcloud

        item.ext.enable(Extensions.POINTCLOUD)
        item.ext.pointcloud.apply(1000, 'lidar', 'laszip', {
            'name': 'X',
            'size': 8,
            'type': 'floating'
        })

    def test_validate_pointcloud(self):
        item = pystac.read_file(self.example_uri)
        item.validate()

    def test_count(self):
        pc_item = pystac.read_file(self.example_uri)

        # Get
        self.assertIn("pc:count", pc_item.properties)
        pc_count = pc_item.ext.pointcloud.count
        self.assertEqual(pc_count, pc_item.properties['pc:count'])

        # Set
        pc_item.ext.pointcloud.count = pc_count + 100
        self.assertEqual(pc_count + 100, pc_item.properties['pc:count'])

        # Validate
        pc_item.validate

        # Cannot text validation errors until the pointcloud schema.json syntax is fixed
        # Ensure setting bad count fails validation
        # with self.assertRaises(STACValidationError):
        #    pc_item.ext.pointcloud.count = 'not_an_int'
        #    pc_item.validate()

    def test_type(self):
        pc_item = pystac.read_file(self.example_uri)

        # Get
        self.assertIn("pc:type", pc_item.properties)
        pc_type = pc_item.ext.pointcloud.type
        self.assertEqual(pc_type, pc_item.properties['pc:type'])

        # Set
        pc_item.ext.pointcloud.type = 'sonar'
        self.assertEqual('sonar', pc_item.properties['pc:type'])

        # Validate
        pc_item.validate

    def test_encoding(self):
        pc_item = pystac.read_file(self.example_uri)

        # Get
        self.assertIn("pc:encoding", pc_item.properties)
        pc_encoding = pc_item.ext.pointcloud.encoding
        self.assertEqual(pc_encoding, pc_item.properties['pc:encoding'])

        # Set
        pc_item.ext.pointcloud.encoding = 'binary'
        self.assertEqual('binary', pc_item.properties['pc:encoding'])

        # Validate
        pc_item.validate

    def test_schemas(self):
        pc_item = pystac.read_file(self.example_uri)

        # Get
        self.assertIn("pc:schemas", pc_item.properties)
        pc_schemas = pc_item.ext.pointcloud.schemas
        self.assertEqual(pc_schemas, pc_item.properties['pc:schemas'])

        # Set
        schema = [{'name': 'X', 'size': 8, 'type': 'floating'}]
        pc_item.ext.pointcloud.schemas = schema
        self.assertEqual(schema, pc_item.properties['pc:schemas'])

        # Validate
        pc_item.validate
