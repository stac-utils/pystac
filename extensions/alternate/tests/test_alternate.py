import datetime as dt
import pathlib
from collections import namedtuple
from collections.abc import Iterable
from contextlib import nullcontext

import pytest

import pystac
from pystac import Asset, Item
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
    return pystac.Item(
        id="example",
        geometry={},
        bbox=[-180, -90, 180, 90],
        datetime=dt.datetime(2021, 5, 12),
        properties={},
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


@pytest.fixture()
def asset(blank_item: Item) -> Asset:
    properties = {"alternate:name": "local", "href": "product.png"}
    asset_ = pystac.Asset(
        href="product1.png",
        extra_fields={
            "alternate": {"local": properties},
            "title": "Product file",
        },
    )
    blank_item.assets["product"] = asset_
    blank_item.stac_extensions.append(AlternateAssetsExtension.get_schema_uri())
    asset_.set_owner(blank_item)

    return asset_


@pytest.fixture()
def alternate_asset(asset: Asset) -> AlternateAsset:
    return AlternateAsset(
        asset.extra_fields["alternate"]["local"],
        asset.owner,
        "product",
        "local",
    )


class TestAlternateAsset:
    @pytest.mark.parametrize("name", ["alternate:name", "href"])
    def test_get_property(self, name: str, alternate_asset: AlternateAsset) -> None:
        actual = alternate_asset._get_property(name, str)
        assert isinstance(actual, str)

    @pytest.mark.parametrize(
        ["name", "value", "pop_if_none"],
        (
            ("alternate:name", "Local", False),
            ("href", "product1.jpg", True),
            ("href", None, True),
        ),
    )
    def test_set_property(
        self,
        name: str,
        value: str | None,
        pop_if_none: bool,
        alternate_asset: AlternateAsset,
    ) -> None:
        alternate_asset._set_property(name, value, pop_if_none=pop_if_none)
        if value is None and pop_if_none:
            assert name not in alternate_asset.properties
        else:
            assert name in alternate_asset.properties
            assert alternate_asset.properties[name] == value

    def test_name_get(self, alternate_asset: AlternateAsset) -> None:
        assert alternate_asset.name == "local"

    def test_name_set(self, alternate_asset: AlternateAsset) -> None:
        alternate_asset.name = "s3"

        assert alternate_asset.properties["alternate:name"] == "s3"
        assert alternate_asset.name == "s3"

    def test_parent(self, alternate_asset: AlternateAsset, blank_item: Item) -> None:
        asset = pystac.Asset(href="product1.png")
        blank_item.assets["product"] = asset

        alternate_asset.owner = blank_item

        assert isinstance(alternate_asset.parent, Asset)

    def test_parent_no_owner(self, alternate_asset: AlternateAsset) -> None:
        alternate_asset.owner = None
        with pytest.raises(ValueError, match="unknown owner"):
            alternate_asset.parent

    def test_href_get_invalid(self, alternate_asset: AlternateAsset) -> None:
        alternate_asset.properties["href"] = None
        with pytest.raises(ValueError, match="invalid href"):
            alternate_asset.href

    def test_href_set(self, alternate_asset: AlternateAsset) -> None:
        alternate_asset.href = "product1.jpg"
        assert alternate_asset.properties["href"] == "product1.jpg"

    def test_href_set_invalid(self, alternate_asset: AlternateAsset) -> None:
        with pytest.raises(ValueError, match="invalid href"):
            alternate_asset.href = None

    def test_to_dict(self, alternate_asset: AlternateAsset, blank_item: Item) -> None:
        actual = alternate_asset.to_dict()
        assert actual == {
            "href": "product.png",
            "alternate:name": "local",
            "title": "Product file",
        }

    def test_to_dict_no_owner(self, alternate_asset: AlternateAsset) -> None:
        alternate_asset.owner = None

        with pytest.raises(ValueError, match="unknown owner"):
            alternate_asset.to_dict()

    def test_to_asset(self, alternate_asset: AlternateAsset) -> None:
        actual = alternate_asset.to_asset()
        assert isinstance(actual, Asset)
        assert actual.owner is not None
        assert actual.to_dict() == {
            "href": "product.png",
            "alternate:name": "local",
            "title": "Product file",
        }

    def test_to_asset_no_owner(self, alternate_asset: AlternateAsset) -> None:
        alternate_asset.owner = None

        with pytest.raises(ValueError, match="unknown owner"):
            alternate_asset.to_asset()

    def test_repr(self, alternate_asset: AlternateAsset) -> None:
        assert (
            repr(alternate_asset) == "<AlternateAsset asset=product, alternate=local>"
        )


class TestExtensionFunctions:
    def test_ext(self, asset: Asset) -> None:
        alternate_ext = AlternateAssetsExtension.ext(asset)

        assert isinstance(alternate_ext, AlternateAssetsExtension)

    def test_ext_wrong_type(self, blank_item: Item) -> None:
        with pytest.raises(pystac.errors.ExtensionTypeError):
            AlternateAssetsExtension.ext(blank_item)

    def test_ext_missing(self, blank_item: Item) -> None:
        asset = Asset(href="product2.zip")
        asset.set_owner(blank_item)

        with pytest.raises(pystac.errors.ExtensionNotImplemented):
            AlternateAssetsExtension.ext(asset)

    def test_asset_name(self, asset: Asset) -> None:
        alternate_ext = AlternateAssetsExtension.ext(asset)
        assert alternate_ext.asset_name == "product"

    def test_asset_name_inconsistent(self, asset: Asset) -> None:
        assert asset.owner is not None
        asset.owner.assets.pop("product", None)
        alternate_ext = AlternateAssetsExtension.ext(asset)

        with pytest.raises(RuntimeError):
            alternate_ext.asset_name

    @pytest.mark.parametrize(
        ["key", "expected"], ((None, True), ("local", True), ("s3", False))
    )
    def test_item_has_asset(self, asset: Asset, key: str, expected: bool) -> None:
        alternate_ext = AlternateAssetsExtension.ext(asset)
        assert alternate_ext.has_asset(key) == expected

    def test_item_get_asset(self, items_alternate: AlternateAssetContainer) -> None:
        asset = items_alternate.asset
        alternate_key = items_alternate.alternate

        print(asset.owner.stac_extensions)
        alternate_ext = AlternateAssetsExtension.ext(asset)
        actual = alternate_ext.get_asset(alternate_key)

        assert isinstance(actual, AlternateAsset)
        assert actual.owner is asset.owner
        assert "alternate" not in actual.properties

    def test_item_get_asset_no_alternate(self, asset: Asset) -> None:
        asset.extra_fields.pop("alternate", None)

        alternate_ext = AlternateAssetsExtension.ext(asset)
        with pytest.raises(ValueError):
            alternate_ext.get_asset("product")

    def test_item_get_asset_unknown(self, asset: Asset) -> None:
        alternate_ext = AlternateAssetsExtension.ext(asset)
        with pytest.raises(ValueError):
            alternate_ext.get_asset("product2")

    @pytest.mark.parametrize(
        ["key", "href"],
        (
            ("zipped", "product2.zip"),
            ("archive", "product2.png"),
        ),
    )
    def test_item_set_asset(self, asset: Asset, key: str, href: str) -> None:
        alternate_asset = AlternateAsset(
            {"href": href, "alternate:name": "zipped"}, asset.owner, "product", key
        )

        alternate_ext = AlternateAssetsExtension.ext(asset)
        alternate_ext.set_asset(key, alternate_asset)

        assert key in asset.extra_fields.get("alternate", {})
        assert asset.extra_fields["alternate"][key]["href"] == href

    def test_item_drop_asset(self, asset: Asset) -> None:
        alternate_ext = AlternateAssetsExtension.ext(asset)
        alternate_ext.drop_asset("local")

        assert "local" not in alternate_ext.properties.get("alternate", {})

    @pytest.mark.parametrize("error_if_missing", [True, False])
    def test_item_drop_asset_nonexistent(
        self, asset: Asset, error_if_missing: bool
    ) -> None:
        alternate_ext = AlternateAssetsExtension.ext(asset)
        context = pytest.raises(KeyError) if error_if_missing else nullcontext()

        with context:
            alternate_ext.drop_asset("unknown", error_if_missing=error_if_missing)

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

    def test_repr(self, asset: Asset) -> None:
        alternate_ext = AlternateAssetsExtension.ext(asset)
        actual = repr(alternate_ext)
        expected = "<AlternateAssetsExtension asset=product>"

        assert actual == expected


class TestAlternateGetitem:
    @pytest.mark.parametrize(
        ["key", "expected"],
        (
            (None, True),
            ("local", True),
            ("unknown", False),
        ),
    )
    def test_item_contains(self, asset: Asset, key: str | None, expected: bool) -> None:
        alternate_ext = AlternateAssetsExtension.ext(asset)

        actual = key in alternate_ext.assets
        assert actual == expected

    def test_item_getitem(self, items_alternate: AlternateAssetContainer) -> None:
        asset = items_alternate.asset
        alternate_key = items_alternate.alternate

        alternate_ext = AlternateAssetsExtension.ext(asset)
        actual = alternate_ext.assets[alternate_key]

        assert isinstance(actual, AlternateAsset)
        assert actual.owner is asset.owner
        assert "alternate" not in actual.properties

    @pytest.mark.parametrize(
        ["key", "href"],
        (
            ("zipped", "product2.zip"),
            ("archive", "product2.png"),
        ),
    )
    def test_item_setitem(self, asset: Asset, key: str, href: str) -> None:
        alternate_asset = AlternateAsset(
            {"href": href, "alternate:name": "zipped"}, asset.owner, "product", key
        )

        alternate_ext = AlternateAssetsExtension.ext(asset)
        alternate_ext.assets[key] = alternate_asset

        assert key in asset.extra_fields.get("alternate", {})
        assert asset.extra_fields["alternate"][key]["href"] == href

    def test_item_delitem(self, asset: Asset) -> None:
        alternate_ext = AlternateAssetsExtension.ext(asset)
        del alternate_ext.assets["local"]

        assert "local" not in alternate_ext.properties.get("alternate", {})

    def test_item_delitem_nonexistent(self, asset: Asset) -> None:
        alternate_ext = AlternateAssetsExtension.ext(asset)

        with pytest.raises(KeyError):
            del alternate_ext.assets["unknown"]

    def test_item_drop(self, asset: Asset) -> None:
        alternate_ext = AlternateAssetsExtension.ext(asset)
        alternate_ext.assets.drop("local")

        assert "local" not in alternate_ext.properties.get("alternate", {})

    @pytest.mark.parametrize("error_if_missing", [True, False])
    def test_item_drop_nonexistent(self, asset: Asset, error_if_missing: bool) -> None:
        alternate_ext = AlternateAssetsExtension.ext(asset)
        context = pytest.raises(KeyError) if error_if_missing else nullcontext()

        with context:
            alternate_ext.assets.drop("unknown", error_if_missing=error_if_missing)

    def test_collection_getitem(
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

        AlternateAssetsExtension.ext(asset, add_if_missing=True)

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
