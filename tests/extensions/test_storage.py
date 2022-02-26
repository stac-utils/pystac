import json
import random
import unittest
from string import ascii_letters

import pystac
from pystac import ExtensionTypeError, Item
from pystac.collection import Collection
from pystac.extensions.storage import StorageExtension, CloudPlatform
from tests.utils import TestCases, assert_to_from_dict


class StorageExtensionTest(unittest.TestCase):
    NAIP_EXAMPLE_URI = TestCases.get_path("data-files/storage/item-naip.json")
    PLAIN_ITEM_URI = TestCases.get_path("data-files/item/sample-item.json")
    NAIP_COLLECTION_URI = TestCases.get_path("data-files/storage/collection-naip.json")

    def setUp(self) -> None:
        self.maxDiff = None
        self.naip_item = Item.from_file(self.NAIP_EXAMPLE_URI)
        self.plain_item = Item.from_file(self.PLAIN_ITEM_URI)
        self.naip_collection = Collection.from_file(self.NAIP_COLLECTION_URI)


class ItemStorageExtensionTest(StorageExtensionTest):
    def test_to_from_dict(self) -> None:
        with open(self.NAIP_EXAMPLE_URI) as f:
            item_dict = json.load(f)
        assert_to_from_dict(self, Item, item_dict)

    def test_add_to(self) -> None:
        item = self.plain_item
        self.assertNotIn(
            StorageExtension.get_schema_uri(), self.plain_item.stac_extensions
        )

        # Check that the URI gets added to stac_extensions
        StorageExtension.add_to(item)
        self.assertIn(StorageExtension.get_schema_uri(), item.stac_extensions)

        # Check that the URI only gets added once, regardless of how many times add_to
        # is called.
        StorageExtension.add_to(item)
        StorageExtension.add_to(item)

        eo_uris = [
            uri
            for uri in item.stac_extensions
            if uri == StorageExtension.get_schema_uri()
        ]
        self.assertEqual(len(eo_uris), 1)

    def test_validate_storage(self) -> None:
        self.naip_item.validate()

    def test_extend_invalid_object(self) -> None:
        link = pystac.Link("child", "https://some-domain.com/some/path/to.json")

        with self.assertRaises(pystac.ExtensionTypeError):
            StorageExtension.ext(link)  # type: ignore

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Item does not include extension URI
        item = pystac.Item.from_file(self.PLAIN_ITEM_URI)

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = StorageExtension.ext(item)

        # Should raise exception if owning Item does not include extension URI
        asset = item.assets["thumbnail"]

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = StorageExtension.ext(asset)

        # Should succeed if Asset has no owner
        ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
        _ = StorageExtension.ext(ownerless_asset)

    def test_item_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.PLAIN_ITEM_URI)
        self.assertNotIn(StorageExtension.get_schema_uri(), item.stac_extensions)

        _ = StorageExtension.ext(item, add_if_missing=True)

        self.assertIn(StorageExtension.get_schema_uri(), item.stac_extensions)

    def test_asset_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.PLAIN_ITEM_URI)
        self.assertNotIn(StorageExtension.get_schema_uri(), item.stac_extensions)
        asset = item.assets["thumbnail"]

        _ = StorageExtension.ext(asset, add_if_missing=True)

        self.assertIn(StorageExtension.get_schema_uri(), item.stac_extensions)

    def test_asset_ext_add_to_ownerless_asset(self) -> None:
        item = pystac.Item.from_file(self.PLAIN_ITEM_URI)
        asset_dict = item.assets["thumbnail"].to_dict()
        asset = pystac.Asset.from_dict(asset_dict)

        with self.assertRaises(pystac.STACError):
            _ = StorageExtension.ext(asset, add_if_missing=True)

    def test_should_raise_exception_when_passing_invalid_extension_object(
        self,
    ) -> None:
        self.assertRaisesRegex(
            ExtensionTypeError,
            r"^StorageExtension does not apply to type 'object'$",
            StorageExtension.ext,
            object(),
        )


