from pathlib import Path

import pytest
from pystac import Collection

DATA_FILES = Path(__file__).resolve().parent / "data-files"


@pytest.fixture
def multi_extent_collection() -> Collection:
    return Collection.from_file(str(DATA_FILES / "collections" / "multi-extent.json"))
