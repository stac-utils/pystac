import json
import random

import pytest

import pystac
from pystac import Asset, Collection, ExtensionTypeError, Item
from pystac.extensions.archive import ArchiveExtension
from pystac.extensions.eo import Band
from tests.utils import TestCases, assert_to_from_dict


@pytest.fixture
def example_item_uri() -> str:
    return TestCases.get_path("data-files/archive/example-Item.json")


@pytest.fixture
def example_empty_item_uri() -> str:
    return TestCases.get_path("data-files/archive/example-empty-Item.json")


@pytest.fixture
def example_collection_uri() -> str:
    return TestCases.get_path("data-files/archive/example-Collection.json")


@pytest.fixture
def archive_asset(example_empty_item_uri: str) -> Asset:
    example_empty_item = pystac.Item.from_file(example_empty_item_uri)
    asset = example_empty_item.assets["example"]
    return asset


@pytest.fixture
def archive_item(example_item_uri: str) -> Item:
    example_item = pystac.Item.from_file(example_item_uri)
    return example_item


@pytest.fixture
def archive_collection() -> Collection:
    test_collection_uri = TestCases.get_path(
        "data-files/archive/example-Collection.json"
    )
    test_collection = pystac.Collection.from_file(test_collection_uri)
    return test_collection


def test_to_from_dict(example_item_uri: str) -> None:
    with open(example_item_uri) as f:
        d = json.load(f)
    assert_to_from_dict(pystac.Item, d)


def test_add_to(sample_item: Item) -> None:
    assert ArchiveExtension.get_schema_uri() not in sample_item.stac_extensions

    # Check that the URI gets added to stac_extensions
    ArchiveExtension.add_to(sample_item)
    assert ArchiveExtension.get_schema_uri() in sample_item.stac_extensions

    # Check that the URI only gets added once, regardless of how many times add_to
    # is called.
    ArchiveExtension.add_to(sample_item)
    ArchiveExtension.add_to(sample_item)

    archive_uris = [
        uri
        for uri in sample_item.stac_extensions
        if uri == ArchiveExtension.get_schema_uri()
    ]
    assert len(archive_uris) == 1


@pytest.mark.vcr()
def test_validate_archive(archive_item: Item) -> None:
    print(f"In test_validate_archive: {archive_item.properties}", flush=True)
    print(f"{archive_item.assets['ext-asset'].extra_fields}", flush=True)
    archive_item.validate()


def test_extend_invalid_object() -> None:
    link = pystac.Link("child", "https://some-domain.com/some/path/to.json")

    with pytest.raises(pystac.ExtensionTypeError):
        ArchiveExtension.ext(link)  # type: ignore


def test_extension_not_implemented(sample_item: Item) -> None:
    # Should raise exception if Item does not include extension URI

    if ArchiveExtension.get_schema_uri() not in sample_item.stac_extensions:
        pytest.raises(pystac.ExtensionNotImplemented)

    # Should raise exception if owning Item does not include extension URI
    asset = sample_item.assets["thumbnail"]

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = ArchiveExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = ArchiveExtension.ext(ownerless_asset)


def test_item_ext_add_to(sample_item: Item) -> None:
    assert ArchiveExtension.get_schema_uri() not in sample_item.stac_extensions

    asset = sample_item.assets["thumbnail"]
    _ = ArchiveExtension.ext(asset, add_if_missing=True)

    assert ArchiveExtension.get_schema_uri() in sample_item.stac_extensions


def test_asset_ext_add_to_ownerless_asset(sample_item: Item) -> None:
    asset_dict = sample_item.assets["thumbnail"].to_dict()
    asset = pystac.Asset.from_dict(asset_dict)

    with pytest.raises(pystac.STACError):
        _ = ArchiveExtension.ext(asset, add_if_missing=True)


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError, match=r"^ArchiveExtension does not apply to type 'object'$"
    ):
        # calling it wrong purposely so ---------v
        ArchiveExtension.ext(object())  # type: ignore


# Tests for summaries
def test_summaries_href(archive_collection: Collection) -> None:
    col_dict = archive_collection.to_dict()
    archive_summaries = ArchiveExtension.summaries(archive_collection)

    # Get
    assert archive_summaries.href == col_dict["summaries"]["archive:href"]
    # Set
    new_href_summary = ["new-example.tar.gz", "new-example-2.tar.gz"]
    assert archive_summaries.href != new_href_summary
    archive_summaries.href = new_href_summary
    assert archive_summaries.href == new_href_summary

    col_dict = archive_collection.to_dict()
    assert col_dict["summaries"]["archive:href"] == new_href_summary


def test_summaries_type(archive_collection: Collection) -> None:
    col_dict = archive_collection.to_dict()
    archive_summaries = ArchiveExtension.summaries(archive_collection)

    # Get
    assert archive_summaries.type == col_dict["summaries"]["archive:type"]
    # Set
    new_type_summary = ["new-example-type", "new-example-type-2"]
    assert archive_summaries.type != new_type_summary
    archive_summaries.type = new_type_summary
    assert archive_summaries.type == new_type_summary

    col_dict = archive_collection.to_dict()
    assert col_dict["summaries"]["archive:type"] == new_type_summary


