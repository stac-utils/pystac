"""Implements the Alternate Assets Extension.

https://github.com/stac-extensions/alternate-assets
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal

import pystac
from pystac.asset import Assets
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension

SCHEMA_URI = "https://stac-extensions.github.io/alternate-assets/v1.2.0/schema.json"


class _AssetLoc:
    def __init__(self, ext: AlternateAssetsExtension):
        self._ext = ext

    def __contains__(self, key: str) -> bool:
        return self._ext.has_asset(key)

    def __getitem__(self, key: str) -> pystac.Asset:
        return self._ext.get_asset(key)


def _remove_alternate(mapping: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in mapping.items() if key != "alternate"}


def _deserialize_asset_with_owner(
    mapping: dict[str, Any], owner: Assets | None
) -> pystac.Asset:
    asset = pystac.Asset.from_dict(mapping)
    asset.owner = owner

    return asset


class AlternateAssetsExtension(
    PropertiesExtension, ExtensionManagementMixin[pystac.Asset]
):
    name: ClassVar[Literal["alternate"]] = "alternate"

    asset: pystac.Asset
    properties: dict[str, Any]

    def __init__(self, asset: pystac.Asset):
        self.asset = asset
        self.properties = asset.extra_fields

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(
        cls, obj: pystac.Asset, add_if_missing: bool = False
    ) -> AlternateAssetsExtension:
        if isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cls(obj)

        raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @property
    def assets(self) -> _AssetLoc:
        return _AssetLoc(self)

    @property
    def alternate_name(self) -> str | None:
        return self.asset.extra_fields.get("alternate:name")

    def has_asset(self, key: str | None) -> bool:
        if key is None:
            return self.asset.href is not None

        return key in self.properties.get("alternate", {})

    def get_asset(self, key: str | None) -> pystac.Asset:
        if key is None:
            serialized_asset = _remove_alternate(self.asset.to_dict())

            return _deserialize_asset_with_owner(serialized_asset, self.asset.owner)

        assets = self.properties.get("alternate")
        if assets is None:
            raise ValueError("no alternate assets defined")

        alternate_asset = assets.get(key)
        if alternate_asset is None:
            raise ValueError(f"unknown alternate asset: {key}")

        serialized_asset = _remove_alternate(self.asset.to_dict() | alternate_asset)

        return _deserialize_asset_with_owner(serialized_asset, self.asset.owner)
