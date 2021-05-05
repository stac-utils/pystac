"""Implements the Satellite extension.

https://github.com/stac-extensions/sat
"""

import enum
from typing import Generic, Optional, Set, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import map_opt

T = TypeVar("T", pystac.Item, pystac.Asset)

SCHEMA_URI = "https://stac-extensions.github.io/sat/v1.0.0/schema.json"

ORBIT_STATE: str = "sat:orbit_state"
RELATIVE_ORBIT: str = "sat:relative_orbit"


class OrbitState(enum.Enum):
    ASCENDING = "ascending"
    DESCENDING = "descending"
    GEOSTATIONARY = "geostationary"


class SatExtension(
    Generic[T], PropertiesExtension, ExtensionManagementMixin[pystac.Item]
):
    """SatItemExt extends Item to add sat properties to a STAC Item.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The item that is being extended.

    Note:
        Using SatItemExt to directly wrap an item will add the 'sat'
        extension ID to the item's stac_extensions.
    """

    def apply(
        self,
        orbit_state: Optional[OrbitState] = None,
        relative_orbit: Optional[int] = None,
    ) -> None:
        """Applies ext extension properties to the extended Item.

        Must specify at least one of orbit_state or relative_orbit in order
        for the sat extension to properties to be valid.

        Args:
            orbit_state (OrbitState): Optional state of the orbit. Either ascending or
                descending for polar orbiting satellites, or geostationary for
                geosynchronous satellites.
            relative_orbit (int): Optional non-negative integer of the orbit number at
                the time of acquisition.
        """

        self.orbit_state = orbit_state
        self.relative_orbit = relative_orbit

    @property
    def orbit_state(self) -> Optional[OrbitState]:
        """Get or sets an orbit state of the item.

        Returns:
            OrbitState or None
        """
        return map_opt(lambda x: OrbitState(x), self._get_property(ORBIT_STATE, str))

    @orbit_state.setter
    def orbit_state(self, v: Optional[OrbitState]) -> None:
        self._set_property(ORBIT_STATE, map_opt(lambda x: x.value, v))

    @property
    def relative_orbit(self) -> Optional[int]:
        """Get or sets a relative orbit number of the item.

        Returns:
            int or None
        """
        return self._get_property(RELATIVE_ORBIT, int)

    @relative_orbit.setter
    def relative_orbit(self, v: Optional[int]) -> None:
        self._set_property(RELATIVE_ORBIT, v)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @staticmethod
    def ext(obj: T) -> "SatExtension[T]":
        if isinstance(obj, pystac.Item):
            return cast(SatExtension[T], ItemSatExtension(obj))
        elif isinstance(obj, pystac.Asset):
            return cast(SatExtension[T], AssetSatExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"File extension does not apply to type {type(obj)}"
            )


class ItemSatExtension(SatExtension[pystac.Item]):
    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemSatExtension Item id={}>".format(self.item.id)


class AssetSatExtension(SatExtension[pystac.Asset]):
    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.properties
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return "<AssetSatExtension Asset href={}>".format(self.asset_href)


class SatExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: Set[str] = set(["sat"])
    stac_object_types: Set[pystac.STACObjectType] = set([pystac.STACObjectType.ITEM])


SAT_EXTENSION_HOOKS = SatExtensionHooks()
