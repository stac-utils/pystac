"""Implement the View Geometry extension.

https://github.com/stac-extensions/view
"""

from typing import Generic, Optional, Set, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
)
from pystac.extensions.hooks import ExtensionHooks

T = TypeVar("T", pystac.Item, pystac.Asset)

SCHEMA_URI = "https://stac-extensions.github.io/view/v1.0.0/schema.json"

OFF_NADIR_PROP = "view:off_nadir"
INCIDENCE_ANGLE_PROP = "view:incidence_angle"
AZIMUTH_PROP = "view:azimuth"
SUN_AZIMUTH_PROP = "view:sun_azimuth"
SUN_ELEVATION_PROP = "view:sun_elevation"


class ViewExtension(
    Generic[T], PropertiesExtension, ExtensionManagementMixin[pystac.Item]
):
    """ViewItemExt is the extension of the Item in the View Geometry Extension.

    View Geometry adds metadata related to angles of sensors and other radiance angles
    that affect the view of resulting data. It will often be combined with other
    extensions that describe the actual data, such as the eo, sat or sar extensions.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The Item that is being extended.

    Note:
        Using ViewItemExt to directly wrap an item will add the 'view' extension ID to
        the item's stac_extensions.
    """

    def apply(
        self,
        off_nadir: Optional[float] = None,
        incidence_angle: Optional[float] = None,
        azimuth: Optional[float] = None,
        sun_azimuth: Optional[float] = None,
        sun_elevation: Optional[float] = None,
    ) -> None:
        """Applies View Geometry extension properties to the extended Item.

        Args:
            off_nadir (float): The angle from the sensor between nadir (straight down)
                and the scene center. Measured in degrees (0-90).
            incidence_angle (float): The incidence angle is the angle between the
                vertical (normal) to the intercepting surface and the line of sight
                back to the satellite at the scene center. Measured in degrees (0-90).
            azimuth (float): Viewing azimuth angle. The angle measured from the
                sub-satellite point (point on the ground below the platform) between
                the scene center and true north. Measured clockwise from north in
                degrees (0-360).
            sun_azimuth (float): Sun azimuth angle. From the scene center point on the
                ground, this is the angle between truth north and the sun. Measured
                clockwise in degrees (0-360).
            sun_elevation (float): Sun elevation angle. The angle from the tangent of
                the scene center point to the sun. Measured from the horizon in
                degrees (0-90).
        """
        self.off_nadir = off_nadir
        self.incidence_angle = incidence_angle
        self.azimuth = azimuth
        self.sun_azimuth = sun_azimuth
        self.sun_elevation = sun_elevation

    @property
    def off_nadir(self) -> Optional[float]:
        """Get or sets the angle from the sensor between nadir (straight down)
        and the scene center. Measured in degrees (0-90).

        Returns:
            float
        """
        return self._get_property(OFF_NADIR_PROP, float)

    @off_nadir.setter
    def off_nadir(self, v: Optional[float]) -> None:
        self._set_property(OFF_NADIR_PROP, v)

    @property
    def incidence_angle(self) -> Optional[float]:
        """Get or sets the incidence angle is the angle between the vertical (normal)
        to the intercepting surface and the line of sight back to the satellite at
        the scene center. Measured in degrees (0-90).

        Returns:
            float
        """
        return self._get_property(INCIDENCE_ANGLE_PROP, float)

    @incidence_angle.setter
    def incidence_angle(self, v: Optional[float]) -> None:
        self._set_property(INCIDENCE_ANGLE_PROP, v)

    @property
    def azimuth(self) -> Optional[float]:
        """Get or sets the viewing azimuth angle.

        The angle measured from the sub-satellite
        point (point on the ground below the platform) between the scene center and true
        north. Measured clockwise from north in degrees (0-360).

        Returns:
            float
        """
        return self._get_property(AZIMUTH_PROP, float)

    @azimuth.setter
    def azimuth(self, v: Optional[float]) -> None:
        self._set_property(AZIMUTH_PROP, v)

    @property
    def sun_azimuth(self) -> Optional[float]:
        """Get or sets the sun azimuth angle.

        From the scene center point on the ground, this
        is the angle between truth north and the sun. Measured clockwise in
        degrees (0-360).

        Returns:
            float
        """
        return self._get_property(SUN_AZIMUTH_PROP, float)

    @sun_azimuth.setter
    def sun_azimuth(self, v: Optional[float]) -> None:
        self._set_property(SUN_AZIMUTH_PROP, v)

    @property
    def sun_elevation(self) -> Optional[float]:
        """Get or sets the sun elevation angle. The angle from the tangent of the scene
        center point to the sun. Measured from the horizon in degrees (0-90).

        Returns:
            float
        """
        return self._get_property(SUN_ELEVATION_PROP, float)

    @sun_elevation.setter
    def sun_elevation(self, v: Optional[float]) -> None:
        self._set_property(SUN_ELEVATION_PROP, v)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @staticmethod
    def ext(obj: T) -> "ViewExtension[T]":
        if isinstance(obj, pystac.Item):
            return cast(ViewExtension[T], ItemViewExtension(obj))
        elif isinstance(obj, pystac.Asset):
            return cast(ViewExtension[T], AssetViewExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"View extension does not apply to type {type(obj)}"
            )


class ItemViewExtension(ViewExtension[pystac.Item]):
    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemViewExtension Item id={}>".format(self.item.id)


class AssetViewExtension(ViewExtension[pystac.Asset]):
    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.properties
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return "<AssetViewExtension Asset href={}>".format(self.asset_href)


class ViewExtensionHooks(ExtensionHooks):
    schema_uri = SCHEMA_URI
    prev_extension_ids: Set[str] = set(["view"])
    stac_object_types: Set[pystac.STACObjectType] = set([pystac.STACObjectType.ITEM])


VIEW_EXTENSION_HOOKS = ViewExtensionHooks()
