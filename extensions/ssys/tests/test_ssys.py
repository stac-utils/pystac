import json
from pathlib import Path
from typing import Any, cast

import pytest

import pystac

DATA_FILES = Path(__file__).resolve().parent / "data-files"

EXAMPLE_ITEM = DATA_FILES / "item.json"
EXAMPLE_COLLECTION = DATA_FILES / "collection.json"
EXAMPLE_CATALOG = DATA_FILES / "catalog.json"


@pytest.fixture
def item_as_url() -> str:
    return str(EXAMPLE_ITEM)


@pytest.fixture
def item_as_dict(item_as_url: str) -> dict[str, Any]:
    with open(item_as_url) as f:
        d = json.load(f)
    return cast(dict[str, Any], d)


@pytest.fixture
def example_item(item_as_url: str) -> pystac.Item:
    return pystac.Item.from_file(item_as_url)


@pytest.fixture
def example_collection() -> pystac.Collection:
    return pystac.Collection.from_file(str(EXAMPLE_COLLECTION))


@pytest.fixture
def example_catalog() -> pystac.Catalog:
    return pystac.Catalog.from_file(str(EXAMPLE_CATALOG))


@pytest.mark.vcr()
def test_item_validate_schema(example_item: pystac.Item) -> None:
    assert example_item.validate()
