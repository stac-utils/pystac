import json
from pathlib import Path

import pytest

import pystac
from pystac import Item, STACWarning
from pystac.constants import DEFAULT_BBOX


def test_init_by_id() -> None:
    _ = Item("an-id")


def test_to_dict_feature() -> None:
    d = Item("an-id").to_dict()
    assert d["type"] == "Feature"


def test_read_file(examples_path: Path) -> None:
    with open(examples_path / "simple-item.json") as f:
        d = json.load(f)
    item = pystac.read_file(examples_path / "simple-item.json")
    assert item.to_dict() == d


def test_no_geometry_but_bbox() -> None:
    with pytest.warns(STACWarning):
        Item("an-id", bbox=DEFAULT_BBOX)


def test_warn_include_self_link() -> None:
    with pytest.warns(FutureWarning):
        Item("an-id").to_dict(include_self_link=True)


def test_warn_transform_hrefs() -> None:
    with pytest.warns(FutureWarning):
        Item("an-id").to_dict(transform_hrefs=True)


def test_migrate() -> None:
    d = Item("an-id").to_dict()
    d["stac_version"] = "1.0.0"
    item = Item.from_dict(d)
    item.migrate()
    assert item.stac_version == "1.1.0"
