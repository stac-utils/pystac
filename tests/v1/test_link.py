import json
import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

import pytest

import pystac
from pystac import Collection, Item, Link
from pystac.errors import STACError
from pystac.link import HIERARCHICAL_LINKS
from pystac.utils import make_posix_style
from tests.v1.utils.test_cases import ARBITRARY_EXTENT

TEST_DATETIME: datetime = datetime(2020, 3, 14, 16, 32)


def test_path_like() -> None:
    rel = "some-rel"
    target = os.path.abspath("../elsewhere")
    link = pystac.Link(rel, target)
    assert os.fspath(link) == make_posix_style(target)


def test_minimal(item: pystac.Item) -> None:
    rel = "my rel"
    target = "https://example.com/a/b"
    link = pystac.Link(rel, target)
    assert target == link.get_href()
    assert target == link.get_absolute_href()

    expected_repr = f"<Link rel={rel} target={target}>"
    assert expected_repr == link.__repr__()

    assert not link.is_resolved()

    expected_dict = {"rel": rel, "href": target}
    assert expected_dict == link.to_dict()

    # Run the same tests on the clone.
    clone = link.clone()
    assert link != clone

    assert target == clone.get_href()
    assert target == clone.get_absolute_href()

    assert expected_repr == clone.__repr__()

    assert expected_dict == clone.to_dict()

    # Try the modification methods.
    assert link.owner is None
    link.set_owner(None)
    assert link.owner is None

    link.set_owner(item)
    assert item == link.owner


def test_relative() -> None:
    rel = "my rel"
    target = "../elsewhere"
    mime_type = "example/stac_thing"
    link = pystac.Link(rel, target, mime_type, "a title", extra_fields={"a": "b"})
    expected_dict = {
        "rel": rel,
        "href": target,
        "type": "example/stac_thing",
        "title": "a title",
        "a": "b",
    }
    assert expected_dict == link.to_dict()


def test_link_does_not_fail_if_href_is_none(item: pystac.Item) -> None:
    """Test to ensure get_href does not fail when the href is None."""
    catalog = pystac.Catalog(id="test", description="test desc")
    catalog.add_item(item)
    catalog.set_self_href("/some/href")

    link = catalog.get_single_link("item")
    assert link is not None
    assert link.get_href() is None


def test_resolve_stac_object_no_root_and_target_is_item(item: pystac.Item) -> None:
    link = pystac.Link("my rel", target=item)
    link.resolve_stac_object()


@pytest.mark.skipif(os.name == "nt", reason="Non-windows test")
def test_resolve_stac_object_throws_informative_error() -> None:
    link = pystac.Link("root", target="/a/b/foo.json")
    with pytest.raises(
        STACError, match="HREF: '/a/b/foo.json' does not resolve to a STAC object"
    ):
        link.resolve_stac_object()


def test_resolved_self_href() -> None:
    catalog = pystac.Catalog(id="test", description="test desc")
    with TemporaryDirectory() as temporary_directory:
        catalog.normalize_and_save(temporary_directory)
        path = os.path.join(temporary_directory, "catalog.json")
        catalog = pystac.Catalog.from_file(path)
        link = catalog.get_single_link(pystac.RelType.SELF)
        assert link
        link.resolve_stac_object()
        assert link.get_absolute_href() == make_posix_style(path)


def test_target_getter_setter(item: pystac.Item) -> None:
    link = pystac.Link("my rel", target="./foo/bar.json")
    assert link.target == "./foo/bar.json"
    assert link.get_target_str() == "./foo/bar.json"

    link.target = item
    assert link.target == item
    assert link.get_target_str() == item.get_self_href()

    link.target = "./bar/foo.json"
    assert link.target == "./bar/foo.json"


def test_get_target_str_no_href(item: pystac.Item) -> None:
    item.remove_links("self")
    link = pystac.Link("self", target=item)
    item.add_link(link)
    assert link.get_target_str() is None


def test_relative_self_href(item: pystac.Item) -> None:
    with TemporaryDirectory() as temporary_directory:
        pystac.write_file(
            item,
            include_self_link=False,
            dest_href=os.path.join(temporary_directory, "item.json"),
        )
        previous = os.getcwd()
        try:
            os.chdir(temporary_directory)
            item = cast(pystac.Item, pystac.read_file("item.json"))
            href = item.get_self_href()
            assert href
            assert os.path.isabs(href), f"Not an absolute path: {href}"
        finally:
            os.chdir(previous)


def test_auto_title_when_resolved(item: pystac.Item) -> None:
    extent = pystac.Extent.from_items([item])
    collection = pystac.Collection(
        id="my_collection",
        description="Test Collection",
        extent=extent,
        title="Collection Title",
    )
    link = pystac.Link("my rel", target=collection)

    assert collection.title == link.title


def test_auto_title_not_found(item: pystac.Item) -> None:
    extent = pystac.Extent.from_items([item])
    collection = pystac.Collection(
        id="my_collection",
        description="Test Collection",
        extent=extent,
    )
    link = pystac.Link("my rel", target=collection)

    assert link.title is None


def test_auto_title_is_serialized(item: pystac.Item) -> None:
    extent = pystac.Extent.from_items([item])
    collection = pystac.Collection(
        id="my_collection",
        description="Test Collection",
        extent=extent,
        title="Collection Title",
    )
    link = pystac.Link("my rel", target=collection)

    assert link.to_dict().get("title") == collection.title


