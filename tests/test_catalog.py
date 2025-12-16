import json
from pathlib import Path

import pytest

import pystac
from pystac import (
    DEFAULT_STAC_VERSION,
    Catalog,
    Item,
    Link,
    PySTACError,
    STACError,
)


def test_catalog() -> None:
    _ = Catalog("an-id", "a description")


def test_read_file(examples_path: Path) -> None:
    with open(examples_path / "catalog.json") as f:
        d = json.load(f)
    catalog = pystac.read_file(examples_path / "catalog.json")
    assert catalog.to_dict() == d


def test_get_collections(catalog: Catalog) -> None:
    collections = list(catalog.get_collections())
    assert len(collections) == 3


def test_get_items(catalog: Catalog) -> None:
    items = list(catalog.get_items())
    assert len(items) == 1


def test_get_items_recursive(catalog: Catalog) -> None:
    items = list(catalog.get_items(recursive=True))
    assert len(items) == 2


def test_add_child() -> None:
    parent = Catalog("parent", "a parent catalog")
    child = Catalog("child", "a child catalog")
    parent.add_child(child)
    assert len(list(parent.get_children())) == 1


def test_add_item() -> None:
    catalog = Catalog("catalog", "a catalog")
    item = Item("an-id")
    catalog.add_item(item)
    assert len(list(catalog.get_items())) == 1


def test_save_catalog(tmp_path: Path) -> None:
    catalog = Catalog("catalog", "a catalog")
    catalog.render(tmp_path)
    catalog.save()
    catalog = Catalog.from_file(tmp_path / "catalog.json")
    assert catalog.id == "catalog"


def test_save_catalog_with_child(tmp_path: Path) -> None:
    catalog = Catalog("catalog", "a catalog")
    catalog.add_child(Catalog("child", "a child catalog"))
    with pytest.raises(PySTACError):
        catalog.save()

    catalog.render(tmp_path)
    catalog.save()

    catalog = Catalog.from_file(tmp_path / "catalog.json")
    assert catalog.id == "catalog"
    child = Catalog.from_file(tmp_path / "child" / "catalog.json")
    assert child.id == "child"
    root_link = child.get_root_link()
    assert root_link
    assert root_link.href == str(tmp_path / "catalog.json")
    parent_link = child.get_parent_link()
    assert parent_link
    assert parent_link.href == str(tmp_path / "catalog.json")


def test_save_catalog_with_grandchild(tmp_path: Path) -> None:
    catalog = Catalog("catalog", "a catalog")
    child = Catalog("child", "a child catalog")
    child.add_child(Catalog("grandchild", "a grandchild catalog"))
    catalog.add_child(child)

    catalog.render(tmp_path)
    catalog.save()

    grandchild = Catalog.from_file(tmp_path / "child" / "grandchild" / "catalog.json")
    assert grandchild.id == "grandchild"
    root_link = grandchild.get_root_link()
    assert root_link
    assert root_link.href == str(tmp_path / "catalog.json")
    parent_link = grandchild.get_parent_link()
    assert parent_link
    assert parent_link.href == str(tmp_path / "child" / "catalog.json")


def test_set_stac_version() -> None:
    catalog = Catalog("parent", "parent catalog")
    assert catalog.stac_version == DEFAULT_STAC_VERSION
    child = Catalog("child", "child catalog")
    assert child.stac_version == DEFAULT_STAC_VERSION
    catalog.add_child(child)

    catalog.set_stac_version("1.0.0")
    assert catalog.stac_version == "1.0.0"
    assert child.stac_version == "1.0.0"


def test_wrong_type_field() -> None:
    d = Catalog("an-id", "a description").to_dict()
    d["type"] = "CustomCatalog"
    with pytest.raises(STACError):
        Catalog.from_dict(d)


def test_read_file_self_link(catalog: Catalog) -> None:
    href = catalog.href
    assert href
    catalog.href = None
    catalog.set_link(Link(href=href, rel="self"))
    children = list(catalog.get_children())
    assert len(children) == 3


def test_normalize_and_save_warns(tmp_path: Path) -> None:
    catalog = Catalog("an-id", "A description")
    with pytest.warns(FutureWarning):
        catalog.normalize_and_save(tmp_path)
