# TODO move all test case code to this file

from datetime import datetime

import pytest

from pystac import Catalog, Collection, Item

from .utils import ARBITRARY_BBOX, ARBITRARY_EXTENT, ARBITRARY_GEOM, TestCases


@pytest.fixture
def catalog() -> Catalog:
    return Catalog("test-catalog", "A test catalog")


@pytest.fixture
def collection() -> Catalog:
    return Collection("test-collection", "A test collection", ARBITRARY_EXTENT)


@pytest.fixture
def item() -> Item:
    return Item("test-item", ARBITRARY_GEOM, ARBITRARY_BBOX, datetime.now(), {})


@pytest.fixture
def test_case_1_catalog() -> Catalog:
    return TestCases.case_1()


@pytest.fixture
def projection_landsat8_item() -> Item:
    path = TestCases.get_path("data-files/projection/example-landsat8.json")
    return Item.from_file(path)


@pytest.fixture
def sample_item() -> Item:
    return Item.from_file(TestCases.get_path("data-files/item/sample-item.json"))
