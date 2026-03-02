from pathlib import Path

import pytest
from pystac import Item

HERE = Path(__file__).resolve().parent


@pytest.fixture
def projection_landsat8_item() -> Item:
    return Item.from_file(str(HERE / "data-files" / "example-landsat8.json"))
