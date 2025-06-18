import json
import random
from copy import deepcopy
from string import ascii_letters

import pytest

import pystac
from pystac import ExtensionTypeError, Item, ItemAssetDefinition
from pystac.collection import Collection
from pystac.extensions.storage import (
    StorageRefsExtension,
    StorageScheme,
    StorageSchemesExtension,
    StorageSchemeType,
)
from tests.utils import TestCases, assert_to_from_dict

NAIP_EXAMPLE_URI = TestCases.get_path("data-files/storage/item-naip.json")
NAIP_COLLECTION_URI = TestCases.get_path("data-files/storage/collection-naip.json")


@pytest.fixture
def naip_item() -> Item:
    return Item.from_file(NAIP_EXAMPLE_URI)


@pytest.fixture
def naip_collection() -> Collection:
    return Collection.from_file(NAIP_COLLECTION_URI)


@pytest.fixture
def sample_scheme() -> StorageScheme:
    return StorageScheme.create(
        type=StorageSchemeType.AWS_S3,
        platform="https://{bucket}.s3.{region}.amazonaws.com",
        region="us-west-2",
        requester_pays=True,
    )


@pytest.fixture
def naip_asset(naip_item: Item) -> pystac.Asset:
    # Grab a random asset with the platform property
    return random.choice(
        [
            _asset
            for _asset in naip_item.assets.values()
            if "storage:refs" in _asset.to_dict()
        ]
    )


def test_to_from_dict() -> None:
    with open(NAIP_EXAMPLE_URI) as f:
        item_dict = json.load(f)
    assert_to_from_dict(Item, item_dict)


def test_add_to(sample_item: Item) -> None:
    assert StorageSchemesExtension.get_schema_uri() not in sample_item.stac_extensions
    # Check that the URI gets added to stac_extensions
    StorageSchemesExtension.add_to(sample_item)
    assert StorageSchemesExtension.get_schema_uri() in sample_item.stac_extensions

    # Check that the URI only gets added once, regardless of how many times add_to
    # is called.
    StorageSchemesExtension.add_to(sample_item)
    StorageSchemesExtension.add_to(sample_item)

    uris = [
        uri
        for uri in sample_item.stac_extensions
        if uri == StorageSchemesExtension.get_schema_uri()
    ]
    assert len(uris) == 1


@pytest.mark.vcr()
def test_validate_storage(naip_item: Item) -> None:
    naip_item.validate()


def test_extend_invalid_object() -> None:
    link = pystac.Link("child", "https://some-domain.com/some/path/to.json")

    with pytest.raises(pystac.ExtensionTypeError):
        StorageSchemesExtension.ext(link)  # type: ignore


def test_extension_not_implemented(sample_item: Item) -> None:
    # Should raise exception if Item does not include extension URI
    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = StorageSchemesExtension.ext(sample_item)

    # Should raise exception if owning Item does not include extension URI
    asset = sample_item.assets["thumbnail"]

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = StorageRefsExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = StorageRefsExtension.ext(ownerless_asset)


def test_collection_ext_add_to(naip_collection: Collection) -> None:
    naip_collection.stac_extensions = []
    assert (
        StorageSchemesExtension.get_schema_uri() not in naip_collection.stac_extensions
    )

    _ = StorageSchemesExtension.ext(naip_collection, add_if_missing=True)

    assert StorageSchemesExtension.get_schema_uri() in naip_collection.stac_extensions


def test_item_ext_add_to(sample_item: Item) -> None:
    assert StorageSchemesExtension.get_schema_uri() not in sample_item.stac_extensions

    _ = StorageSchemesExtension.ext(sample_item, add_if_missing=True)

    assert StorageSchemesExtension.get_schema_uri() in sample_item.stac_extensions


def test_catalog_ext_add_to() -> None:
    catalog = pystac.Catalog("stac", "a catalog")

    assert StorageSchemesExtension.get_schema_uri() not in catalog.stac_extensions

    _ = StorageSchemesExtension.ext(catalog, add_if_missing=True)

    assert StorageSchemesExtension.get_schema_uri() in catalog.stac_extensions


def test_asset_ext_add_to(sample_item: Item) -> None:
    assert StorageSchemesExtension.get_schema_uri() not in sample_item.stac_extensions
    asset = sample_item.assets["thumbnail"]

    _ = StorageRefsExtension.ext(asset, add_if_missing=True)

    assert StorageSchemesExtension.get_schema_uri() in sample_item.stac_extensions


def test_link_ext_add_to(sample_item: Item) -> None:
    assert StorageSchemesExtension.get_schema_uri() not in sample_item.stac_extensions
    asset = sample_item.links[0]

    _ = StorageRefsExtension.ext(asset, add_if_missing=True)

    assert StorageSchemesExtension.get_schema_uri() in sample_item.stac_extensions


def test_asset_ext_add_to_ownerless_asset(sample_item: Item) -> None:
    asset_dict = sample_item.assets["thumbnail"].to_dict()
    asset = pystac.Asset.from_dict(asset_dict)

    with pytest.raises(pystac.STACError):
        _ = StorageRefsExtension.ext(asset, add_if_missing=True)


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError,
        match=r"^StorageRefsExtension does not apply to type 'object'$",
    ):
        # calling it wrong purposely so ---------v
        StorageRefsExtension.ext(object())  # type: ignore


