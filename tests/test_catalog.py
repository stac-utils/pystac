import json
from pathlib import Path

from pystac import Catalog


def test_catalog() -> None:
    catalog = Catalog(id="an-id", description="a description")
    catalog.validate()


def test_catalog_from_dict(examples_path: Path) -> None:
    with open(examples_path / "catalog.json") as f:
        data = json.load(f)
    catalog = Catalog.from_dict(data)
    catalog.validate()
    assert catalog.to_dict() == data
