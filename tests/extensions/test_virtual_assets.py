import json
import logging
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, cast, TypeVar

import pytest
from dateutil.parser import parse

from pystac import Item
from pystac.extensions.virtual_assets import VirtualAssetsExtension
from tests.utils import TestCases

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

SENTINEL_ITEM_EXAMPLE_URI = TestCases.get_path(
    "data-files/virtual-assets/sentinel-item.json"
)

@pytest.fixture
def item_dict() -> Dict[str, Any]:
    with open(SENTINEL_ITEM_EXAMPLE_URI) as f:
        return cast(Dict[str, Any], json.load(f))

@pytest.fixture
def sentinel_item() -> Item:
    return Item.from_file(SENTINEL_ITEM_EXAMPLE_URI)

def test_stac_extensions(sentinel_item: Item) -> None:
    assert VirtualAssetsExtension.has_extension(sentinel_item)

def test_has_hrefs(sentinel_item: Item) -> None:
    asset = sentinel_item.assets['sir']
    assert VirtualAssetsExtension.ext(asset).hrefs == ['#B12', '#B8A', '#B04']

