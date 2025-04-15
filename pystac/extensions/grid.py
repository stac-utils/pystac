"""Implements the :stac-ext:`Grid Extension <grid>`."""

from __future__ import annotations

import re
import warnings
from re import Pattern
from typing import Any, Literal

import pystac
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension
from pystac.extensions.hooks import ExtensionHooks

SCHEMA_URI: str = "https://stac-extensions.github.io/grid/v1.1.0/schema.json"
SCHEMA_URIS: list[str] = [
    "https://stac-extensions.github.io/grid/v1.0.0/schema.json",
    SCHEMA_URI,
]
PREFIX: str = "grid:"

# Field names
CODE_PROP: str = PREFIX + "code"  # required

CODE_REGEX: str = r"[A-Z0-9]+-[-_.A-Za-z0-9]+"
CODE_PATTERN: Pattern[str] = re.compile(CODE_REGEX)


def validated_code(v: str) -> str:
    if not isinstance(v, str):
        raise ValueError("Invalid Grid code: must be str")
    if not CODE_PATTERN.fullmatch(v):
        raise ValueError(
            f"Invalid Grid code: {v} does not match the regex {CODE_REGEX}"
        )
    return v


class GridExtension(
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """A concrete implementation of :class:`~pystac.extensions.grid.GridExtension`
    on an :class:`~pystac.Item`
    that extends the properties of the Item to include properties defined in the
    :stac-ext:`Grid Extension <grid>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`~pystac.extensions.grid.GridExtension.ext` on an :class:`~pystac.Item`
    to extend it.

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> proj_ext = GridExtension.ext(item)
    """

    name: Literal["grid"] = "grid"

    item: pystac.Item
    """The :class:`~pystac.Item` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemGridExtension Item id={self.item.id}>"

    def apply(self, code: str) -> None:
        """Applies Grid extension properties to the extended Item.

        Args:
            code : REQUIRED. The code of the Item's grid location.
        """
        self.code = validated_code(code)

    @property
    def code(self) -> str | None:
        """Get or sets the grid code of the datasource."""
        return self._get_property(CODE_PROP, str)

    @code.setter
    def code(self, v: str) -> None:
        self._set_property(CODE_PROP, validated_code(v), pop_if_none=False)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def get_schema_uris(cls) -> list[str]:
        warnings.warn(
            "get_schema_uris is deprecated and will be removed in v2",
            DeprecationWarning,
        )
        return SCHEMA_URIS

    @classmethod
    def ext(cls, obj: pystac.Item, add_if_missing: bool = False) -> GridExtension:
        """Extends the given STAC Object with properties from the :stac-ext:`Grid
        Extension <grid>`.

        This extension can be applied to instances of :class:`~pystac.Item`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return GridExtension(obj)
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))


class GridExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: set[str] = {*[uri for uri in SCHEMA_URIS if uri != SCHEMA_URI]}
    stac_object_types = {pystac.STACObjectType.ITEM}


GRID_EXTENSION_HOOKS: ExtensionHooks = GridExtensionHooks()
