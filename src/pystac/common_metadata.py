from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Protocol, override

from .provider import Provider
from .utils import datetime_to_str, str_to_datetime

if TYPE_CHECKING:
    from .asset import Asset
    from .item import Item


class Basics(Protocol):
    """Protocol for basic descriptive fields."""

    extra_fields: dict[str, Any]

    @property
    def title(self) -> str | None:
        """A human readable title describing the STAC entity."""
        return self.extra_fields.get("title")

    @title.setter
    def title(self, value: str | None) -> None:
        self.extra_fields["title"] = value

    @property
    def description(self) -> str | None:
        """
        Detailed multi-line description to fully explain the STAC entity.
        CommonMark 0.29 syntax MAY be used for rich text representation.
        """
        return self.extra_fields.get("description")

    @description.setter
    def description(self, value: str | None) -> None:
        if value == "":
            raise ValueError("description cannot be an empty string")
        self.extra_fields["description"] = value

    @property
    def keywords(self) -> list[str] | None:
        """List of keywords describing the STAC entity."""
        return self.extra_fields.get("keywords")

    @keywords.setter
    def keywords(self, value: list[str] | None) -> None:
        self.extra_fields["keywords"] = value

    @property
    def roles(self) -> list[str] | None:
        """
        The semantic roles of the entity, e.g. for assets,
        links, providers, bands, etc.
        """
        return self.extra_fields.get("roles")

    @roles.setter
    def roles(self, value: list[str] | None) -> None:
        self.extra_fields["roles"] = value


class DateTime(Protocol):
    """Protocol for date and time fields."""

    extra_fields: dict[str, Any]

    @property
    def datetime(self) -> dt.datetime | None:
        """See the Item Specification Fields for more information."""
        value: str | None = self.extra_fields.get("datetime")
        datetime: dt.datetime | None = None
        if value is not None:
            datetime = str_to_datetime(value)
        return datetime

    @datetime.setter
    def datetime(self, value: str | dt.datetime | None) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        datetime: str | None = None
        if isinstance(value, str):
            datetime = value
        elif isinstance(value, dt.datetime):
            datetime = datetime_to_str(value)
        self.extra_fields["datetime"] = datetime

    @property
    def created(self) -> dt.datetime | None:
        """Creation date and time of the corresponding STAC entity or Asset, in UTC."""
        value: str | None = self.extra_fields.get("created")
        datetime: dt.datetime | None = None
        if value is not None:
            datetime = str_to_datetime(value)
        return datetime

    @created.setter
    def created(self, value: str | dt.datetime | None) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        datetime: str | None = None
        if isinstance(value, str):
            datetime = value
        elif isinstance(value, dt.datetime):
            datetime = datetime_to_str(value)
        self.extra_fields["created"] = datetime

    @property
    def updated(self) -> dt.datetime | None:
        """
        Date and time the corresponding STAC entity or Asset
        was updated last, in UTC.
        """
        value: str | None = self.extra_fields.get("updated")
        datetime: dt.datetime | None = None
        if value is not None:
            datetime = str_to_datetime(value)
        return datetime

    @updated.setter
    def updated(self, value: str | dt.datetime | None) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        datetime: str | None = None
        if isinstance(value, str):
            datetime = value
        elif isinstance(value, dt.datetime):
            datetime = datetime_to_str(value)
        self.extra_fields["updated"] = datetime

    @property
    def start_datetime(self) -> dt.datetime | None:
        """The first or start date and time for the resource, in UTC."""
        value: str | None = self.extra_fields.get("start_datetime")
        datetime: dt.datetime | None = None
        if value is not None:
            datetime = str_to_datetime(value)
        return datetime

    @start_datetime.setter
    def start_datetime(self, value: str | dt.datetime | None) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        datetime: str | None = None
        if isinstance(value, str):
            datetime = value
        elif isinstance(value, dt.datetime):
            datetime = datetime_to_str(value)
        self.extra_fields["start_datetime"] = datetime

    @property
    def end_datetime(self) -> dt.datetime | None:
        """The last or end date and time for the resource, in UTC."""
        value: str | None = self.extra_fields.get("end_datetime")
        datetime: dt.datetime | None = None
        if value is not None:
            datetime = str_to_datetime(value)
        return datetime

    @end_datetime.setter
    def end_datetime(self, value: str | dt.datetime | None) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        datetime: str | None = None
        if isinstance(value, str):
            datetime = value
        elif isinstance(value, dt.datetime):
            datetime = datetime_to_str(value)
        self.extra_fields["end_datetime"] = datetime


class Licensing(Protocol):
    """Protocol for information about the license(s) of the data"""

    extra_fields: dict[str, Any]

    @property
    def license(self) -> str | None:
        """License(s) of the data that the STAC entity provides."""
        return self.extra_fields.get("license")

    @license.setter
    def license(self, value: str | None) -> None:
        self.extra_fields["license"] = value


class Providers(Protocol):
    """Protocol for nformation about the organizations capturing, producing,
    processing, hosting or publishing this data."""

    extra_fields: dict[str, Any]

    @property
    def providers(self) -> list[Provider] | None:
        """Provider(s) of the data that the STAC entity provides."""
        return [
            Provider.try_from(p) for p in self.extra_fields.get("providers", [])
        ] or None

    @providers.setter
    def providers(self, value: list[Provider] | None) -> None:
        providers: list[dict[str, Any]] | None = None
        if isinstance(value, list):
            providers = [Provider.try_from(p).to_dict() for p in value]
        self.extra_fields["providers"] = providers


