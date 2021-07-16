import json
from typing import Any, Dict
import unittest

# from copy import deepcopy

import pystac
from pystac.asset import Asset
from pystac.errors import ExtensionTypeError, STACError, RequiredPropertyMissing
from pystac.extensions.pointcloud import (
    AssetPointcloudExtension,
    PhenomenologyType,
    PointcloudExtension,
    Schema,
    SchemaType,
    Statistic,
)
from pystac.summaries import RangeSummary
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
            PhenomenologyType.LIDAR,
            "laszip",
            [Schema({"name": "X", "size": 8, "type": "floating"})],
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
        schema = [Schema({"name": "X", "size": 8, "type": "floating"})]
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
            Statistic(
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
        schema = Schema(props)
        self.assertEqual(props, schema.properties)

        # test all getters and setters
        for k in props:
            if isinstance(props[k], str):
                val = props[k] + str(1)
            else:
                val = props[k] + 1
            setattr(schema, k, val)
            self.assertEqual(getattr(schema, k), val)

        schema = Schema.create("intensity", 16, SchemaType.UNSIGNED)
        self.assertEqual(schema.name, "intensity")
        self.assertEqual(schema.size, 16)
        self.assertEqual(schema.type, "unsigned")

        with self.assertRaises(STACError):
            schema.size = 0.5  # type: ignore

        empty_schema = Schema({})
        for required_prop in {"size", "name", "type"}:
            with self.subTest(attr=required_prop):
                with self.assertRaises(RequiredPropertyMissing):
                    getattr(empty_schema, required_prop)

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
        stat = Statistic(props)
        self.assertEqual(props, stat.properties)

        # test all getters and setters
        for k in props:
            if isinstance(props[k], str):
                val = props[k] + str(1)
            else:
                val = props[k] + 1
            setattr(stat, k, val)
            self.assertEqual(getattr(stat, k), val)

        stat = Statistic.create("foo", 1, 2, 3, 4, 5, 6, 7)
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

        empty_stat = Statistic({})
        with self.assertRaises(RequiredPropertyMissing):
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


class PointcloudSummariesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.collection = pystac.Collection.from_file(
            TestCases.get_path("data-files/collections/multi-extent.json")
        )

    def test_count(self) -> None:
        collection = self.collection.clone()
        summaries_ext = PointcloudExtension.summaries(collection, True)
        count_range = RangeSummary(1000, 10000)

        summaries_ext.count = count_range

        self.assertEqual(
            summaries_ext.count,
            count_range,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["pc:count"],
            count_range.to_dict(),
        )

    def test_type(self) -> None:
        collection = self.collection.clone()
        summaries_ext = PointcloudExtension.summaries(collection, True)
        type_list = [PhenomenologyType.LIDAR, "something"]

        summaries_ext.type = type_list

        self.assertEqual(
            summaries_ext.type,
            type_list,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["pc:type"],
            type_list,
        )

    def test_encoding(self) -> None:
        collection = self.collection.clone()
        summaries_ext = PointcloudExtension.summaries(collection, True)
        encoding_list = ["LASzip"]

        summaries_ext.encoding = encoding_list

        self.assertEqual(
            summaries_ext.encoding,
            encoding_list,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["pc:encoding"],
            encoding_list,
        )

    def test_density(self) -> None:
        collection = self.collection.clone()
        summaries_ext = PointcloudExtension.summaries(collection, True)
        density_range = RangeSummary(500.0, 1000.0)

        summaries_ext.density = density_range

        self.assertEqual(
            summaries_ext.density,
            density_range,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["pc:density"],
            density_range.to_dict(),
        )

    def test_statistics(self) -> None:
        collection = self.collection.clone()
        summaries_ext = PointcloudExtension.summaries(collection, True)
        statistics_list = [
            Statistic(
                {
                    "average": 637294.1783,
                    "count": 10653336,
                    "maximum": 639003.73,
                    "minimum": 635577.79,
                    "name": "X",
                    "position": 0,
                    "stddev": 967.9329805,
                    "variance": 936894.2548,
                }
            )
        ]

        summaries_ext.statistics = statistics_list

        self.assertEqual(
            summaries_ext.statistics,
            statistics_list,
        )

        summaries_dict = collection.to_dict()["summaries"]

        self.assertEqual(
            summaries_dict["pc:statistics"],
            [s.to_dict() for s in statistics_list],
        )
