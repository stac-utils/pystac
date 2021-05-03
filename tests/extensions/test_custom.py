"""Tests creating a custom extension"""

from pystac.collection import RangeSummary
from typing import Any, Dict, Generic, List, Optional, Set, TypeVar, Union, cast
import unittest

import pystac
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks

T = TypeVar("T", pystac.Catalog, pystac.Collection, pystac.Item, pystac.Asset)

SCHEMA_URI = "https://example.com/v2.0/custom-schema.json"

TEST_PROP = "test:prop"
TEST_LINK_REL = "test-link"


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
        self._get_property(TEST_PROP, str)

    @test_prop.setter
    def test_prop(self, v: Optional[str]) -> None:
        self._set_property(TEST_PROP, v)

    def add_link(self, target: pystac.STACObject) -> None:
        if self.obj is not None:
            self.obj.add_link(pystac.Link(TEST_LINK_REL, target))
        else:
            raise pystac.ExtensionAlreadyExistsError(f"{self} does not support links")

    @classmethod
    def get_schema_uri(cls) -> str:
        return super().get_schema_uri()

    @staticmethod
    def custom_ext(obj: T) -> "CustomExtension[T]":
        if isinstance(obj, pystac.Asset):
            return cast(CustomExtension[T], AssetCustomExtension(obj))
        if isinstance(obj, pystac.Item):
            return cast(CustomExtension[T], ItemCustomExtension(obj))
        if isinstance(obj, pystac.Collection):
            return cast(CustomExtension[T], CollectionCustomExtension(obj))
        if isinstance(obj, pystac.Catalog):
            return cast(CustomExtension[T], CatalogCustomExtension(obj))

        raise pystac.ExtensionTypeError(
            f"Custom extension does not apply to {type(obj)}"
        )

    @staticmethod
    def summaries(obj: pystac.Collection) -> "SummariesCustomExtension":
        return SummariesCustomExtension(obj)


class CatalogCustomExtension(CustomExtension[pystac.Catalog]):
    def __init__(self, catalog: pystac.Catalog) -> None:
        self.catalog = catalog
        self.properties = catalog.extra_fields
        super().__init__(catalog)


class CollectionCustomExtension(CustomExtension[pystac.Collection]):
    def __init__(self, collection: pystac.Collection) -> None:
        self.catalog = collection
        self.properties = collection.extra_fields
        super().__init__(collection)


class ItemCustomExtension(CustomExtension[pystac.Item]):
    def __init__(self, item: pystac.Item) -> None:
        self.catalog = item
        self.properties = item.properties
        super().__init__(item)


class AssetCustomExtension(CustomExtension[pystac.Asset]):
    def __init__(self, asset: pystac.Asset) -> None:
        self.catalog = asset
        self.properties = asset.properties
        if asset.owner:
            if isinstance(asset.owner, pystac.Item):
                self.additional_read_properties = [asset.owner.properties]
            elif isinstance(asset.owner, pystac.Collection):
                self.additional_read_properties = [asset.owner.extra_fields]
        super().__init__(None)


class SummariesCustomExtension(SummariesExtension):
    @property
    def test_prop(self) -> Optional[RangeSummary[str]]:
        return self.summaries.get_range(TEST_PROP, str)

    @test_prop.setter
    def test_prop(self, v: Optional[RangeSummary[str]]) -> None:
        self._set_summary(TEST_PROP, v)


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

    def get_object_links(self, obj: pystac.STACObject) -> Optional[List[str]]:
        return [TEST_LINK_REL]

    def migrate(
        self, obj: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        if version < "1.0.0-rc2" and info.object_type == pystac.STACObjectType.ITEM:
            if "test:old-prop-name" in obj["properties"]:
                obj["properties"][TEST_PROP] = obj["properties"]["test:old-prop-name"]
        super().migrate(obj, version, info)


class CustomExtensionTest(unittest.TestCase):
    def setUp(self):
        pystac.EXTENSION_HOOKS.add_extension_hooks(CustomExtensionHooks())

    def tearDown(self) -> None:
        pystac.EXTENSION_HOOKS.remove_extension_hooks(SCHEMA_URI)

    # TODO: Test custom extensions and extension hooks

    def test_migrates(self):
        pass
