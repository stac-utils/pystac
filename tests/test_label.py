import json
import os
import unittest
from tempfile import TemporaryDirectory

from pystac import (Catalog, CatalogType, LabelItem, STAC_IO)
from tests.utils import (SchemaValidator, TestCases, test_to_from_dict)


class LabelItemTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.label_example_1_uri = TestCases.get_path(
            'data-files/label/label-example-1.json')

    def test_to_from_dict(self):
        with open(self.label_example_1_uri) as f:
            label_example_1_dict = json.load(f)

        test_to_from_dict(self, LabelItem, label_example_1_dict)

    def test_from_file(self):
        label_example_1 = LabelItem.from_file(self.label_example_1_uri)

        self.assertEqual(len(label_example_1.label_overviews[0].counts), 2)

    def test_from_file_pre_081(self):
        d = STAC_IO.read_json(self.label_example_1_uri)

        d['properties']['label:property'] = d['properties']['label:properties']
        d['properties'].pop('label:properties')
        d['properties']['label:overview'] = d['properties']['label:overviews']
        d['properties'].pop('label:overviews')
        d['properties']['label:method'] = d['properties']['label:methods']
        d['properties'].pop('label:methods')
        d['properties']['label:task'] = d['properties']['label:tasks']
        d['properties'].pop('label:tasks')
        label_example_1 = LabelItem.from_dict(d)

        self.assertEqual(len(label_example_1.label_tasks), 1)

    def test_get_sources(self):
        cat = TestCases.test_case_1()

        items = cat.get_all_items()
        item_ids = set([i.id for i in items])

        for li in items:
            if isinstance(li, LabelItem):
                sources = li.get_sources()
                self.assertEqual(len(sources), 1)
                self.assertTrue(sources[0].id in item_ids)

    def test_validate_label(self):
        sv = SchemaValidator()
        with open(self.label_example_1_uri) as f:
            label_example_1_dict = json.load(f)
        sv.validate_dict(label_example_1_dict, LabelItem)

        with TemporaryDirectory() as tmp_dir:
            cat_dir = os.path.join(tmp_dir, 'catalog')
            catalog = TestCases.test_case_1()
            label_item = LabelItem.from_dict(label_example_1_dict)
            catalog.add_item(label_item)
            catalog.normalize_and_save(cat_dir,
                                       catalog_type=CatalogType.SELF_CONTAINED)

            cat_read = Catalog.from_file(os.path.join(cat_dir, 'catalog.json'))
            label_item_read = cat_read.get_item("label-example-1-label-item")
            sv = SchemaValidator()
            sv.validate_object(label_item_read)

    def test_read_label_item_owns_asset(self):
        item = next(x for x in TestCases.test_case_2().get_all_items()
                    if isinstance(x, LabelItem))
        assert len(item.assets) > 0
        for asset_key in item.assets:
            self.assertEqual(item.assets[asset_key].owner, item)

    # TODO: Test raster labels in LabelItems.
