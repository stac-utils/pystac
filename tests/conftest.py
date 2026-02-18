# TODO move all test case code to this file

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.request import Request

import pytest
from pystac import Asset, Catalog, Collection, Item, ItemCollection, Link

from .utils import ARBITRARY_BBOX, ARBITRARY_EXTENT, ARBITRARY_GEOM, TestCases

HERE = Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, Any]:
    def scrub_response_headers(response: dict[str, Any]) -> dict[str, Any]:
        retain = ["location"]
        response["headers"] = {
            key: value
            for (key, value) in response["headers"].items()
            if key.lower() in retain
        }
        return response

    def scrub_request_headers(request: Request) -> Request:
        drop = ["User-Agent"]
        for header in drop:
            request.headers.pop(header, None)

        return request

    return {
        "before_record_response": scrub_response_headers,
        "before_record_request": scrub_request_headers,
    }


@pytest.fixture
def catalog() -> Catalog:
    return Catalog("test-catalog", "A test catalog")


@pytest.fixture
def collection() -> Catalog:
    return Collection("test-collection", "A test collection", ARBITRARY_EXTENT)


@pytest.fixture
def multi_extent_collection() -> Collection:
    # TODO this code is repeated many times; refactor to use this fixture
    return Collection.from_file(
        TestCases.get_path("data-files/collections/multi-extent.json")
    )


@pytest.fixture
def item() -> Item:
    return Item("test-item", ARBITRARY_GEOM, ARBITRARY_BBOX, datetime.now(), {})


@pytest.fixture
def asset(item: Item) -> Asset:
    item.add_asset("foo", Asset("https://example.tif"))
    return item.assets["foo"]


@pytest.fixture
def link(item: Item) -> Link:
    item.add_link(Link(rel="child", target="https://example.tif"))
    return item.links[0]


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


@pytest.fixture(autouse=True)
def clear_validator() -> None:
    from pystac.validation import RegisteredValidator

    RegisteredValidator._validator = None
