"""Implement the Satellite (SAT) Extension.

https://github.com/radiantearth/stac-spec/tree/dev/extensions/sat
"""

import enum
from typing import List, Optional

import pystac
from pystac import Extensions
from pystac import item
from pystac.extensions import base

ORBIT_STATE: str = 'sat:orbit_state'
RELATIVE_ORBIT: str = 'sat:relative_orbit'


class OrbitState(enum.Enum):
    ASCENDING: str = 'ascending'
    DESCENDING: str = 'descending'
    GEOSTATIONARY: str = 'geostationary'


class SatItemExt(base.ItemExtension):
    """SatItemExt extends Item to add sat properties to a STAC Item.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The item that is being extended.

    Note:
        Using SatItemExt to directly wrap an item will add the 'sat'
        extension ID to the item's stac_extensions.
    """
    item: pystac.Item

    def __init__(self, an_item: item.Item) -> None:
        self.item = an_item

    def apply(self, orbit_state: Optional[OrbitState] = None, relative_orbit: Optional[str] = None):
        """Applies ext extension properties to the extended Item.

        Must specify at least one of orbit_state or relative_orbit.

        Args:
            orbit_state (OrbitState): Optional state of the orbit. Either ascending or descending
                for polar orbiting satellites, or geostationary for geosynchronous satellites.
            relative_orbit (int): Optional non-negative integer of the orbit number at the time
                of acquisition.
        """
        if orbit_state is None and relative_orbit is None:
            raise pystac.STACError('Must provide at least one of: orbit_state or relative_orbit')
        if orbit_state:
            self.orbit_state = orbit_state
        if relative_orbit:
            self.relative_orbit = relative_orbit

    @classmethod
    def from_item(cls, an_item: item.Item):
        return cls(an_item)

    @classmethod
    def _object_links(cls) -> List:
        return []

    @property
    def orbit_state(self) -> Optional[OrbitState]:
        """Get or sets an orbit state of the item.

        Returns:
            OrbitState or None
        """
        if ORBIT_STATE not in self.item.properties:
            return
        return OrbitState(self.item.properties.get(ORBIT_STATE))

    @orbit_state.setter
    def orbit_state(self, v: Optional[OrbitState]) -> None:
        if v is None:
            if self.relative_orbit is None:
                raise pystac.STACError('Must set relative_orbit before clearing orbit_state')
            if ORBIT_STATE in self.item.properties:
                del self.item.properties[ORBIT_STATE]
        else:
            self.item.properties[ORBIT_STATE] = v.value

    @property
    def relative_orbit(self) -> int:
        """Get or sets a relative orbit number of the item.

        Returns:
            int or None
        """
        return self.item.properties.get(RELATIVE_ORBIT)

    @relative_orbit.setter
    def relative_orbit(self, v: int) -> None:
        if v is None and self.orbit_state is None:
            raise pystac.STACError('Must set orbit_state before clearing relative_orbit')
        if v is None:
            if RELATIVE_ORBIT in self.item.properties:
                del self.item.properties[RELATIVE_ORBIT]
            return
        if v < 0:
            raise pystac.STACError(f'relative_orbit must be >= 0.  Found {v}.')

        self.item.properties[RELATIVE_ORBIT] = v


SAT_EXTENSION_DEFINITION = base.ExtensionDefinition(Extensions.SAT, [
    base.ExtendedObject(pystac.Item, SatItemExt),
])
