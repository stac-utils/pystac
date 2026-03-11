"""Tests for pystac.tests.extensions.xarray_assets"""

import json

import pytest

import pystac
from pystac.extensions.xarray_assets import XarrayAssetsExtension

from ..conftest import get_data_file


@pytest.fixture
def ext_collection_uri() -> str:
    return get_data_file("xarray-assets/collection.json")


@pytest.fixture
def ext_collection(ext_collection_uri: str) -> pystac.Collection:
    return pystac.Collection.from_file(ext_collection_uri)


@pytest.fixture
def ext_item_uri() -> str:
    return get_data_file("xarray-assets/item.json")


@pytest.fixture
def ext_item(ext_item_uri: str) -> pystac.Item:
    return pystac.Item.from_file(ext_item_uri)


@pytest.fixture
def ext_asset(ext_item: pystac.Item) -> pystac.Asset:
    return ext_item.assets["data"]


def test_item_stac_extensions(ext_item: pystac.Item) -> None:
    assert XarrayAssetsExtension.has_extension(ext_item)


def test_collection_stac_extensions(ext_collection: pystac.Collection) -> None:
    assert XarrayAssetsExtension.has_extension(ext_collection)


def test_item_get_schema_uri(ext_item: pystac.Item) -> None:
    assert XarrayAssetsExtension.get_schema_uri() in ext_item.stac_extensions


def test_collection_get_schema_uri(ext_collection: pystac.Collection) -> None:
    assert XarrayAssetsExtension.get_schema_uri() in ext_collection.stac_extensions


def test_ext_raises_if_item_does_not_conform(item: pystac.Item) -> None:
    with pytest.raises(pystac.errors.ExtensionNotImplemented):
        XarrayAssetsExtension.ext(item)


def test_ext_raises_if_collection_does_not_conform(
    collection: pystac.Collection,
) -> None:
    with pytest.raises(pystac.errors.ExtensionNotImplemented):
        XarrayAssetsExtension.ext(collection)


def test_ext_raises_on_catalog(catalog: pystac.Catalog) -> None:
    with pytest.raises(
        pystac.errors.ExtensionTypeError,
        match="XarrayAssetsExtension does not apply to type 'Catalog'",
    ):
        XarrayAssetsExtension.ext(catalog)  # type: ignore


def test_item_to_from_dict(ext_item_uri: str, ext_item: pystac.Item) -> None:
    with open(ext_item_uri) as f:
        d = json.load(f)
    actual = ext_item.to_dict(include_self_link=False)
    assert actual == d


def test_collection_to_from_dict(
    ext_collection_uri: str, ext_collection: pystac.Item
) -> None:
    with open(ext_collection_uri) as f:
        d = json.load(f)
    actual = ext_collection.to_dict(include_self_link=False)
    assert actual == d


def test_add_to_item(item: pystac.Item) -> None:
    assert not XarrayAssetsExtension.has_extension(item)
    XarrayAssetsExtension.add_to(item)

    assert XarrayAssetsExtension.has_extension(item)


def test_add_to_collection(collection: pystac.Collection) -> None:
    assert not XarrayAssetsExtension.has_extension(collection)
    XarrayAssetsExtension.add_to(collection)

    assert XarrayAssetsExtension.has_extension(collection)


@pytest.mark.vcr
def test_item_validate(ext_item: pystac.Item) -> None:
    assert ext_item.validate()


@pytest.mark.vcr
def test_collection_validate(ext_collection: pystac.Collection) -> None:
    assert ext_collection.validate()


def test_fields_are_not_on_item(ext_item: pystac.Item) -> None:
    assert not hasattr(XarrayAssetsExtension.ext(ext_item), "storage_options")
    assert not hasattr(XarrayAssetsExtension.ext(ext_item), "open_kwargs")


def test_fields_are_not_on_collection(ext_collection: pystac.Item) -> None:
    assert not hasattr(XarrayAssetsExtension.ext(ext_collection), "storage_options")
    assert not hasattr(XarrayAssetsExtension.ext(ext_collection), "open_kwargs")


@pytest.mark.parametrize("field", ["storage_options", "open_kwargs"])
def test_get_field(ext_asset: pystac.Asset, field: str) -> None:
    prop = ext_asset.extra_fields[f"xarray:{field}"]
    attr = getattr(XarrayAssetsExtension.ext(ext_asset), field)

    assert attr is not None
    assert attr == prop


@pytest.mark.parametrize(
    "field,value",
    [
        ("storage_options", {"anon": True}),
        ("open_kwargs", {"engine": "zarr"}),
    ],
)
@pytest.mark.vcr
def test_set_field(ext_asset: pystac.Asset, field: str, value) -> None:  # type: ignore
    original = ext_asset.extra_fields[f"xarray:{field}"]
    setattr(XarrayAssetsExtension.ext(ext_asset), field, value)
    new = ext_asset.extra_fields[f"xarray:{field}"]

    assert new != original
    assert new == value

    item = ext_asset.owner
    assert item is not None
    assert isinstance(item, pystac.Item)
    assert item.validate()


@pytest.mark.parametrize("field", ["storage_options", "open_kwargs"])
def test_set_field_to_none_pops_from_dict(ext_asset: pystac.Asset, field: str) -> None:
    prop_name = f"xarray:{field}"
    assert prop_name in ext_asset.extra_fields

    setattr(XarrayAssetsExtension.ext(ext_asset), field, None)
    assert prop_name not in ext_asset.extra_fields
