"""Implements the :stac-ext:`Satellite Extension <sat>`."""

from datetime import datetime as Datetime
from pystac.summaries import RangeSummary
from typing import Dict, Any, List, Iterable, Generic, Optional, TypeVar, Union, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import StringEnum, str_to_datetime, datetime_to_str, map_opt

T = TypeVar("T", pystac.Item, pystac.Asset)

SCHEMA_URI = "https://stac-extensions.github.io/sat/v1.0.0/schema.json"

PREFIX: str = "sat:"
PLATFORM_INTERNATIONAL_DESIGNATOR_PROP: str = (
    PREFIX + "platform_international_designator"
)
ABSOLUTE_ORBIT_PROP: str = PREFIX + "absolute_orbit"
ORBIT_STATE_PROP: str = PREFIX + "orbit_state"
RELATIVE_ORBIT_PROP: str = PREFIX + "relative_orbit"
ANX_DATETIME_PROP: str = PREFIX + "anx_datetime"


class OrbitState(StringEnum):
    ASCENDING = "ascending"
    DESCENDING = "descending"
    GEOSTATIONARY = "geostationary"


class SatExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[pystac.Item, pystac.Collection]],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Item` or :class:`~pystac.Asset` with properties from the
    :stac-ext:`Satellite Extension <sat>`. This class is generic over the type of
    STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Collection`).

    To create a concrete instance of :class:`SatExtension`, use the
    :meth:`SatExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> sat_ext = SatExtension.ext(item)
    """

    def apply(
        self,
        orbit_state: Optional[OrbitState] = None,
        relative_orbit: Optional[int] = None,
        absolute_orbit: Optional[int] = None,
        platform_international_designator: Optional[str] = None,
        anx_datetime: Optional[Datetime] = None,
    ) -> None:
        """Applies ext extension properties to the extended :class:`~pystac.Item` or
        class:`~pystac.Asset`.

        Must specify at least one of orbit_state or relative_orbit in order
        for the sat extension to properties to be valid.

        Args:
            orbit_state : Optional state of the orbit. Either ascending or
                descending for polar orbiting satellites, or geostationary for
                geosynchronous satellites.
            relative_orbit : Optional non-negative integer of the orbit number at
                the time of acquisition.
        """

        self.platform_international_designator = platform_international_designator
        self.orbit_state = orbit_state
        self.absolute_orbit = absolute_orbit
        self.relative_orbit = relative_orbit
        self.anx_datetime = anx_datetime

    @property
    def platform_international_designator(self) -> Optional[str]:
        """Gets or sets the International Designator, also known as COSPAR ID, and
        NSSDCA ID."""
        return self._get_property(PLATFORM_INTERNATIONAL_DESIGNATOR_PROP, str)

    @platform_international_designator.setter
    def platform_international_designator(self, v: Optional[str]) -> None:
        self._set_property(PLATFORM_INTERNATIONAL_DESIGNATOR_PROP, v)

    @property
    def orbit_state(self) -> Optional[OrbitState]:
        """Get or sets an orbit state of the object."""
        return map_opt(
            lambda x: OrbitState(x), self._get_property(ORBIT_STATE_PROP, str)
        )

    @orbit_state.setter
    def orbit_state(self, v: Optional[OrbitState]) -> None:
        self._set_property(ORBIT_STATE_PROP, map_opt(lambda x: x.value, v))

    @property
    def absolute_orbit(self) -> Optional[int]:
        """Get or sets a absolute orbit number of the item."""
        return self._get_property(ABSOLUTE_ORBIT_PROP, int)

    @absolute_orbit.setter
    def absolute_orbit(self, v: Optional[int]) -> None:
        self._set_property(ABSOLUTE_ORBIT_PROP, v)

    @property
    def relative_orbit(self) -> Optional[int]:
        """Get or sets a relative orbit number of the item."""
        return self._get_property(RELATIVE_ORBIT_PROP, int)

    @relative_orbit.setter
    def relative_orbit(self, v: Optional[int]) -> None:
        self._set_property(RELATIVE_ORBIT_PROP, v)

    @property
    def anx_datetime(self) -> Optional[Datetime]:
        return map_opt(str_to_datetime, self._get_property(ANX_DATETIME_PROP, str))

    @anx_datetime.setter
    def anx_datetime(self, v: Optional[Datetime]) -> None:
        self._set_property(ANX_DATETIME_PROP, map_opt(datetime_to_str, v))

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> "SatExtension[T]":
        """Extends the given STAC Object with properties from the :stac-ext:`Satellite
        Extension <sat>`.

        This extension can be applied to instances of :class:`~pystac.Item` or
        :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(SatExtension[T], ItemSatExtension(obj))
        elif isinstance(obj, pystac.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return cast(SatExtension[T], AssetSatExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"Satellite extension does not apply to type '{type(obj).__name__}'"
            )

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> "SummariesSatExtension":
        """Returns the extended summaries object for the given collection."""
        cls.validate_has_extension(obj, add_if_missing)
        return SummariesSatExtension(obj)


class ItemSatExtension(SatExtension[pystac.Item]):
    """A concrete implementation of :class:`SatExtension` on an :class:`~pystac.Item`
    that extends the properties of the Item to include properties defined in the
    :stac-ext:`Satellite Extension <sat>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`SatExtension.ext` on an :class:`~pystac.Item` to
    extend it.
    """

    item: pystac.Item
    """The :class:`~pystac.Item` being extended."""

    properties: Dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemSatExtension Item id={}>".format(self.item.id)


class AssetSatExtension(SatExtension[pystac.Asset]):
    """A concrete implementation of :class:`SatExtension` on an :class:`~pystac.Asset`
    that extends the properties of the Asset to include properties defined in the
    :stac-ext:`Satellite Extension <sat>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`SatExtension.ext` on an :class:`~pystac.Asset` to
    extend it.
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
        return "<AssetSatExtension Asset href={}>".format(self.asset_href)


class SummariesSatExtension(SummariesExtension):
    """A concrete implementation of :class:`~SummariesExtension` that extends
    the ``summaries`` field of a :class:`~pystac.Collection` to include properties
    defined in the :stac-ext:`Satellite Extension <sat>`.
    """

    @property
    def platform_international_designator(self) -> Optional[List[str]]:
        """Get or sets the summary of
        :attr:`SatExtension.platform_international_designator` values for this
        Collection.
        """

        return self.summaries.get_list(PLATFORM_INTERNATIONAL_DESIGNATOR_PROP)

    @platform_international_designator.setter
    def platform_international_designator(self, v: Optional[List[str]]) -> None:
        self._set_summary(PLATFORM_INTERNATIONAL_DESIGNATOR_PROP, v)

    @property
    def orbit_state(self) -> Optional[List[OrbitState]]:
        """Get or sets the summary of :attr:`SatExtension.orbit_state` values
        for this Collection.
        """

        return self.summaries.get_list(ORBIT_STATE_PROP)

    @orbit_state.setter
    def orbit_state(self, v: Optional[List[OrbitState]]) -> None:
        self._set_summary(ORBIT_STATE_PROP, v)

    @property
    def absolute_orbit(self) -> Optional[RangeSummary[int]]:
        return self.summaries.get_range(ABSOLUTE_ORBIT_PROP)

    @absolute_orbit.setter
    def absolute_orbit(self, v: Optional[RangeSummary[int]]) -> None:
        self._set_summary(ABSOLUTE_ORBIT_PROP, v)

    @property
    def relative_orbit(self) -> Optional[RangeSummary[int]]:
        return self.summaries.get_range(RELATIVE_ORBIT_PROP)

    @relative_orbit.setter
    def relative_orbit(self, v: Optional[RangeSummary[int]]) -> None:
        self._set_summary(RELATIVE_ORBIT_PROP, v)

    @property
    def anx_datetime(self) -> Optional[RangeSummary[Datetime]]:
        return map_opt(
            lambda s: RangeSummary(
                str_to_datetime(s.minimum), str_to_datetime(s.maximum)
            ),
            self.summaries.get_range(ANX_DATETIME_PROP),
        )

    @anx_datetime.setter
    def anx_datetime(self, v: Optional[RangeSummary[Datetime]]) -> None:
        self._set_summary(
            ANX_DATETIME_PROP,
            map_opt(
                lambda s: RangeSummary(
                    datetime_to_str(s.minimum), datetime_to_str(s.maximum)
                ),
                v,
            ),
        )


class SatExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"sat"}
    stac_object_types = {pystac.STACObjectType.ITEM}


SAT_EXTENSION_HOOKS: ExtensionHooks = SatExtensionHooks()