def test_summaries_schemes(naip_collection: Collection) -> None:
    col_dict = naip_collection.to_dict()
    storage_summaries = StorageSchemesExtension.summaries(naip_collection)
    print(naip_collection.summaries)
    # Get
    assert (
        list(
            map(
                lambda x: {k: c.to_dict() for k, c in x.items()},
                storage_summaries.schemes or [],
            )
        )
        == col_dict["summaries"]["storage:schemes"]
    )
    # Set
    new_schemes_summary = [
        {"key": StorageScheme.create("aws-s3", "https://a.platform.example.com")}
    ]
    assert storage_summaries.schemes != new_schemes_summary
    storage_summaries.schemes = new_schemes_summary
    assert storage_summaries.schemes == new_schemes_summary

    col_dict = naip_collection.to_dict()
    assert col_dict["summaries"]["storage:schemes"] == [
        {k: c.to_dict() for k, c in x.items()} for x in new_schemes_summary
    ]


def test_summaries_adds_uri(naip_collection: Collection) -> None:
    naip_collection.stac_extensions = []
    with pytest.raises(
        pystac.ExtensionNotImplemented,
        match="Extension 'storage' is not implemented",
    ):
        StorageSchemesExtension.summaries(naip_collection, add_if_missing=False)

    _ = StorageSchemesExtension.summaries(naip_collection, add_if_missing=True)

    assert StorageSchemesExtension.get_schema_uri() in naip_collection.stac_extensions

    StorageSchemesExtension.remove_from(naip_collection)
    assert (
        StorageSchemesExtension.get_schema_uri() not in naip_collection.stac_extensions
    )


def test_schemes_apply(naip_item: Item) -> None:
    storage_ext = StorageSchemesExtension.ext(naip_item)
    new_key = random.choice(ascii_letters)
    new_type = random.choice(ascii_letters)
    new_platform = random.choice(ascii_letters)
    new_region = random.choice(ascii_letters)
    new_requestor_pays = random.choice([v for v in {True, False}])

    storage_ext.apply(
        schemes={
            new_key: StorageScheme.create(
                new_type, new_platform, new_region, new_requestor_pays
            ),
        }
    )

    applied_schemes = storage_ext.schemes
    assert list(applied_schemes) == [new_key]
    assert applied_schemes[new_key].type == new_type
    assert applied_schemes[new_key].platform == new_platform
    assert applied_schemes[new_key].region == new_region
    assert applied_schemes[new_key].requester_pays == new_requestor_pays


@pytest.mark.vcr()
def test_refs_apply(naip_asset: pystac.Asset) -> None:
    test_refs = ["a_ref", "b_ref"]

    storage_ext = StorageRefsExtension.ext(naip_asset)

    storage_ext.apply(test_refs)

    # Get
    assert storage_ext.refs == test_refs

    # Set
    new_refs = [random.choice(ascii_letters)]
    storage_ext.refs = new_refs
    assert storage_ext.refs == new_refs


def test_add_storage_scheme(naip_item: Item) -> None:
    storage_ext = naip_item.ext.storage
    storage_ext.add_scheme("new_scheme", StorageScheme.create("type", "platform"))
    assert "new_scheme" in storage_ext.schemes

    storage_ext.properties.pop("storage:schemes")
    storage_ext.add_scheme("new_scheme", StorageScheme.create("type", "platform"))
    assert len(storage_ext.schemes) == 1
    assert "new_scheme" in storage_ext.schemes


def test_add_refs(naip_item: Item) -> None:
    scheme_name = random.choice(ascii_letters)
    asset = naip_item.assets["GEOTIFF_AZURE_RGBIR"]
    storage_ext = asset.ext.storage
    assert isinstance(storage_ext, StorageRefsExtension)

    storage_ext.add_ref(scheme_name)
    assert scheme_name in storage_ext.refs

    storage_ext.properties.pop("storage:refs")
    scheme_name_2 = random.choice(ascii_letters)
    storage_ext.add_ref(scheme_name_2)
    assert len(storage_ext.refs) == 1
    assert scheme_name_2 in storage_ext.refs


def test_storage_scheme_create(sample_scheme: StorageScheme) -> None:
    assert sample_scheme.type == StorageSchemeType.AWS_S3
    assert sample_scheme.platform == "https://{bucket}.s3.{region}.amazonaws.com"
    assert sample_scheme.region == "us-west-2"
    assert sample_scheme.requester_pays is True

    sample_scheme.type = StorageSchemeType.AZURE
    sample_scheme.platform = "https://{account}.blob.core.windows.net"
    sample_scheme.region = "eastus"
    sample_scheme.account = "account"
    sample_scheme.requester_pays = False

    assert sample_scheme.type == StorageSchemeType.AZURE
    assert sample_scheme.platform == "https://{account}.blob.core.windows.net"
    assert sample_scheme.region == "eastus"
    assert sample_scheme.account == "account"
    assert sample_scheme.requester_pays is False


def test_storage_scheme_equality(sample_scheme: StorageScheme) -> None:
    other = deepcopy(sample_scheme)
    assert sample_scheme == other

    other.requester_pays = False
    assert sample_scheme != other

    assert sample_scheme != object()


def test_item_asset_accessor() -> None:
    item_asset = ItemAssetDefinition.create(
        title="title", description="desc", media_type="media", roles=["a_role"]
    )
    assert isinstance(item_asset.ext.storage, StorageRefsExtension)
