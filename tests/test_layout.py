import posixpath
import unittest
from datetime import datetime, timedelta
from typing import Callable

import pytest

import pystac
from pystac.collection import Collection
from pystac.layout import (
    APILayoutStrategy,
    AsIsLayoutStrategy,
    BestPracticesLayoutStrategy,
    CustomLayoutStrategy,
    LayoutTemplate,
    TemplateLayoutStrategy,
)
from tests.utils import ARBITRARY_BBOX, ARBITRARY_GEOM, TestCases


class LayoutTemplateTest(unittest.TestCase):
    def test_templates_item_datetime(self) -> None:
        year = 2020
        month = 11
        day = 3
        date = "2020-11-03"
        dt = datetime(year, month, day, 18, 30)

        template = LayoutTemplate("${year}/${month}/${day}/${date}/item.json")

        item = pystac.Item(
            "test",
            geometry=ARBITRARY_GEOM,
            bbox=ARBITRARY_BBOX,
            datetime=dt,
            properties={},
        )

        parts = template.get_template_values(item)

        self.assertEqual(set(parts), {"year", "month", "day", "date"})

        self.assertEqual(parts["year"], year)
        self.assertEqual(parts["month"], month)
        self.assertEqual(parts["day"], day)
        self.assertEqual(parts["date"], date)

        path = template.substitute(item)
        self.assertEqual(path, "2020/11/3/2020-11-03/item.json")

    def test_templates_item_start_datetime(self) -> None:
        year = 2020
        month = 11
        day = 3
        date = "2020-11-03"
        dt = datetime(year, month, day, 18, 30)

        template = LayoutTemplate("${year}/${month}/${day}/${date}/item.json")

        item = pystac.Item(
            "test",
            geometry=ARBITRARY_GEOM,
            bbox=ARBITRARY_BBOX,
            datetime=None,
            properties={
                "start_datetime": dt.isoformat(),
                "end_datetime": (dt + timedelta(days=1)).isoformat(),
            },
        )

        parts = template.get_template_values(item)

        self.assertEqual(set(parts), {"year", "month", "day", "date"})

        self.assertEqual(parts["year"], year)
        self.assertEqual(parts["month"], month)
        self.assertEqual(parts["day"], day)
        self.assertEqual(parts["date"], date)

        path = template.substitute(item)
        self.assertEqual(path, "2020/11/3/2020-11-03/item.json")

    def test_templates_item_collection(self) -> None:
        template = LayoutTemplate("${collection}/item.json")

        collection = TestCases.case_4().get_child("acc")
        assert collection is not None
        item = next(collection.get_items())
        assert item.collection_id is not None

        parts = template.get_template_values(item)
        self.assertEqual(len(parts), 1)
        self.assertIn("collection", parts)
        self.assertEqual(parts["collection"], item.collection_id)

        path = template.substitute(item)
        self.assertEqual(path, f"{item.collection_id}/item.json")

    def test_throws_for_no_collection(self) -> None:
        template = LayoutTemplate("${collection}/item.json")

        collection = TestCases.case_4().get_child("acc")
        assert collection is not None
        item = next(collection.get_items())
        item.set_collection(None)
        assert item.collection_id is None

        with self.assertRaises(pystac.TemplateError):
            template.get_template_values(item)

    def test_nested_properties(self) -> None:
        dt = datetime(2020, 11, 3, 18, 30)

        template = LayoutTemplate("${test.prop}/${ext:extra.test.prop}/item.json")

        item = pystac.Item(
            "test",
            geometry=ARBITRARY_GEOM,
            bbox=ARBITRARY_BBOX,
            datetime=dt,
            properties={"test": {"prop": 4326}},
            extra_fields={"ext:extra": {"test": {"prop": 3857}}},
        )

        parts = template.get_template_values(item)

        self.assertEqual(set(parts), {"test.prop", "ext:extra.test.prop"})

        self.assertEqual(parts["test.prop"], 4326)
        self.assertEqual(parts["ext:extra.test.prop"], 3857)

        path = template.substitute(item)

        self.assertEqual(path, "4326/3857/item.json")

    def test_substitute_with_colon_properties(self) -> None:
        dt = datetime(2020, 11, 3, 18, 30)

        template = LayoutTemplate("${ext:prop}/item.json")

        item = pystac.Item(
            "test",
            geometry=ARBITRARY_GEOM,
            bbox=ARBITRARY_BBOX,
            datetime=dt,
            properties={"ext:prop": 1},
        )

        path = template.substitute(item)

        self.assertEqual(path, "1/item.json")

    def test_defaults(self) -> None:
        template = LayoutTemplate(
            "${doesnotexist}/collection.json", defaults={"doesnotexist": "yes"}
        )

        catalog = TestCases.case_4().get_child("acc")
        assert catalog is not None
        catalog.extra_fields = {"one": "two"}
        path = template.substitute(catalog)

        self.assertEqual(path, "yes/collection.json")

    def test_docstring_examples(self) -> None:
        item = pystac.Item.from_file(
            TestCases.get_path(
                "data-files/examples/1.0.0-beta.2/item-spec/"
                "examples/landsat8-sample.json"
            )
        )
        item.common_metadata.license = "CC-BY-3.0"
        # Uses the year, month and day of the item
        template1 = LayoutTemplate("${year}/${month}/${day}")
        path1 = template1.substitute(item)
        self.assertEqual(path1, "2014/6/2")

        # Uses a custom extension properties found on in the item properties.
        template2 = LayoutTemplate("${landsat:path}/${landsat:row}")
        path2 = template2.substitute(item)
        self.assertEqual(path2, "107/18")

        # Uses the collection ID and a common metadata property for an item.
        template3 = LayoutTemplate("${collection}/${common_metadata.license}")
        path3 = template3.substitute(item)
        self.assertEqual(path3, "landsat-8-l1/CC-BY-3.0")