class Instrument(Protocol):
    """Protocol for instrument metadata fields."""

    extra_fields: dict[str, Any]

    @property
    def platform(self) -> str | None:
        """Unique name of the specific platform to which the instrument is attached."""
        return self.extra_fields.get("platform")

    @platform.setter
    def platform(self, value: str | None) -> None:
        self.extra_fields["platform"] = value

    @property
    def instruments(self) -> list[str] | None:
        """Name of instrument or sensor used (e.g., MODIS, ASTER, OLI, Canon F-1)."""
        return self.extra_fields.get("instruments")

    @instruments.setter
    def instruments(self, value: list[str] | None) -> None:
        self.extra_fields["instruments"] = value

    @property
    def constellation(self) -> str | None:
        """Name of the constellation to which the platform belongs."""
        return self.extra_fields.get("constellation")

    @constellation.setter
    def constellation(self, value: str | None) -> None:
        self.extra_fields["constellation"] = value

    @property
    def mission(self) -> str | None:
        """Name of the mission for which data is collected."""
        return self.extra_fields.get("mission")

    @mission.setter
    def mission(self, value: str | None) -> None:
        self.extra_fields["mission"] = value

    @property
    def gsd(self) -> int | None:
        """
        Ground Sample Distance at the sensor, in meters (m),
        must be greater than 0.
        """
        return self.extra_fields.get("gsd")

    @gsd.setter
    def gsd(self, value: int | None) -> None:
        self.extra_fields["gsd"] = value


class DataType(StrEnum):
    int8 = "int8"
    int16 = "int16"
    int32 = "int32"
    int64 = "int64"
    uint8 = "uint8"
    uint16 = "uint16"
    uint32 = "uint32"
    uint64 = "uint64"
    float16 = "float16"
    float32 = "float32"
    float64 = "float64"
    cint16 = "cint16"
    cint32 = "cint32"
    cfloat32 = "cfloat32"
    cfloat64 = "cfloat64"
    other = "other"

    @override
    def __repr__(self):
        return self.value


@dataclass
class Statistics:
    statistics: dict[str, Any]

    @property
    def minimum(self) -> float | None:
        return self.statistics.get("minimum")

    @minimum.setter
    def minimum(self, value: float | None) -> None:
        self.statistics["minimum"] = value

    @property
    def maximum(self) -> float | None:
        return self.statistics.get("maximum")

    @maximum.setter
    def maximum(self, value: float | None) -> None:
        self.statistics["maximum"] = value

    @property
    def mean(self) -> float | None:
        return self.statistics.get("mean")

    @mean.setter
    def mean(self, value: float | None) -> None:
        self.statistics["mean"] = value

    @property
    def stddev(self) -> float | None:
        return self.statistics.get("stddev")

    @stddev.setter
    def stddev(self, value: float | None) -> None:
        self.statistics["stddev"] = value

    @property
    def count(self) -> int | None:
        return self.statistics.get("count")

    @count.setter
    def count(self, value: int | None) -> None:
        self.statistics["count"] = value

    @property
    def valid_percent(self) -> float | None:
        return self.statistics.get("valid_percent")

    @valid_percent.setter
    def valid_percent(self, value: float | None) -> None:
        self.statistics["valid_percent"] = value

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.statistics.items() if v is not None}


class DataValue(Protocol):
    extra_fields: dict[str, Any]

    @property
    def nodata(self) -> float | str | None:
        """
        The no-data value must be provided either as:

        - a number
        - a string:
            nan - NaN (not a number) as defined in IEEE-754
            inf - Positive Infinity
            -inf - Negative Infinity
        """
        return self.extra_fields.get("nodata")

    @nodata.setter
    def nodata(self, value: float | str | None) -> None:
        self.extra_fields["nodata"] = value

    @property
    def unit(self) -> str | None:
        """
        It is STRONGLY RECOMMENDED to provide units in one of the following two formats:

        UCUM: The unit code that is compliant to the UCUM specification.
        UDUNITS-2: The unit symbol if available, otherwise the singular unit name.
        """
        return self.extra_fields.get("unit")

    @unit.setter
    def unit(self, value: str | None) -> None:
        self.extra_fields["unit"] = value

    @property
    def data_type(self) -> DataType | str | None:
        return self.extra_fields.get("data_type")

    @data_type.setter
    def data_type(self, value: DataType | str | None) -> None:
        self.extra_fields["data_type"] = DataType(value)

    @property
    def statistics(self) -> Statistics:
        if not self.extra_fields.get("statistics"):
            statistics: dict[str, Any] = {}
            self.extra_fields["statistics"] = statistics
        return Statistics(self.extra_fields["statistics"])


class CommonMetadata(Basics, DateTime, Licensing, Providers, Instrument, DataValue):
    object: Asset | Item
    """The object from which common metadata is obtained."""

    def __init__(self, /, object: Asset | Item):
        self.object = object

    @property
    @override
    def extra_fields(self) -> dict[str, Any]:  # pyright: ignore[reportIncompatibleVariableOverride]
        from pystac import Item

        if isinstance(self.object, Item):
            return self.object.properties.extra_fields
        return self.object.extra_fields

    @override
    def __repr__(self):
        fields: str = ", ".join(
            f"{k}={v}" for k, v in self.extra_fields.items() if v is not None
        )
        if len(fields) > 100:
            fields = f"{fields[:50]}...{fields[-50:]}"
        return f"<CommonMetadata {fields}>"
