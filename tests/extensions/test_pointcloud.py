import json
from typing import Any, Dict
import unittest

# from copy import deepcopy

import pystac
from pystac.extensions.pointcloud import (
    PointcloudExtension,
    PointcloudSchema,
    PointcloudStatistic,
)
from tests.utils import TestCases, test_to_from_dict


class PointcloudTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.example_uri = TestCases.get_path("data-files/pointcloud/example-laz.json")
        self.example_uri_no_statistics = TestCases.get_path(
            "data-files/pointcloud/example-laz-no-statistics.json"
        )

    def test_to_from_dict(self):
        with open(self.example_uri) as f:
            d = json.load(f)
        test_to_from_dict(self, pystac.Item, d)

    def test_apply(self):
        item = next(iter(TestCases.test_case_2().get_all_items()))

        self.assertFalse(PointcloudExtension.has_extension(item))

        PointcloudExtension.add_to(item)
        PointcloudExtension.ext(item).apply(
            1000,
            "lidar",
            "laszip",
            [PointcloudSchema({"name": "X", "size": 8, "type": "floating"})],
        )
        self.assertTrue(PointcloudExtension.has_extension(item))

    def test_validate_pointcloud(self):
        item = pystac.read_file(self.example_uri)
        item.validate()

    def test_count(self):
        pc_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("pc:count", pc_item.properties)
        pc_count = PointcloudExtension.ext(pc_item).count
        self.assertEqual(pc_count, pc_item.properties["pc:count"])

        # Set
        PointcloudExtension.ext(pc_item).count = pc_count + 100
        self.assertEqual(pc_count + 100, pc_item.properties["pc:count"])

        # Validate
        pc_item.validate()

        # Cannot test validation errors until the pointcloud schema.json syntax is fixed
        # Ensure setting bad count fails validation

        with self.assertRaises(pystac.STACValidationError):
            PointcloudExtension.ext(pc_item).count = "not_an_int"  # type:ignore
            pc_item.validate()

    def test_type(self):
        pc_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("pc:type", pc_item.properties)
        pc_type = PointcloudExtension.ext(pc_item).type
        self.assertEqual(pc_type, pc_item.properties["pc:type"])

        # Set
        PointcloudExtension.ext(pc_item).type = "sonar"
        self.assertEqual("sonar", pc_item.properties["pc:type"])

        # Validate
        pc_item.validate()

    def test_encoding(self):
        pc_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("pc:encoding", pc_item.properties)
        pc_encoding = PointcloudExtension.ext(pc_item).encoding
        self.assertEqual(pc_encoding, pc_item.properties["pc:encoding"])

        # Set
        PointcloudExtension.ext(pc_item).encoding = "binary"
        self.assertEqual("binary", pc_item.properties["pc:encoding"])

        # Validate
        pc_item.validate()

    def test_schemas(self):
        pc_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("pc:schemas", pc_item.properties)
        pc_schemas = [s.to_dict() for s in PointcloudExtension.ext(pc_item).schemas]
        self.assertEqual(pc_schemas, pc_item.properties["pc:schemas"])

        # Set
        schema = [PointcloudSchema({"name": "X", "size": 8, "type": "floating"})]
        PointcloudExtension.ext(pc_item).schemas = schema
        self.assertEqual(
            [s.to_dict() for s in schema], pc_item.properties["pc:schemas"]
        )

        # Validate
        pc_item.validate()

    def test_statistics(self):
        pc_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("pc:statistics", pc_item.properties)
        pc_statistics = [
            s.to_dict() for s in PointcloudExtension.ext(pc_item).statistics
        ]
        self.assertEqual(pc_statistics, pc_item.properties["pc:statistics"])

        # Set
        stats = [
            PointcloudStatistic(
                {
                    "average": 1,
                    "count": 1,
                    "maximum": 1,
                    "minimum": 1,
                    "name": "Test",
                    "position": 1,
                    "stddev": 1,
                    "variance": 1,
                }
            )
        ]
        PointcloudExtension.ext(pc_item).statistics = stats
        self.assertEqual(
            [s.to_dict() for s in stats], pc_item.properties["pc:statistics"]
        )

        # Validate
        pc_item.validate

    def test_density(self):
        pc_item = pystac.Item.from_file(self.example_uri)
        # Get
        self.assertIn("pc:density", pc_item.properties)
        pc_density = PointcloudExtension.ext(pc_item).density
        self.assertEqual(pc_density, pc_item.properties["pc:density"])
        # Set
        density = 100
        PointcloudExtension.ext(pc_item).density = density
        self.assertEqual(density, pc_item.properties["pc:density"])
        # Validate
        pc_item.validate()

    def test_pointcloud_schema(self):
        props: Dict[str, Any] = {
            "name": "test",
            "size": 8,
            "type": "floating",
        }
        schema = PointcloudSchema(props)
        self.assertEqual(props, schema.properties)

        # test all getters and setters
        for k in props:
            if isinstance(props[k], str):
                val = props[k] + str(1)
            else:
                val = props[k] + 1
            setattr(schema, k, val)
            self.assertEqual(getattr(schema, k), val)

    def test_pointcloud_statistics(self):
        props: Dict[str, Any] = {
            "average": 1,
            "count": 1,
            "maximum": 1,
            "minimum": 1,
            "name": "Test",
            "position": 1,
            "stddev": 1,
            "variance": 1,
        }
        stat = PointcloudStatistic(props)
        self.assertEqual(props, stat.properties)

        # test all getters and setters
        for k in props:
            if isinstance(props[k], str):
                val = props[k] + str(1)
            else:
                val = props[k] + 1
            setattr(stat, k, val)
            self.assertEqual(getattr(stat, k), val)

    def test_statistics_accessor_when_no_stats(self):
        pc_item = pystac.Item.from_file(self.example_uri_no_statistics)
        self.assertEqual(PointcloudExtension.ext(pc_item).statistics, None)
