import json
from pathlib import Path

import pystac
from pystac import Collection


def test_catalog() -> None:
    _ = Collection("an-id", "a description")


def test_read_file(examples_path: Path) -> None:
    with open(examples_path / "collection.json") as f:
        d = json.load(f)
    collection = pystac.read_file(examples_path / "collection.json")
    assert collection.to_dict() == d
