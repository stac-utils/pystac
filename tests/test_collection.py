import json
from pathlib import Path

import pytest

from pystac import Collection


def test_collection() -> None:
    collection = Collection(id="an-id", description="a-description")
    collection.validate()


@pytest.mark.vcr
def test_collection_from_dict(examples_path: Path) -> None:
    with open(examples_path / "collection.json") as f:
        data = json.load(f)
    collection = Collection.from_dict(data)
    collection.validate()
    assert collection.to_dict() == data
