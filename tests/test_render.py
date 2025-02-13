import pytest

from pystac import Catalog, Collection, DefaultRenderer, Item, Renderer, STACObject


@pytest.fixture
def renderer() -> Renderer:
    return DefaultRenderer("/pystac")


def assert_link(stac_object: STACObject, rel: str, href: str) -> None:
    link = stac_object.get_link(rel)
    assert link
    assert link.href == href


def test_solo_item_render(renderer: Renderer) -> None:
    item = Item("an-id")
    renderer.render(item)
    assert_link(item, "self", "/pystac/an-id.json")


def test_solo_catalog_render(renderer: Renderer) -> None:
    catalog = Catalog("an-id", "a description")
    renderer.render(catalog)
    assert_link(catalog, "self", "/pystac/catalog.json")


def test_solo_collection_render(renderer: Renderer) -> None:
    collection = Collection("an-id", "a description")
    renderer.render(collection)
    assert_link(collection, "self", "/pystac/collection.json")


def test_child_catalog_render(renderer: Renderer) -> None:
    catalog = Catalog("parent", "parent catalog")
    child = Catalog("child", "child catalog")
    catalog.add_child(child)
    renderer.render(catalog)
    assert catalog.href == "/pystac/catalog.json"
    child_link = next(catalog.iter_links("child"))
    assert child_link.href
    assert child.href == "/pystac/child/catalog.json"


def test_full_tree_render(renderer: Renderer) -> None:
    catalog = Catalog("parent", "parent catalog")
    child = Collection("child", "child collection")
    item = Item("an-id")
    catalog.add_child(child)
    child.add_item(item)
    renderer.render(catalog)
    assert catalog.href == "/pystac/catalog.json"
    assert child.href == "/pystac/child/collection.json"
    assert item.href == "/pystac/child/an-id/an-id.json"
