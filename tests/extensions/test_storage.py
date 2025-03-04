import json
import random
import unittest
from string import ascii_letters

import pytest

import pystac
from pystac import ExtensionTypeError, Item
from pystac.collection import Collection
from pystac.extensions.storage import CloudPlatform, StorageExtension
from tests.utils import TestCases, assert_to_from_dict

NAIP_EXAMPLE_URI = TestCases.get_path("data-files/storage/item-naip.json")
NAIP_COLLECTION_URI = TestCases.get_path("data-files/storage/collection-naip.json")

@pytest.fixture
def naip_item() -> Item:
    return Item.from_file(NAIP_EXAMPLE_URI)

@pytest.fixture
def naip_collection() -> Collection:
    return Collection.from_file(NAIP_COLLECTION_URI)



def test_to_from_dict() -> None:
    with open(NAIP_EXAMPLE_URI) as f:
        item_dict = json.load(f)
    assert_to_from_dict(Item, item_dict)


def test_add_to(sample_item: Item) -> None:
    assert  StorageExtension.get_schema_uri() not in sample_item.stac_extensions
    # Check that the URI gets added to stac_extensions
    StorageExtension.add_to(sample_item)
    assert StorageExtension.get_schema_uri() in sample_item.stac_extensions

    # Check that the URI only gets added once, regardless of how many times add_to
    # is called.
    StorageExtension.add_to(sample_item)
    StorageExtension.add_to(sample_item)

    eo_uris = [
        uri
        for uri in sample_item.stac_extensions
        if uri == StorageExtension.get_schema_uri()
    ]
    assert len(eo_uris) == 1

@pytest.mark.vcr()
def test_validate_storage(naip_item) -> None:
    naip_item.validate()


def test_extend_invalid_object() -> None:
    link = pystac.Link("child", "https://some-domain.com/some/path/to.json")

    with pytest.raises(pystac.ExtensionTypeError):
        StorageExtension.ext(link)  # type: ignore


def test_extension_not_implemented(sample_item: Item) -> None:
    # Should raise exception if Item does not include extension URI
    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = StorageExtension.ext(sample_item)

    # Should raise exception if owning Item does not include extension URI
    asset = sample_item.assets["thumbnail"]

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = StorageExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = StorageExtension.ext(ownerless_asset)

def test_item_ext_add_to(sample_item: Item) -> None:
    assert StorageExtension.get_schema_uri() not in sample_item.stac_extensions

    _ = StorageExtension.ext(sample_item, add_if_missing=True)

    assert StorageExtension.get_schema_uri() in sample_item.stac_extensions

def test_asset_ext_add_to(sample_item: Item) -> None:
    assert StorageExtension.get_schema_uri() not in sample_item.stac_extensions
    asset = sample_item.assets["thumbnail"]

    _ = StorageExtension.ext(asset, add_if_missing=True)

    assert StorageExtension.get_schema_uri() in sample_item.stac_extensions

def test_asset_ext_add_to_ownerless_asset(sample_item: Item) -> None:
    asset_dict = sample_item.assets["thumbnail"].to_dict()
    asset = pystac.Asset.from_dict(asset_dict)

    with pytest.raises(pystac.STACError):
        _ = StorageExtension.ext(asset, add_if_missing=True)

def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError,
        match=r"^StorageExtension does not apply to type 'object'$"
    ):
        # calling it wrong purposely so ---------v
        StorageExtension.ext(object()) # type: ignore

def test_platform(naip_collection: Collection) -> None:
    col_dict = naip_collection.to_dict()
    storage_summaries = StorageExtension.summaries(naip_collection)

    # Get
    assert storage_summaries.platform == col_dict["summaries"]["storage:platform"]
    # Set
    new_platform_summary = [random.choice([v for v in CloudPlatform])]
    assert storage_summaries.platform != new_platform_summary
    storage_summaries.platform = new_platform_summary
    assert storage_summaries.platform == new_platform_summary

    col_dict = naip_collection.to_dict()
    assert col_dict["summaries"]["storage:platform"] == new_platform_summary


class StorageExtensionSummariesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.naip_collection = Collection.from_file(NAIP_COLLECTION_URI)

    def test_region(self) -> None:
        col = self.naip_collection
        col_dict = col.to_dict()
        storage_summaries = StorageExtension.summaries(col)

        # Get
        assert  storage_summaries.region == col_dict["summaries"]["storage:region"] 
        # Set
        new_region_summary = [random.choice(ascii_letters)]
        assert storage_summaries.region != new_region_summary
        storage_summaries.region = new_region_summary
        assert storage_summaries.region == new_region_summary

        col_dict = col.to_dict()
        assert col_dict["summaries"]["storage:region"] == new_region_summary

    def test_requester_pays(self) -> None:
        col = self.naip_collection
        col_dict = col.to_dict()
        storage_summaries = StorageExtension.summaries(col)

        # Get
        assert  storage_summaries.requester_pays == col_dict["summaries"]["storage:requester_pays"] 

        # Set
        new_requester_pays_summary = [True]
        assert  storage_summaries.requester_pays != new_requester_pays_summary 
        storage_summaries.requester_pays = new_requester_pays_summary
        assert storage_summaries.requester_pays == new_requester_pays_summary

        col_dict = col.to_dict()
        assert  col_dict["summaries"]["storage:requester_pays"] == new_requester_pays_summary 

    def test_tier(self) -> None:
        col = self.naip_collection
        col_dict = col.to_dict()
        storage_summaries = StorageExtension.summaries(col)

        # Get
        assert storage_summaries.tier == col_dict["summaries"]["storage:tier"]

        # Set
        new_tier_summary = [random.choice(ascii_letters)]
        assert storage_summaries.tier != new_tier_summary
        storage_summaries.tier = new_tier_summary
        assert storage_summaries.tier == new_tier_summary

        col_dict = col.to_dict()
        assert col_dict["summaries"]["storage:tier"] == new_tier_summary

    def test_summaries_adds_uri(self) -> None:
        col = self.naip_collection
        col.stac_extensions = []
        with pytest.raises(
            pystac.ExtensionNotImplemented,
            match="Extension 'storage' is not implemented",
        ):
            StorageExtension.summaries(col, add_if_missing=False)

        _ = StorageExtension.summaries(col, add_if_missing=True)

        assert StorageExtension.get_schema_uri() in col.stac_extensions

        StorageExtension.remove_from(col)
        assert StorageExtension.get_schema_uri() not in col.stac_extensions


class AssetStorageExtensionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.naip_item = Item.from_file(NAIP_EXAMPLE_URI)

    def test_item_apply(self) -> None:
        item = self.naip_item
        asset = random.choice(list(item.assets.values()))

        storage_ext = StorageExtension.ext(asset)

        new_platform = random.choice(
            [v for v in CloudPlatform if v != storage_ext.platform]
        )
        new_region = random.choice(ascii_letters)
        new_requestor_pays = random.choice(
            [v for v in {True, False} if v != storage_ext.requester_pays]
        )
        new_tier = random.choice(ascii_letters)

        storage_ext.apply(
            platform=new_platform,
            region=new_region,
            requester_pays=new_requestor_pays,
            tier=new_tier,
        )

        assert storage_ext.platform == new_platform
        assert storage_ext.region == new_region
        assert storage_ext.requester_pays == new_requestor_pays
        assert storage_ext.tier == new_tier

    @pytest.mark.vcr()
    def test_platform(self) -> None:
        item = self.naip_item

        # Grab a random asset with the platform property
        asset = random.choice(
            [
                _asset
                for _asset in item.assets.values()
                if "storage:platform" in _asset.to_dict()
            ]
        )

        storage_ext = StorageExtension.ext(asset)

        # Get
        assert  storage_ext.platform == asset.extra_fields.get("storage:platform") 

        # Set
        new_platform = random.choice(
            [val for val in CloudPlatform if val != storage_ext.platform]
        )
        storage_ext.platform = new_platform
        assert storage_ext.platform == new_platform

        item.validate()

    @pytest.mark.vcr()
    def test_region(self) -> None:
        item = self.naip_item

        # Grab a random asset with the platform property
        asset = random.choice(
            [
                _asset
                for _asset in item.assets.values()
                if "storage:region" in _asset.to_dict()
            ]
        )

        storage_ext = StorageExtension.ext(asset)

        # Get
        assert storage_ext.region == asset.extra_fields.get("storage:region")

        # Set
        new_region = random.choice(
            [val for val in CloudPlatform if val != storage_ext.region]
        )
        storage_ext.region = new_region
        assert storage_ext.region == new_region

        item.validate()

        # Set to None
        storage_ext.region = None
        assert "storage:region" not in asset.extra_fields

    @pytest.mark.vcr()
    def test_requester_pays(self) -> None:
        item = self.naip_item

        # Grab a random asset with the platform property
        asset = random.choice(
            [
                _asset
                for _asset in item.assets.values()
                if "storage:requester_pays" in _asset.to_dict()
            ]
        )

        storage_ext = StorageExtension.ext(asset)

        # Get
        assert  storage_ext.requester_pays == asset.extra_fields.get("storage:requester_pays") 

        # Set
        new_requester_pays = True if not storage_ext.requester_pays else False
        storage_ext.requester_pays = new_requester_pays
        assert storage_ext.requester_pays == new_requester_pays

        item.validate()

        # Set to None
        storage_ext.requester_pays = None
        assert "storage:requester_pays" not in asset.extra_fields

    @pytest.mark.vcr()
    def test_tier(self) -> None:
        item = self.naip_item

        # Grab a random asset with the platform property
        asset = random.choice(
            [
                _asset
                for _asset in item.assets.values()
                if "storage:tier" in _asset.to_dict()
            ]
        )

        storage_ext = StorageExtension.ext(asset)

        # Get
        assert storage_ext.tier == asset.extra_fields.get("storage:tier")

        # Set
        new_tier = random.choice(ascii_letters)
        storage_ext.tier = new_tier
        assert storage_ext.tier == new_tier

        item.validate()

        # Set to None
        storage_ext.tier = None
        assert "storage:tier" not in asset.extra_fields
