from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, TypeVar, cast

import pystac
from pystac import utils
from pystac.errors import STACError

if TYPE_CHECKING:
    from pystac.asset import Asset
    from pystac.band import Band
    from pystac.item import Item
    from pystac.provider import Provider


P = TypeVar("P")


class DataType(utils.StringEnum):
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    UINT64 = "uint64"
    FLOAT16 = "float16"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    CINT16 = "cint16"
    CINT32 = "cint32"
    CFLOAT32 = "cfloat32"
    CFLOAT64 = "cfloat64"
    OTHER = "other"


class NoDataStrings(utils.StringEnum):
    INF = "inf"
    NINF = "-inf"
    NAN = "nan"


class Statistics:
    """Represents statistics information attached to raster bands in the
    common metadata.

    Use Statistics.create to create a new Statistics instance.
    """

    properties: dict[str, Any]

    def __init__(self, properties: dict[str, float | None]) -> None:
        self.properties = properties

    def apply(
        self,
        minimum: float | None = None,
        maximum: float | None = None,
        mean: float | None = None,
        stddev: float | None = None,
        count: int | None = None,
        valid_percent: float | None = None,
    ) -> None:
        """
        Sets the properties for this Statistics object.

        Args:
            minimum : Minimum value of all the pixels in the band.
            maximum : Maximum value of all the pixels in the band.
            mean : Mean value of all the pixels in the band.
            stddev : Standard Deviation value of all the pixels in the band.
            count : Ttal number of all data values (>=0)
            valid_percent : Percentage of valid (not nodata) pixel.
        """
        self.minimum = minimum
        self.maximum = maximum
        self.mean = mean
        self.stddev = stddev
        self.count = count
        self.valid_percent = valid_percent

    @classmethod
    def create(
        cls,
        minimum: float | None = None,
        maximum: float | None = None,
        mean: float | None = None,
        stddev: float | None = None,
        count: int | None = None,
        valid_percent: float | None = None,
    ) -> Statistics:
        """
        Creates a new statistics object.

        Args:
            minimum : Minimum value of all the pixels in the band.
            maximum : Maximum value of all the pixels in the band.
            mean : Mean value of all the pixels in the band.
            stddev : Standard Deviation value of all the pixels in the band.
            valid_percent : Percentage of valid (not nodata) pixel.
            extra_fields : Additional information (ie. land/vegetation cover)
        """
        b = cls({})
        b.apply(
            minimum=minimum,
            maximum=maximum,
            mean=mean,
            stddev=stddev,
            count=count,
            valid_percent=valid_percent,
        )
        return b

    @property
    def minimum(self) -> float | None:
        """Get or sets the minimum pixel value

        Returns:
            Optional[float]
        """
        return self.properties.get("minimum")

    @minimum.setter
    def minimum(self, v: float | None) -> None:
        if v is not None:
            self.properties["minimum"] = v
        else:
            self.properties.pop("minimum", None)

    @property
    def maximum(self) -> float | None:
        """Get or sets the maximum pixel value

        Returns:
            Optional[float]
        """
        return self.properties.get("maximum")

    @maximum.setter
    def maximum(self, v: float | None) -> None:
        if v is not None:
            self.properties["maximum"] = v
        else:
            self.properties.pop("maximum", None)

    @property
    def mean(self) -> float | None:
        """Get or sets the mean pixel value

        Returns:
            Optional[float]
        """
        return self.properties.get("mean")

    @mean.setter
    def mean(self, v: float | None) -> None:
        if v is not None:
            self.properties["mean"] = v
        else:
            self.properties.pop("mean", None)

    @property
    def stddev(self) -> float | None:
        """Get or sets the standard deviation pixel value

        Returns:
            Optional[float]
        """
        return self.properties.get("stddev")

    @stddev.setter
    def stddev(self, v: float | None) -> None:
        if v is not None:
            self.properties["stddev"] = v
        else:
            self.properties.pop("stddev", None)

    @property
    def count(self) -> int | None:
        """Get or sets the total number of data values (>= 0)."""
        return self.properties.get("count")

    @count.setter
    def count(self, v: int | None) -> None:
        if v is not None:
            self.properties["count"] = v
        else:
            self.properties.pop("count", None)

    @property
    def valid_percent(self) -> float | None:
        """Get or sets the Percentage of valid (not nodata) pixel

        Returns:
            Optional[float]
        """
        return self.properties.get("valid_percent")

    @valid_percent.setter
    def valid_percent(self, v: float | None) -> None:
        if v is not None:
            self.properties["valid_percent"] = v
        else:
            self.properties.pop("valid_percent", None)

    def to_dict(self) -> dict[str, Any]:
        """Returns these statistics as a dictionary.

        Returns:
            dict: The serialization of the Statistics.
        """
        return self.properties

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Statistics:
        """Constructs a Statistics from a dict.

        Returns:
            Statistics: The Statistics deserialized from the JSON dict.
        """
        return Statistics(properties=d)