def test_summaries_roles(archive_collection: Collection) -> None:
    col_dict = archive_collection.to_dict()
    archive_summaries = ArchiveExtension.summaries(archive_collection)

    # Get
    assert archive_summaries.roles == col_dict["summaries"]["archive:roles"]
    # Set
    new_roles_summary = [["new-example-roles"], ["new-example-roles-2"]]
    assert archive_summaries.roles != new_roles_summary
    archive_summaries.roles = new_roles_summary
    assert archive_summaries.roles == new_roles_summary

    col_dict = archive_collection.to_dict()
    assert col_dict["summaries"]["archive:roles"] == new_roles_summary


def test_summaries_range(archive_collection: Collection) -> None:
    col_dict = archive_collection.to_dict()
    archive_summaries = ArchiveExtension.summaries(archive_collection)

    # Get
    assert archive_summaries.range == col_dict["summaries"]["archive:range"]
    # Set
    new_range_summary = [[100, 200], [ 400, 500]]
    assert archive_summaries.range != new_range_summary
    archive_summaries.range = new_range_summary
    assert archive_summaries.range == new_range_summary

    col_dict = archive_collection.to_dict()
    assert col_dict["summaries"]["archive:range"] == new_range_summary


def test_summaries_title(archive_collection: Collection) -> None:
    col_dict = archive_collection.to_dict()
    archive_summaries = ArchiveExtension.summaries(archive_collection)

    # Get
    assert archive_summaries.title == col_dict["summaries"]["archive:title"]
    # Set
    new_title_summary = ["new-example-title", "new-example-title-2"]
    assert archive_summaries.title != new_title_summary
    archive_summaries.title = new_title_summary
    assert archive_summaries.title == new_title_summary

    col_dict = archive_collection.to_dict()
    assert col_dict["summaries"]["archive:title"] == new_title_summary


def test_summaries_description(archive_collection: Collection) -> None:
    col_dict = archive_collection.to_dict()
    archive_summaries = ArchiveExtension.summaries(archive_collection)

    # Get
    assert archive_summaries.description == col_dict["summaries"]["archive:description"]
    # Set
    new_description_summary = ["new-example-description", "new-example-description-2"]
    assert archive_summaries.description != new_description_summary
    archive_summaries.description = new_description_summary
    assert archive_summaries.description == new_description_summary

    col_dict = archive_collection.to_dict()
    assert col_dict["summaries"]["archive:description"] == new_description_summary


def test_summaries_bands(archive_collection: Collection) -> None:
    col_dict = archive_collection.to_dict()
    archive_summaries = ArchiveExtension.summaries(archive_collection)

    # Get
    assert archive_summaries.bands == col_dict["summaries"]["archive:bands"]
    # Set
    new_bands_summary = [[Band({"name": "B1"})], [Band({"name": "B2"})]] # type: list[list[Band]] | None
    assert archive_summaries.bands != new_bands_summary
    archive_summaries.bands = new_bands_summary
    assert archive_summaries.bands == new_bands_summary

    col_dict = archive_collection.to_dict()
    assert col_dict["summaries"]["archive:bands"] == new_bands_summary


def test_item_apply() -> None:
    example_empty_item_uri = TestCases.get_path(
        "data-files/archive/example-empty-Item.json"
    )
    example_empty_item = pystac.Item.from_file(example_empty_item_uri)
    asset = example_empty_item.assets["example"]

    archive_ext = ArchiveExtension.ext(asset)

    archive_ext.apply(
        href="some/href/path",
        type="application/zip",
        roles=["data"],
        range=[],
        title="An Archive",
        description="This is an example archive.",
        bands=[],
        archive=[],
    )

    assert archive_ext.href == "some/href/path"
    assert archive_ext.type == "application/zip"
    assert archive_ext.roles == ["data"]
    assert archive_ext.range == []
    assert archive_ext.title == "An Archive"
    assert archive_ext.description == "This is an example archive."
    assert archive_ext.bands == []
    assert archive_ext.archive == []
    # example_empty_item.validate()


@pytest.mark.vcr()
def test_partial_apply(archive_asset: Asset) -> None:
    ArchiveExtension.ext(archive_asset).apply(href="some/href/path")

    assert ArchiveExtension.ext(archive_asset).href == "some/href/path"


@pytest.mark.vcr()
def test_asset_href(archive_item: Item) -> None:
    # Grab a random asset with the platform property
    asset = random.choice(
        [
            _asset
            for _asset in archive_item.assets.values()
            if "archive:href" in _asset.to_dict()
        ]
    )

    archive_ext = ArchiveExtension.ext(asset)

    # Get
    assert archive_ext.href == asset.extra_fields.get("archive:href")

    # Set
    new_href = "some/other/href/path"
    archive_ext.href = new_href
    assert archive_ext.href == new_href

    archive_item.validate()

    # Set to None
    archive_ext.href = None
    assert "archive:href" not in asset.extra_fields