class CustomLayoutStrategyTest(unittest.TestCase):
    def get_custom_catalog_func(self) -> Callable[[pystac.Catalog, str, bool], str]:
        def fn(cat: pystac.Catalog, parent_dir: str, is_root: bool) -> str:
            return posixpath.join(parent_dir, f"cat/{is_root}/{cat.id}.json")

        return fn

    def get_custom_collection_func(
        self,
    ) -> Callable[[pystac.Collection, str, bool], str]:
        def fn(col: pystac.Collection, parent_dir: str, is_root: bool) -> str:
            return posixpath.join(parent_dir, f"col/{is_root}/{col.id}.json")

        return fn

    def get_custom_item_func(self) -> Callable[[pystac.Item, str], str]:
        def fn(item: pystac.Item, parent_dir: str) -> str:
            return posixpath.join(parent_dir, f"item/{item.id}.json")

        return fn

    def test_produces_layout_for_catalog(self) -> None:
        strategy = CustomLayoutStrategy(catalog_func=self.get_custom_catalog_func())
        cat = pystac.Catalog(id="test", description="test desc")
        href = strategy.get_href(cat, parent_dir="http://example.com", is_root=True)
        self.assertEqual(href, "http://example.com/cat/True/test.json")

    def test_produces_fallback_layout_for_catalog(self) -> None:
        fallback = BestPracticesLayoutStrategy()
        strategy = CustomLayoutStrategy(
            collection_func=self.get_custom_collection_func(),
            item_func=self.get_custom_item_func(),
            fallback_strategy=fallback,
        )
        cat = pystac.Catalog(id="test", description="test desc")
        href = strategy.get_href(cat, parent_dir="http://example.com")
        expected = fallback.get_href(cat, parent_dir="http://example.com")
        self.assertEqual(href, expected)

    def test_produces_layout_for_collection(self) -> None:
        strategy = CustomLayoutStrategy(
            collection_func=self.get_custom_collection_func()
        )
        collection = TestCases.case_8()
        href = strategy.get_href(collection, parent_dir="http://example.com")
        self.assertEqual(href, f"http://example.com/col/False/{collection.id}.json")

    def test_produces_fallback_layout_for_collection(self) -> None:
        fallback = BestPracticesLayoutStrategy()
        strategy = CustomLayoutStrategy(
            catalog_func=self.get_custom_catalog_func(),
            item_func=self.get_custom_item_func(),
            fallback_strategy=fallback,
        )
        collection = TestCases.case_8()
        href = strategy.get_href(collection, parent_dir="http://example.com")
        expected = fallback.get_href(collection, parent_dir="http://example.com")
        self.assertEqual(href, expected)

    def test_produces_layout_for_item(self) -> None:
        strategy = CustomLayoutStrategy(item_func=self.get_custom_item_func())
        collection = TestCases.case_8()
        item = next(collection.get_items(recursive=True))
        href = strategy.get_href(item, parent_dir="http://example.com")
        self.assertEqual(href, f"http://example.com/item/{item.id}.json")

    def test_produces_fallback_layout_for_item(self) -> None:
        fallback = BestPracticesLayoutStrategy()
        strategy = CustomLayoutStrategy(
            catalog_func=self.get_custom_catalog_func(),
            collection_func=self.get_custom_collection_func(),
            fallback_strategy=fallback,
        )
        collection = TestCases.case_8()
        item = next(collection.get_items(recursive=True))
        href = strategy.get_href(item, parent_dir="http://example.com")
        expected = fallback.get_href(item, parent_dir="http://example.com")
        self.assertEqual(href, expected)


