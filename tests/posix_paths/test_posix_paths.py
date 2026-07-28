import json
import os
from datetime import datetime
from pathlib import Path

import pytest

import pystac
from tests.conftest import get_data_file
from tests.utils import ARBITRARY_BBOX, ARBITRARY_EXTENT, ARBITRARY_GEOM


def check_link(link: pystac.Link | None) -> None:
    assert link is not None
    href = link.get_target_str()
    assert href is not None
    assert "\\" not in href


def test_create_item_from_absolute_posix_href() -> None:
    absolute_href = get_data_file("item/sample-item.json")
    absolute_posix_href = absolute_href.replace("\\", "/")
    pystac.Item.from_file(absolute_posix_href)
    pystac.read_file(absolute_posix_href)


def test_create_item_from_relative_posix_href() -> None:
    absolute_href = get_data_file("item/sample-item.json")
    relative_href = os.path.relpath(absolute_href)
    relative_posix_href = relative_href.replace("\\", "/")
    pystac.Item.from_file(relative_posix_href)
    pystac.read_file(relative_posix_href)


def test_create_item_containing_posix_hrefs(tmp_path: Path) -> None:
    collection = pystac.Collection(
        "test-collection", "A test collection", ARBITRARY_EXTENT
    )
    item = pystac.Item("test-item", ARBITRARY_GEOM, ARBITRARY_BBOX, datetime.now(), {})
    collection.add_item(item)
    collection.normalize_and_save(
        str(tmp_path), catalog_type=pystac.CatalogType.ABSOLUTE_PUBLISHED
    )

    item_href = str(tmp_path / "test-item/test-item.json")
    item_dict = pystac.Item.from_file(item_href).to_dict()
    for link in item_dict["links"]:
        link["href"] = str(link["href"]).replace("\\\\", "/").replace("\\", "/")
    with open(item_href, "w") as f:
        json.dump(item_dict, f)

    collection_href = str(tmp_path / "collection.json")
    collection_dict = pystac.Collection.from_file(collection_href).to_dict()
    for link in collection_dict["links"]:
        link["href"] = str(link["href"]).replace("\\\\", "/").replace("\\", "/")
    with open(collection_href, "w") as f:
        json.dump(collection_dict, f)

    item_href = item_href.replace("\\", "/")
    pystac.Item.from_file(item_href)
    pystac.read_file(item_href)

    collection_href = collection_href.replace("\\", "/")
    pystac.Collection.from_file(collection_href)
    pystac.read_file(collection_href)


@pytest.mark.skipif(os.name != "nt", reason="windows only test")
def test_posix_self_link_from_absolute_href(tmp_path: Path) -> None:
    # Check that we convert to a windows style (\\) absolute href to posix style
    # in the self link
    absolute_windows_href = get_data_file("item/sample-item.json")
    assert "\\" in absolute_windows_href
    item = pystac.Item.from_file(absolute_windows_href)
    check_link(item.get_single_link(rel="self"))
    item2 = pystac.read_file(absolute_windows_href)
    check_link(item2.get_single_link(rel="self"))

    absolute_windows_href = get_data_file("collections/multi-extent.json")
    assert "\\" in absolute_windows_href
    collection = pystac.Collection.from_file(absolute_windows_href)
    check_link(collection.get_single_link(rel="self"))
    collection2 = pystac.read_file(absolute_windows_href)
    check_link(collection2.get_single_link(rel="self"))

    absolute_windows_href = get_data_file("catalogs/test-case-1/catalog.json")
    assert "\\" in absolute_windows_href
    catalog = pystac.Catalog.from_file(absolute_windows_href)
    check_link(catalog.get_single_link(rel="self"))
    catalog2 = pystac.read_file(absolute_windows_href)
    check_link(catalog2.get_single_link(rel="self"))

    # check that we retain a posix style (/) absolute href in the self link
    absolute_windows_href = get_data_file("item/sample-item.json")
    assert "\\" in absolute_windows_href
    absolute_posix_href = absolute_windows_href.replace("\\", "/")
    item = pystac.Item.from_file(absolute_posix_href)
    check_link(item.get_single_link(rel="self"))
    item2 = pystac.read_file(absolute_posix_href)
    check_link(item2.get_single_link(rel="self"))

    absolute_windows_href = get_data_file("collections/multi-extent.json")
    assert "\\" in absolute_windows_href
    absolute_posix_href = absolute_windows_href.replace("\\", "/")
    collection = pystac.Collection.from_file(absolute_posix_href)
    check_link(collection.get_single_link(rel="self"))
    collection2 = pystac.read_file(absolute_posix_href)
    check_link(collection2.get_single_link(rel="self"))

    absolute_windows_href = get_data_file("collections/multi-extent.json")
    assert "\\" in absolute_windows_href
    absolute_posix_href = absolute_windows_href.replace("\\", "/")
    catalog = pystac.Collection.from_file(absolute_posix_href)
    check_link(catalog.get_single_link(rel="self"))
    catalog2 = pystac.read_file(absolute_posix_href)
    check_link(catalog2.get_single_link(rel="self"))


