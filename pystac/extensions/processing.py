"""Implements the :stac-ext:`Processing <processing>` STAC Extension.

https://github.com/stac-extensions/processing
"""

from __future__ import annotations

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
from pystac.utils import StringEnum

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
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


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

    def __init__(self: Self, item: pystac.Item) -> None:
        self.item = item
        self.properties = item.properties

    def __repr__(self: Self) -> str:
        return f"<ProcessingExtension Item id={self.item.id}>"

    def apply(self: Self, level: str | None = None) -> None:
        self.level = level

    @property
    def level(self: Self) -> str | None:
        return self._get_property(LEVEL_PROP, str)

    @level.setter
    def level(self: Self, v: str | None) -> None:
        self._set_property(LEVEL_PROP, v, pop_if_none=True)

    @property
    def datetime(self: Self) -> str | None:
        return self._get_property(DATETIME_PROP, str)

    @datetime.setter
    def datetime(self: Self, v: str | None) -> None:
        self._set_property(DATETIME_PROP, v, pop_if_none=True)

    @property
    def expression(self: Self) -> str | None:
        return self._get_property(EXPRESSION_PROP, str)

    @expression.setter
    def expression(self: Self, v: str | None) -> None:
        self._set_property(EXPRESSION_PROP, v, pop_if_none=True)

    @property
    def lineage(self: Self) -> str | None:
        return self._get_property(LINEAGE_PROP, str)

    @lineage.setter
    def lineage(self: Self, v: str | None) -> None:
        self._set_property(LINEAGE_PROP, v, pop_if_none=True)

    @property
    def facility(self: Self) -> str | None:
        return self._get_property(FACILITY_PROP, str)

    @facility.setter
    def facility(self: Self, v: str | None) -> None:
        self._set_property(FACILITY_PROP, v, pop_if_none=True)

    @property
    def version(self: Self) -> str | None:
        return self._get_property(VERSION_PROP, str)

    @version.setter
    def version(self: Self, v: str | None) -> None:
        self._set_property(VERSION_PROP, v, pop_if_none=True)

    @property
    def software(self: Self) -> str | None:
        return self._get_property(SOFTWARE_PROP, str)

    @software.setter
    def software(self: Self, v: str | None) -> None:
        self._set_property(SOFTWARE_PROP, v, pop_if_none=True)

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
