import os
import unittest
from tempfile import TemporaryDirectory

from pystac import *
from tests.utils import (TestCases, RANDOM_GEOM, RANDOM_BBOX)

class CatalogTest(unittest.TestCase):
    def test_create_and_read(self):
        with TemporaryDirectory() as tmp_dir:
            cat_dir = os.path.join(tmp_dir, 'catalog')
            catalog = TestCases.test_case_1()

            catalog.set_uris_from_root(cat_dir)
            catalog.save()

            read_catalog = Catalog.from_file('{}/catalog.json'.format(cat_dir))

            collections = catalog.get_children()
            self.assertEqual(len(collections), 2)

            items = read_catalog.get_all_items()

            self.assertEqual(len(items), 8)

    def test_read_remote(self):
        catalog_url = ('https://raw.githubusercontent.com/radiantearth/stac-spec/'
                       '252cc892cdccf7ba0b9564bcae42bb6ec4189f14'
                       '/extensions/label/examples/multidataset/catalog.json')
        cat = Catalog.from_file(catalog_url)

        zanzibar = cat.get_child('zanzibar-collection')

        self.assertEqual(len(zanzibar.get_items()), 2)


    def test_map_items(self):
        def item_mapper(item):
            item.properties['ITEM_MAPPER'] = 'YEP'
            return item

        with TemporaryDirectory() as tmp_dir:
            catalog = TestCases.test_case_1()

            new_cat = catalog.map_items(item_mapper)

            new_cat.set_uris_from_root(os.path.join(tmp_dir, 'cat'))
            new_cat.save()

            result_cat = Catalog.from_file(os.path.join(tmp_dir, 'cat', 'catalog.json'))

            for item in result_cat.get_all_items():
                self.assertTrue('ITEM_MAPPER' in item.properties)

            for item in catalog.get_all_items():
                self.assertFalse('ITEM_MAPPER' in item.properties)

    def test_map_items_multiple(self):
        def item_mapper(item):
            item2 = item.clone()
            item2.id = item2.id + '_2'
            item.properties['ITEM_MAPPER_1'] = 'YEP'
            item2.properties['ITEM_MAPPER_2'] = 'YEP'
            return [item, item2]

        with TemporaryDirectory() as tmp_dir:
            catalog = TestCases.test_case_1()
            catalog_items = catalog.get_all_items()

            new_cat = catalog.map_items(item_mapper)


            new_cat.set_uris_from_root(os.path.join(tmp_dir, 'cat'))
            new_cat.save()

            result_cat = Catalog.from_file(os.path.join(tmp_dir, 'cat', 'catalog.json'))
            result_items = result_cat.get_all_items()

            self.assertEqual(len(catalog_items)*2, len(result_items))

            ones, twos = 0, 0
            for item in result_items:
                self.assertTrue(('ITEM_MAPPER_1' in item.properties) or
                                ('ITEM_MAPPER_2' in item.properties))
                if 'ITEM_MAPPER_1' in item.properties:
                    ones += 1

                if 'ITEM_MAPPER_2' in item.properties:
                    twos += 1

            self.assertEqual(ones, twos)

            for item in catalog.get_all_items():
                self.assertFalse(('ITEM_MAPPER_1' in item.properties) or
                                 ('ITEM_MAPPER_2' in item.properties))