@pytest.mark.skipif(os.name != "nt", reason="windows only test")
def test_posix_self_link_from_relative_href(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # check that we convert a windows style (\\) relative href to posix style
    # in the self link (which is always converted to an absolute href)
    test_item = pystac.Item(
        "test-item", ARBITRARY_GEOM, ARBITRARY_BBOX, datetime.now(), {}
    )
    (tmp_path / "subdirectory").mkdir()
    test_item_href = str(tmp_path / "subdirectory" / "test-item.json")
    assert "\\" in test_item_href
    test_item.save_object(include_self_link=False, dest_href=test_item_href)

    monkeypatch.chdir(tmp_path)
    item = pystac.Item.from_file("subdirectory\\test-item.json")
    check_link(item.get_single_link(rel="self"))
    item2 = pystac.read_file("subdirectory\\test-item.json")
    check_link(item2.get_single_link(rel="self"))


def test_all_generated_links_have_posix_hrefs(tmp_path: Path) -> None:
    asset_href = Path(tmp_path / "test-asset-file.txt")
    asset_href.touch()
    asset = pystac.Asset(str(asset_href), media_type=pystac.MediaType.TEXT)

    item = pystac.Item("test-item", ARBITRARY_GEOM, ARBITRARY_BBOX, datetime.now(), {})
    item.add_asset("test-asset", asset)

    collection = pystac.Collection(
        "test-collection", "A test collection", ARBITRARY_EXTENT
    )
    collection.add_item(item)
    collection.normalize_hrefs(str(tmp_path))

    for link in collection.links:
        check_link(link)
    for link in item.links:
        check_link(link)


@pytest.mark.skipif(os.name != "nt", reason="windows only test")
def test_all_existing_links_converted_to_posix_hrefs() -> None:
    href = get_data_file("windows_hrefs/test-collection/test-item/test-item.json")
    item = pystac.Item.from_file(href)
    for link in item.links:
        check_link(link)
    with open(href) as f:
        item_dict = json.load(f)
    item2 = pystac.Item.from_dict(item_dict)
    for link in item2.links:
        check_link(link)

    href = get_data_file("windows_hrefs/test-collection/collection.json")
    collection = pystac.Collection.from_file(href)
    for link in collection.links:
        check_link(link)
    with open(href) as f:
        collection_dict = json.load(f)
    collection2 = pystac.Collection.from_dict(collection_dict)
    for link in collection2.links:
        check_link(link)

    href = get_data_file("windows_hrefs/catalog.json")
    catalog = pystac.Catalog.from_file(href)
    for link in catalog.links:
        check_link(link)
    with open(href) as f:
        catalog_dict = json.load(f)
    catalog2 = pystac.Catalog.from_dict(catalog_dict)
    for link in catalog2.links:
        check_link(link)


@pytest.mark.skipif(os.name != "nt", reason="windows only test")
def test_existing_asset_hrefs_converted_to_posix() -> None:
    href = get_data_file("windows_hrefs/test-collection/test-item/test-item.json")
    item = pystac.Item.from_file(href)
    for asset in item.get_assets().values():
        assert "\\" not in asset.href
