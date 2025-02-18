import unittest
from typing import Any

import pystac
from pystac.cache import ResolvedObjectCache, ResolvedObjectCollectionCache
from pystac.utils import get_opt
from tests.utils import TestCases


def create_catalog(suffix: Any, include_href: bool = True) -> pystac.Catalog:
    return pystac.Catalog(
        id=f"test {suffix}",
        description=f"test desc {suffix}",
        href=(f"http://example.com/catalog_{suffix}.json" if include_href else None),
    )


def test_ResolvedObjectCache_get_or_cache_returns_previously_cached_href() -> None:
    cache = ResolvedObjectCache()
    cat = create_catalog(1)
    cache_result_1 = cache.get_or_cache(cat)
    assert cache_result_1 is cat

    identical_cat = create_catalog(1)
    cache_result_2 = cache.get_or_cache(identical_cat)
    assert cache_result_2 is cat

def test_ResolvedObjectCache_get_or_cache_returns_previously_cached_id() -> None:
    cache = ResolvedObjectCache()
    cat = create_catalog(1, include_href=False)
    cache_result_1 = cache.get_or_cache(cat)
    assert cache_result_1 is cat

    identical_cat = create_catalog(1, include_href=False)
    cache_result_2 = cache.get_or_cache(identical_cat)
    assert cache_result_2 is cat


# class ResolvedObjectCollectionCacheTest(unittest.TestCase):
def test_ResolvedObjectCollectionCache_merge() -> None:
    cat1 = create_catalog(1, include_href=False)
    cat2 = create_catalog(2)
    cat3 = create_catalog(3, include_href=False)
    cat4 = create_catalog(4)

    identical_cat1 = create_catalog(1, include_href=False)
    identical_cat2 = create_catalog(2)

    cached_ids_1: dict[str, Any] = {cat1.id: cat1}
    cached_hrefs_1: dict[str, Any] = {get_opt(cat2.get_self_href()): cat2}
    cached_ids_2: dict[str, Any] = {cat3.id: cat3, cat1.id: identical_cat1}
    cached_hrefs_2: dict[str, Any] = {
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

    assert set(merged.cached_ids.keys()) == {cat.id for cat in [cat1, cat3]}
    assert merged.get_by_id(cat1.id) is cat1
    assert set(merged.cached_hrefs.keys()) == {cat.get_self_href() for cat in [cat2, cat4]}
    assert merged.get_by_href(get_opt(cat2.get_self_href())) is cat2

def test_ResolvedObjectCollectionCache_cache() -> None:
    cache = ResolvedObjectCache().as_collection_cache()
    collection = TestCases.case_8()
    collection_json = collection.to_dict()
    cache.cache(collection_json, collection.get_self_href())
    cached = cache.get_by_id(collection.id)
    assert isinstance(cached, dict)
    assert cached["id"] == collection.id