class TemplateLayoutStrategyTest(unittest.TestCase):
    TEST_CATALOG_TEMPLATE = "cat/${id}/${description}"
    TEST_COLLECTION_TEMPLATE = "col/${id}/${license}"
    TEST_ITEM_TEMPLATE = "item/${collection}/${id}.json"

    def _get_collection(self) -> Collection:
        result = TestCases.case_4().get_child("acc")
        assert isinstance(result, Collection)
        return result

    def test_produces_layout_for_catalog(self) -> None:
        strategy = TemplateLayoutStrategy(catalog_template=self.TEST_CATALOG_TEMPLATE)
        cat = pystac.Catalog(id="test", description="test-desc")
        href = strategy.get_href(cat, parent_dir="http://example.com")
        self.assertEqual(href, "http://example.com/cat/test/test-desc/catalog.json")

    def test_produces_layout_for_catalog_with_filename(self) -> None:
        template = "cat/${id}/${description}/${id}.json"
        strategy = TemplateLayoutStrategy(catalog_template=template)
        cat = pystac.Catalog(id="test", description="test-desc")
        href = strategy.get_href(cat, parent_dir="http://example.com")
        self.assertEqual(href, "http://example.com/cat/test/test-desc/test.json")

    def test_produces_fallback_layout_for_catalog(self) -> None:
        fallback = BestPracticesLayoutStrategy()
        strategy = TemplateLayoutStrategy(
            collection_template=self.TEST_COLLECTION_TEMPLATE,
            item_template=self.TEST_ITEM_TEMPLATE,
            fallback_strategy=fallback,
        )
        cat = pystac.Catalog(id="test", description="test desc")
        href = strategy.get_href(cat, parent_dir="http://example.com")
        expected = fallback.get_href(cat, parent_dir="http://example.com")
        self.assertEqual(href, expected)

    def test_produces_layout_for_collection(self) -> None:
        strategy = TemplateLayoutStrategy(
            collection_template=self.TEST_COLLECTION_TEMPLATE
        )
        collection = self._get_collection()
        href = strategy.get_href(collection, parent_dir="http://example.com")
        self.assertEqual(
            href,
            "http://example.com/col/{}/{}/collection.json".format(
                collection.id, collection.license
            ),
        )

    def test_produces_layout_for_collection_with_filename(self) -> None:
        template = "col/${id}/${license}/col.json"
        strategy = TemplateLayoutStrategy(collection_template=template)
        collection = self._get_collection()
        href = strategy.get_href(collection, parent_dir="http://example.com")
        self.assertEqual(
            href,
            "http://example.com/col/{}/{}/col.json".format(
                collection.id, collection.license
            ),
        )

    def test_produces_fallback_layout_for_collection(self) -> None:
        fallback = BestPracticesLayoutStrategy()
        strategy = TemplateLayoutStrategy(
            catalog_template=self.TEST_CATALOG_TEMPLATE,
            item_template=self.TEST_ITEM_TEMPLATE,
            fallback_strategy=fallback,
        )
        collection = self._get_collection()
        href = strategy.get_href(collection, parent_dir="http://example.com")
        expected = fallback.get_href(collection, parent_dir="http://example.com")
        self.assertEqual(href, expected)

    def test_produces_layout_for_item(self) -> None:
        strategy = TemplateLayoutStrategy(item_template=self.TEST_ITEM_TEMPLATE)
        collection = self._get_collection()
        item = next(collection.get_items())
        href = strategy.get_href(item, parent_dir="http://example.com")
        self.assertEqual(
            href,
            f"http://example.com/item/{item.collection_id}/{item.id}.json",
        )

    def test_produces_layout_for_item_without_filename(self) -> None:
        template = "item/${collection}"
        strategy = TemplateLayoutStrategy(item_template=template)
        collection = self._get_collection()
        item = next(collection.get_items())
        href = strategy.get_href(item, parent_dir="http://example.com")
        self.assertEqual(
            href,
            f"http://example.com/item/{item.collection_id}/{item.id}.json",
        )

    def test_produces_fallback_layout_for_item(self) -> None:
        fallback = BestPracticesLayoutStrategy()
        strategy = TemplateLayoutStrategy(
            catalog_template=self.TEST_CATALOG_TEMPLATE,
            collection_template=self.TEST_COLLECTION_TEMPLATE,
            fallback_strategy=fallback,
        )
        collection = self._get_collection()
        item = next(collection.get_items())
        href = strategy.get_href(item, parent_dir="http://example.com")
        expected = fallback.get_href(item, parent_dir="http://example.com")
        self.assertEqual(href, expected)


class BestPracticesLayoutStrategyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = BestPracticesLayoutStrategy()

    def test_produces_layout_for_root_catalog(self) -> None:
        cat = pystac.Catalog(id="test", description="test desc")
        href = self.strategy.get_href(
            cat, parent_dir="http://example.com", is_root=True
        )
        self.assertEqual(href, "http://example.com/catalog.json")

    def test_produces_layout_for_child_catalog(self) -> None:
        cat = pystac.Catalog(id="test", description="test desc")
        href = self.strategy.get_href(cat, parent_dir="http://example.com")
        self.assertEqual(href, "http://example.com/test/catalog.json")

    def test_produces_layout_for_root_collection(self) -> None:
        collection = TestCases.case_8()
        href = self.strategy.get_href(
            collection, parent_dir="http://example.com", is_root=True
        )
        self.assertEqual(href, "http://example.com/collection.json")

    def test_produces_layout_for_child_collection(self) -> None:
        collection = TestCases.case_8()
        href = self.strategy.get_href(collection, parent_dir="http://example.com")
        self.assertEqual(href, f"http://example.com/{collection.id}/collection.json")

    def test_produces_layout_for_item(self) -> None:
        collection = TestCases.case_8()
        item = next(collection.get_items(recursive=True))
        href = self.strategy.get_href(item, parent_dir="http://example.com")
        expected = f"http://example.com/{item.id}/{item.id}.json"
        self.assertEqual(href, expected)


class AsIsLayoutStrategyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = AsIsLayoutStrategy()

    def test_catalog(self) -> None:
        cat = pystac.Catalog(id="test", description="test desc")
        with self.assertRaises(ValueError):
            self.strategy.get_href(cat, parent_dir="http://example.com", is_root=True)
        cat.set_self_href("/an/href")
        href = self.strategy.get_href(
            cat, parent_dir="https://example.com", is_root=True
        )
        self.assertEqual(href, "/an/href")

    def test_collection(self) -> None:
        collection = TestCases.case_8()
        collection.set_self_href(None)
        with self.assertRaises(ValueError):
            self.strategy.get_href(
                collection, parent_dir="http://example.com", is_root=True
            )
        collection.set_self_href("/an/href")
        href = self.strategy.get_href(
            collection, parent_dir="https://example.com", is_root=True
        )
        self.assertEqual(href, "/an/href")

    def test_item(self) -> None:
        collection = TestCases.case_8()
        item = next(collection.get_items(recursive=True))
        item.set_self_href(None)
        with self.assertRaises(ValueError):
            self.strategy.get_href(item, parent_dir="http://example.com")
        item.set_self_href("/an/href")
        href = self.strategy.get_href(item, parent_dir="http://example.com")
        self.assertEqual(href, "/an/href")


class APILayoutStrategyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = APILayoutStrategy()

    def test_produces_layout_for_root_catalog(self) -> None:
        cat = pystac.Catalog(id="test", description="test desc")
        href = self.strategy.get_href(
            cat, parent_dir="http://example.com", is_root=True
        )
        self.assertEqual(href, "http://example.com")

    def test_produces_layout_for_child_catalog(self) -> None:
        cat = pystac.Catalog(id="test", description="test desc")
        href = self.strategy.get_href(cat, parent_dir="http://example.com")
        self.assertEqual(href, "http://example.com/test")

    def test_cannot_produce_layout_for_root_collection(self) -> None:
        collection = TestCases.case_8()
        with pytest.raises(ValueError):
            self.strategy.get_href(
                collection, parent_dir="http://example.com", is_root=True
            )

    def test_produces_layout_for_child_collection(self) -> None:
        collection = TestCases.case_8()
        href = self.strategy.get_href(collection, parent_dir="http://example.com")
        self.assertEqual(href, f"http://example.com/collections/{collection.id}")

    def test_produces_layout_for_item(self) -> None:
        collection = TestCases.case_8()
        col_href = self.strategy.get_href(collection, parent_dir="http://example.com")
        item = next(collection.get_items(recursive=True))
        href = self.strategy.get_href(item, parent_dir=col_href)
        expected = f"http://example.com/collections/{collection.id}/items/{item.id}"
        self.assertEqual(href, expected)

    def test_produces_normalized_layout(self) -> None:
        cat = pystac.Catalog(id="test_catalog", description="Test Catalog")
        col = pystac.Collection(
            id="test_collection",
            description="Test Collection",
            extent=pystac.Extent(
                spatial=pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
                temporal=pystac.TemporalExtent(
                    [[datetime(2023, 1, 1), datetime(2023, 12, 31)]]
                ),
            ),
        )
        item = pystac.Item(
            id="test_item",
            geometry={
                "type": "Polygon",
                "coordinates": [
                    [
                        [180.0, -90.0],
                        [180.0, 90.0],
                        [-180.0, 90.0],
                        [-180.0, -90.0],
                        [180.0, -90.0],
                    ]
                ],
            },
            bbox=[-180, -90, 180, 90],
            datetime=datetime(2023, 1, 1),
            properties={},
            assets={
                "data": pystac.Asset(
                    href="http://example.com/assets/data.tif",
                    roles=["data"],
                    title="DATA",
                )
            },
        )
        cat.add_child(col)
        col.add_item(item)
        cat.normalize_hrefs("http://example.com", strategy=self.strategy)

        assert cat.self_href == "http://example.com"
        assert col.self_href == "http://example.com/collections/test_collection"
        assert (
            item.self_href
            == "http://example.com/collections/test_collection/items/test_item"
        )
