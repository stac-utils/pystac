import os
import unittest
from tempfile import TemporaryDirectory
from datetime import datetime

from pystac import *
from pystac.utils import is_absolute_href
from tests.utils import (TestCases, RANDOM_GEOM, RANDOM_BBOX)


class CatalogTest(unittest.TestCase):
    def test_create_and_read(self):
        with TemporaryDirectory() as tmp_dir:
            cat_dir = os.path.join(tmp_dir, 'catalog')
            catalog = TestCases.test_case_1()

            catalog.normalize_and_save(cat_dir, catalog_type=CatalogType.ABSOLUTE_PUBLISHED)

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

            new_cat.normalize_hrefs(os.path.join(tmp_dir, 'cat'))
            new_cat.save(catalog_type=CatalogType.ABSOLUTE_PUBLISHED)

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


            new_cat.normalize_hrefs(os.path.join(tmp_dir, 'cat'))
            new_cat.save(catalog_type=CatalogType.ABSOLUTE_PUBLISHED)

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

    def test_map_assets_single(self):
        changed_asset = 'd43bead8-e3f8-4c51-95d6-e24e750a402b'

        def asset_mapper(key, asset):
            if key == changed_asset:
                asset.title = 'NEW TITLE'

            return asset

        with TemporaryDirectory() as tmp_dir:
            catalog = TestCases.test_case_2()

            new_cat = catalog.map_assets(asset_mapper)

            new_cat.normalize_hrefs(os.path.join(tmp_dir, 'cat'))
            new_cat.save(catalog_type=CatalogType.ABSOLUTE_PUBLISHED)

            result_cat = Catalog.from_file(os.path.join(tmp_dir, 'cat', 'catalog.json'))

            found = False
            for item in result_cat.get_all_items():
                for key, asset in item.assets.items():
                    if key == changed_asset:
                        found = True
                        self.assertEqual(asset.title, 'NEW TITLE')
                    else:
                        self.assertNotEqual(asset.title, 'NEW TITLE')
            self.assertTrue(found)

    def test_map_assets_tup(self):
        changed_assets = []

        def asset_mapper(key, asset):
            if 'geotiff' in asset.media_type:
                asset.title = 'NEW TITLE'
                changed_assets.append(key)
                return ('{}-modified'.format(key), asset)
            else:
                return asset

        with TemporaryDirectory() as tmp_dir:
            catalog = TestCases.test_case_2()

            new_cat = catalog.map_assets(asset_mapper)

            new_cat.normalize_hrefs(os.path.join(tmp_dir, 'cat'))
            new_cat.save(catalog_type=CatalogType.ABSOLUTE_PUBLISHED)

            result_cat = Catalog.from_file(os.path.join(tmp_dir, 'cat', 'catalog.json'))

            found = False
            not_found = False
            for item in result_cat.get_all_items():
                for key, asset in item.assets.items():
                    if key.replace('-modified', '') in changed_assets:
                        found = True
                        self.assertEqual(asset.title, 'NEW TITLE')
                    else:
                        not_found = True
                        self.assertNotEqual(asset.title, 'NEW TITLE')

            self.assertTrue(found)
            self.assertTrue(not_found)

    def test_map_assets_multi(self):
        changed_assets = []

        def asset_mapper(key, asset):
            if 'geotiff' in asset.media_type:
                changed_assets.append(key)
                mod1 = asset.clone()
                mod1.title = 'NEW TITLE 1'
                mod2 = asset.clone()
                mod2.title = 'NEW TITLE 2'
                return {
                    '{}-mod-1'.format(key): mod1,
                    '{}-mod-2'.format(key): mod2
                }
            else:
                return asset

        with TemporaryDirectory() as tmp_dir:
            catalog = TestCases.test_case_2()

            new_cat = catalog.map_assets(asset_mapper)

            new_cat.normalize_hrefs(os.path.join(tmp_dir, 'cat'))
            new_cat.save(catalog_type=CatalogType.ABSOLUTE_PUBLISHED)

            result_cat = Catalog.from_file(os.path.join(tmp_dir, 'cat', 'catalog.json'))

            found1 = False
            found2 = False
            not_found =  False
            for item in result_cat.get_all_items():
                for key, asset in item.assets.items():
                    if key.replace('-mod-1', '') in changed_assets:
                        found1 = True
                        self.assertEqual(asset.title, 'NEW TITLE 1')
                    elif key.replace('-mod-2', '') in changed_assets:
                        found2 = True
                        self.assertEqual(asset.title, 'NEW TITLE 2')
                    else:
                        not_found = True
                        self.assertNotEqual(asset.title, 'NEW TITLE')

            self.assertTrue(found1)
            self.assertTrue(found2)
            self.assertTrue(not_found)

    def test_make_all_asset_hrefs_absolute(self):
        cat = TestCases.test_case_2()
        cat.make_all_asset_hrefs_absolute()
        item = cat.get_item('cf73ec1a-d790-4b59-b077-e101738571ed', recursive=True)

        href = item.assets['cf73ec1a-d790-4b59-b077-e101738571ed'].href
        self.assertTrue(is_absolute_href(href))


    def test_make_all_links_relative_or_absolute(self):
        def check_all_relative(cat):
            for root, catalogs, items in cat.walk():
                for l in root.links:
                    if l.rel != 'self':
                        self.assertTrue(l.link_type == LinkType.RELATIVE)
                        self.assertFalse(is_absolute_href(l.get_href()))
                for i in items:
                    for l in i.links:
                        if l.rel != 'self':
                            self.assertTrue(l.link_type == LinkType.RELATIVE)
                            self.assertFalse(is_absolute_href(l.get_href()))


        def check_all_absolute(cat):
            for root, catalogs, items in cat.walk():
                for l in root.links:
                    self.assertTrue(l.link_type == LinkType.ABSOLUTE)
                    self.assertTrue(is_absolute_href(l.get_href()))
                for i in items:
                    for l in i.links:
                        self.assertTrue(l.link_type == LinkType.ABSOLUTE)
                        self.assertTrue(is_absolute_href(l.get_href()))

        test_cases = [TestCases.test_case_1(),
                      TestCases.test_case_2(),
                      TestCases.test_case_3()]

        for catalog in test_cases:
            with TemporaryDirectory() as tmp_dir:
                c2 = catalog.full_copy()
                c2.normalize_hrefs(tmp_dir)
                c2.make_all_links_relative()
                check_all_relative(c2)
                c2.make_all_links_absolute()
                check_all_absolute(c2)


