import logging

import pytest

from pystac import Asset, Collection, Item
from pystac.errors import ExtensionNotImplemented
from pystac.extensions.ext import (
    EXTENSION_NAME_MAPPING,
    EXTENSION_NAMES,
    AssetExt,
    CollectionExt,
    ItemExt,
)
from tests.conftest import get_data_file

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


@pytest.fixture
def eo_ext_item() -> Item:
    ext_item_uri = get_data_file("eo/eo-landsat-example.json")
    return Item.from_file(ext_item_uri)


def test_ext_syntax_has(eo_ext_item: Item) -> None:
    assert eo_ext_item.ext.has("eo") is True
    assert eo_ext_item.ext.has("proj") is False

    assert eo_ext_item.assets["B1"].ext.has("eo") is True
    assert eo_ext_item.assets["B1"].ext.has("proj") is False


def test_ext_syntax_raises_if_ext_not_on_obj(eo_ext_item: Item) -> None:
    with pytest.raises(ExtensionNotImplemented):
        eo_ext_item.ext.proj.epsg


def test_ext_syntax_ext_can_be_added(eo_ext_item: Item) -> None:
    eo_ext_item.ext.add("proj")
    assert eo_ext_item.ext.proj.epsg is None


def test_ext_syntax_trying_to_add_invalid_ext_raises(item: Item) -> None:
    with pytest.raises(KeyError, match="Extension 'foo' is not a valid extension"):
        item.ext.add("foo")  # type: ignore


def test_ext_syntax_ext_can_be_removed(eo_ext_item: Item) -> None:
    original_n = len(eo_ext_item.stac_extensions)
    eo_ext_item.ext.remove("eo")
    with pytest.raises(
        ExtensionNotImplemented, match="Extension 'eo' is not implemented"
    ):
        eo_ext_item.ext.eo
    assert len(eo_ext_item.stac_extensions) == original_n - 1


all_asset_ext_props = {a for a in dir(AssetExt) if not a.startswith("_")} - {
    "has",
    "add",
    "remove",
}
all_item_ext_props = {a for a in dir(ItemExt) if not a.startswith("_")} - {
    "has",
    "add",
    "remove",
}
all_collection_ext_props = {a for a in dir(CollectionExt) if not a.startswith("_")} - {
    "has",
    "add",
    "remove",
}


@pytest.mark.parametrize("name", all_asset_ext_props)
def test_ext_syntax_every_prop_can_be_added_to_asset(
    asset: Asset, name: EXTENSION_NAMES
) -> None:
    assert asset.ext.has(name) is False
    asset.ext.add(name)
    assert asset.ext.has(name) is True
    asset.ext.remove(name)
    with pytest.raises(
        ExtensionNotImplemented, match=f"Extension '{name}' is not implemented"
    ):
        getattr(asset.ext, name)


@pytest.mark.parametrize("name", all_item_ext_props)
def test_ext_syntax_every_prop_can_be_added_to_item(
    item: Item, name: EXTENSION_NAMES
) -> None:
    assert item.ext.has(name) is False
    item.ext.add(name)
    assert item.ext.has(name) is True
    item.ext.remove(name)
    with pytest.raises(
        ExtensionNotImplemented, match=f"Extension '{name}' is not implemented"
    ):
        getattr(item.ext, name)


@pytest.mark.parametrize("name", all_collection_ext_props)
def test_ext_syntax_every_prop_can_be_added_to_collection(
    collection: Collection, name: EXTENSION_NAMES
) -> None:
    assert collection.ext.has(name) is False
    collection.ext.add(name)
    assert collection.ext.has(name) is True
    collection.ext.remove(name)
    with pytest.raises(
        ExtensionNotImplemented, match=f"Extension '{name}' is not implemented"
    ):
        getattr(collection.ext, name)


def test_ext_syntax_every_name_has_a_prop() -> None:
    assert {
        *all_asset_ext_props,
        *all_item_ext_props,
        *all_collection_ext_props,
    } == set(EXTENSION_NAME_MAPPING.keys())
