from datetime import datetime

import pytest

from pystac import Catalog, Collection, Item

from .utils import ARBITRARY_BBOX, ARBITRARY_EXTENT, ARBITRARY_GEOM


@pytest.fixture
def test_catalog() -> Catalog:
    return Catalog("test-catalog", "A test catalog")


@pytest.fixture
def test_collection() -> Catalog:
    return Collection("test-collection", "A test collection", ARBITRARY_EXTENT)


@pytest.fixture
def test_item() -> Item:
    return Item("test-item", ARBITRARY_GEOM, ARBITRARY_BBOX, datetime.now(), {})
