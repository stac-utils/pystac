"""Implements the :stac-ext:`Processing <processing>` STAC Extension.

https://github.com/stac-extensions/processing
"""

from __future__ import annotations

from datetime import datetime
from typing import (
    Any,
    Generic,
    Literal,
    Self,
    TypeVar,
    cast,
)

import pystac
from pystac.extensions import item_assets
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
)
from pystac.utils import StringEnum, datetime_to_str, map_opt, str_to_datetime

T = TypeVar("T", pystac.Item, pystac.Asset, item_assets.AssetDefinition)

SCHEMA_URI: str = "https://stac-extensions.github.io/processing/v1.2.0/schema.json"
SCHEMA_URIS: list[str] = [
    SCHEMA_URI,
]
PREFIX: str = "processing:"

# Field names
LEVEL_PROP: str = PREFIX + "level"
DATETIME_PROP: str = PREFIX + "datetime"
EXPRESSION_PROP: str = PREFIX + "expression"
LINEAGE_PROP: str = PREFIX + "lineage"
FACILITY_PROP: str = PREFIX + "facility"
VERSION_PROP: str = PREFIX + "version"
SOFTWARE_PROP: str = PREFIX + "software"


class ProcessingLevel(StringEnum):
    RAW = "RAW"
    """Data in their original packets, as received from the instrument."""
    L0 = "L0"
    """Reconstructed unprocessed instrument data at full space time resolution with all
    available supplemental information to be used in subsequent processing
    (e.g., ephemeris, health and safety) appended."""
    L1 = "L1"
    """Unpacked, reformatted level 0 data, with all supplemental information to be used
    in subsequent processing appended. Optional radiometric and geometric correction
    applied to produce parameters in physical units. Data generally presented as full
    time/space resolution."""
    L1A = "L1A"
    """Unpacked, reformatted level 0 data, with all supplemental information to be used
    in subsequent processing appended. Optional radiometric and geometric correction
    applied to produce parameters in physical units. Data generally presented as full
    time/space resolution."""
    L1B = "L1B"
    """Unpacked, reformatted level 0 data, with all supplemental information to be used
    in subsequent processing appended. Optional radiometric and geometric correction
    applied to produce parameters in physical units. Data generally presented as full
    time/space resolution."""
    L1C = "L1C"
    """Unpacked, reformatted level 0 data, with all supplemental information to be used
    in subsequent processing appended. Optional radiometric and geometric correction
    applied to produce parameters in physical units. Data generally presented as full
    time/space resolution."""
    L2 = "L2"
    """Retrieved environmental variables (e.g., ocean wave height, soil-moisture,
    ice concentration) at the same resolution and location as the level 1 source
    data."""
    L2A = "L2A"
    """Retrieved environmental variables (e.g., ocean wave height, soil-moisture,
    ice concentration) at the same resolution and location as the level 1 source
    data."""
    L3 = "L3"
    """Data or retrieved environmental variables which have been spatially and/or
    temporally re-sampled (i.e., derived from level 1 or 2 products). Such
    re-sampling may include averaging and compositing."""
    L4 = "L4"
    """Model output or results from analyses of lower level data (i.e., variables that 
    are not directly measured by the instruments, but are derived from these
    measurements)"""


class ProcessingRelType(StringEnum):
    """A list of rel types defined in the Processing Extension.

    See the :stac-ext:`Processing Extension Relation types
    <processing#relation-types>` documentation
    for details."""

    EXPRESSION = "processing-expression"
    """A processing chain (or script) that describes how the data has been processed."""

    EXECUTION = "processing-execution"
    """URL to any resource representing the processing execution 
    (e.g. OGC Process API)."""

    SOFTWARE = "processing-software"
    """URL to any resource that identifies the software and versions used for processing
    the data, e.g. a Pipfile.lock (Python) or package-lock.json (NodeJS)."""

    VALIDATION = "processing-validation"
    """URL to any kind of validation that has been applied after processing, e.g. a 
    validation report or a script used for validation."""


class ProcessingExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Item` or :class:`~pystac.Asset` with properties from the
    :stac-ext:`Processing Extension <processing>`. This class is generic over the type
    of STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Collection`).

    To create a concrete instance of :class:`ProcessingExtension`, use the
    :meth:`ProcessingExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> proc_ext = ProcessingExtension.ext(item)

    """

    name: Literal["processing"] = "processing"

    def __init__(self: Self, item: pystac.Item) -> None:
        self.item = item
        self.properties = item.properties

    def __repr__(self: Self) -> str:
        return f"<ProcessingExtension Item id={self.item.id}>"

    def apply(
        self: Self,
        level: ProcessingLevel | None = None,
        datetime: datetime | None = None,
        expression: str | None = None,
        lineage: str | None = None,
        facility: str | None = None,
        version: str | None = None,
        software: dict[str, str] | None = None,
    ) -> None:
        """Applies the processing extension properties to the extended Item.

        Args:
            level: The processing level of the product. This should be the short name,
                as one of the available options under the `ProcessingLevel` enum.
            datetime: The datetime when the product was processed. Might be already
                specified in the common STAC metadata.
            expression: The expression used to obtain the processed product, like
                `gdal-calc` or `rio-calc`.
            lineage: Free text information about the how observations were processed or
                models that were used to create the resource being described.
            facility: The name of the facility that produced the data, like ESA.
            version: The version of the primary processing software or processing chain
                that produced the data, like the processing baseline for the Sentinel
                missions.
            software: A dictionary describing one or more applications or libraries that
                were involved during the production of the data for provenance purposes.
        """
        self.level = level
        self.datetime = datetime
        self.expression = expression
        self.lineage = lineage
        self.facility = facility
        self.version = version
        self.software = software

    @property
    def level(self: Self) -> ProcessingLevel | None:
        """Get or sets the processing level as the name commonly used to refer to the
        processing level to make it easier to search for product level across
        collections or items. This property is expected to be a `ProcessingLevel`"""
        return map_opt(
            lambda x: ProcessingLevel(x), self._get_property(LEVEL_PROP, str)
        )

    @level.setter
    def level(self: Self, v: ProcessingLevel | None) -> None:
        self._set_property(LEVEL_PROP, map_opt(lambda x: x.value, v))

    @property
    def datetime(self: Self) -> datetime | None:
        """Gets or set the processing date and time of the corresponding data formatted
        according to RFC 3339, section 5.6, in UTC. The time of the processing can be
        specified as a global field in processing:datetime, but it can also be specified
        directly and individually via the created properties of the target asset as
        specified in the STAC Common metadata. See more at
        https://github.com/stac-extensions/processing?tab=readme-ov-file#processing-date-time"""
        return map_opt(str_to_datetime, self._get_property(DATETIME_PROP, str))

    @datetime.setter
    def datetime(self: Self, v: datetime | None) -> None:
        self._set_property(DATETIME_PROP, map_opt(datetime_to_str, v))

    @property
    def expression(self: Self) -> dict[str, str | Any] | None:
        """Gets or sets an expression or processing chain that describes how the data
        has been processed. Alternatively, you can also link to a processing chain with
        the relation type processing-expression.
        .. code-block:: python
            >>> proc_ext.expression = "(b4-b1)/(b4+b1)"
            >>> proc_ext.expression = "(b4-b1)/(b4+b1)"
        """
        return self._get_property(EXPRESSION_PROP, dict[str, str | Any])

    @expression.setter
    def expression(self: Self, v: str | Any | None) -> None:
        if isinstance(v, str):
            exp_format = "string"
        elif isinstance(v, object):
            exp_format = "object"
        else:
            raise ValueError(
                "The provided expression is not a valid type (string or object)"
            )

        expression = {
            "format": exp_format,
            "expression": v,
        }

        self._set_property(EXPRESSION_PROP, expression)

    @property
    def lineage(self: Self) -> str | None:
        """Gets or sets the lineage provided as free text information about how
        observations were processed or models that were used to create the resource
        being described NASA ISO. For example, GRD Post Processing for "GRD" product of
        Sentinel-1 satellites. CommonMark 0.29 syntax MAY be used for rich text
        representation."""
        return self._get_property(LINEAGE_PROP, str)

    @lineage.setter
    def lineage(self: Self, v: str | None) -> None:
        self._set_property(LINEAGE_PROP, v)

    @property
    def facility(self: Self) -> str | None:
        """Gets or sets the name of the facility that produced the data. For example,
        Copernicus S1 Core Ground Segment - DPA for product of Sentinel-1 satellites."""
        return self._get_property(FACILITY_PROP, str)

    @facility.setter
    def facility(self: Self, v: str | None) -> None:
        self._set_property(FACILITY_PROP, v)

    @property
    def version(self: Self) -> str | None:
        """Gets or sets The version of the primary processing software or processing
        chain that produced the data. For example, this could be the processing baseline
        for the Sentinel missions."""
        return self._get_property(VERSION_PROP, str)

    @version.setter
    def version(self: Self, v: str | None) -> None:
        self._set_property(VERSION_PROP, v)

    @property
    def software(self: Self) -> dict[str, str] | None:
        """Gets or sets the processing software as a dictionary with name/version for
        key/value describing one or more applications or libraries that were involved
        during the production of the data for provenance purposes.

        They are mostly informative and important to be complete for reproducibility
        purposes. Thus, the values in the object can not just be version numbers, but
        also be e.g. tag names, commit hashes or similar. For example, you could expose
        a simplified version of the Pipfile.lock (Python) or package-lock.json (NodeJS).
        If you need more information, you could also link to such files via the relation
        type processing-software.
        .. code-block:: python
            >>> proc_ext.software = {
                    "Sentinel-1 IPF": "002.71"
                }
        """
        return self._get_property(SOFTWARE_PROP, dict[str, str])

    @software.setter
    def software(self: Self, v: dict[str, str] | None) -> None:
        self._set_property(SOFTWARE_PROP, v)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> ProcessingExtension[T]:
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(ProcessingExtension, ItemProcessingExtension(obj))
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))


class ItemProcessingExtension(ProcessingExtension[pystac.Item]):
    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self: Self, item: pystac.Item) -> None:
        self.item = item
        self.properties = item.properties

    def __repr__(self: Self) -> str:
        return f"<ItemProcessingExtension Item id={self.item.id}>"
