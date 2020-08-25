import json
import os
import unittest
from tempfile import TemporaryDirectory

import pystac
from pystac import (Catalog, Item, CatalogType, STAC_IO)
from pystac.extensions import label
from tests.utils import (TestCases, test_to_from_dict)


class LabelTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.label_example_1_uri = TestCases.get_path('data-files/label/label-example-1.json')
        self.label_example_2_uri = TestCases.get_path('data-files/label/label-example-2.json')

    def test_to_from_dict(self):
        with open(self.label_example_1_uri) as f:
            label_example_1_dict = json.load(f)

        test_to_from_dict(self, Item, label_example_1_dict)

    def test_from_file(self):
        label_example_1 = Item.from_file(self.label_example_1_uri)

        self.assertEqual(len(label_example_1.ext.label.label_overviews[0].counts), 2)
        label_example_1.validate()

        label_example_2 = Item.from_file(self.label_example_2_uri)
        self.assertEqual(len(label_example_2.ext.label.label_overviews[0].counts), 2)

        label_example_2.validate()

    def test_from_file_pre_081(self):
        d = STAC_IO.read_json(self.label_example_1_uri)

        d['stac_version'] = '0.8.0-rc1'
        d['properties']['label:property'] = d['properties']['label:properties']
        d['properties'].pop('label:properties')
        d['properties']['label:overview'] = d['properties']['label:overviews']
        d['properties'].pop('label:overviews')
        d['properties']['label:method'] = d['properties']['label:methods']
        d['properties'].pop('label:methods')
        d['properties']['label:task'] = d['properties']['label:tasks']
        d['properties'].pop('label:tasks')
        label_example_1 = STAC_IO.stac_object_from_dict(d)

        self.assertEqual(len(label_example_1.ext.label.label_tasks), 2)

    def test_get_sources(self):
        cat = TestCases.test_case_1()

        items = cat.get_all_items()
        item_ids = set([i.id for i in items])

        for li in items:
            if li.ext.implements('label'):
                sources = li.ext.label.get_sources()
                self.assertEqual(len(sources), 1)
                self.assertTrue(sources[0].id in item_ids)

    def test_validate_label(self):
        with open(self.label_example_1_uri) as f:
            label_example_1_dict = json.load(f)
        pystac.validation.validate_dict(label_example_1_dict, "ITEM")

        with TemporaryDirectory() as tmp_dir:
            cat_dir = os.path.join(tmp_dir, 'catalog')
            catalog = TestCases.test_case_1()
            catalog.normalize_and_save(cat_dir, catalog_type=CatalogType.SELF_CONTAINED)

            cat_read = Catalog.from_file(os.path.join(cat_dir, 'catalog.json'))
            label_item_read = cat_read.get_item("area-2-2-labels", recursive=True)
            label_item_read.validate()

    def test_read_label_item_owns_asset(self):
        item = next(x for x in TestCases.test_case_2().get_all_items() if x.ext.implements("label"))
        assert len(item.assets) > 0
        for asset_key in item.assets:
            self.assertEqual(item.assets[asset_key].owner, item)

    def test_label_description(self):
        label_item = pystac.read_file(self.label_example_1_uri)

        # Get
        self.assertIn("label:description", label_item.properties)
        label_desc = label_item.ext.label.label_description
        self.assertEqual(label_desc, label_item.properties['label:description'])

        # Set
        label_item.ext.label.label_description = "A detailed description"
        self.assertEqual("A detailed description", label_item.properties['label:description'])
        label_item.validate()

    def test_label_type(self):
        label_item = pystac.read_file(self.label_example_1_uri)

        # Get
        self.assertIn("label:type", label_item.properties)
        label_type = label_item.ext.label.label_type
        self.assertEqual(label_type, label_item.properties['label:type'])

        # Set
        label_item.ext.label.label_type = label.LabelType.RASTER
        self.assertEqual(label.LabelType.RASTER, label_item.properties['label:type'])
        label_item.validate()

    def test_label_properties(self):
        label_item = pystac.read_file(self.label_example_1_uri)
        label_item2 = pystac.read_file(self.label_example_2_uri)

        # Get
        self.assertIn("label:properties", label_item.properties)
        label_prop = label_item.ext.label.label_properties
        self.assertEqual(label_prop, label_item.properties['label:properties'])
        raster_label_prop = label_item2.ext.label.label_properties
        self.assertEqual(raster_label_prop, None)

        # Set
        label_item.ext.label.label_properties = ["prop1", "prop2"]
        self.assertEqual(["prop1", "prop2"], label_item.properties['label:properties'])
        label_item.validate()

    def test_label_classes(self):
        # Get
        label_item = pystac.read_file(self.label_example_1_uri)
        label_classes = label_item.ext.label.label_classes

        self.assertEqual(len(label_classes), 2)
        self.assertEqual(label_classes[1].classes, ["three", "four"])

        # Set
        new_classes = [
            label.LabelClasses.create(name="label2", classes=["five", "six"]),
            label.LabelClasses.create(name="label", classes=["seven", "eight"])
        ]

        label_item.ext.label.label_classes = new_classes
        self.assertEqual([
            class_name for lc in label_item.properties["label:classes"]
            for class_name in lc["classes"]
        ], ["five", "six", "seven", "eight"])

        label_item.validate()

    def test_label_tasks(self):
        label_item = pystac.read_file(self.label_example_1_uri)

        # Get
        self.assertIn("label:tasks", label_item.properties)
        label_prop = label_item.ext.label.label_tasks
        self.assertEqual(label_prop, ["classification", "regression"])

        # Set
        label_item.ext.label.label_tasks = ["classification"]
        self.assertEqual(["classification"], label_item.properties['label:tasks'])
        label_item.validate()

    def test_label_methods(self):
        label_item = pystac.read_file(self.label_example_1_uri)

        # Get
        self.assertIn("label:methods", label_item.properties)
        label_prop = label_item.ext.label.label_methods
        self.assertEqual(label_prop, ["manual"])

        # Set
        label_item.ext.label.label_methods = ["manual", "automated"]
        self.assertEqual(["manual", "automated"], label_item.properties['label:methods'])
        label_item.validate()

    def test_label_overviews(self):
        # Get
        label_item = pystac.read_file(self.label_example_1_uri)
        label_overviews = label_item.ext.label.label_overviews

        label_item2 = pystac.read_file(self.label_example_2_uri)
        label_overviews2 = label_item2.ext.label.label_overviews

        self.assertEqual(len(label_overviews), 2)
        self.assertEqual(label_overviews[1].property_key, "label-reg")
        self.assertEqual(label_overviews2[1].property_key, None)  # Raster

        label_counts = label_overviews[0].counts
        self.assertEqual(label_counts[1].count, 17)
        label_item.ext.label.label_overviews[0].counts[1].count = 18
        self.assertEqual(label_item.properties['label:overviews'][0]['counts'][1]['count'], 18)

        label_statistics = label_overviews[1].statistics
        self.assertEqual(label_statistics[0].name, "mean")
        label_item.ext.label.label_overviews[1].statistics[0].name = "avg"
        self.assertEqual(label_item.properties['label:overviews'][1]['statistics'][0]['name'],
                         "avg")

        # Set
        new_overviews = [
            label.LabelOverview.create(property_key="label2",
                                       counts=[
                                           label.LabelCount.create(name="one", count=1),
                                           label.LabelCount.create(name="two", count=1),
                                       ]),
            label.LabelOverview.create(property_key="label-reg",
                                       statistics=[
                                           label.LabelStatistics.create(name="min", value=0.1),
                                           label.LabelStatistics.create(name="max", value=1.0),
                                       ])
        ]

        label_item.ext.label.label_overviews = new_overviews
        self.assertEqual([(count['name'], count['count'])
                          for count in label_item.properties["label:overviews"][0]['counts']],
                         [("one", 1), ("two", 1)])

        self.assertEqual([(count['name'], count['value'])
                          for count in label_item.properties["label:overviews"][1]['statistics']],
                         [("min", 0.1), ("max", 1.0)])

        label_item.validate()
