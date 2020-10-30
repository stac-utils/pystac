from datetime import (datetime, timedelta)
import os
import unittest

import pystac
from pystac.layout import (LayoutTemplate, CustomLayoutStrategy, TemplateLayoutStrategy,
                           BestPracticesLayoutStrategy, TemplateError)
from tests.utils import (TestCases, RANDOM_GEOM, RANDOM_BBOX)


class LayoutTemplateTest(unittest.TestCase):
    def test_templates_item_datetime(self):
        year = 2020
        month = 11
        day = 3
        date = '2020-11-03'
        dt = datetime(year, month, day, 18, 30)

        template = LayoutTemplate('${year}/${month}/${day}/${date}/item.json')

        item = pystac.Item('test',
                           geometry=RANDOM_GEOM,
                           bbox=RANDOM_BBOX,
                           datetime=dt,
                           properties={})

        parts = template.get_template_values(item)

        self.assertEqual(set(parts), set(['year', 'month', 'day', 'date']))

        self.assertEqual(parts['year'], year)
        self.assertEqual(parts['month'], month)
        self.assertEqual(parts['day'], day)
        self.assertEqual(parts['date'], date)

        path = template.substitute(item)
        self.assertEqual(path, '2020/11/3/2020-11-03/item.json')

    def test_templates_item_start_datetime(self):
        year = 2020
        month = 11
        day = 3
        date = '2020-11-03'
        dt = datetime(year, month, day, 18, 30)

        template = LayoutTemplate('${year}/${month}/${day}/${date}/item.json')

        item = pystac.Item('test',
                           geometry=RANDOM_GEOM,
                           bbox=RANDOM_BBOX,
                           datetime=None,
                           properties={
                               'start_datetime': dt.isoformat(),
                               'end_datetime': (dt + timedelta(days=1)).isoformat()
                           })

        parts = template.get_template_values(item)

        self.assertEqual(set(parts), set(['year', 'month', 'day', 'date']))

        self.assertEqual(parts['year'], year)
        self.assertEqual(parts['month'], month)
        self.assertEqual(parts['day'], day)
        self.assertEqual(parts['date'], date)

        path = template.substitute(item)
        self.assertEqual(path, '2020/11/3/2020-11-03/item.json')

    def test_templates_item_collection(self):
        template = LayoutTemplate('${collection}/item.json')

        collection = TestCases.test_case_4().get_child('acc')
        item = next(collection.get_all_items())
        assert item.collection_id is not None

        parts = template.get_template_values(item)
        self.assertEqual(len(parts), 1)
        self.assertIn('collection', parts)
        self.assertEqual(parts['collection'], item.collection_id)

        path = template.substitute(item)
        self.assertEqual(path, '{}/item.json'.format(item.collection_id))

    def test_throws_for_no_collection(self):
        template = LayoutTemplate('${collection}/item.json')

        collection = TestCases.test_case_4().get_child('acc')
        item = next(collection.get_all_items())
        item.set_collection(None)
        assert item.collection_id is None

        with self.assertRaises(TemplateError):
            template.get_template_values(item)

    def test_nested_properties(self):
        dt = datetime(2020, 11, 3, 18, 30)

        template = LayoutTemplate('${test.prop}/${ext:extra.test.prop}/item.json')

        item = pystac.Item('test',
                           geometry=RANDOM_GEOM,
                           bbox=RANDOM_BBOX,
                           datetime=dt,
                           properties={'test': {
                               'prop': 4326
                           }},
                           extra_fields={'ext:extra': {
                               'test': {
                                   'prop': 3857
                               }
                           }})

        parts = template.get_template_values(item)

        self.assertEqual(set(parts), set(['test.prop', 'ext:extra.test.prop']))

        self.assertEqual(parts['test.prop'], 4326)
        self.assertEqual(parts['ext:extra.test.prop'], 3857)

        path = template.substitute(item)

        self.assertEqual(path, '4326/3857/item.json')

    def test_substitute_with_colon_properties(self):
        dt = datetime(2020, 11, 3, 18, 30)

        template = LayoutTemplate('${ext:prop}/item.json')

        item = pystac.Item('test',
                           geometry=RANDOM_GEOM,
                           bbox=RANDOM_BBOX,
                           datetime=dt,
                           properties={'ext:prop': 1})

        path = template.substitute(item)

        self.assertEqual(path, "1/item.json")

    def test_defaults(self):
        template = LayoutTemplate('${doesnotexist}/collection.json',
                                  defaults={'doesnotexist': 'yes'})

        collection = TestCases.test_case_4().get_child('acc')
        collection.properties = {'up': 'down'}
        collection.extra_fields = {'one': 'two'}
        path = template.substitute(collection)

        self.assertEqual(path, 'yes/collection.json')

    def test_docstring_examples(self):
        item = pystac.read_file(
            TestCases.get_path(
                "data-files/examples/1.0.0-beta.2/item-spec/examples/landsat8-sample.json"))
        item.common_metadata.license = "CC-BY-3.0"
        # Uses the year, month and day of the item
        template1 = LayoutTemplate("${year}/${month}/${day}")
        path1 = template1.substitute(item)
        self.assertEqual(path1, '2014/6/2')

        # Uses a custom extension properties found on in the item properties.
        template2 = LayoutTemplate("${landsat:path}/${landsat:row}")
        path2 = template2.substitute(item)
        self.assertEqual(path2, '107/18')

        # Uses the collection ID and a common metadata property for an item.
        template3 = LayoutTemplate("${collection}/${common_metadata.license}")
        path3 = template3.substitute(item)
        self.assertEqual(path3, 'landsat-8-l1/CC-BY-3.0')


