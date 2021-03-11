import os
import json
import unittest
from tempfile import TemporaryDirectory
from datetime import datetime
from collections import defaultdict

import pystac
from pystac import (Catalog, Collection, CatalogType, LinkType, Item, Asset, MediaType, Extensions)
from pystac.extensions.label import LabelClasses
from pystac.validation import STACValidationError
from pystac.utils import is_absolute_href
from tests.utils import (TestCases, RANDOM_GEOM, RANDOM_BBOX, MockStacIO)


class CatalogTypeTest(unittest.TestCase):
    def test_determine_type_for_absolute_published(self):
        cat = TestCases.test_case_1()
        with TemporaryDirectory() as tmp_dir:
            cat.normalize_and_save(tmp_dir, catalog_type=CatalogType.ABSOLUTE_PUBLISHED)
            cat_json = pystac.STAC_IO.read_json(os.path.join(tmp_dir, 'catalog.json'))

        catalog_type = CatalogType.determine_type(cat_json)
        self.assertEqual(catalog_type, CatalogType.ABSOLUTE_PUBLISHED)

    def test_determine_type_for_relative_published(self):
        cat = TestCases.test_case_2()
        with TemporaryDirectory() as tmp_dir:
            cat.normalize_and_save(tmp_dir, catalog_type=CatalogType.RELATIVE_PUBLISHED)
            cat_json = pystac.STAC_IO.read_json(os.path.join(tmp_dir, 'catalog.json'))

        catalog_type = CatalogType.determine_type(cat_json)
        self.assertEqual(catalog_type, CatalogType.RELATIVE_PUBLISHED)

    def test_determine_type_for_self_contained(self):
        cat_json = pystac.STAC_IO.read_json(
            TestCases.get_path('data-files/catalogs/test-case-1/catalog.json'))
        catalog_type = CatalogType.determine_type(cat_json)
        self.assertEqual(catalog_type, CatalogType.SELF_CONTAINED)

    def test_determine_type_for_unknown(self):
        catalog = Catalog(id='test', description='test desc')
        subcat = Catalog(id='subcat', description='subcat desc')
        catalog.add_child(subcat)
        catalog.normalize_hrefs('http://example.com')
        d = catalog.to_dict(include_self_link=False)

        self.assertIsNone(CatalogType.determine_type(d))


