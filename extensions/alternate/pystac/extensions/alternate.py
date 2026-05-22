"""Implements the Alternate Assets Extension.

https://github.com/stac-extensions/alternate-assets
"""

from __future__ import annotations

from typing import Any, ClassVar, Literal

import pystac
from pystac.extensions.base import PropertiesExtension

SCHEMA_URI = "https://stac-extensions.github.io/alternate-assets/v1.2.0/schema.json"


class AssetAlternateAssetsExtension(
    PropertiesExtension
):
    name: ClassVar[Literal["alternate-assets"]] = "alternate-assets"

    asset: pystac.Asset
    alternate_assets: dict[str, Any]

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

    def __init__(self, obj: pystac.Asset):
        self.asset = obj
        self.alternate_assets = obj.extra_fields.get("alternate", {})

    @property
    def alternate_name(self) -> str | None:
        return self.asset.extra_fields.get("alternate:name")

    def get_asset(self, name: str) -> pystac.Asset:
        if name == self.alternate_name:
            return self.asset

        alternate_asset = self.alternate_assets.get(name)
        if alternate_asset is None:
            raise ValueError(f"unknown alternate asset: {name}")

        asset = pystac.Asset.from_dict(self.asset.to_dict() | alternate_asset)
        asset.owner = self.asset.owner

        return asset

class ItemAlternateAssetsExtension(
