import json
import os
import unittest
import tempfile

import pystac
from pystac import Catalog, Item, CatalogType
from pystac.extensions.label import (
    LabelExtension,
    LabelClasses,
    LabelCount,
    LabelOverview,
    LabelStatistics,
    LabelType,
    LabelRelType,
)
import pystac.validation
from pystac.utils import get_opt
from tests.utils import TestCases, assert_to_from_dict


class LabelTypeTest(unittest.TestCase):
    def test_to_str(self) -> None:
        self.assertEqual(str(LabelType.VECTOR), "vector")
        self.assertEqual(str(LabelType.RASTER), "raster")


class LabelRelTypeTest(unittest.TestCase):
    def test_rel_types(self) -> None:
        self.assertEqual(str(LabelRelType.SOURCE), "source")


class LabelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.label_example_1_uri = TestCases.get_path(
            "data-files/label/label-example-1.json"
        )
        self.label_example_2_uri = TestCases.get_path(
            "data-files/label/label-example-2.json"
        )

    def test_to_from_dict(self) -> None:
        with open(self.label_example_1_uri, encoding="utf-8") as f:
            label_example_1_dict = json.load(f)

        assert_to_from_dict(self, Item, label_example_1_dict)

    def test_from_file(self) -> None:
        label_example_1 = Item.from_file(self.label_example_1_uri)

        overviews = get_opt(LabelExtension.ext(label_example_1).label_overviews)
        self.assertEqual(len(get_opt(overviews[0].counts)), 2)
        label_example_1.validate()

        label_example_2 = Item.from_file(self.label_example_2_uri)
        overviews2 = get_opt(LabelExtension.ext(label_example_2).label_overviews)
        self.assertEqual(len(get_opt(overviews2[0].counts)), 2)

        label_example_2.validate()

    def test_from_file_pre_081(self) -> None:
        d = pystac.StacIO.default().read_json(self.label_example_1_uri)

        d["stac_version"] = "0.8.0-rc1"
        d["properties"]["label:property"] = d["properties"]["label:properties"]
        d["properties"].pop("label:properties")
        d["properties"]["label:overview"] = d["properties"]["label:overviews"]
        d["properties"].pop("label:overviews")
        d["properties"]["label:method"] = d["properties"]["label:methods"]
        d["properties"].pop("label:methods")
        d["properties"]["label:task"] = d["properties"]["label:tasks"]
        d["properties"].pop("label:tasks")
        label_example_1 = pystac.Item.from_dict(d, migrate=True)

        self.assertEqual(len(LabelExtension.ext(label_example_1).label_tasks or []), 2)

    def test_get_sources(self) -> None:
        cat = TestCases.test_case_1()

        items = cat.get_all_items()
        item_ids = set([i.id for i in items])

        for li in items:
            if LabelExtension.ext(li).has_extension:
                sources = list(LabelExtension.ext(li).get_sources() or [])
                self.assertEqual(len(sources), 1)
                self.assertTrue(sources[0].id in item_ids)

    def test_validate_label(self) -> None:
        with open(self.label_example_1_uri, encoding="utf-8") as f:
            label_example_1_dict = json.load(f)
        pystac.validation.validate_dict(
            label_example_1_dict, pystac.STACObjectType.ITEM
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            cat_dir = os.path.join(tmp_dir, "catalog")
            catalog = TestCases.test_case_1()
            catalog.normalize_and_save(cat_dir, catalog_type=CatalogType.SELF_CONTAINED)

            cat_read = Catalog.from_file(os.path.join(cat_dir, "catalog.json"))
            label_item_read = cat_read.get_item("area-2-2-labels", recursive=True)
            assert label_item_read is not None
            label_item_read.validate()

    def test_read_label_item_owns_asset(self) -> None:
        item = next(
            x
            for x in TestCases.test_case_2().get_all_items()
            if LabelExtension.ext(x).has_extension
        )
        assert len(item.assets) > 0
        for asset_key in item.assets:
            self.assertEqual(item.assets[asset_key].owner, item)

    def test_label_description(self) -> None:
        label_item = pystac.Item.from_file(self.label_example_1_uri)

        # Get
        self.assertIn("label:description", label_item.properties)
        label_desc = LabelExtension.ext(label_item).label_description
        self.assertEqual(label_desc, label_item.properties["label:description"])

        # Set
        LabelExtension.ext(label_item).label_description = "A detailed description"
        self.assertEqual(
            "A detailed description", label_item.properties["label:description"]
        )
        label_item.validate()

    def test_label_type(self) -> None:
        label_item = pystac.Item.from_file(self.label_example_1_uri)

        # Get
        self.assertIn("label:type", label_item.properties)
        label_type = LabelExtension.ext(label_item).label_type
        self.assertEqual(label_type, label_item.properties["label:type"])

        # Set
        LabelExtension.ext(label_item).label_type = LabelType.RASTER
        self.assertEqual(LabelType.RASTER, label_item.properties["label:type"])
        label_item.validate()

    def test_label_properties(self) -> None:
        label_item = pystac.Item.from_file(self.label_example_1_uri)
        label_item2 = pystac.Item.from_file(self.label_example_2_uri)

        # Get
        self.assertIn("label:properties", label_item.properties)
        label_prop = LabelExtension.ext(label_item).label_properties
        self.assertEqual(label_prop, label_item.properties["label:properties"])
        raster_label_prop = LabelExtension.ext(label_item2).label_properties
        self.assertEqual(raster_label_prop, None)

        # Set
        LabelExtension.ext(label_item).label_properties = ["prop1", "prop2"]
        self.assertEqual(["prop1", "prop2"], label_item.properties["label:properties"])
        label_item.validate()

    def test_label_classes(self) -> None:
        # Get
        label_item = pystac.Item.from_file(self.label_example_1_uri)
        label_classes = LabelExtension.ext(label_item).label_classes

        self.assertEqual(len(get_opt(label_classes)), 2)
        self.assertEqual(get_opt(label_classes)[1].classes, ["three", "four"])

        # Set
        new_classes = [
            LabelClasses.create(name="label2", classes=["five", "six"]),
            LabelClasses.create(name="label", classes=["seven", "eight"]),
        ]

        label_ext = LabelExtension.ext(label_item)
        label_ext.label_classes = new_classes
        self.assertEqual(
            [
                class_name
                for lc in label_item.properties["label:classes"]
                for class_name in lc["classes"]
            ],
            ["five", "six", "seven", "eight"],
        )

        self.assertListEqual(
            [lc.name for lc in label_ext.label_classes], ["label2", "label"]
        )

        first_lc = label_ext.label_classes[0]
        self.assertEqual("<ClassObject classes=five,six>", first_lc.__repr__())

        label_item.validate()

    def test_label_tasks(self) -> None:
        label_item = pystac.Item.from_file(self.label_example_1_uri)

        # Get
        self.assertIn("label:tasks", label_item.properties)
        label_prop = LabelExtension.ext(label_item).label_tasks
        self.assertEqual(label_prop, ["classification", "regression"])

        # Set
        LabelExtension.ext(label_item).label_tasks = ["classification"]
        self.assertEqual(["classification"], label_item.properties["label:tasks"])
        label_item.validate()

    def test_label_methods(self) -> None:
        label_item = pystac.Item.from_file(self.label_example_1_uri)

        # Get
        self.assertIn("label:methods", label_item.properties)
        label_prop = LabelExtension.ext(label_item).label_methods
        self.assertEqual(label_prop, ["manual"])

        # Set
        LabelExtension.ext(label_item).label_methods = ["manual", "automated"]
        self.assertEqual(
            ["manual", "automated"], label_item.properties["label:methods"]
        )
        label_item.validate()

    def test_label_overviews(self) -> None:
        # Get
        label_item = pystac.Item.from_file(self.label_example_1_uri)
        label_ext = LabelExtension.ext(label_item)
        label_overviews = get_opt(label_ext.label_overviews)

        label_item2 = pystac.Item.from_file(self.label_example_2_uri)
        label_ext2 = LabelExtension.ext(label_item2)
        label_overviews2 = get_opt(label_ext2.label_overviews)

        self.assertEqual(len(label_overviews), 2)
        self.assertEqual(label_overviews[1].property_key, "label-reg")
        self.assertEqual(label_overviews2[1].property_key, None)  # Raster

        label_counts = get_opt(label_overviews[0].counts)
        self.assertEqual(label_counts[1].count, 17)
        first_overview_counts = get_opt(label_ext.label_overviews)[0].counts
        assert first_overview_counts is not None
        first_overview_counts[1].count = 18
        self.assertEqual(
            label_item.properties["label:overviews"][0]["counts"][1]["count"], 18
        )
        self.assertEqual(first_overview_counts[1].name, "two")

        label_statistics = get_opt(label_overviews[1].statistics)
        self.assertEqual(label_statistics[0].name, "mean")
        second_overview_statistics = get_opt(label_ext.label_overviews)[1].statistics
        assert second_overview_statistics is not None
        second_overview_statistics[0].name = "avg"
        self.assertEqual(
            label_item.properties["label:overviews"][1]["statistics"][0]["name"], "avg"
        )

        # Set
        new_overviews = [
            LabelOverview.create(
                property_key="label2",
                counts=[
                    LabelCount.create(name="one", count=1),
                    LabelCount.create(name="two", count=1),
                ],
            ),
            LabelOverview.create(
                property_key="label-reg",
                statistics=[
                    LabelStatistics.create(name="min", value=0.1),
                    LabelStatistics.create(name="max", value=1.0),
                ],
            ),
        ]

        label_ext.label_overviews = new_overviews
        self.assertEqual(
            [
                (count["name"], count["count"])
                for count in label_item.properties["label:overviews"][0]["counts"]
            ],
            [("one", 1), ("two", 1)],
        )

        self.assertEqual(
            [
                (count["name"], count["value"])
                for count in label_item.properties["label:overviews"][1]["statistics"]
            ],
            [("min", 0.1), ("max", 1.0)],
        )

        label_item.validate()

    def test_merge_label_overviews(self) -> None:

        overview_1 = LabelOverview.create(
            property_key="label",
            counts=[
                LabelCount.create(name="water", count=25),
                LabelCount.create(name="land", count=17),
            ],
        )
        overview_2 = LabelOverview.create(
            property_key="label",
            counts=[
                LabelCount.create(name="water", count=10),
                LabelCount.create(name="unknown", count=4),
            ],
        )
        merged_overview = overview_1.merge_counts(overview_2)

        merged_counts = get_opt(merged_overview.counts)

        water_count = next(c for c in merged_counts if c.name == "water")
        land_count = next(c for c in merged_counts if c.name == "land")
        unknown_count = next(c for c in merged_counts if c.name == "unknown")

        self.assertEqual(35, water_count.count)
        self.assertEqual(17, land_count.count)
        self.assertEqual(4, unknown_count.count)

    def test_merge_label_overviews_empty_counts(self) -> None:
        # Right side is empty
        overview_1 = LabelOverview.create(
            property_key="label",
            counts=[
                LabelCount.create(name="water", count=25),
                LabelCount.create(name="land", count=17),
            ],
        )
        overview_2 = LabelOverview.create(
            property_key="label",
            counts=None,
        )

        merged_overview_1 = overview_1.merge_counts(overview_2)
        expected_counts = [c.to_dict() for c in get_opt(overview_1.counts)]
        actual_counts = [c.to_dict() for c in get_opt(merged_overview_1.counts)]
        self.assertListEqual(expected_counts, actual_counts)

        # Left side is empty
        merged_overview_2 = overview_2.merge_counts(overview_1)
        expected_counts = [c.to_dict() for c in get_opt(overview_1.counts)]
        actual_counts = [c.to_dict() for c in get_opt(merged_overview_2.counts)]
        self.assertEqual(expected_counts, actual_counts)

    def test_merge_label_overviews_error(self) -> None:
        overview_1 = LabelOverview.create(
            property_key="label",
            counts=[
                LabelCount.create(name="water", count=25),
                LabelCount.create(name="land", count=17),
            ],
        )
        overview_2 = LabelOverview.create(
            property_key="not label",
            counts=[
                LabelCount.create(name="water", count=10),
                LabelCount.create(name="unknown", count=4),
            ],
        )

        with self.assertRaises(AssertionError):
            _ = overview_1.merge_counts(overview_2)

    def test_extension_type_error(self) -> None:
        collection = pystac.Collection.from_file(
            TestCases.get_path("data-files/collections/with-assets.json")
        )
        with self.assertRaises(pystac.ExtensionTypeError):
            _ = LabelExtension.ext(collection)  # type: ignore

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Item does not include extension URI
        item = pystac.Item.from_file(self.label_example_1_uri)
        item.stac_extensions.remove(LabelExtension.get_schema_uri())

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = LabelExtension.ext(item)

    def test_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.label_example_1_uri)
        item.stac_extensions.remove(LabelExtension.get_schema_uri())
        self.assertNotIn(LabelExtension.get_schema_uri(), item.stac_extensions)

        _ = LabelExtension.ext(item, add_if_missing=True)

        self.assertIn(LabelExtension.get_schema_uri(), item.stac_extensions)