@pytest.mark.vcr()
def test_asset_type(archive_item: Item) -> None:
    # Grab a random asset with the platform property
    asset = random.choice(
        [
            _asset
            for _asset in archive_item.assets.values()
            if "archive:href" in _asset.to_dict()
        ]
    )

    archive_ext = ArchiveExtension.ext(asset)

    # Get
    assert archive_ext.type == asset.extra_fields.get("archive:type")

    # Set
    new_type = "some/file/type"
    archive_ext.type = new_type
    assert archive_ext.type == new_type

    archive_item.validate()

    # Set to None
    archive_ext.type = None
    assert "archive:type" not in asset.extra_fields


@pytest.mark.vcr()
def test_asset_roles(archive_item: Item) -> None:
    # Grab a random asset with the platform property
    asset = random.choice(
        [
            _asset
            for _asset in archive_item.assets.values()
            if "archive:roles" in _asset.to_dict()
        ]
    )

    archive_ext = ArchiveExtension.ext(asset)

    # Get
    assert archive_ext.roles == asset.extra_fields.get("archive:roles")

    # Set
    new_roles = ["some", "file", "roles"]
    archive_ext.roles = new_roles
    assert archive_ext.roles == new_roles

    archive_item.validate()

    # Set to None
    archive_ext.type = None
    assert "archive:type" not in asset.extra_fields

    archive_item.validate()


@pytest.mark.vcr()
def test_asset_range(archive_item: Item) -> None:
    # Grab a random asset with the platform property
    asset = random.choice(
        [
            _asset
            for _asset in archive_item.assets.values()
            if "archive:range" in _asset.to_dict()
        ]
    )

    archive_ext = ArchiveExtension.ext(asset)

    # Get
    assert archive_ext.range == asset.extra_fields.get("archive:range")

    # Set
    new_range = [0, 1000]
    archive_ext.range = new_range
    assert archive_ext.range == new_range

    archive_item.validate()

    # Set to None
    archive_ext.range = None
    assert "archive:range" not in asset.extra_fields

    archive_item.validate()


@pytest.mark.vcr()
def test_asset_title(archive_item: Item) -> None:
    # Grab a random asset with the platform property
    asset = random.choice(
        [
            _asset
            for _asset in archive_item.assets.values()
            if "archive:title" in _asset.to_dict()
        ]
    )

    archive_ext = ArchiveExtension.ext(asset)

    # Get
    assert archive_ext.title == asset.extra_fields.get("archive:title")

    # Set
    new_title = "some new title"
    archive_ext.title = new_title
    assert archive_ext.title == new_title

    archive_item.validate()

    # Set to None
    archive_ext.title = None
    assert "archive:title" not in asset.extra_fields

    archive_item.validate()


@pytest.mark.vcr()
def test_asset_description(archive_item: Item) -> None:
    # Grab a random asset with the platform property
    asset = random.choice(
        [
            _asset
            for _asset in archive_item.assets.values()
            if "archive:description" in _asset.to_dict()
        ]
    )

    archive_ext = ArchiveExtension.ext(asset)

    # Get
    assert archive_ext.description == asset.extra_fields.get("archive:description")

    # Set
    new_description = "some new description"
    archive_ext.description = new_description
    assert archive_ext.description == new_description

    archive_item.validate()

    # Set to None
    archive_ext.description = None
    assert "archive:description" not in asset.extra_fields

    archive_item.validate()


@pytest.mark.vcr()
def test_asset_bands(archive_item: Item) -> None:
    # Grab a random asset with the platform property
    asset = random.choice(
        [
            _asset
            for _asset in archive_item.assets.values()
            if "archive:bands" in _asset.to_dict()
        ]
    )

    archive_ext = ArchiveExtension.ext(asset)

    # Get
    assert archive_ext.bands == asset.extra_fields.get("archive:bands")

    # Set
    new_bands = None
    archive_ext.bands = new_bands
    assert archive_ext.bands == new_bands

    archive_item.validate()

    # Set to None
    archive_ext.bands = None
    assert "archive:bands" not in asset.extra_fields

    archive_item.validate()


@pytest.mark.vcr()
def test_asset_archive(archive_item: Item) -> None:
    # Grab a random asset with the platform property
    asset = random.choice(
        [
            _asset
            for _asset in archive_item.assets.values()
            if "archive:archive" in _asset.to_dict()
        ]
    )

    archive_ext = ArchiveExtension.ext(asset)

    # Get
    assert archive_ext.archive == asset.extra_fields.get("archive:archive")

    # Set
    new_archive = None
    archive_ext.archive = new_archive
    assert archive_ext.archive == new_archive

    archive_item.validate()

    # Set to None
    archive_ext.archive = None
    assert "archive:archive" not in asset.extra_fields

    archive_item.validate()
