import json
from typing import Any, Dict
import unittest

# from copy import deepcopy

import pystac
from pystac.asset import Asset
from pystac.errors import ExtensionTypeError, STACError
from pystac.extensions.pointcloud import (
    AssetPointcloudExtension,
    PointcloudExtension,
    PointcloudSchema,
    PointcloudStatistic,
)
from tests.utils import TestCases, assert_to_from_dict


class PointcloudTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.example_uri = TestCases.get_path("data-files/pointcloud/example-laz.json")
        self.example_uri_no_statistics = TestCases.get_path(
            "data-files/pointcloud/example-laz-no-statistics.json"
        )

    def test_to_from_dict(self) -> None:
        with open(self.example_uri) as f:
            d = json.load(f)
        assert_to_from_dict(self, pystac.Item, d)

    def test_apply(self) -> None:
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

    def test_validate_pointcloud(self) -> None:
        item = pystac.Item.from_file(self.example_uri)
        item.validate()

    def test_count(self) -> None:
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

    def test_type(self) -> None:
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

    def test_encoding(self) -> None:
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

    def test_schemas(self) -> None:
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

    def test_statistics(self) -> None:
        pc_item = pystac.Item.from_file(self.example_uri)

        # Get
        self.assertIn("pc:statistics", pc_item.properties)
        statistics = PointcloudExtension.ext(pc_item).statistics
        assert statistics is not None
        pc_statistics = [s.to_dict() for s in statistics]
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

    def test_density(self) -> None:
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

    def test_pointcloud_schema(self) -> None:
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

        schema = PointcloudSchema.create("intensity", 16, "unsigned")
        self.assertEqual(schema.name, "intensity")
        self.assertEqual(schema.size, 16)
        self.assertEqual(schema.type, "unsigned")

        with self.assertRaises(STACError):
            schema.size = 0.5  # type: ignore

        empty_schema = PointcloudSchema({})
        with self.assertRaises(STACError):
            empty_schema.size
        with self.assertRaises(STACError):
            empty_schema.name
        with self.assertRaises(STACError):
            empty_schema.type

    def test_pointcloud_statistics(self) -> None:
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

        stat = PointcloudStatistic.create("foo", 1, 2, 3, 4, 5, 6, 7)
        self.assertEqual(stat.name, "foo")
        self.assertEqual(stat.position, 1)
        self.assertEqual(stat.average, 2)
        self.assertEqual(stat.count, 3)
        self.assertEqual(stat.maximum, 4)
        self.assertEqual(stat.minimum, 5)
        self.assertEqual(stat.stddev, 6)
        self.assertEqual(stat.variance, 7)

        stat.name = None  # type: ignore
        self.assertNotIn("name", stat.properties)
        stat.position = None
        self.assertNotIn("position", stat.properties)
        stat.average = None
        self.assertNotIn("average", stat.properties)
        stat.count = None
        self.assertNotIn("count", stat.properties)
        stat.maximum = None
        self.assertNotIn("maximum", stat.properties)
        stat.minimum = None
        self.assertNotIn("minimum", stat.properties)
        stat.stddev = None
        self.assertNotIn("stddev", stat.properties)
        stat.variance = None
        self.assertNotIn("variance", stat.properties)

        empty_stat = PointcloudStatistic({})
        with self.assertRaises(STACError):
            empty_stat.name

    def test_statistics_accessor_when_no_stats(self) -> None:
        pc_item = pystac.Item.from_file(self.example_uri_no_statistics)
        self.assertEqual(PointcloudExtension.ext(pc_item).statistics, None)

    def test_asset_extension(self) -> None:
        asset = Asset(
            "https://github.com/PDAL/PDAL/blob"
            "/a6c986f68458e92414a66c664408bee4737bbb08/test/data/laz"
            "/autzen_trim.laz",
            "laz file",
            "The laz data",
            "application/octet-stream",
            ["data"],
            {"foo": "bar"},
        )
        pc_item = pystac.Item.from_file(self.example_uri_no_statistics)
        pc_item.add_asset("data", asset)
        ext = AssetPointcloudExtension(asset)
        self.assertEqual(ext.asset_href, asset.href)
        self.assertEqual(ext.properties, asset.extra_fields)
        self.assertEqual(ext.additional_read_properties, [pc_item.properties])

    def test_ext(self) -> None:
        pc_item = pystac.Item.from_file(self.example_uri_no_statistics)
        PointcloudExtension.ext(pc_item)
        asset = Asset(
            "https://github.com/PDAL/PDAL/blob"
            "/a6c986f68458e92414a66c664408bee4737bbb08/test/data/laz"
            "/autzen_trim.laz",
            "laz file",
            "The laz data",
            "application/octet-stream",
            ["data"],
            {"foo": "bar"},
        )
        PointcloudExtension.ext(asset)

        class RandomObject:
            pass

        self.assertRaisesRegex(
            ExtensionTypeError,
            r"^Pointcloud extension does not apply to type 'RandomObject'$",
            PointcloudExtension.ext,
            RandomObject(),
        )

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Item does not include extension URI
        plain_item_uri = TestCases.get_path("data-files/item/sample-item.json")
        item = pystac.Item.from_file(plain_item_uri)

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = PointcloudExtension.ext(item)

        # Should raise exception if owning Item does not include extension URI
        asset = item.assets["thumbnail"]

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = PointcloudExtension.ext(asset)

        # Should succeed if Asset has no owner
        ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
        _ = PointcloudExtension.ext(ownerless_asset)

    def test_item_ext_add_to(self) -> None:
        plain_item_uri = TestCases.get_path("data-files/item/sample-item.json")
        item = pystac.Item.from_file(plain_item_uri)
        self.assertNotIn(PointcloudExtension.get_schema_uri(), item.stac_extensions)

        _ = PointcloudExtension.ext(item, add_if_missing=True)

        self.assertIn(PointcloudExtension.get_schema_uri(), item.stac_extensions)

    def test_asset_ext_add_to(self) -> None:
        plain_item_uri = TestCases.get_path("data-files/item/sample-item.json")
        item = pystac.Item.from_file(plain_item_uri)
        self.assertNotIn(PointcloudExtension.get_schema_uri(), item.stac_extensions)
        asset = item.assets["thumbnail"]

        _ = PointcloudExtension.ext(asset, add_if_missing=True)

        self.assertIn(PointcloudExtension.get_schema_uri(), item.stac_extensions)