class CustomLayoutStrategyTest(unittest.TestCase):
    def get_custom_catalog_func(self):
        def fn(cat, parent_dir, is_root):
            return os.path.join(parent_dir, 'cat/{}/{}.json'.format(is_root, cat.id))

        return fn

    def get_custom_collection_func(self):
        def fn(col, parent_dir, is_root):
            return os.path.join(parent_dir, 'col/{}/{}.json'.format(is_root, col.id))

        return fn

    def get_custom_item_func(self):
        def fn(item, parent_dir):
            return os.path.join(parent_dir, 'item/{}.json'.format(item.id))

        return fn

    def test_produces_layout_for_catalog(self):
        strategy = CustomLayoutStrategy(catalog_func=self.get_custom_catalog_func())
        cat = pystac.Catalog(id='test', description='test desc')
        href = strategy.get_href(cat, parent_dir='http://example.com', is_root=True)
        self.assertEqual(href, 'http://example.com/cat/True/test.json')

    def test_produces_fallback_layout_for_catalog(self):
        fallback = BestPracticesLayoutStrategy()
        strategy = CustomLayoutStrategy(collection_func=self.get_custom_collection_func(),
                                        item_func=self.get_custom_item_func(),
                                        fallback_strategy=fallback)
        cat = pystac.Catalog(id='test', description='test desc')
        href = strategy.get_href(cat, parent_dir='http://example.com')
        expected = fallback.get_href(cat, parent_dir='http://example.com')
        self.assertEqual(href, expected)

    def test_produces_layout_for_collection(self):
        strategy = CustomLayoutStrategy(collection_func=self.get_custom_collection_func())
        collection = TestCases.test_case_8()
        href = strategy.get_href(collection, parent_dir='http://example.com')
        self.assertEqual(href, 'http://example.com/col/False/{}.json'.format(collection.id))

    def test_produces_fallback_layout_for_collection(self):
        fallback = BestPracticesLayoutStrategy()
        strategy = CustomLayoutStrategy(catalog_func=self.get_custom_catalog_func(),
                                        item_func=self.get_custom_item_func(),
                                        fallback_strategy=fallback)
        collection = TestCases.test_case_8()
        href = strategy.get_href(collection, parent_dir='http://example.com')
        expected = fallback.get_href(collection, parent_dir='http://example.com')
        self.assertEqual(href, expected)

    def test_produces_layout_for_item(self):
        strategy = CustomLayoutStrategy(item_func=self.get_custom_item_func())
        collection = TestCases.test_case_8()
        item = next(collection.get_all_items())
        href = strategy.get_href(item, parent_dir='http://example.com')
        self.assertEqual(href, 'http://example.com/item/{}.json'.format(item.id))

    def test_produces_fallback_layout_for_item(self):
        fallback = BestPracticesLayoutStrategy()
        strategy = CustomLayoutStrategy(catalog_func=self.get_custom_item_func(),
                                        collection_func=self.get_custom_collection_func(),
                                        fallback_strategy=fallback)
        collection = TestCases.test_case_8()
        item = next(collection.get_all_items())
        href = strategy.get_href(item, parent_dir='http://example.com')
        expected = fallback.get_href(item, parent_dir='http://example.com')
        self.assertEqual(href, expected)