class FullCopyTest(unittest.TestCase):
    def check_link(self, l, tag):
        if l.is_resolved():
            target_href = l.target.get_self_href()
        else:
            target_href = l.target
        self.assertTrue(tag in target_href)

    def check_item(self, i, tag):
        for l in i.links:
            self.check_link(l, tag)

    def check_catalog(self, c, tag):
        self.assertEqual(len(c.get_links('root')), 1)

        for l in c.links:
            self.check_link(l, tag)

        for child in c.get_children():
            self.check_catalog(child, tag)

        for item in c.get_items():
            self.check_item(item, tag)

    def test_full_copy_1(self):
        with TemporaryDirectory() as tmp_dir:
            cat = Catalog(id='test', description='test catalog')

            item = Item(id='test_item',
                        geometry=RANDOM_GEOM,
                        bbox=RANDOM_BBOX,
                        datetime=datetime.utcnow(),
                        properties={})

            cat.normalize_hrefs(os.path.join(tmp_dir, 'catalog-full-copy-1-source'))
            cat2 = cat.full_copy()
            cat2.normalize_hrefs(os.path.join(tmp_dir, 'catalog-full-copy-1-dest'))

            self.check_catalog(cat, 'source')
            self.check_catalog(cat2, 'dest')

    def test_full_copy_2(self):
        with TemporaryDirectory() as tmp_dir:
            cat = Catalog(id='test', description='test catalog')
            image_item = Item(id='Imagery',
                              geometry=RANDOM_GEOM,
                              bbox=RANDOM_BBOX,
                              datetime=datetime.utcnow(),
                              properties={})
            for key in ['ortho', 'dsm']:
                image_item.add_asset(key,
                                     Asset(href='some/{}.tif'.format(key),
                                           media_type=Asset.MEDIA_TYPE.GEOTIFF))

            label_item = LabelItem(id='Labels',
                                   geometry=RANDOM_GEOM,
                                   bbox=RANDOM_BBOX,
                                   datetime=datetime.utcnow(),
                                   properties={},
                                   label_description='labels',
                                   label_type='vector',
                                   label_property='label',
                                   label_classes=[LabelClasses(classes=['one', 'two'],
                                                               name='label')],
                                   label_task='classification')
            label_item.add_source(image_item, assets=['ortho'])

            cat.add_items([image_item, label_item])

            cat.normalize_hrefs(os.path.join(tmp_dir, 'catalog-full-copy-2-source'))
            cat.save(catalog_type=CatalogType.ABSOLUTE_PUBLISHED)
            cat2 = cat.full_copy()
            cat2.normalize_hrefs(os.path.join(tmp_dir, 'catalog-full-copy-2-dest'))
            cat2.save(catalog_type=CatalogType.ABSOLUTE_PUBLISHED)

            self.check_catalog(cat, 'source')
            self.check_catalog(cat2, 'dest')


    def test_full_copy_3(self):
        with TemporaryDirectory() as tmp_dir:
            root_cat = TestCases.test_case_1()
            root_cat.normalize_hrefs(os.path.join(tmp_dir, 'catalog-full-copy-3-source'))
            root_cat.save(catalog_type=CatalogType.ABSOLUTE_PUBLISHED)
            cat2 = root_cat.full_copy()
            cat2.normalize_hrefs(os.path.join(tmp_dir, 'catalog-full-copy-3-dest'))
            cat2.save(catalog_type=CatalogType.ABSOLUTE_PUBLISHED)

            self.check_catalog(root_cat, 'source')
            self.check_catalog(cat2, 'dest')

    def test_full_copy_4(self):
        with TemporaryDirectory() as tmp_dir:
            root_cat = TestCases.test_case_2()
            root_cat.normalize_hrefs(os.path.join(tmp_dir, 'catalog-full-copy-4-source'))
            root_cat.save(catalog_type=CatalogType.ABSOLUTE_PUBLISHED)
            cat2 = root_cat.full_copy()
            cat2.normalize_hrefs(os.path.join(tmp_dir, 'catalog-full-copy-4-dest'))
            cat2.save(catalog_type=CatalogType.ABSOLUTE_PUBLISHED)

            self.check_catalog(root_cat, 'source')
            self.check_catalog(cat2, 'dest')

            # Check that the relative asset link was saved correctly in the copy.
            item = cat2.get_item('cf73ec1a-d790-4b59-b077-e101738571ed', recursive=True)

            href = item.assets['cf73ec1a-d790-4b59-b077-e101738571ed'].get_absolute_href()
            self.assertTrue(os.path.exists(href))
