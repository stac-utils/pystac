import pathlib
from collections import namedtuple
from collections.abc import Iterable

import pytest

import pystac
from pystac.asset import Assets
from pystac.extensions.alternate import AlternateAsset, AlternateAssetsExtension

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


AlternateAssetContainer = namedtuple("AlternateAssetContainer", "asset alternate")


@pytest.fixture()
def blank_item() -> pystac.Item:
    return pystac.Item.from_dict(
        {
            "id": "example",
            "geometry": {},
            "bbox": [-180, -90, 180, 90],
            "datetime": "2021-05-12",
            "properties": {},
        }
    )


@pytest.fixture()
def blank_collection() -> pystac.Collection:
    extent = pystac.Extent.from_dict(
        {
            "spatial": {"bbox": [[-180, -90, 180, 90]]},
            "temporal": {"interval": [["2025-12-07", "2026-06-12"]]},
        }
    )
    return pystac.Collection(id="example", description="Example", extent=extent)


@pytest.fixture(params=construct_alternate_assets_item(ITEMS))
def items_alternate(request: pytest.FixtureRequest) -> AlternateAssetContainer:
    return AlternateAssetContainer(*request.param)


@pytest.fixture(params=construct_alternate_assets_collection(COLLECTIONS))
def collections_alternate(request: pytest.FixtureRequest) -> AlternateAssetContainer:
    return AlternateAssetContainer(*request.param)


class TestGetAlternate:
    def test_get_asset_item(self, items_alternate: AlternateAssetContainer) -> None:
        asset = items_alternate.asset
        alternate_key = items_alternate.alternate

        print(asset.owner.stac_extensions)
        alternate_ext = AlternateAssetsExtension.ext(asset)
        actual = alternate_ext.get_asset(alternate_key)

        assert isinstance(actual, AlternateAsset)
        assert actual.owner is asset.owner
        assert "alternate" not in actual.properties

    def test_get_asset_collection(
        self, collections_alternate: AlternateAssetContainer
    ) -> None:
        asset = collections_alternate.asset
        alternate_key = collections_alternate.alternate

        alternate_ext = AlternateAssetsExtension.ext(asset)
        actual = alternate_ext.get_asset(alternate_key)

        assert isinstance(actual, AlternateAsset)
        assert actual.owner is asset.owner
        assert "alternate" not in actual.properties

    def test_getitem_item(self, items_alternate: AlternateAssetContainer) -> None:
        asset = items_alternate.asset
        alternate_key = items_alternate.alternate

        alternate_ext = AlternateAssetsExtension.ext(asset)
        actual = alternate_ext.assets[alternate_key]

        assert isinstance(actual, AlternateAsset)
        assert actual.owner is asset.owner
        assert "alternate" not in actual.properties

    def test_getitem_collection(
        self, collections_alternate: AlternateAssetContainer
    ) -> None:
        asset = collections_alternate.asset
        alternate_key = collections_alternate.alternate

        alternate_ext = AlternateAssetsExtension.ext(asset)
        actual = alternate_ext.assets[alternate_key]

        assert isinstance(actual, AlternateAsset)
        assert actual.owner is asset.owner
        assert "alternate" not in actual.properties


class TestMutation:
    def test_item_add_extension(self, blank_item: pystac.Item) -> None:
        asset = pystac.Asset(href="asset.png")
        asset.set_owner(blank_item)

        assert (
            AlternateAssetsExtension.get_schema_uri() not in blank_item.stac_extensions
        )

        AlternateAssetsExtension.add_to(asset)

        assert AlternateAssetsExtension.get_schema_uri() in blank_item.stac_extensions

    def test_item_set_alternate_asset(self, blank_item: pystac.Item) -> None:
        asset = pystac.Asset(href="asset.png")
        asset.set_owner(blank_item)

        blank_item.assets["product"] = asset
        blank_item.stac_extensions.append(AlternateAssetsExtension.get_schema_uri())

        assert "alternate" not in asset.extra_fields

        alternate_asset = AlternateAsset(
            {"href": "product1.png"},
            owner=blank_item,
            asset_name="product",
            alternate="s3",
        )
        asset.ext.alternate.set_asset("s3", alternate_asset)

        assert "alternate" in asset.extra_fields
        assert blank_item.assets["product"] is asset

        alternates = blank_item.assets["product"].extra_fields.get("alternate", {})
        actual = alternates.get("s3")
        assert actual is not None
        assert actual.get("href") == alternate_asset.href

    def test_collection_add_extension(
        self, blank_collection: pystac.Collection
    ) -> None:
        asset = pystac.Asset(href="asset.png")
        asset.set_owner(blank_collection)

        assert (
            AlternateAssetsExtension.get_schema_uri()
            not in blank_collection.stac_extensions
        )

        AlternateAssetsExtension.ext(asset, add_if_missing=True)

        assert (
            AlternateAssetsExtension.get_schema_uri()
            in blank_collection.stac_extensions
        )

    def test_collection_set_alternate_asset(
        self, blank_collection: pystac.Collection
    ) -> None:
        asset = pystac.Asset(href="asset.png")
        asset.set_owner(blank_collection)

        blank_collection.assets["product"] = asset
        blank_collection.stac_extensions.append(
            AlternateAssetsExtension.get_schema_uri()
        )

        assert "alternate" not in asset.extra_fields

        alternate_asset = AlternateAsset(
            {"href": "product1.png"},
            owner=blank_collection,
            asset_name="product",
            alternate="s3",
        )
        asset.ext.alternate.set_asset("s3", alternate_asset)

        assert "alternate" in asset.extra_fields
        assert blank_collection.assets["product"] is asset

        alternates = blank_collection.assets["product"].extra_fields.get(
            "alternate", {}
        )
        actual = alternates.get("s3")
        assert actual is not None
        assert actual.get("href") == alternate_asset.href
