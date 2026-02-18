from pathlib import Path

import pytest
from pystac import Catalog

DATA_FILES = Path(__file__).resolve().parent / "data-files"


@pytest.fixture
def test_case_1_catalog() -> Catalog:
    return Catalog.from_file(
        str(DATA_FILES / "catalogs" / "test-case-1" / "catalog.json")
    )
