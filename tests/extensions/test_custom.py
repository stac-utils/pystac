"""Tests creating a custom extension"""

import unittest
from datetime import datetime
from typing import Any, Dict, Generic, Optional, Set, TypeVar, Union, cast

import pytest

import pystac
from pystac import (
    Asset,
    Catalog,
    Collection,
    Extent,
    Item,
    SpatialExtent,
    TemporalExtent,
)
from pystac.errors import ExtensionTypeError
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension
from pystac.extensions.hooks import ExtensionHooks
from pystac.serialization.identify import STACJSONDescription, STACVersionID

T = TypeVar("T", pystac.Catalog, pystac.Collection, pystac.Item, pystac.Asset)

SCHEMA_URI = "https://example.com/v2.0/custom-schema.json"

TEST_PROP = "test:prop"


class CustomExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[pystac.Catalog, pystac.Collection, pystac.Item]],
):
    def __init__(self, obj: Optional[pystac.STACObject]) -> None:
        self.obj = obj

    def apply(self, test_prop: Optional[str]) -> None:
        self.test_prop = test_prop

    @property
    def test_prop(self) -> Optional[str]:
        return self._get_property(TEST_PROP, str)

    @test_prop.setter
    def test_prop(self, v: Optional[str]) -> None:
        self._set_property(TEST_PROP, v)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> "CustomExtension[T]":
        if isinstance(obj, pystac.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return cast(CustomExtension[T], AssetCustomExtension(obj))
        if isinstance(obj, pystac.Item):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(CustomExtension[T], ItemCustomExtension(obj))
        if isinstance(obj, pystac.Collection):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(CustomExtension[T], CollectionCustomExtension(obj))
        if isinstance(obj, pystac.Catalog):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(CustomExtension[T], CatalogCustomExtension(obj))

        raise pystac.ExtensionTypeError(
            f"Custom extension does not apply to {type(obj).__name__}"
        )


class CatalogCustomExtension(CustomExtension[pystac.Catalog]):
    def __init__(self, catalog: pystac.Catalog) -> None:
        self.properties = catalog.extra_fields
        super().__init__(catalog)


class CollectionCustomExtension(CustomExtension[pystac.Collection]):
    def __init__(self, collection: pystac.Collection) -> None:
        self.properties = collection.extra_fields
        super().__init__(collection)


class ItemCustomExtension(CustomExtension[pystac.Item]):
    def __init__(self, item: pystac.Item) -> None:
        self.properties = item.properties
        super().__init__(item)


class AssetCustomExtension(CustomExtension[pystac.Asset]):
    def __init__(self, asset: pystac.Asset) -> None:
        self.properties = asset.extra_fields
        if asset.owner:
            if isinstance(asset.owner, pystac.Item):
                self.additional_read_properties = [asset.owner.properties]
            elif isinstance(asset.owner, pystac.Collection):
                self.additional_read_properties = [asset.owner.extra_fields]
        super().__init__(None)


class CustomExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: Set[str] = set(
        ["custom", "https://example.com/v1.0/custom-schema.json"]
    )
    stac_object_types: Set[pystac.STACObjectType] = set(
        [
            pystac.STACObjectType.CATALOG,
            pystac.STACObjectType.COLLECTION,
            pystac.STACObjectType.ITEM,
        ]
    )

    def migrate(
        self, obj: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        if version < "1.0.0-rc2" and info.object_type == pystac.STACObjectType.ITEM:
            if "test:old-prop-name" in obj["properties"]:
                obj["properties"][TEST_PROP] = obj["properties"]["test:old-prop-name"]
        super().migrate(obj, version, info)


class CustomExtensionTest(unittest.TestCase):
    def setUp(self) -> None:
        pystac.EXTENSION_HOOKS.add_extension_hooks(CustomExtensionHooks())

    def tearDown(self) -> None:
        pystac.EXTENSION_HOOKS.remove_extension_hooks(SCHEMA_URI)

    def test_add_to_item_asset(self) -> None:
        item = Item("an-id", None, None, datetime.now(), {})
        item.add_asset("foo", Asset("http://pystac.test/asset.tif"))
        custom = CustomExtension.ext(item.assets["foo"], add_if_missing=True)
        assert CustomExtension.has_extension(item)
        custom.apply("bar")
        item_as_dict = item.to_dict()
        assert item_as_dict["assets"]["foo"]["test:prop"] == "bar"

    def test_add_to_item(self) -> None:
        item = Item("an-id", None, None, datetime.now(), {})
        custom = CustomExtension.ext(item, add_if_missing=True)
        assert CustomExtension.has_extension(item)
        custom.test_prop = "foo"
        item_as_dict = item.to_dict()
        assert item_as_dict["properties"]["test:prop"] == "foo"

    def test_add_to_catalog(self) -> None:
        catalog = Catalog("an-id", "a description")
        custom = CustomExtension.ext(catalog, add_if_missing=True)
        assert CustomExtension.has_extension(catalog)
        custom.test_prop = "foo"
        catalog_as_dict = catalog.to_dict()
        assert catalog_as_dict["test:prop"] == "foo"

    def test_add_to_collection(self) -> None:
        collection = Collection(
            "an-id",
            "a description",
            extent=Extent(
                spatial=SpatialExtent([-180.0, -90.0, 180.0, 90.0]),
                temporal=TemporalExtent([[datetime.now(), None]]),
            ),
        )
        custom = CustomExtension.ext(collection, add_if_missing=True)
        assert CustomExtension.has_extension(collection)
        custom.test_prop = "foo"
        collection_as_dict = collection.to_dict()
        assert collection_as_dict["test:prop"] == "foo"

    def test_add_to_collection_asset(self) -> None:
        collection = Collection(
            "an-id",
            "a description",
            extent=Extent(
                spatial=SpatialExtent([-180.0, -90.0, 180.0, 90.0]),
                temporal=TemporalExtent([[datetime.now(), None]]),
            ),
        )
        collection.add_asset("foo", Asset("http://pystac.test/asset.tif"))
        custom = CustomExtension.ext(collection.assets["foo"], add_if_missing=True)
        assert CustomExtension.has_extension(collection)
        custom.test_prop = "bar"
        collection_as_dict = collection.to_dict()
        assert collection_as_dict["assets"]["foo"]["test:prop"] == "bar"

    def test_ext_non_stac_object(self) -> None:
        with pytest.raises(ExtensionTypeError):
            CustomExtension.ext({})  # type: ignore

    def test_migrates(self) -> None:
        item = Item("an-id", None, None, datetime.now(), {})
        item_as_dict = item.to_dict()
        item_as_dict["stac_version"] = "1.0.0-rc.1"
        item_as_dict["stac_extensions"] = [
            "https://example.com/v1.0/custom-schema.json"
        ]
        item_as_dict["properties"]["test:old-prop-name"] = "foo"
        item = Item.from_dict(item_as_dict, migrate=True)
        custom = CustomExtension.ext(item)
        assert custom.test_prop == "foo"
