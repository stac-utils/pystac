import pathlib
from collections import namedtuple
from collections.abc import Iterable

import pytest

import pystac
from pystac.asset import Assets
from pystac.extensions.alternate import AlternateAssetsExtension

DATA_FILES = pathlib.Path(__file__).resolve().parent / "data-files"

ITEMS = [DATA_FILES / "basic/item.json"]
COLLECTIONS = [DATA_FILES / "basic/collection.json"]


def extract_alternate_assets(obj: Assets) -> Iterable[tuple[pystac.Asset, str | None]]:
    for asset in obj.assets.values():
        yield (asset, None)

        yield from ((asset, key) for key in asset.extra_fields.get("alternate", {}))


def construct_alternate_assets_item(
    paths: list[pathlib.Path],
) -> Iterable[tuple[pystac.Asset, str | None]]:
    for path in paths:
        obj = pystac.Item.from_file(path)

        yield from extract_alternate_assets(obj)


def construct_alternate_assets_collection(
    paths: list[pathlib.Path],
) -> Iterable[tuple[pystac.Asset, str | None]]:
    for path in paths:
        obj = pystac.Collection.from_file(path)

        yield from extract_alternate_assets(obj)


AlternateAssets = namedtuple("AlternateAssets", "asset alternate")


@pytest.fixture(params=construct_alternate_assets_item(ITEMS))
def items_alternate(request: pytest.FixtureRequest) -> AlternateAssets:
    return AlternateAssets(*request.param)


@pytest.fixture(params=construct_alternate_assets_collection(COLLECTIONS))
def collections_alternate(request: pytest.FixtureRequest) -> AlternateAssets:
    return AlternateAssets(*request.param)


def test_get_asset_item(items_alternate) -> None:
    asset = items_alternate.asset
    alternate_key = items_alternate.alternate

    print(asset.owner.stac_extensions)
    alternate_ext = AlternateAssetsExtension.ext(asset)
    actual = alternate_ext.get_asset(alternate_key)

    assert isinstance(actual, pystac.Asset)
    assert actual.owner is asset.owner
    assert "alternate" not in actual.extra_fields


def test_get_asset_collection(collections_alternate) -> None:
    asset = collections_alternate.asset
    alternate_key = collections_alternate.alternate

    alternate_ext = AlternateAssetsExtension.ext(asset)
    actual = alternate_ext.get_asset(alternate_key)

    assert isinstance(actual, pystac.Asset)
    assert actual.owner is asset.owner
    assert "alternate" not in actual.extra_fields


def test_getitem_item(items_alternate) -> None:
    asset = items_alternate.asset
    alternate_key = items_alternate.alternate

    print(asset.owner.stac_extensions)
    alternate_ext = AlternateAssetsExtension.ext(asset)
    actual = alternate_ext.assets[alternate_key]

    assert isinstance(actual, pystac.Asset)
    assert actual.owner is asset.owner
    assert "alternate" not in actual.extra_fields


def test_getitem_collection(collections_alternate) -> None:
    asset = collections_alternate.asset
    alternate_key = collections_alternate.alternate

    print(asset.owner.stac_extensions)
    alternate_ext = AlternateAssetsExtension.ext(asset)
    actual = alternate_ext.assets[alternate_key]

    assert isinstance(actual, pystac.Asset)
    assert actual.owner is asset.owner
    assert "alternate" not in actual.extra_fields
