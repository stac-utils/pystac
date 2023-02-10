"""Implement the :stac-ext:`View Geometry Extension <view>`."""

from __future__ import annotations

from typing import Any, Dict, Generic, Iterable, Optional, TypeVar, Union, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.summaries import RangeSummary

T = TypeVar("T", pystac.Item, pystac.Asset)

SCHEMA_URI: str = "https://stac-extensions.github.io/view/v1.0.0/schema.json"
PREFIX: str = "view:"

OFF_NADIR_PROP: str = PREFIX + "off_nadir"
INCIDENCE_ANGLE_PROP: str = PREFIX + "incidence_angle"
AZIMUTH_PROP: str = PREFIX + "azimuth"
SUN_AZIMUTH_PROP: str = PREFIX + "sun_azimuth"
SUN_ELEVATION_PROP: str = PREFIX + "sun_elevation"


class ViewExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[pystac.Item, pystac.Collection]],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Item` with properties from the :stac-ext:`View Geometry
    Extension <view>`. This class is generic over the type of STAC Object to be
    extended (e.g. :class:`~pystac.Item`, :class:`~pystac.Asset`).

    To create a concrete instance of :class:`ViewExtension`, use the
    :meth:`ViewExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> view_ext = ViewExtension.ext(item)
    """

    def apply(
        self,
        off_nadir: Optional[float] = None,
        incidence_angle: Optional[float] = None,
        azimuth: Optional[float] = None,
        sun_azimuth: Optional[float] = None,
        sun_elevation: Optional[float] = None,
    ) -> None:
        """Applies View Geometry extension properties to the extended
        :class:`~pystac.Item`.

        Args:
            off_nadir : The angle from the sensor between nadir (straight down)
                and the scene center. Measured in degrees (0-90).
            incidence_angle : The incidence angle is the angle between the
                vertical (normal) to the intercepting surface and the line of sight
                back to the satellite at the scene center. Measured in degrees (0-90).
            azimuth : Viewing azimuth angle. The angle measured from the
                sub-satellite point (point on the ground below the platform) between
                the scene center and true north. Measured clockwise from north in
                degrees (0-360).
            sun_azimuth : Sun azimuth angle. From the scene center point on the
                ground, this is the angle between truth north and the sun. Measured
                clockwise in degrees (0-360).
            sun_elevation : Sun elevation angle. The angle from the tangent of
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
        """
        return self._get_property(SUN_AZIMUTH_PROP, float)

    @sun_azimuth.setter
    def sun_azimuth(self, v: Optional[float]) -> None:
        self._set_property(SUN_AZIMUTH_PROP, v)

    @property
    def sun_elevation(self) -> Optional[float]:
        """Get or sets the sun elevation angle. The angle from the tangent of the scene
        center point to the sun. Measured from the horizon in degrees (0-90).
        """
        return self._get_property(SUN_ELEVATION_PROP, float)

    @sun_elevation.setter
    def sun_elevation(self, v: Optional[float]) -> None:
        self._set_property(SUN_ELEVATION_PROP, v)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> ViewExtension[T]:
        """Extends the given STAC Object with properties from the :stac-ext:`View
        Geometry Extension <scientific>`.

        This extension can be applied to instances of :class:`~pystac.Item` or
        :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(ViewExtension[T], ItemViewExtension(obj))
        elif isinstance(obj, pystac.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return cast(ViewExtension[T], AssetViewExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"View extension does not apply to type '{type(obj).__name__}'"
            )

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesViewExtension:
        """Returns the extended summaries object for the given collection."""
        cls.validate_has_extension(obj, add_if_missing)
        return SummariesViewExtension(obj)


class ItemViewExtension(ViewExtension[pystac.Item]):
    """A concrete implementation of :class:`ViewExtension` on an :class:`~pystac.Item`
    that extends the properties of the Item to include properties defined in the
    :stac-ext:`View Geometry Extension <view>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`ViewExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    """The :class:`~pystac.Item` being extended."""

    properties: Dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemViewExtension Item id={}>".format(self.item.id)


class AssetViewExtension(ViewExtension[pystac.Asset]):
    """A concrete implementation of :class:`ViewExtension` on an :class:`~pystac.Asset`
    that extends the Asset fields to include properties defined in the
    :stac-ext:`View Geometry Extension <view>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`ViewExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset_href: str
    """The ``href`` value of the :class:`~pystac.Asset` being extended."""

    properties: Dict[str, Any]
    """The :class:`~pystac.Asset` fields, including extension properties."""

    additional_read_properties: Optional[Iterable[Dict[str, Any]]] = None
    """If present, this will be a list containing 1 dictionary representing the
    properties of the owning :class:`~pystac.Item`."""

    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return "<AssetViewExtension Asset href={}>".format(self.asset_href)


class SummariesViewExtension(SummariesExtension):
    """A concrete implementation of :class:`~SummariesExtension` that extends
    the ``summaries`` field of a :class:`~pystac.Collection` to include properties
    defined in the :stac-ext:`View Object Extension <view>`.
    """

    @property
    def off_nadir(self) -> Optional[RangeSummary[float]]:
        """Get or sets the summary of :attr:`ViewExtension.off_nadir` values for
        this Collection.
        """
        return self.summaries.get_range(OFF_NADIR_PROP)

    @off_nadir.setter
    def off_nadir(self, v: Optional[RangeSummary[float]]) -> None:
        self._set_summary(OFF_NADIR_PROP, v)

    @property
    def incidence_angle(self) -> Optional[RangeSummary[float]]:
        """Get or sets the summary of :attr:`ViewExtension.incidence_angle` values
        for this Collection.
        """
        return self.summaries.get_range(INCIDENCE_ANGLE_PROP)

    @incidence_angle.setter
    def incidence_angle(self, v: Optional[RangeSummary[float]]) -> None:
        self._set_summary(INCIDENCE_ANGLE_PROP, v)

    @property
    def azimuth(self) -> Optional[RangeSummary[float]]:
        """Get or sets the summary of :attr:`ViewExtension.azimuth` values
        for this Collection.
        """
        return self.summaries.get_range(AZIMUTH_PROP)

    @azimuth.setter
    def azimuth(self, v: Optional[RangeSummary[float]]) -> None:
        self._set_summary(AZIMUTH_PROP, v)

    @property
    def sun_azimuth(self) -> Optional[RangeSummary[float]]:
        """Get or sets the summary of :attr:`ViewExtension.sun_azimuth` values
        for this Collection.
        """
        return self.summaries.get_range(SUN_AZIMUTH_PROP)

    @sun_azimuth.setter
    def sun_azimuth(self, v: Optional[RangeSummary[float]]) -> None:
        self._set_summary(SUN_AZIMUTH_PROP, v)

    @property
    def sun_elevation(self) -> Optional[RangeSummary[float]]:
        """Get or sets the summary of :attr:`ViewExtension.sun_elevation` values
        for this Collection.
        """
        return self.summaries.get_range(SUN_ELEVATION_PROP)

    @sun_elevation.setter
    def sun_elevation(self, v: Optional[RangeSummary[float]]) -> None:
        self._set_summary(SUN_ELEVATION_PROP, v)


class ViewExtensionHooks(ExtensionHooks):
    schema_uri = SCHEMA_URI
    prev_extension_ids = {"view"}
    stac_object_types = {pystac.STACObjectType.ITEM}


VIEW_EXTENSION_HOOKS: ExtensionHooks = ViewExtensionHooks()
