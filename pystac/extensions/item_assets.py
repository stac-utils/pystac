"""Implements the Item Assets Definition extension.

https://github.com/stac-extensions/item-assets
"""

from typing import Any, Dict, List, Optional, Set

import pystac
from pystac.extensions.base import ExtensionManagementMixin
from pystac.extensions.hooks import ExtensionHooks
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.utils import get_required

SCHEMA_URI = "https://stac-extensions.github.io/item-assets/v1.0.0/schema.json"

ITEM_ASSETS_PROP = "item_assets"

ASSET_TITLE_PROP = "title"
ASSET_DESC_PROP = "description"
ASSET_TYPE_PROP = "type"
ASSET_ROLES_PROP = "roles"


class AssetDefinition:
    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    @property
    def title(self) -> Optional[str]:
        self.properties.get(ASSET_TITLE_PROP)

    @title.setter
    def title(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(ASSET_TITLE_PROP, None)
        else:
            self.properties[ASSET_TITLE_PROP] = v

    @property
    def description(self) -> Optional[str]:
        self.properties.get(ASSET_DESC_PROP)

    @description.setter
    def description(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(ASSET_DESC_PROP, None)
        else:
            self.properties[ASSET_DESC_PROP] = v

    @property
    def media_type(self) -> Optional[str]:
        self.properties.get(ASSET_TYPE_PROP)

    @media_type.setter
    def media_type(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(ASSET_TYPE_PROP, None)
        else:
            self.properties[ASSET_TYPE_PROP] = v

    @property
    def roles(self) -> Optional[List[str]]:
        self.properties.get(ASSET_ROLES_PROP)

    @roles.setter
    def roles(self, v: Optional[List[str]]) -> None:
        if v is None:
            self.properties.pop(ASSET_ROLES_PROP, None)
        else:
            self.properties[ASSET_ROLES_PROP] = v

    def create_asset(self, href: str) -> pystac.Asset:
        return pystac.Asset(
            href=href,
            title=self.title,
            description=self.description,
            media_type=self.media_type,
            roles=self.roles,
            properties={
                k: v
                for k, v in self.properties
                if k
                not in set(
                    [
                        ASSET_TITLE_PROP,
                        ASSET_DESC_PROP,
                        ASSET_TYPE_PROP,
                        ASSET_ROLES_PROP,
                    ]
                )
            },
        )


class ItemAssetsExtension(ExtensionManagementMixin[pystac.Collection]):
    def __init__(self, collection: pystac.Collection) -> None:
        self.collection = collection

    @property
    def item_assets(self) -> Dict[str, AssetDefinition]:
        result = get_required(
            self.collection.extra_fields.get(ITEM_ASSETS_PROP), self, ITEM_ASSETS_PROP
        )
        return {k: AssetDefinition(v) for k, v in result.items()}

    @item_assets.setter
    def item_assets(self, v: Dict[str, AssetDefinition]) -> None:
        self.collection.extra_fields[ITEM_ASSETS_PROP] = {
            k: asset_def.properties for k, asset_def in v.items()
        }

    def __repr__(self) -> str:
        return f"<ItemAssetsExtension collection.id = {self.collection.id}>"

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, collection: pystac.Collection) -> "ItemAssetsExtension":
        return cls(collection)


class ItemAssetsExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: Set[str] = set(["asset", "item-assets"])
    stac_object_types: Set[pystac.STACObjectType] = set(
        [pystac.STACObjectType.COLLECTION]
    )

    def migrate(
        self, obj: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        # Handle that the "item-assets" extension had the id of "assets", before
        # collection assets (since removed) took over the ID of "assets"
        if version < "1.0.0-beta.1" and "asset" in info.extensions:
            if "assets" in obj:
                obj["item_assets"] = obj["assets"]
                del obj["assets"]

        super().migrate(obj, version, info)


ITEM_ASSETS_EXTENSION_HOOKS = ItemAssetsExtensionHooks()