def test_no_auto_title_if_not_resolved() -> None:
    link = pystac.Link("my rel", target="https://www.some-domain.com/path/to/thing.txt")

    assert link.title is None


def test_title_as_init_argument(item: pystac.Item) -> None:
    link_title = "Link title"
    extent = pystac.Extent.from_items([item])
    collection = pystac.Collection(
        id="my_collection",
        description="Test Collection",
        extent=extent,
        title="Collection Title",
    )
    link = pystac.Link("my rel", title=link_title, target=collection)

    assert link.title == link_title
    assert link.to_dict().get("title") == link_title


def test_serialize_link() -> None:
    href = "https://some-domain/path/to/item.json"
    title = "A Test Link"
    link = pystac.Link(pystac.RelType.SELF, href, pystac.MediaType.JSON, title)
    link_dict = link.to_dict()

    assert link_dict["rel"] == "self"
    assert link_dict["type"] == "application/json"
    assert link_dict["title"] == title
    assert link_dict["href"] == href


def test_static_from_dict_round_trip() -> None:
    test_cases: list[dict[str, Any]] = [
        {"rel": "", "href": ""},  # Not valid, but works.
        {"rel": "r", "href": "t"},
        {"rel": "r", "href": "/t"},
        {"rel": "r", "href": "t", "type": "a/b", "title": "t", "c": "d", "1": 2},
    ]
    for d in test_cases:
        d2 = pystac.Link.from_dict(d).to_dict()
        assert d == d2
    d = {"rel": "self", "href": "t"}
    d2 = {"rel": "self", "href": make_posix_style(os.path.join(os.getcwd(), "t"))}
    assert pystac.Link.from_dict(d).to_dict() == d2


def test_static_from_dict_failures() -> None:
    dicts: list[dict[str, Any]] = [{}, {"href": "t"}, {"rel": "r"}]
    for d in dicts:
        with pytest.raises(KeyError):
            pystac.Link.from_dict(d)


def test_static_collection(collection: pystac.Collection) -> None:
    link = pystac.Link.collection(collection)
    expected = {"rel": "collection", "href": None, "type": "application/json"}
    assert expected == link.to_dict()


def test_static_child(collection: pystac.Collection) -> None:
    link = pystac.Link.child(collection)
    expected = {"rel": "child", "href": None, "type": "application/json"}
    assert expected == link.to_dict()


def test_static_canonical_item(item: pystac.Item) -> None:
    link = pystac.Link.canonical(item)
    expected = {"rel": "canonical", "href": None, "type": "application/json"}
    assert expected == link.to_dict()


def test_static_canonical_collection(collection: pystac.Collection) -> None:
    link = pystac.Link.canonical(collection)
    expected = {"rel": "canonical", "href": None, "type": "application/json"}
    assert expected == link.to_dict()


class CustomLink(pystac.Link):
    pass


def test_inheritance_from_dict() -> None:
    link = CustomLink.from_dict(
        {"rel": "r", "href": "t", "type": "a/b", "title": "t", "c": "d", "1": 2}
    )
    assert isinstance(link, CustomLink)


def test_inheritance_collection(collection: Collection) -> None:
    link = CustomLink.collection(collection)
    assert isinstance(link, CustomLink)


def test_inheritance_child(collection: Collection) -> None:
    link = CustomLink.child(collection)
    assert isinstance(link, CustomLink)


def test_inheritance_canonical_item(item: Item) -> None:
    link = CustomLink.canonical(item)
    assert isinstance(link, CustomLink)


def test_inheritance_canonical_collection(collection: Collection) -> None:
    link = CustomLink.canonical(collection)
    assert isinstance(link, CustomLink)


def test_inheritance_clone() -> None:
    link = CustomLink.from_dict(
        {"rel": "r", "href": "t", "type": "a/b", "title": "t", "c": "d", "1": 2}
    )
    cloned_link = link.clone()
    assert isinstance(cloned_link, CustomLink)


def test_relative_self_link(tmp_path: Path) -> None:
    # https://github.com/stac-utils/pystac/issues/801
    item = Item("an-id", None, None, datetime.now(), {})
    item_as_dict = item.to_dict(include_self_link=False)
    item_as_dict["links"] = [{"href": "item.json", "rel": "self"}]
    item_as_dict["assets"] = {"data": {"href": "asset.tif"}}
    with open(tmp_path / "item.json", "w") as f:
        json.dump(item_as_dict, f)
    Path(tmp_path / "asset.tif").touch()
    collection = Collection("an-id", "a description", ARBITRARY_EXTENT)
    collection.add_link(Link("item", "item.json"))
    collection.save_object(
        include_self_link=False, dest_href=str(tmp_path / "collection.json")
    )
    collection = Collection.from_file(tmp_path / "collection.json")
    read_item = collection.get_item("an-id")
    assert read_item
    asset_href = read_item.assets["data"].get_absolute_href()
    assert asset_href
    assert Path(asset_href).exists()


@pytest.mark.parametrize("rel", HIERARCHICAL_LINKS)
def test_is_hierarchical(rel: str) -> None:
    assert Link(rel, "a-target").is_hierarchical()


@pytest.mark.parametrize(
    "rel", ["canonical", "derived_from", "alternate", "via", "prev", "next", "preview"]
)
def test_is_not_hierarchical(rel: str) -> None:
    assert not Link(rel, "a-target").is_hierarchical()


def test_item_link_type(item: Item) -> None:
    # https://github.com/stac-utils/pystac/issues/1494
    link = Link.item(item)
    assert link.media_type == "application/geo+json"