class CommonMetadata:
    """Object containing fields that are not included in core item schema but
    are still commonly used. All attributes are defined within the properties of
    this item and are optional

    Args:
        properties : Dictionary of attributes that is the Item's properties
    """

    object: Asset | Item
    """The object from which common metadata is obtained."""

    def __init__(self, object: Asset | Item):
        self.object = object

    def _set_field(self, prop_name: str, v: Any | None) -> None:
        if hasattr(self.object, prop_name):
            setattr(self.object, prop_name, v)
        elif hasattr(self.object, "properties"):
            item = cast(pystac.Item, self.object)
            if v is None:
                item.properties.pop(prop_name, None)
            else:
                item.properties[prop_name] = v
        elif hasattr(self.object, "extra_fields") and isinstance(
            self.object.extra_fields, dict
        ):
            if v is None:
                self.object.extra_fields.pop(prop_name, None)
            else:
                self.object.extra_fields[prop_name] = v
        else:
            raise pystac.STACError(f"Cannot set field {prop_name} on {self}.")

    def _get_field(self, prop_name: str, _typ: type[P]) -> P | None:
        if hasattr(self.object, prop_name):
            return cast(Optional[P], getattr(self.object, prop_name))
        elif hasattr(self.object, "properties"):
            item = cast(pystac.Item, self.object)
            return item.properties.get(prop_name)
        elif hasattr(self.object, "extra_fields") and isinstance(
            self.object.extra_fields, dict
        ):
            return self.object.extra_fields.get(prop_name)
        else:
            raise STACError(f"Cannot get field {prop_name} from {self}.")

    # Basics
    @property
    def title(self) -> str | None:
        """Gets or set the object's title."""
        return self._get_field("title", str)

    @title.setter
    def title(self, v: str | None) -> None:
        self._set_field("title", v)

    @property
    def description(self) -> str | None:
        """Gets or set the object's description."""
        return self._get_field("description", str)

    @description.setter
    def description(self, v: str | None) -> None:
        if v == "":
            raise ValueError("description cannot be an empty string")
        self._set_field("description", v)

    # Date and Time Range
    @property
    def start_datetime(self) -> datetime | None:
        """Get or set the object's start_datetime.

        Note:
            ``start_datetime`` is an inclusive datetime.
        """
        return utils.map_opt(
            utils.str_to_datetime, self._get_field("start_datetime", str)
        )

    @start_datetime.setter
    def start_datetime(self, v: datetime | None) -> None:
        self._set_field("start_datetime", utils.map_opt(utils.datetime_to_str, v))

    @property
    def end_datetime(self) -> datetime | None:
        """Get or set the item's end_datetime.

        Note:
            ``end_datetime`` is an inclusive datetime.
        """
        return utils.map_opt(
            utils.str_to_datetime, self._get_field("end_datetime", str)
        )

    @end_datetime.setter
    def end_datetime(self, v: datetime | None) -> None:
        self._set_field("end_datetime", utils.map_opt(utils.datetime_to_str, v))

    # License
    @property
    def license(self) -> str | None:
        """Get or set the current license. License should be provided
        as a `SPDX License identifier <https://spdx.org/licenses/>`_,
        or `other`. If object includes data with multiple
        different licenses, use `other` and add a link for
        each.

        Note:
            The licenses `various` and `proprietary` are deprecated.
        """
        return self._get_field("license", str)

    @license.setter
    def license(self, v: str | None) -> None:
        self._set_field("license", v)

    # Providers
    @property
    def providers(self) -> list[Provider] | None:
        """Get or set a list of the object's providers."""
        return utils.map_opt(
            lambda providers: [pystac.Provider.from_dict(d) for d in providers],
            self._get_field("providers", list[dict[str, Any]]),
        )

    @providers.setter
    def providers(self, v: list[Provider] | None) -> None:
        self._set_field(
            "providers",
            utils.map_opt(lambda providers: [p.to_dict() for p in providers], v),
        )

    # Bands
    # V2.0.0 for some extensions like raster and eo regroup them
    @property
    def bands(self) -> list[Band] | None:
        """Get or set a list of the object's bands."""
        return utils.map_opt(
            lambda bands: [pystac.Band.from_dict(d) for d in bands],
            self._get_field("bands", list[dict[str, Any]]),
        )

    @bands.setter
    def bands(self, v: list[Band] | None) -> None:
        self._set_field(
            "bands", utils.map_opt(lambda bands: [b.to_dict() for b in bands], v)
        )

    # Instrument
    @property
    def platform(self) -> str | None:
        """Gets or set the object's platform attribute."""
        return self._get_field("platform", str)

    @platform.setter
    def platform(self, v: str | None) -> None:
        self._set_field("platform", v)

    @property
    def instruments(self) -> list[str] | None:
        """Gets or sets the names of the instruments used."""
        return self._get_field("instruments", list[str])

    @instruments.setter
    def instruments(self, v: list[str] | None) -> None:
        self._set_field("instruments", v)

    @property
    def constellation(self) -> str | None:
        """Gets or set the name of the constellation associate with an object."""
        return self._get_field("constellation", str)

    @constellation.setter
    def constellation(self, v: str | None) -> None:
        self._set_field("constellation", v)

    @property
    def mission(self) -> str | None:
        """Gets or set the name of the mission associated with an object."""
        return self._get_field("mission", str)

    @mission.setter
    def mission(self, v: str | None) -> None:
        self._set_field("mission", v)

    @property
    def gsd(self) -> float | None:
        """Gets or sets the Ground Sample Distance at the sensor."""
        return self._get_field("gsd", float)

    @gsd.setter
    def gsd(self, v: float | None) -> None:
        self._set_field("gsd", v)

    # Metadata
    @property
    def created(self) -> datetime | None:
        """Get or set the metadata file's creation date. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string.

        Note:
            ``created`` has a different meaning depending on the type of STAC object.
            On an :class:`~pystac.Item`, it refers to the creation time of the
            metadata. On an :class:`~pystac.Asset`, it refers to the creation time of
            the actual data linked to in :attr:`~pystac.Asset.href`.
        """
        return utils.map_opt(utils.str_to_datetime, self._get_field("created", str))

    @created.setter
    def created(self, v: datetime | None) -> None:
        self._set_field("created", utils.map_opt(utils.datetime_to_str, v))

    @property
    def updated(self) -> datetime | None:
        """Get or set the metadata file's update date. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Note:
            ``updated`` has a different meaning depending on the type of STAC object.
            On an :class:`~pystac.Item`, it refers to the update time of the
            metadata. On an :class:`~pystac.Asset`, it refers to the update time of
            the actual data linked to in :attr:`~pystac.Asset.href`.
        """
        return utils.map_opt(utils.str_to_datetime, self._get_field("updated", str))

    @updated.setter
    def updated(self, v: datetime | None) -> None:
        self._set_field("updated", utils.map_opt(utils.datetime_to_str, v))

    @property
    def keywords(self) -> list[str] | None:
        """Get or set the keywords describing the STAC entity."""
        return self._get_field("keywords", list[str])

    @keywords.setter
    def keywords(self, v: list[str] | None) -> None:
        self._set_field("keywords", v)

    @property
    def roles(self) -> list[str] | None:
        """Get or set the semantic roles of the entity."""
        return self._get_field("roles", list[str])

    @roles.setter
    def roles(self, v: list[str] | None) -> None:
        self._set_field("roles", v)

    # nodata
    @property
    def nodata(self) -> float | NoDataStrings | None:
        """Get or set the no-data value of the entity

        `nodata` can be a string or a number
        """
        return utils.map_opt(
            lambda v: NoDataStrings(v) if v in NoDataStrings else float(v),
            self._get_field("nodata", str),
        )

    @nodata.setter
    def nodata(self, v: float | NoDataStrings | None) -> None:
        self._set_field("nodata", v)

    # data_type
    @property
    def data_type(self) -> DataType | None:
        """Get or set the data type of the values"""
        return self._get_field("data_type", DataType)

    @data_type.setter
    def data_type(self, v: DataType) -> None:
        self._set_field("data_type", v)

    # statistics
    @property
    def statistics(self) -> Statistics | None:
        """Get or set the statistics of all the values"""
        return self._get_field("statistics", Statistics)

    @statistics.setter
    def statistics(self, v: Statistics) -> None:
        self._set_field("statistics", v)

    # unit
    @property
    def unit(self) -> str | None:
        """Get or set the unit of measurement of the value

        It is STRONGLY RECOMMENDED to provide units in one of the following two formats:

            - UCUM: The unit code that is compliant to the UCUM specification.
                https://ucum.org/
            - UDUNITS-2: The unit symbol if available, otherwise the singular unit name.
                https://ncics.org/portfolio/other-resources/udunits2/
        """
        return self._get_field("unit", str)

    @unit.setter
    def unit(self, v: str | None) -> None:
        self._set_field("unit", v)
