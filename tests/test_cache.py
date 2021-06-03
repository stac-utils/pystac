from typing import Any, Dict
from pystac.utils import get_opt
import unittest

import pystac
from pystac.cache import ResolvedObjectCache, ResolvedObjectCollectionCache
from tests.utils import TestCases


def create_catalog(suffix: Any, include_href: bool = True) -> pystac.Catalog:
    return pystac.Catalog(
        id="test {}".format(suffix),
        description="test desc {}".format(suffix),
        href=(
            "http://example.com/catalog_{}.json".format(suffix)
            if include_href
            else None
        ),
    )


class ResolvedObjectCacheTest(unittest.TestCase):
    def tests_get_or_cache_returns_previously_cached_href(self) -> None:
        cache = ResolvedObjectCache()
        cat = create_catalog(1)
        cache_result_1 = cache.get_or_cache(cat)
        self.assertIs(cache_result_1, cat)

        identical_cat = create_catalog(1)
        cache_result_2 = cache.get_or_cache(identical_cat)
        self.assertIs(cache_result_2, cat)

    def test_get_or_cache_returns_previously_cached_id(self) -> None:
        cache = ResolvedObjectCache()
        cat = create_catalog(1, include_href=False)
        cache_result_1 = cache.get_or_cache(cat)
        self.assertIs(cache_result_1, cat)

        identical_cat = create_catalog(1, include_href=False)
        cache_result_2 = cache.get_or_cache(identical_cat)
        self.assertIs(cache_result_2, cat)


class ResolvedObjectCollectionCacheTest(unittest.TestCase):
    def test_merge(self) -> None:
        cat1 = create_catalog(1, include_href=False)
        cat2 = create_catalog(2)
        cat3 = create_catalog(3, include_href=False)
        cat4 = create_catalog(4)

        identical_cat1 = create_catalog(1, include_href=False)
        identical_cat2 = create_catalog(2)

        cached_ids_1: Dict[str, Any] = {cat1.id: cat1}
        cached_hrefs_1: Dict[str, Any] = {get_opt(cat2.get_self_href()): cat2}
        cached_ids_2: Dict[str, Any] = {cat3.id: cat3, cat1.id: identical_cat1}
        cached_hrefs_2: Dict[str, Any] = {
            get_opt(cat4.get_self_href()): cat4,
            get_opt(cat2.get_self_href()): identical_cat2,
        }
        cache1 = ResolvedObjectCollectionCache(
            ResolvedObjectCache(), cached_ids=cached_ids_1, cached_hrefs=cached_hrefs_1
        )
        cache2 = ResolvedObjectCollectionCache(
            ResolvedObjectCache(), cached_ids=cached_ids_2, cached_hrefs=cached_hrefs_2
        )

        merged = ResolvedObjectCollectionCache.merge(
            ResolvedObjectCache(), cache1, cache2
        )

        self.assertEqual(
            set(merged.cached_ids.keys()), set([cat.id for cat in [cat1, cat3]])
        )
        self.assertIs(merged.get_by_id(cat1.id), cat1)
        self.assertEqual(
            set(merged.cached_hrefs.keys()),
            set([cat.get_self_href() for cat in [cat2, cat4]]),
        )
        self.assertIs(merged.get_by_href(get_opt(cat2.get_self_href())), cat2)

    def test_cache(self) -> None:
        cache = ResolvedObjectCache().as_collection_cache()
        collection = TestCases.test_case_8()
        collection_json = collection.to_dict()
        cache.cache(collection_json, collection.get_self_href())
        cached = cache.get_by_id(collection.id)
        assert isinstance(cached, dict)
        self.assertEqual(cached["id"], collection.id)
