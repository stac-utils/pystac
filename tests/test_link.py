import json
import os
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List

import pytest

import pystac
from pystac import Collection, Item, Link
from pystac.link import HIERARCHICAL_LINKS
from tests.utils.test_cases import ARBITRARY_EXTENT

TEST_DATETIME: datetime = datetime(2020, 3, 14, 16, 32)


class LinkTest(unittest.TestCase):
    item: pystac.Item

    def setUp(self) -> None:
        self.item = pystac.Item(
            id="test-item",
            geometry=None,
            bbox=None,
            datetime=TEST_DATETIME,
            properties={},
        )

    def test_path_like(self) -> None:
        rel = "some-rel"
        target = os.path.abspath("../elsewhere")
        link = pystac.Link(rel, target)

        self.assertEqual(os.fspath(link), target)

    def test_minimal(self) -> None:
        rel = "my rel"
        target = "https://example.com/a/b"
        link = pystac.Link(rel, target)
        self.assertEqual(target, link.get_href())
        self.assertEqual(target, link.get_absolute_href())

        expected_repr = f"<Link rel={rel} target={target}>"
        self.assertEqual(expected_repr, link.__repr__())

        self.assertFalse(link.is_resolved())

        expected_dict = {"rel": rel, "href": target}
        self.assertEqual(expected_dict, link.to_dict())

        # Run the same tests on the clone.
        clone = link.clone()
        self.assertNotEqual(link, clone)

        self.assertEqual(target, clone.get_href())
        self.assertEqual(target, clone.get_absolute_href())

        self.assertEqual(expected_repr, clone.__repr__())

        self.assertEqual(expected_dict, clone.to_dict())

        # Try the modification methods.
        self.assertIsNone(link.owner)
        link.set_owner(None)
        self.assertIsNone(link.owner)

        link.set_owner(self.item)
        self.assertEqual(self.item, link.owner)

    def test_relative(self) -> None:
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
        self.assertEqual(expected_dict, link.to_dict())

    def test_link_does_not_fail_if_href_is_none(self) -> None:
        """Test to ensure get_href does not fail when the href is None."""
        catalog = pystac.Catalog(id="test", description="test desc")
        catalog.add_item(self.item)
        catalog.set_self_href("/some/href")

        link = catalog.get_single_link("item")
        assert link is not None
        self.assertIsNone(link.get_href())

    def test_resolve_stac_object_no_root_and_target_is_item(self) -> None:
        link = pystac.Link("my rel", target=self.item)
        link.resolve_stac_object()

    def test_resolved_self_href(self) -> None:
        catalog = pystac.Catalog(id="test", description="test desc")
        with TemporaryDirectory() as temporary_directory:
            catalog.normalize_and_save(temporary_directory)
            path = os.path.join(temporary_directory, "catalog.json")
            catalog = pystac.Catalog.from_file(path)
            link = catalog.get_single_link(pystac.RelType.SELF)
            assert link
            link.resolve_stac_object()
            self.assertEqual(link.get_absolute_href(), path)

    def test_target_getter_setter(self) -> None:
        link = pystac.Link("my rel", target="./foo/bar.json")
        self.assertEqual(link.target, "./foo/bar.json")
        self.assertEqual(link.get_target_str(), "./foo/bar.json")

        link.target = self.item
        self.assertEqual(link.target, self.item)
        self.assertEqual(link.get_target_str(), self.item.get_self_href())

        link.target = "./bar/foo.json"
        self.assertEqual(link.target, "./bar/foo.json")

    def test_get_target_str_no_href(self) -> None:
        self.item.remove_links("self")
        link = pystac.Link("self", target=self.item)
        self.item.add_link(link)
        self.assertIsNone(link.get_target_str())

    def test_relative_self_href(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            pystac.write_file(
                self.item,
                include_self_link=False,
                dest_href=os.path.join(temporary_directory, "item.json"),
            )
            previous = os.getcwd()
            try:
                os.chdir(temporary_directory)
                item = pystac.read_file("item.json")
                href = item.get_self_href()
                assert href
                self.assertTrue(os.path.isabs(href), f"Not an absolute path: {href}")
            finally:
                os.chdir(previous)

    def test_auto_title_when_resolved(self) -> None:
        extent = pystac.Extent.from_items([self.item])
        collection = pystac.Collection(
            id="my_collection",
            description="Test Collection",
            extent=extent,
            title="Collection Title",
        )
        link = pystac.Link("my rel", target=collection)

        self.assertEqual(collection.title, link.title)

    def test_auto_title_not_found(self) -> None:
        extent = pystac.Extent.from_items([self.item])
        collection = pystac.Collection(
            id="my_collection",
            description="Test Collection",
            extent=extent,
        )
        link = pystac.Link("my rel", target=collection)

        self.assertEqual(None, link.title)

    def test_auto_title_is_serialized(self) -> None:
        extent = pystac.Extent.from_items([self.item])
        collection = pystac.Collection(
            id="my_collection",
            description="Test Collection",
            extent=extent,
            title="Collection Title",
        )
        link = pystac.Link("my rel", target=collection)

        assert link.to_dict().get("title") == collection.title

    def test_no_auto_title_if_not_resolved(self) -> None:
        link = pystac.Link(
            "my rel", target="https://www.some-domain.com/path/to/thing.txt"
        )

        assert link.title is None

    def test_title_as_init_argument(self) -> None:
        link_title = "Link title"
        extent = pystac.Extent.from_items([self.item])
        collection = pystac.Collection(
            id="my_collection",
            description="Test Collection",
            extent=extent,
            title="Collection Title",
        )
        link = pystac.Link("my rel", title=link_title, target=collection)

        assert link.title == link_title
        assert link.to_dict().get("title") == link_title

    def test_serialize_link(self) -> None:
        href = "https://some-domain/path/to/item.json"
        title = "A Test Link"
        link = pystac.Link(pystac.RelType.SELF, href, pystac.MediaType.JSON, title)
        link_dict = link.to_dict()

        self.assertEqual(str(link_dict["rel"]), "self")
        self.assertEqual(str(link_dict["type"]), "application/json")
        self.assertEqual(link_dict["title"], title)
        self.assertEqual(link_dict["href"], href)


class StaticLinkTest(unittest.TestCase):
    def setUp(self) -> None:
        self.item = pystac.Item(
            id="test-item",
            geometry=None,
            bbox=None,
            datetime=TEST_DATETIME,
            properties={},
        )

        self.collection = pystac.Collection(
            "collection id", "desc", extent=ARBITRARY_EXTENT
        )

    def test_from_dict_round_trip(self) -> None:
        test_cases: List[Dict[str, Any]] = [
            {"rel": "", "href": ""},  # Not valid, but works.
            {"rel": "r", "href": "t"},
            {"rel": "r", "href": "/t"},
            {"rel": "r", "href": "t", "type": "a/b", "title": "t", "c": "d", "1": 2},
        ]
        for d in test_cases:
            d2 = pystac.Link.from_dict(d).to_dict()
            self.assertEqual(d, d2)
        d = {"rel": "self", "href": "t"}
        d2 = {"rel": "self", "href": os.path.join(os.getcwd(), "t")}
        self.assertEqual(pystac.Link.from_dict(d).to_dict(), d2)

    def test_from_dict_failures(self) -> None:
        dicts: List[Dict[str, Any]] = [{}, {"href": "t"}, {"rel": "r"}]
        for d in dicts:
            with self.assertRaises(KeyError):
                pystac.Link.from_dict(d)

    def test_collection(self) -> None:
        link = pystac.Link.collection(self.collection)
        expected = {"rel": "collection", "href": None, "type": "application/json"}
        self.assertEqual(expected, link.to_dict())

    def test_child(self) -> None:
        link = pystac.Link.child(self.collection)
        expected = {"rel": "child", "href": None, "type": "application/json"}
        self.assertEqual(expected, link.to_dict())

    def test_canonical_item(self) -> None:
        link = pystac.Link.canonical(self.item)
        expected = {"rel": "canonical", "href": None, "type": "application/json"}
        self.assertEqual(expected, link.to_dict())

    def test_canonical_collection(self) -> None:
        link = pystac.Link.canonical(self.collection)
        expected = {"rel": "canonical", "href": None, "type": "application/json"}
        self.assertEqual(expected, link.to_dict())


class LinkInheritanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.collection = pystac.Collection(
            "collection id", "desc", extent=ARBITRARY_EXTENT
        )
        self.item = pystac.Item(
            id="test-item",
            geometry=None,
            bbox=None,
            datetime=TEST_DATETIME,
            properties={},
        )

    class CustomLink(pystac.Link):
        pass

    def test_from_dict(self) -> None:
        link = self.CustomLink.from_dict(
            {"rel": "r", "href": "t", "type": "a/b", "title": "t", "c": "d", "1": 2}
        )
        self.assertIsInstance(link, self.CustomLink)

    def test_collection(self) -> None:
        link = self.CustomLink.collection(self.collection)
        self.assertIsInstance(link, self.CustomLink)

    def test_child(self) -> None:
        link = self.CustomLink.child(self.collection)
        self.assertIsInstance(link, self.CustomLink)

    def test_canonical_item(self) -> None:
        link = self.CustomLink.canonical(self.item)
        self.assertIsInstance(link, self.CustomLink)

    def test_canonical_collection(self) -> None:
        link = self.CustomLink.canonical(self.collection)
        self.assertIsInstance(link, self.CustomLink)

    def test_clone(self) -> None:
        link = self.CustomLink.from_dict(
            {"rel": "r", "href": "t", "type": "a/b", "title": "t", "c": "d", "1": 2}
        )
        cloned_link = link.clone()
        self.assertIsInstance(cloned_link, self.CustomLink)


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
    collection = Collection.from_file(str(tmp_path / "collection.json"))
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
