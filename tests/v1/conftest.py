import json
from typing import Any

import pytest

from pystac import Item

from .utils import TestCases


@pytest.fixture
def sample_item_dict() -> dict[str, Any]:
    m = TestCases.get_path("data-files/item/sample-item.json")
    with open(m) as f:
        item_dict: dict[str, Any] = json.load(f)
    return item_dict


@pytest.fixture
def sample_item() -> Item:
    return Item.from_file(TestCases.get_path("data-files/item/sample-item.json"))