class StorageExtensionSummariesTest(StorageExtensionTest):
    def test_platform(self) -> None:
        col = self.naip_collection
        col_dict = col.to_dict()
        storage_summaries = StorageExtension.summaries(col)

        # Get
        self.assertEqual(
            storage_summaries.platform, col_dict["summaries"]["storage:platform"]
        )

        # Set
        new_platform_summary = [random.choice([v for v in CloudPlatform])]
        self.assertNotEqual(storage_summaries.platform, new_platform_summary)
        storage_summaries.platform = new_platform_summary
        self.assertEqual(storage_summaries.platform, new_platform_summary)

        col_dict = col.to_dict()
        self.assertEqual(
            col_dict["summaries"]["storage:platform"], new_platform_summary
        )

    def test_region(self) -> None:
        col = self.naip_collection
        col_dict = col.to_dict()
        storage_summaries = StorageExtension.summaries(col)

        # Get
        self.assertEqual(
            storage_summaries.region, col_dict["summaries"]["storage:region"]
        )

        # Set
        new_region_summary = [random.choice(ascii_letters)]
        self.assertNotEqual(storage_summaries.region, new_region_summary)
        storage_summaries.region = new_region_summary
        self.assertEqual(storage_summaries.region, new_region_summary)

        col_dict = col.to_dict()
        self.assertEqual(col_dict["summaries"]["storage:region"], new_region_summary)

    def test_requester_pays(self) -> None:
        col = self.naip_collection
        col_dict = col.to_dict()
        storage_summaries = StorageExtension.summaries(col)

        # Get
        self.assertEqual(
            storage_summaries.requester_pays,
            col_dict["summaries"]["storage:requester_pays"],
        )

        # Set
        new_requester_pays_summary = [True]
        self.assertNotEqual(
            storage_summaries.requester_pays, new_requester_pays_summary
        )
        storage_summaries.requester_pays = new_requester_pays_summary
        self.assertEqual(storage_summaries.requester_pays, new_requester_pays_summary)

        col_dict = col.to_dict()
        self.assertEqual(
            col_dict["summaries"]["storage:requester_pays"], new_requester_pays_summary
        )

    def test_tier(self) -> None:
        col = self.naip_collection
        col_dict = col.to_dict()
        storage_summaries = StorageExtension.summaries(col)

        # Get
        self.assertEqual(storage_summaries.tier, col_dict["summaries"]["storage:tier"])

        # Set
        new_tier_summary = [random.choice(ascii_letters)]
        self.assertNotEqual(storage_summaries.tier, new_tier_summary)
        storage_summaries.tier = new_tier_summary
        self.assertEqual(storage_summaries.tier, new_tier_summary)

        col_dict = col.to_dict()
        self.assertEqual(col_dict["summaries"]["storage:tier"], new_tier_summary)

    def test_summaries_adds_uri(self) -> None:
        col = self.naip_collection
        col.stac_extensions = []
        self.assertRaisesRegex(
            pystac.ExtensionNotImplemented,
            r"Could not find extension schema URI.*",
            StorageExtension.summaries,
            col,
            False,
        )
        _ = StorageExtension.summaries(col, add_if_missing=True)

        self.assertIn(StorageExtension.get_schema_uri(), col.stac_extensions)

        StorageExtension.remove_from(col)
        self.assertNotIn(StorageExtension.get_schema_uri(), col.stac_extensions)


class AssetStorageExtensionTest(StorageExtensionTest):
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

        self.assertEqual(storage_ext.platform, new_platform)
        self.assertEqual(storage_ext.region, new_region)
        self.assertEqual(storage_ext.requester_pays, new_requestor_pays)
        self.assertEqual(storage_ext.tier, new_tier)

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
        self.assertEqual(
            storage_ext.platform, asset.extra_fields.get("storage:platform")
        )

        # Set
        new_platform = random.choice(
            [val for val in CloudPlatform if val != storage_ext.platform]
        )
        storage_ext.platform = new_platform
        self.assertEqual(storage_ext.platform, new_platform)

        item.validate()

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
        self.assertEqual(storage_ext.region, asset.extra_fields.get("storage:region"))

        # Set
        new_region = random.choice(
            [val for val in CloudPlatform if val != storage_ext.region]
        )
        storage_ext.region = new_region
        self.assertEqual(storage_ext.region, new_region)

        item.validate()

        # Set to None
        storage_ext.region = None
        self.assertNotIn("storage:region", asset.extra_fields)

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
        self.assertEqual(
            storage_ext.requester_pays, asset.extra_fields.get("storage:requester_pays")
        )

        # Set
        new_requester_pays = True if not storage_ext.requester_pays else False
        storage_ext.requester_pays = new_requester_pays
        self.assertEqual(storage_ext.requester_pays, new_requester_pays)

        item.validate()

        # Set to None
        storage_ext.requester_pays = None
        self.assertNotIn("storage:requester_pays", asset.extra_fields)

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
        self.assertEqual(storage_ext.tier, asset.extra_fields.get("storage:tier"))

        # Set
        new_tier = random.choice(ascii_letters)
        storage_ext.tier = new_tier
        self.assertEqual(storage_ext.tier, new_tier)

        item.validate()

        # Set to None
        storage_ext.tier = None
        self.assertNotIn("storage:tier", asset.extra_fields)
