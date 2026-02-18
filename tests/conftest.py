# TODO move all test case code to this file

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

import pytest
from pystac import Asset, Catalog, Collection, Item, ItemCollection

from .utils import TestCases

HERE = Path(__file__).resolve().parent


@pytest.fixture
def multi_extent_collection() -> Collection:
    # TODO this code is repeated many times; refactor to use this fixture
    return Collection.from_file(
        TestCases.get_path("data-files/collections/multi-extent.json")
    )


@pytest.fixture
def test_case_1_catalog() -> Catalog:
    return TestCases.case_1()


@pytest.fixture
def test_case_8_collection() -> Collection:
    return TestCases.case_8()


@pytest.fixture
def projection_landsat8_item() -> Item:
    path = TestCases.get_path("data-files/projection/example-landsat8.json")
    return Item.from_file(path)


def get_data_file(rel_path: str) -> str:
    return str(HERE / "data-files" / rel_path)


@pytest.fixture
def sample_item_dict() -> dict[str, Any]:
    m = TestCases.get_path("data-files/item/sample-item.json")
    with open(m) as f:
        item_dict: dict[str, Any] = json.load(f)
    return item_dict


@pytest.fixture
def sample_item() -> Item:
    return Item.from_file(TestCases.get_path("data-files/item/sample-item.json"))


@pytest.fixture
def sample_item_collection() -> ItemCollection:
    return ItemCollection.from_file(
        TestCases.get_path("data-files/item-collection/sample-item-collection.json")
    )


@pytest.fixture
def sample_items(sample_item_collection: ItemCollection) -> list[Item]:
    return list(sample_item_collection)


@pytest.fixture(scope="function")
def tmp_asset(tmp_path: Path) -> Asset:
    """Copy the entirety of test-case-2 to tmp and"""
    src = get_data_file("catalogs/test-case-2")
    dst = str(tmp_path / str(uuid.uuid4()))
    shutil.copytree(src, dst)

    catalog = Catalog.from_file(f"{dst}/catalog.json")
    item = next(catalog.get_items(recursive=True))
    return next(v for v in item.assets.values())
