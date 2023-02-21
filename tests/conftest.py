from datetime import datetime

import pytest
from pytest import FixtureRequest

from pystac import Catalog, Collection, Item

from .utils import ARBITRARY_BBOX, ARBITRARY_EXTENT, ARBITRARY_GEOM, TestCases


@pytest.fixture
def catalog() -> Catalog:
    return Catalog("test-catalog", "A test catalog")


@pytest.fixture
def prebuilt_catalog_1() -> Catalog:
    path = TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
    return Catalog.from_file(path)


@pytest.fixture
def prebuilt_catalog_2() -> Catalog:
    path = TestCases.get_path("data-files/catalogs/test-case-2/catalog.json")
    return Catalog.from_file(path)


@pytest.fixture
def prebuilt_catalog_4() -> Catalog:
    path = TestCases.get_path("data-files/catalogs/test-case-4/catalog.json")
    return Catalog.from_file(path)


@pytest.fixture
def prebuilt_catalog_5() -> Catalog:
    path = TestCases.get_path("data-files/catalogs/test-case-5/catalog.json")
    return Catalog.from_file(path)


@pytest.fixture
def prebuilt_catalog_6() -> Catalog:
    path = TestCases.get_path("data-files/catalogs/test-case-6/catalog.json")
    return Catalog.from_file(path)


@pytest.fixture(params=["1", "2", "4", "5", "6"])
def prebuilt_catalog(request: FixtureRequest) -> Catalog:
    path = TestCases.get_path(
        f"data-files/catalogs/test-case-{request.param}/catalog.json"
    )
    return Catalog.from_file(path)


@pytest.fixture
def collection() -> Catalog:
    return Collection("test-collection", "A test collection", ARBITRARY_EXTENT)


@pytest.fixture
def item() -> Item:
    return Item("test-item", ARBITRARY_GEOM, ARBITRARY_BBOX, datetime.now(), {})