class CatalogTest(unittest.TestCase):
    def test_create_and_read(self):
        with TemporaryDirectory() as tmp_dir:
            cat_dir = os.path.join(tmp_dir, 'catalog')
            catalog = TestCases.test_case_1()

            catalog.normalize_and_save(cat_dir, catalog_type=CatalogType.ABSOLUTE_PUBLISHED)

            read_catalog = Catalog.from_file('{}/catalog.json'.format(cat_dir))

            collections = catalog.get_children()
            self.assertEqual(len(list(collections)), 2)

            items = read_catalog.get_all_items()

            self.assertEqual(len(list(items)), 8)

    def test_read_remote(self):
        # TODO: Move this URL to the main stac-spec repo once the example JSON is fixed.
        catalog_url = (
            'https://raw.githubusercontent.com/lossyrob/stac-spec/0.9.0/pystac-upgrade-fixes'
            '/extensions/label/examples/multidataset/catalog.json')
        cat = Catalog.from_file(catalog_url)

        zanzibar = cat.get_child('zanzibar-collection')

        self.assertEqual(len(list(zanzibar.get_items())), 2)

    def test_clear_items_removes_from_cache(self):
        catalog = Catalog(id='test', description='test')
        subcat = Catalog(id='subcat', description='test')
        catalog.add_child(subcat)
        item = Item(id='test-item',
                    geometry=RANDOM_GEOM,
                    bbox=RANDOM_BBOX,
                    datetime=datetime.utcnow(),
                    properties={'key': 'one'})
        subcat.add_item(item)

        items = list(catalog.get_all_items())
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].properties['key'], 'one')

        subcat.clear_items()
        item = Item(id='test-item',
                    geometry=RANDOM_GEOM,
                    bbox=RANDOM_BBOX,
                    datetime=datetime.utcnow(),
                    properties={'key': 'two'})
        subcat.add_item(item)

        items = list(catalog.get_all_items())
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].properties['key'], 'two')

        subcat.remove_item('test-item')
        item = Item(id='test-item',
                    geometry=RANDOM_GEOM,
                    bbox=RANDOM_BBOX,
                    datetime=datetime.utcnow(),
                    properties={'key': 'three'})
        subcat.add_item(item)

        items = list(catalog.get_all_items())
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].properties['key'], 'three')

    def test_clear_children_removes_from_cache(self):
        catalog = Catalog(id='test', description='test')
        subcat = Catalog(id='subcat', description='test')
        catalog.add_child(subcat)

        children = list(catalog.get_children())
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].description, 'test')

        catalog.clear_children()
        subcat = Catalog(id='subcat', description='test2')
        catalog.add_child(subcat)

        children = list(catalog.get_children())
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].description, 'test2')

        catalog.remove_child('subcat')
        subcat = Catalog(id='subcat', description='test3')
        catalog.add_child(subcat)

        children = list(catalog.get_children())
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].description, 'test3')

    def test_clear_children_sets_parent_and_root_to_None(self):
        catalog = Catalog(id='test', description='test')
        subcat1 = Catalog(id='subcat', description='test')
        subcat2 = Catalog(id='subcat2', description='test2')
        catalog.add_children([subcat1, subcat2])

        self.assertIsNotNone(subcat1.get_parent())
        self.assertIsNotNone(subcat2.get_parent())
        self.assertIsNotNone(subcat1.get_root())
        self.assertIsNotNone(subcat2.get_root())

        children = list(catalog.get_children())
        self.assertEqual(len(children), 2)

        catalog.clear_children()

        self.assertIsNone(subcat1.get_parent())
        self.assertIsNone(subcat2.get_parent())
        self.assertIsNone(subcat1.get_root())
        self.assertIsNone(subcat2.get_root())

    def test_add_child_throws_if_item(self):
        cat = TestCases.test_case_1()
        item = next(cat.get_all_items())
        with self.assertRaises(pystac.STACError):
            cat.add_child(item)

    def test_add_item_throws_if_child(self):
        cat = TestCases.test_case_1()
        child = next(cat.get_children())
        with self.assertRaises(pystac.STACError):
            cat.add_item(child)

    def test_get_child_returns_none_if_not_found(self):
        cat = TestCases.test_case_1()
        child = cat.get_child('thisshouldnotbeachildid', recursive=True)
        self.assertIsNone(child)

    def test_get_item_returns_none_if_not_found(self):
        cat = TestCases.test_case_1()
        item = cat.get_item('thisshouldnotbeanitemid', recursive=True)
        self.assertIsNone(item)

    def test_sets_catalog_type(self):
        cat = TestCases.test_case_1()

        self.assertEqual(cat.catalog_type, CatalogType.SELF_CONTAINED)

    def test_walk_iterates_correctly(self):
        def test_catalog(cat):
            expected_catalog_iterations = 1
            actual_catalog_iterations = 0
            with self.subTest(title='Testing catalog {}'.format(cat.id)):
                for root, children, items in cat.walk():
                    actual_catalog_iterations += 1
                    expected_catalog_iterations += len(list(root.get_children()))

                    self.assertEqual(set([c.id for c in root.get_children()]),
                                     set([c.id for c in children]), 'Children unequal')
                    self.assertEqual(set([c.id for c in root.get_items()]),
                                     set([c.id for c in items]), 'Items unequal')

                self.assertEqual(actual_catalog_iterations, expected_catalog_iterations)

        for cat in TestCases.all_test_catalogs():
            test_catalog(cat)

    def test_clone_generates_correct_links(self):
        catalogs = TestCases.all_test_catalogs()

        for catalog in catalogs:
            expected_link_types_to_counts = {}
            actual_link_types_to_counts = {}

            for root, _, items in catalog.walk():
                expected_link_types_to_counts[root.id] = defaultdict(int)
                actual_link_types_to_counts[root.id] = defaultdict(int)

                for link in root.get_links():
                    expected_link_types_to_counts[root.id][link.rel] += 1

                for link in root.clone().get_links():
                    actual_link_types_to_counts[root.id][link.rel] += 1

                for item in items:
                    expected_link_types_to_counts[item.id] = defaultdict(int)
                    actual_link_types_to_counts[item.id] = defaultdict(int)
                    for link in item.get_links():
                        expected_link_types_to_counts[item.id][link.rel] += 1
                    for link in item.get_links():
                        actual_link_types_to_counts[item.id][link.rel] += 1

            self.assertEqual(set(expected_link_types_to_counts.keys()),
                             set(actual_link_types_to_counts.keys()))

            for obj_id in actual_link_types_to_counts:
                expected_counts = expected_link_types_to_counts[obj_id]
                actual_counts = actual_link_types_to_counts[obj_id]
                self.assertEqual(set(expected_counts.keys()), set(actual_counts.keys()))
                for rel in expected_counts:
                    self.assertEqual(
                        actual_counts[rel], expected_counts[rel],
                        'Clone of {} has {} {} links, original has {}'.format(
                            obj_id, actual_counts[rel], rel, expected_counts[rel]))

    def test_save_uses_previous_catalog_type(self):
        catalog = TestCases.test_case_1()
        assert catalog.catalog_type == CatalogType.SELF_CONTAINED
        with TemporaryDirectory() as tmp_dir:
            catalog.normalize_hrefs(tmp_dir)
            href = catalog.get_self_href()
            catalog.save()

            cat2 = pystac.read_file(href)
            self.assertEqual(cat2.catalog_type, CatalogType.SELF_CONTAINED)

    def test_clone_uses_previous_catalog_type(self):
        catalog = TestCases.test_case_1()
        assert catalog.catalog_type == CatalogType.SELF_CONTAINED
        clone = catalog.clone()
        self.assertEqual(clone.catalog_type, CatalogType.SELF_CONTAINED)

    def test_save_throws_if_no_catalog_type(self):
        catalog = TestCases.test_case_3()
        assert catalog.catalog_type is None
        with TemporaryDirectory() as tmp_dir:
            catalog.normalize_hrefs(tmp_dir)
            with self.assertRaises(ValueError):
                catalog.save()

    def test_normalize_hrefs_sets_all_hrefs(self):
        catalog = TestCases.test_case_1()
        catalog.normalize_hrefs('http://example.com')
        for root, _, items in catalog.walk():
            self.assertTrue(root.get_self_href().startswith('http://example.com'))
            for link in root.links:
                if link.is_resolved():
                    target_href = link.target.get_self_href()
                else:
                    target_href = link.get_absolute_href()
                self.assertTrue(
                    'http://example.com' in target_href,
                    '[{}] {} does not contain "{}"'.format(link.rel, target_href,
                                                           'http://example.com'))
            for item in items:
                self.assertIn('http://example.com', item.get_self_href())

    def test_normalize_hrefs_makes_absolute_href(self):
        catalog = TestCases.test_case_1()
        catalog.normalize_hrefs('./relativepath')
        abspath = os.path.abspath('./relativepath')
        self.assertTrue(catalog.get_self_href().startswith(abspath))

    def test_normalize_href_works_with_label_source_links(self):
        catalog = TestCases.test_case_1()
        catalog.normalize_hrefs('http://example.com')
        item = catalog.get_item('area-1-1-labels', recursive=True)
        source = next(item.ext.label.get_sources())
        self.assertEqual(
            source.get_self_href(),
            "http://example.com/country-1/area-1-1/area-1-1-imagery/area-1-1-imagery.json")

    def test_generate_subcatalogs_works_with_custom_properties(self):
        catalog = TestCases.test_case_8()
        defaults = {'pl:item_type': 'PlanetScope'}
        catalog.generate_subcatalogs('${year}/${month}/${pl:item_type}', defaults=defaults)

        month_cat = catalog.get_child('8', recursive=True)
        type_cats = set([cat.id for cat in month_cat.get_children()])

        self.assertEqual(type_cats, set(['PSScene4Band', 'SkySatScene', 'PlanetScope']))

    def test_generate_subcatalogs_does_not_change_item_count(self):
        catalog = TestCases.test_case_7()

        item_counts = {cat.id: len(list(cat.get_all_items())) for cat in catalog.get_children()}

        catalog.generate_subcatalogs("${year}/${day}")

        with TemporaryDirectory() as tmp_dir:
            catalog.normalize_hrefs(tmp_dir)
            catalog.save(pystac.CatalogType.SELF_CONTAINED)

            cat2 = pystac.read_file(os.path.join(tmp_dir, 'catalog.json'))
            for child in cat2.get_children():
                actual = len(list(child.get_all_items()))
                expected = item_counts[child.id]
                self.assertEqual(actual, expected, msg=" for child '{}'".format(child.id))

    def test_generate_subcatalogs_can_be_applied_multiple_times(self):
        catalog = TestCases.test_case_8()

        _ = catalog.generate_subcatalogs('${year}/${month}')
        catalog.normalize_hrefs('/tmp')
        expected_hrefs = {item.id: item.get_self_href() for item in catalog.get_all_items()}

        result = catalog.generate_subcatalogs('${year}/${month}')
        self.assertEqual(len(result), 0)
        catalog.normalize_hrefs('/tmp')
        for item in catalog.get_all_items():
            self.assertEqual(item.get_self_href(),
                             expected_hrefs[item.id],
                             msg=" for item '{}'".format(item.id))

    def test_generate_subcatalogs_works_after_adding_more_items(self):
        catalog = Catalog(id='test', description='Test')
        properties = dict(property1='A', property2=1)
        catalog.add_item(
            Item(id='item1',
                 geometry=RANDOM_GEOM,
                 bbox=RANDOM_BBOX,
                 datetime=datetime.utcnow(),
                 properties=properties))
        catalog.generate_subcatalogs('${property1}/${property2}')
        catalog.add_item(
            Item(id='item2',
                 geometry=RANDOM_GEOM,
                 bbox=RANDOM_BBOX,
                 datetime=datetime.utcnow(),
                 properties=properties))
        catalog.generate_subcatalogs('${property1}/${property2}')

        catalog.normalize_hrefs('/tmp')
        item1_parent = catalog.get_item('item1', recursive=True).get_parent()
        item2_parent = catalog.get_item('item2', recursive=True).get_parent()
        self.assertEqual(item1_parent.get_self_href(), item2_parent.get_self_href())

    def test_generate_subcatalogs_works_for_branched_subcatalogs(self):
        catalog = Catalog(id='test', description='Test')
        item_properties = [
            dict(property1='A', property2=1, property3='i'),  # add 3 subcats
            dict(property1='A', property2=1, property3='j'),  # add 1 more
            dict(property1='A', property2=2, property3='i'),  # add 2 more
            dict(property1='B', property2=1, property3='i'),  # add 3 more
        ]
        for ni, properties in enumerate(item_properties):
            catalog.add_item(
                Item(id='item{}'.format(ni),
                     geometry=RANDOM_GEOM,
                     bbox=RANDOM_BBOX,
                     datetime=datetime.utcnow(),
                     properties=properties))
        result = catalog.generate_subcatalogs('${property1}/${property2}/${property3}')
        self.assertEqual(len(result), 9)

        actual_subcats = set([cat.id for cat in result])
        expected_subcats = {'A', 'B', '1', '2', 'i', 'j'}
        self.assertSetEqual(actual_subcats, expected_subcats)

    def test_generate_subcatalogs_works_for_subcatalogs_with_same_ids(self):
        catalog = Catalog(id='test', description='Test')
        item_properties = [
            dict(property1=1, property2=1),  # add 2 subcats
            dict(property1=1, property2=2),  # add 1 more
            dict(property1=2, property2=1),  # add 2 more
            dict(property1=2, property2=2),  # add 1 more
        ]
        for ni, properties in enumerate(item_properties):
            catalog.add_item(
                Item(id='item{}'.format(ni),
                     geometry=RANDOM_GEOM,
                     bbox=RANDOM_BBOX,
                     datetime=datetime.utcnow(),
                     properties=properties))
        result = catalog.generate_subcatalogs('${property1}/${property2}')
        self.assertEqual(len(result), 6)

        catalog.normalize_hrefs('/')
        for item in catalog.get_all_items():
            parent_href = item.get_parent().get_self_href()
            path_to_parent, _ = os.path.split(parent_href)
            subcats = [el for el in path_to_parent.split('/') if el]
            self.assertEqual(len(subcats), 2, msg=" for item '{}'".format(item.id))

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

            self.assertEqual(len(list(catalog_items)) * 2, len(list(result_items)))

            ones, twos = 0, 0
            for item in result_items:
                self.assertTrue(('ITEM_MAPPER_1' in item.properties)
                                or ('ITEM_MAPPER_2' in item.properties))
                if 'ITEM_MAPPER_1' in item.properties:
                    ones += 1

                if 'ITEM_MAPPER_2' in item.properties:
                    twos += 1

            self.assertEqual(ones, twos)

            for item in catalog.get_all_items():
                self.assertFalse(('ITEM_MAPPER_1' in item.properties)
                                 or ('ITEM_MAPPER_2' in item.properties))

    def test_map_items_multiple_2(self):
        catalog = Catalog(id='test-1', description='Test1')
        item1 = Item(id='item1',
                     geometry=RANDOM_GEOM,
                     bbox=RANDOM_BBOX,
                     datetime=datetime.utcnow(),
                     properties={})
        item1.add_asset('ortho', Asset(href='/some/ortho.tif'))
        catalog.add_item(item1)
        kitten = Catalog(id='test-kitten', description='A cuter version of catalog')
        catalog.add_child(kitten)
        item2 = Item(id='item2',
                     geometry=RANDOM_GEOM,
                     bbox=RANDOM_BBOX,
                     datetime=datetime.utcnow(),
                     properties={})
        item2.add_asset('ortho', Asset(href='/some/other/ortho.tif'))
        kitten.add_item(item2)

        def modify_item_title(item):
            item.title = 'Some new title'
            return item

        def create_label_item(item):
            # Assumes the GEOJSON labels are in the
            # same location as the image
            img_href = item.assets['ortho'].href
            label_href = '{}.geojson'.format(os.path.splitext(img_href)[0])
            label_item = Item(id='Labels',
                              geometry=item.geometry,
                              bbox=item.bbox,
                              datetime=datetime.utcnow(),
                              properties={})
            label_item.ext.enable(Extensions.LABEL)
            label_ext = label_item.ext.label
            label_ext.apply(
                label_description='labels',
                label_type='vector',
                label_properties=['label'],
                label_classes=[LabelClasses.create(classes=['one', 'two'], name='label')],
                label_tasks=['classification'])
            label_ext.add_source(item, assets=['ortho'])
            label_ext.add_geojson_labels(label_href)

            return [item, label_item]

        c = catalog.map_items(modify_item_title)
        c = c.map_items(create_label_item)
        new_catalog = c

        items = new_catalog.get_all_items()
        self.assertTrue(len(list(items)) == 4)

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
                return {'{}-mod-1'.format(key): mod1, '{}-mod-2'.format(key): mod2}
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
            not_found = False
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

    def test_make_all_asset_hrefs_relative(self):
        cat = TestCases.test_case_2()
        item = cat.get_item('cf73ec1a-d790-4b59-b077-e101738571ed', recursive=True)
        asset = item.assets['cf73ec1a-d790-4b59-b077-e101738571ed']
        original_href = asset.href
        cat.make_all_asset_hrefs_absolute()

        assert is_absolute_href(asset.href)

        cat.make_all_asset_hrefs_relative()

        self.assertFalse(is_absolute_href(asset.href))
        self.assertEqual(asset.href, original_href)

    def test_make_all_links_relative_or_absolute(self):
        def check_all_relative(cat):
            for root, catalogs, items in cat.walk():
                for link in root.links:
                    if link.rel != 'self':
                        self.assertTrue(link.link_type == LinkType.RELATIVE)
                        self.assertFalse(is_absolute_href(link.get_href()))
                for item in items:
                    for link in item.links:
                        if link.rel != 'self':
                            self.assertTrue(link.link_type == LinkType.RELATIVE)
                            self.assertFalse(is_absolute_href(link.get_href()))

        def check_all_absolute(cat):
            for root, catalogs, items in cat.walk():
                for link in root.links:
                    self.assertTrue(link.link_type == LinkType.ABSOLUTE)
                    self.assertTrue(is_absolute_href(link.get_href()))
                for item in items:
                    for link in item.links:
                        self.assertTrue(link.link_type == LinkType.ABSOLUTE)
                        self.assertTrue(is_absolute_href(link.get_href()))

        test_cases = TestCases.all_test_catalogs()

        for catalog in test_cases:
            with TemporaryDirectory() as tmp_dir:
                c2 = catalog.full_copy()
                c2.normalize_hrefs(tmp_dir)
                c2.make_all_links_relative()
                check_all_relative(c2)
                c2.make_all_links_absolute()
                check_all_absolute(c2)

    def test_full_copy_and_normalize_works_with_created_stac(self):
        cat = TestCases.test_case_3()
        cat_copy = cat.full_copy()
        cat_copy.normalize_hrefs('http://example.com')
        for root, catalogs, items in cat_copy.walk():
            for link in root.links:
                if link.rel != 'self':
                    self.assertIsNot(link.target, None)
            for item in items:
                for link in item.links:
                    if link.rel != 'self':
                        self.assertIsNot(link.get_href(), None)

    def test_extra_fields(self):
        catalog = TestCases.test_case_1()

        catalog.extra_fields['type'] = 'FeatureCollection'

        with TemporaryDirectory() as tmp_dir:
            p = os.path.join(tmp_dir, 'catalog.json')
            catalog.save_object(include_self_link=False, dest_href=p)
            with open(p) as f:
                cat_json = json.load(f)
            self.assertTrue('type' in cat_json)
            self.assertEqual(cat_json['type'], 'FeatureCollection')

            read_cat = pystac.read_file(p)
            self.assertTrue('type' in read_cat.extra_fields)
            self.assertEqual(read_cat.extra_fields['type'], 'FeatureCollection')

    def test_validate_all(self):
        for cat in TestCases.all_test_catalogs():
            with self.subTest(cat.id):
                # If hrefs are not set, it will fail validation.
                if cat.get_self_href() is None:
                    cat.normalize_hrefs('/tmp')
                cat.validate_all()

        # Make one invalid, write it off, read it in, ensure it throws
        cat = TestCases.test_case_1()
        item = cat.get_item('area-1-1-labels', recursive=True)
        item.geometry = {'type': 'INVALID', 'coordinates': 'NONE'}
        with TemporaryDirectory() as tmp_dir:
            cat.normalize_hrefs(tmp_dir)
            cat.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)

            cat2 = pystac.read_file(os.path.join(tmp_dir, 'catalog.json'))

            with self.assertRaises(STACValidationError):
                cat2.validate_all()

    def test_set_hrefs_manually(self):
        catalog = TestCases.test_case_1()

        # Modify the datetimes
        year = 2004
        month = 2
        for item in catalog.get_all_items():
            item.datetime = item.datetime.replace(year=year, month=month)
            year += 1
            month += 1

        with TemporaryDirectory() as tmp_dir:
            for root, _, items in catalog.walk():

                # Set root's HREF based off the parent
                parent = root.get_parent()
                if parent is None:
                    root_dir = tmp_dir
                else:
                    d = os.path.dirname(parent.get_self_href())
                    root_dir = os.path.join(d, root.id)
                root_href = os.path.join(root_dir, root.DEFAULT_FILE_NAME)
                root.set_self_href(root_href)

                # Set each item's HREF based on it's datetime
                for item in items:
                    item_href = '{}/{}-{}/{}.json'.format(root_dir, item.datetime.year,
                                                          item.datetime.month, item.id)
                    item.set_self_href(item_href)

            catalog.save(catalog_type=CatalogType.SELF_CONTAINED)

            read_catalog = Catalog.from_file(os.path.join(tmp_dir, 'catalog.json'))

            for root, _, items in read_catalog.walk():
                parent = root.get_parent()
                if parent is None:
                    self.assertEqual(root.get_self_href(), os.path.join(tmp_dir, 'catalog.json'))
                else:
                    d = os.path.dirname(parent.get_self_href())
                    self.assertEqual(root.get_self_href(),
                                     os.path.join(d, root.id, root.DEFAULT_FILE_NAME))
                for item in items:
                    end = '{}-{}/{}.json'.format(item.datetime.year, item.datetime.month, item.id)
                    self.assertTrue(item.get_self_href().endswith(end))

    def test_collections_cache_correctly(self):
        catalogs = TestCases.all_test_catalogs()
        for cat in catalogs:
            with MockStacIO() as mock_io:
                expected_collection_reads = set([])
                for root, children, items in cat.walk():
                    if isinstance(root, Collection) and root != cat:
                        expected_collection_reads.add(root.get_self_href())

                    # Iterate over items to make sure they are read
                    self.assertNotEqual(list(items), None)

                call_uris = [
                    call[0][0] for call in mock_io.read_text_method.call_args_list
                    if call[0][0] in expected_collection_reads
                ]

                for collection_uri in expected_collection_reads:
                    calls = len([x for x in call_uris if x == collection_uri])
                    self.assertEqual(
                        calls, 1,
                        '{} was read {} times instead of once!'.format(collection_uri, calls))

    def test_reading_iterating_and_writing_works_as_expected(self):
        """ Test case to cover issue #88 """
        stac_uri = 'tests/data-files/catalogs/test-case-6/catalog.json'
        cat = Catalog.from_file(stac_uri)

        # Iterate over the items. This was causing failure in
        # in the later iterations as per issue #88
        for item in cat.get_all_items():
            pass

        with TemporaryDirectory() as tmp_dir:
            new_stac_uri = os.path.join(tmp_dir, 'test-case-6')
            cat.normalize_hrefs(new_stac_uri)
            cat.save(catalog_type=CatalogType.SELF_CONTAINED)

            # Open the local copy and iterate over it.
            cat2 = Catalog.from_file(os.path.join(new_stac_uri, 'catalog.json'))

            for item in cat2.get_all_items():
                # Iterate again over the items. This would fail in #88
                pass

    def test_get_children_cbers(self):
        cat = TestCases.test_case_6()
        self.assertEqual(len(list(cat.get_children())), 4)

    def test_resolve_planet(self):
        """Test against a bug that caused infinite recursion during link resolution"""
        cat = TestCases.test_case_8()
        for root, _, items in cat.walk():
            for item in items:
                item.resolve_links()
            root.resolve_links()

    def test_handles_children_with_same_id(self):
        # This catalog has the root and child collection share an ID.
        cat = pystac.read_file(TestCases.get_path('data-files/invalid/shared-id/catalog.json'))
        items = list(cat.get_all_items())

        self.assertEqual(len(items), 1)

    def test_catalog_with_href_caches_by_href(self):
        cat = TestCases.test_case_1()
        cache = cat._resolved_objects

        # Since all of our STAC objects have HREFs, everything should be
        # cached only by HREF
        self.assertEqual(len(cache.id_keys_to_objects), 0)


class FullCopyTest(unittest.TestCase):
    def check_link(self, link, tag):
        if link.is_resolved():
            target_href = link.target.get_self_href()
        else:
            target_href = link.target
        self.assertTrue(tag in target_href,
                        '[{}] {} does not contain "{}"'.format(link.rel, target_href, tag))

    def check_item(self, item, tag):
        for link in item.links:
            self.check_link(link, tag)

    def check_catalog(self, c, tag):
        self.assertEqual(len(c.get_links('root')), 1)

        for link in c.links:
            self.check_link(link, tag)

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

            cat.add_item(item)

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
                image_item.add_asset(
                    key, Asset(href='some/{}.tif'.format(key), media_type=MediaType.GEOTIFF))

            label_item = Item(id='Labels',
                              geometry=RANDOM_GEOM,
                              bbox=RANDOM_BBOX,
                              datetime=datetime.utcnow(),
                              properties={},
                              stac_extensions=[Extensions.LABEL])
            label_ext = label_item.ext.label
            label_ext.apply(
                label_description='labels',
                label_type='vector',
                label_properties=['label'],
                label_classes=[LabelClasses.create(classes=['one', 'two'], name='label')],
                label_tasks=['classification'])
            label_ext.add_source(image_item, assets=['ortho'])

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
