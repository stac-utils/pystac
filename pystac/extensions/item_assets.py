"""Implements the :stac-ext:`Item Assets Definition Extension <item-assets>`."""

from __future__ import annotations

import warnings
from typing import Any, Literal

import pystac
from pystac.errors import DeprecatedWarning
from pystac.extensions.base import ExtensionManagementMixin
from pystac.extensions.hooks import ExtensionHooks
from pystac.item_assets import ItemAssetDefinition
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.utils import get_required

SCHEMA_URI = "https://stac-extensions.github.io/item-assets/v1.0.0/schema.json"

ITEM_ASSETS_PROP = "item_assets"


class AssetDefinition(ItemAssetDefinition):
    """
    DEPRECATED

    .. deprecated:: 1.12.0
        Use :class:`~pystac.ItemAssetDefinition` instead.
    """

    def __init__(cls, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            (
                "``AssetDefinition`` is deprecated. "
                "Please use ``pystac.ItemAssetDefinition`` instead."
            ),
            DeprecationWarning,
        )
        super().__init__(*args, **kwargs)


class ItemAssetsExtension(ExtensionManagementMixin[pystac.Collection]):
    """
    DEPRECATED

    .. deprecated:: 1.12.0
        Use :attr:`~pystac.Collection.item_assets` instead.
    """

    name: Literal["item_assets"] = "item_assets"
    collection: pystac.Collection

    def __init__(self, collection: pystac.Collection) -> None:
        warnings.warn(
            (
                "The ``item_assets`` extension is deprecated. "
                "``item_assets`` is now a top-level property of ``Collection``."
            ),
            DeprecatedWarning,
        )
        self.collection = collection

    @property
    def item_assets(self) -> dict[str, ItemAssetDefinition]:
        """Gets or sets a dictionary of assets that can be found in member Items. Maps
        the asset key to an :class:`AssetDefinition` instance."""
        result: dict[str, Any] = get_required(
            self.collection.extra_fields.get(ITEM_ASSETS_PROP), self, ITEM_ASSETS_PROP
        )
        return {k: ItemAssetDefinition(v, self.collection) for k, v in result.items()}

    @item_assets.setter
    def item_assets(self, v: dict[str, ItemAssetDefinition]) -> None:
        self.collection.extra_fields[ITEM_ASSETS_PROP] = {
            k: asset_def.properties for k, asset_def in v.items()
        }

    def __repr__(self) -> str:
        return f"<ItemAssetsExtension collection.id = {self.collection.id}>"

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> ItemAssetsExtension:
        """Extends the given :class:`~pystac.Collection` with properties from the
        :stac-ext:`Item Assets Extension <item-assets>`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return cls(obj)
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))


class ItemAssetsExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"asset", "item-assets"}
    stac_object_types = {pystac.STACObjectType.COLLECTION}

    def migrate(
        self, obj: dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        # Handle that the "item-assets" extension had the id of "assets", before
        # collection assets (since removed) took over the ID of "assets"
        if version < "1.0.0-beta.1" and "asset" in info.extensions:
            if "assets" in obj:
                obj["item_assets"] = obj["assets"]
                del obj["assets"]

        super().migrate(obj, version, info)

        # As of STAC spec version 1.1.0 item-assets are part of core
        if obj["stac_version"] >= "1.1.0" and self.schema_uri in obj.get(
            "stac_extensions", []
        ):
            obj["stac_extensions"].remove(self.schema_uri)


ITEM_ASSETS_EXTENSION_HOOKS: ExtensionHooks = ItemAssetsExtensionHooks()
