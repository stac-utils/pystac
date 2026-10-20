"""Implements the Alternate Assets Extension.

https://github.com/stac-extensions/alternate-assets
"""

from __future__ import annotations

from typing import Any, ClassVar, Literal, TypeVar, cast

import pystac
from pystac import Collection, Item
from pystac.asset import Assets
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension

SCHEMA_URI = "https://stac-extensions.github.io/alternate-assets/v1.2.0/schema.json"

PREFIX: str = "alternate:"

ALTERNATE_PROP: str = "alternate"
NAME_PROP: str = PREFIX + "name"


T = TypeVar("T")


def _remove_alternate(mapping: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in mapping.items() if key != ALTERNATE_PROP}


def deduplicate(mapping: dict[str, Any], against: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in mapping.items()
        if key in {"href", "alternate:name"} or against.get(key) != value
    }


class AlternateAsset:
    properties: dict[str, Any]

    owner: Assets | None
    asset_name: str
    alternate: str | None

    def __init__(
        self,
        properties: dict[str, Any],
        owner: Assets | None,
        asset_name: str,
        alternate: str | None,
    ):
        self.properties = properties

        self.owner = owner
        self.asset_name = asset_name
        self.alternate = alternate

    def _get_property(self, property: str, typ: type[T]) -> T | None:
        return self.properties.get(property)

    def _set_property(
        self, property: str, new: T | None, pop_if_none: bool = True
    ) -> None:
        if new is None:
            self.properties.pop(property, None)
        else:
            self.properties[property] = new

    @property
    def name(self) -> str | None:
        return self._get_property(NAME_PROP, str)

    @name.setter
    def name(self, new: str | None) -> None:
        self._set_property(NAME_PROP, new, pop_if_none=True)

    @property
    def parent(self) -> pystac.Asset:
        if self.owner is None:
            raise ValueError("unknown owner")

        return self.owner.assets[self.asset_name]

    @property
    def href(self) -> str:
        href = self._get_property("href", str)
        if href is None:
            raise ValueError("invalid href found, must not be None")
        return href

    @href.setter
    def href(self, new: str) -> None:
        if new is None:
            raise ValueError("invalid href, cannot be None")
        self._set_property("href", new)

    def to_dict(self) -> dict[str, Any]:
        merged = self.parent.to_dict() | self.properties
        merged.pop("alternate", None)

        return merged

    def to_asset(self) -> pystac.Asset:
        asset = pystac.Asset.from_dict(self.to_dict())
        # to_dict raises if self.owner is None
        asset.set_owner(cast(Assets, self.owner))

        return asset

    def __repr__(self) -> str:
        return f"<AlternateAsset asset={self.asset_name}, alternate={self.alternate}>"


class _AssetLoc:
    def __init__(self, ext: AlternateAssetsExtension):
        self._ext = ext

    def __contains__(self, key: str) -> bool:
        return self._ext.has_asset(key)

    def __getitem__(self, key: str) -> AlternateAsset:
        return self._ext.get_asset(key)

    def __setitem__(self, key: str, asset: AlternateAsset) -> None:
        self._ext.set_asset(key, asset)


class AlternateAssetsExtension(
    PropertiesExtension, ExtensionManagementMixin[Collection | Item]
):
    """A class that can be used to extend the properties of an :class:`pystac.Asset`
    with properties from the :stac-ext:`Alternate Assets Extension <alternate-assets>`.
    To create a concrete instance of :class:`AlternateAssetsExtension`, use the
    :meth:`AlternateAssetsExtension.ext` method. For example:

    .. code-block:: python

       >>> asset: pystac.Asset = ...
       >>> alternate_ext = AlternateAssetsExtension.ext(asset)
    """

    name: ClassVar[Literal["alternate"]] = "alternate"

    asset: pystac.Asset
    """The :class:`~pystac.Asset` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Asset` properties, including extension properties."""

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
        """Extends the given STAC Object with properties from the :stac-ext:`Alternate
        Assets Extension <alternate-assets>`.

        This extension can be applied to instances of :class:`~pystac.Asset`.

        Raises:
            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cls(obj)

        raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @property
    def assets(self) -> _AssetLoc:
        """Access alternate assets through a getitem syntax.

        Similar to :meth:`AlternateAssetsExtension.get_asset`
        and :meth:`AlternateAssetsExtension.has_asset`.
        """

        return _AssetLoc(self)

    @property
    def asset_name(self) -> str:
        """Name of the current asset."""
        assets = getattr(self.asset.owner, "assets", {})
        matches: list[str] = [
            key for key, value in assets.items() if value == self.asset
        ]

        if len(matches) != 1:
            raise RuntimeError(
                "inconsistent state, can't find the asset on the owner,"
                " or more than one asset found"
            )
        return matches[0]

    def has_asset(self, key: str | None) -> bool:
        """Check if the given alternate asset key exists."""
        if key is None:
            return self.asset.href is not None

        return key in self.properties.get(ALTERNATE_PROP, {})

    def get_asset(self, key: str | None) -> AlternateAsset:
        """Get a alternate asset from the asset."""
        if key is None:
            return AlternateAsset(
                _remove_alternate(self.asset.extra_fields),
                self.asset.owner,
                self.asset_name,
                key,
            )

        assets = self.properties.get(ALTERNATE_PROP)
        if assets is None:
            raise ValueError("no alternate assets defined")

        alternate_asset = assets.get(key)
        if alternate_asset is None:
            raise ValueError(f"unknown alternate asset: {key}")

        return AlternateAsset(alternate_asset, self.asset.owner, self.asset_name, key)

    def set_asset(self, key: str, asset: AlternateAsset) -> None:
        alternate = self.properties.setdefault(ALTERNATE_PROP, {})
        alternate[key] = deduplicate(asset.to_dict(), against=self.asset.to_dict())

    def __repr__(self) -> str:
        return f"<AlternateAssetsExtension asset={self.asset_name}>"
