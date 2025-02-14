from pystac import Catalog, Collection, Item, STACObject


def assert_link(stac_object: STACObject, rel: str, href: str) -> None:
    link = stac_object.get_link(rel)
    assert link
    assert link.href == href


def test_child_catalog_render() -> None:
    catalog = Catalog("parent", "parent catalog")
    child = Catalog("child", "child catalog")
    catalog.add_child(child)
    catalog.render("/pystac")
    child_link = next(catalog.iter_links("child"))
    assert child_link.href
    assert child.href == "/pystac/child/catalog.json"


def test_full_tree_render() -> None:
    catalog = Catalog("parent", "parent catalog")
    child = Collection("child", "child collection")
    item = Item("an-id")
    catalog.add_child(child)
    child.add_item(item)
    catalog.render("/pystac")
    assert catalog.href == "/pystac/catalog.json"
    assert child.href == "/pystac/child/collection.json"
    assert item.href == "/pystac/child/an-id/an-id.json"
