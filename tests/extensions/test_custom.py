"""Tests creating a custom extension"""
from typing import Any, Dict, Generic, List, Optional, Set, TypeVar, Union, cast
import unittest

from pystac import EXTENSION_HOOKS
from pystac.link import Link
from pystac.asset import Asset
from pystac.summaries import RangeSummary
from pystac.stac_object import STACObject, STACObjectType
from pystac.collection import Collection
from pystac.errors import ExtensionAlreadyExistsError, ExtensionTypeError
from pystac.item import Item
from pystac.catalog import Catalog
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks

T = TypeVar("T", Catalog, Collection, Item, Asset)

SCHEMA_URI = "https://example.com/v2.0/custom-schema.json"

TEST_PROP = "test:prop"
TEST_LINK_REL = "test-link"


class CustomExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[Catalog, Collection, Item]],
):
    def __init__(self, obj: Optional[STACObject]) -> None:
        self.obj = obj

    def apply(self, test_prop: Optional[str]) -> None:
        self.test_prop = test_prop

    @property
    def test_prop(self) -> Optional[str]:
        return self._get_property(TEST_PROP, str)

    @test_prop.setter
    def test_prop(self, v: Optional[str]) -> None:
        self._set_property(TEST_PROP, v)

    def add_link(self, target: STACObject) -> None:
        if self.obj is not None:
            self.obj.add_link(Link(TEST_LINK_REL, target))
        else:
            raise ExtensionAlreadyExistsError(f"{self} does not support links")

    @classmethod
    def get_schema_uri(cls) -> str:
        return super().get_schema_uri()

    @staticmethod
    def custom_ext(obj: T) -> "CustomExtension[T]":
        if isinstance(obj, Asset):
            return cast(CustomExtension[T], AssetCustomExtension(obj))
        if isinstance(obj, Item):
            return cast(CustomExtension[T], ItemCustomExtension(obj))
        if isinstance(obj, Collection):
            return cast(CustomExtension[T], CollectionCustomExtension(obj))
        if isinstance(obj, Catalog):
            return cast(CustomExtension[T], CatalogCustomExtension(obj))

        raise ExtensionTypeError(
            f"Custom extension does not apply to {type(obj).__name__}"
        )

    @staticmethod
    def summaries(obj: Collection) -> "SummariesCustomExtension":
        return SummariesCustomExtension(obj)


class CatalogCustomExtension(CustomExtension[Catalog]):
    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog
        self.properties = catalog.extra_fields
        super().__init__(catalog)


class CollectionCustomExtension(CustomExtension[Collection]):
    def __init__(self, collection: Collection) -> None:
        self.catalog = collection
        self.properties = collection.extra_fields
        super().__init__(collection)


class ItemCustomExtension(CustomExtension[Item]):
    def __init__(self, item: Item) -> None:
        self.catalog = item
        self.properties = item.properties
        super().__init__(item)


class AssetCustomExtension(CustomExtension[Asset]):
    def __init__(self, asset: Asset) -> None:
        self.catalog = asset
        self.properties = asset.extra_fields
        if asset.owner:
            if isinstance(asset.owner, Item):
                self.additional_read_properties = [asset.owner.properties]
            elif isinstance(asset.owner, Collection):
                self.additional_read_properties = [asset.owner.extra_fields]
        super().__init__(None)


class SummariesCustomExtension(SummariesExtension):
    @property
    def test_prop(self) -> Optional[RangeSummary[str]]:
        return self.summaries.get_range(TEST_PROP)

    @test_prop.setter
    def test_prop(self, v: Optional[RangeSummary[str]]) -> None:
        self._set_summary(TEST_PROP, v)


class CustomExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: Set[str] = set(
        ["custom", "https://example.com/v1.0/custom-schema.json"]
    )
    stac_object_types: Set[STACObjectType] = set(
        [
            STACObjectType.CATALOG,
            STACObjectType.COLLECTION,
            STACObjectType.ITEM,
        ]
    )

    def get_object_links(self, obj: STACObject) -> Optional[List[str]]:
        return [TEST_LINK_REL]

    def migrate(
        self, obj: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        if version < "1.0.0-rc2" and info.object_type == STACObjectType.ITEM:
            if "test:old-prop-name" in obj["properties"]:
                obj["properties"][TEST_PROP] = obj["properties"]["test:old-prop-name"]
        super().migrate(obj, version, info)


class CustomExtensionTest(unittest.TestCase):
    def setUp(self) -> None:
        EXTENSION_HOOKS.add_extension_hooks(CustomExtensionHooks())

    def tearDown(self) -> None:
        EXTENSION_HOOKS.remove_extension_hooks(SCHEMA_URI)

    # TODO: Test custom extensions and extension hooks

    def test_migrates(self) -> None:
        pass
