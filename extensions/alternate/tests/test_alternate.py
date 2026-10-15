import json
import pathlib
from collections import namedtuple
from typing import Any

import pytest

import pystac
from pystac.extensions.alternate import AlternateAssetsExtension

DATA_FILES = pathlib.Path(__file__).resolve().parent / "data-files"

ITEM_PATHS = [
    DATA_FILES / "basic/item.json",
]
COLLECTION_PATHS = [
    DATA_FILES / "basic/collection.json",
]


def load_json(path: pathlib.Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def construct_item_assets(paths: list[pathlib.Path]) -> list[pystac.Asset]:
    items = (pystac.Item.from_dict(load_json(path)) for path in paths)
    item_assets = (asset for item in items for asset in item.assets.values())

    return [
        (asset, alternate)
        for asset in item_assets
        for alternate in list(asset.extra_fields.get("alternate", {}).keys()) + [None]
    ]


def construct_collection_assets(paths: list[pathlib.Path]) -> list[pystac.Asset]:
    collections = (pystac.Collection.from_dict(load_json(path)) for path in paths)
    collection_assets = (
        asset for collection in collections for asset in collection.assets.values()
    )

    return [
        (asset, alternate)
        for asset in collection_assets
        for alternate in list(asset.extra_fields.get("alternate", {}).keys()) + [None]
    ]


AlternateAssets = namedtuple("AlternateAssets", "asset alternate")


@pytest.fixture(params=construct_item_assets(ITEM_PATHS))
def item_assets(request) -> pystac.Asset:
    yield AlternateAssets(*request.param)


@pytest.fixture(params=construct_collection_assets(COLLECTION_PATHS))
def collection_assets(request) -> pystac.Asset:
    yield AlternateAssets(*request.param)


def test_get_item_asset(item_assets):
    asset = item_assets.asset
    alternate_key = item_assets.alternate

    print(asset.owner.stac_extensions)
    alternate_ext = AlternateAssetsExtension.ext(asset)
    actual = alternate_ext.get_asset(alternate_key)

    assert isinstance(actual, pystac.Asset)
    assert actual.owner is asset.owner
    assert "alternate" not in actual.extra_fields


def test_get_collection_assets(collection_assets):
    asset = collection_assets.asset
    alternate_key = collection_assets.alternate

    alternate_ext = AlternateAssetsExtension.ext(asset)
    actual = alternate_ext.get_asset(alternate_key)

    assert isinstance(actual, pystac.Asset)
    assert actual.owner is asset.owner
    assert "alternate" not in actual.extra_fields


def test_getitem_item_assets(item_assets):
    asset = item_assets.asset
    alternate_key = item_assets.alternate

    print(asset.owner.stac_extensions)
    alternate_ext = AlternateAssetsExtension.ext(asset)
    actual = alternate_ext.assets[alternate_key]

    assert isinstance(actual, pystac.Asset)
    assert actual.owner is asset.owner
    assert "alternate" not in actual.extra_fields


def test_getitem_collection_assets(collection_assets):
    asset = collection_assets.asset
    alternate_key = collection_assets.alternate

    print(asset.owner.stac_extensions)
    alternate_ext = AlternateAssetsExtension.ext(asset)
    actual = alternate_ext.assets[alternate_key]

    assert isinstance(actual, pystac.Asset)
    assert actual.owner is asset.owner
    assert "alternate" not in actual.extra_fields
