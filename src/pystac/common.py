from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol


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
        self.extra_fields["data_type"] = value

    @property
    def statistics(self) -> Statistics:
        if not self.extra_fields.get("statistics"):
            statistics: dict[str, Any] = {}
            self.extra_fields["statistics"] = statistics
        return Statistics(self.extra_fields["statistics"])


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
    def datetime(self) -> str | None:
        """See the Item Specification Fields for more information."""
        return self.extra_fields.get("datetime")

    @datetime.setter
    def datetime(self, value: str | None) -> None:
        self.extra_fields["datetime"] = value

    @property
    def created(self) -> str | None:
        """Creation date and time of the corresponding STAC entity or Asset, in UTC."""
        return self.extra_fields.get("created")

    @created.setter
    def created(self, value: str | None) -> None:
        self.extra_fields["created"] = value

    @property
    def updated(self) -> str | None:
        """
        Date and time the corresponding STAC entity or Asset
        was updated last, in UTC.
        """
        return self.extra_fields.get("updated")

    @updated.setter
    def updated(self, value: str | None) -> None:
        self.extra_fields["updated"] = value

    @property
    def start_datetime(self) -> str | None:
        """The first or start date and time for the resource, in UTC."""
        return self.extra_fields.get("start_datetime")

    @start_datetime.setter
    def start_datetime(self, value: str | None) -> None:
        self.extra_fields["start_datetime"] = value

    @property
    def end_datetime(self) -> str | None:
        """The last or end date and time for the resource, in UTC."""
        return self.extra_fields.get("end_datetime")

    @end_datetime.setter
    def end_datetime(self, value: str | None) -> None:
        self.extra_fields["end_datetime"] = value


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
    def gsd(self) -> float | None:
        """
        Ground Sample Distance at the sensor, in meters (m),
        must be greater than 0.
        """
        return self.extra_fields.get("gsd")

    @gsd.setter
    def gsd(self, value: float | None) -> None:
        self.extra_fields["gsd"] = value