class TemplateLayoutStrategyTest(unittest.TestCase):
    TEST_CATALOG_TEMPLATE = 'cat/${id}/${description}'
    TEST_COLLECTION_TEMPLATE = 'col/${id}/${license}'
    TEST_ITEM_TEMPLATE = 'item/${collection}/${id}.json'

    def test_produces_layout_for_catalog(self):
        strategy = TemplateLayoutStrategy(catalog_template=self.TEST_CATALOG_TEMPLATE)
        cat = pystac.Catalog(id='test', description='test-desc')
        href = strategy.get_href(cat, parent_dir='http://example.com')
        self.assertEqual(href, 'http://example.com/cat/test/test-desc/catalog.json')

    def test_produces_layout_for_catalog_with_filename(self):
        template = 'cat/${id}/${description}/${id}.json'
        strategy = TemplateLayoutStrategy(catalog_template=template)
        cat = pystac.Catalog(id='test', description='test-desc')
        href = strategy.get_href(cat, parent_dir='http://example.com')
        self.assertEqual(href, 'http://example.com/cat/test/test-desc/test.json')

    def test_produces_fallback_layout_for_catalog(self):
        fallback = BestPracticesLayoutStrategy()
        strategy = TemplateLayoutStrategy(collection_template=self.TEST_COLLECTION_TEMPLATE,
                                          item_template=self.TEST_ITEM_TEMPLATE,
                                          fallback_strategy=fallback)
        cat = pystac.Catalog(id='test', description='test desc')
        href = strategy.get_href(cat, parent_dir='http://example.com')
        expected = fallback.get_href(cat, parent_dir='http://example.com')
        self.assertEqual(href, expected)

    def test_produces_layout_for_collection(self):
        strategy = TemplateLayoutStrategy(collection_template=self.TEST_COLLECTION_TEMPLATE)
        collection = TestCases.test_case_4().get_child('acc')
        href = strategy.get_href(collection, parent_dir='http://example.com')
        self.assertEqual(
            href,
            'http://example.com/col/{}/{}/collection.json'.format(collection.id,
                                                                  collection.license))

    def test_produces_layout_for_collection_with_filename(self):
        template = 'col/${id}/${license}/col.json'
        strategy = TemplateLayoutStrategy(collection_template=template)
        collection = TestCases.test_case_4().get_child('acc')
        href = strategy.get_href(collection, parent_dir='http://example.com')
        self.assertEqual(
            href, 'http://example.com/col/{}/{}/col.json'.format(collection.id, collection.license))

    def test_produces_fallback_layout_for_collection(self):
        fallback = BestPracticesLayoutStrategy()
        strategy = TemplateLayoutStrategy(catalog_template=self.TEST_CATALOG_TEMPLATE,
                                          item_template=self.TEST_ITEM_TEMPLATE,
                                          fallback_strategy=fallback)
        collection = TestCases.test_case_4().get_child('acc')
        href = strategy.get_href(collection, parent_dir='http://example.com')
        expected = fallback.get_href(collection, parent_dir='http://example.com')
        self.assertEqual(href, expected)

    def test_produces_layout_for_item(self):
        strategy = TemplateLayoutStrategy(item_template=self.TEST_ITEM_TEMPLATE)
        collection = TestCases.test_case_4().get_child('acc')
        item = next(collection.get_all_items())
        href = strategy.get_href(item, parent_dir='http://example.com')
        self.assertEqual(href,
                         'http://example.com/item/{}/{}.json'.format(item.collection_id, item.id))

    def test_produces_layout_for_item_without_filename(self):
        template = 'item/${collection}'
        strategy = TemplateLayoutStrategy(item_template=template)
        collection = TestCases.test_case_4().get_child('acc')
        item = next(collection.get_all_items())
        href = strategy.get_href(item, parent_dir='http://example.com')
        self.assertEqual(href,
                         'http://example.com/item/{}/{}.json'.format(item.collection_id, item.id))

    def test_produces_fallback_layout_for_item(self):
        fallback = BestPracticesLayoutStrategy()
        strategy = TemplateLayoutStrategy(catalog_template=self.TEST_CATALOG_TEMPLATE,
                                          collection_template=self.TEST_COLLECTION_TEMPLATE,
                                          fallback_strategy=fallback)
        collection = TestCases.test_case_4().get_child('acc')
        item = next(collection.get_all_items())
        href = strategy.get_href(item, parent_dir='http://example.com')
        expected = fallback.get_href(item, parent_dir='http://example.com')
        self.assertEqual(href, expected)


class BestPracticesLayoutStrategyTest(unittest.TestCase):
    def setUp(self):
        self.strategy = BestPracticesLayoutStrategy()

    def test_produces_layout_for_root_catalog(self):
        cat = pystac.Catalog(id='test', description='test desc')
        href = self.strategy.get_href(cat, parent_dir='http://example.com', is_root=True)
        self.assertEqual(href, 'http://example.com/catalog.json')

    def test_produces_layout_for_child_catalog(self):
        cat = pystac.Catalog(id='test', description='test desc')
        href = self.strategy.get_href(cat, parent_dir='http://example.com')
        self.assertEqual(href, 'http://example.com/test/catalog.json')

    def test_produces_layout_for_root_collection(self):
        collection = TestCases.test_case_8()
        href = self.strategy.get_href(collection, parent_dir='http://example.com', is_root=True)
        self.assertEqual(href, 'http://example.com/collection.json')

    def test_produces_layout_for_child_collection(self):
        collection = TestCases.test_case_8()
        href = self.strategy.get_href(collection, parent_dir='http://example.com')
        self.assertEqual(href, 'http://example.com/{}/collection.json'.format(collection.id))

    def test_produces_layout_for_item(self):
        collection = TestCases.test_case_8()
        item = next(collection.get_all_items())
        href = self.strategy.get_href(item, parent_dir='http://example.com')
        expected = 'http://example.com/{}/{}.json'.format(item.id, item.id)
        self.assertEqual(href, expected)
