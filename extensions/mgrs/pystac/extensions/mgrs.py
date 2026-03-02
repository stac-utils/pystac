"""Implements the :stac-ext:`MGRS Extension <mgrs>`."""

import re
from re import Pattern
from typing import Any, Literal

import pystac
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension
from pystac.extensions.hooks import ExtensionHooks

SCHEMA_URI: str = "https://stac-extensions.github.io/mgrs/v1.0.0/schema.json"
SCHEMA_STARTSWITH: str = "https://stac-extensions.github.io/mgrs/"
PREFIX: str = "mgrs:"

# Field names
LATITUDE_BAND_PROP: str = PREFIX + "latitude_band"  # required
GRID_SQUARE_PROP: str = PREFIX + "grid_square"  # required
UTM_ZONE_PROP: str = PREFIX + "utm_zone"

LATITUDE_BANDS: frozenset[str] = frozenset(
    {
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "J",
        "K",
        "L",
        "M",
        "N",
        "P",
        "Q",
        "R",
        "S",
        "T",
        "U",
        "V",
        "W",
        "X",
    }
)

UTM_ZONES: frozenset[int] = frozenset(
    {
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32,
        33,
        34,
        35,
        36,
        37,
        38,
        39,
        40,
        41,
        42,
        43,
        44,
        45,
        46,
        47,
        48,
        49,
        50,
        51,
        52,
        53,
        54,
        55,
        56,
        57,
        58,
        59,
        60,
    }
)

GRID_SQUARE_REGEX: str = (
    r"[ABCDEFGHJKLMNPQRSTUVWXYZ][ABCDEFGHJKLMNPQRSTUV](\d{2}|\d{4}|\d{6}|\d{8}|\d{10})?"
)
GRID_SQUARE_PATTERN: Pattern[str] = re.compile(GRID_SQUARE_REGEX)


def validated_latitude_band(v: str) -> str:
    if not isinstance(v, str):
        raise ValueError("Invalid MGRS latitude band: must be str")
    if v not in LATITUDE_BANDS:
        raise ValueError(f"Invalid MGRS latitude band: {v} is not in {LATITUDE_BANDS}")
    return v


def validated_grid_square(v: str) -> str:
    if not isinstance(v, str):
        raise ValueError("Invalid MGRS grid square identifier: must be str")
    if not GRID_SQUARE_PATTERN.fullmatch(v):
        raise ValueError(
            f"Invalid MGRS grid square identifier: {v}"
            f" does not match the regex {GRID_SQUARE_REGEX}"
        )
    return v


def validated_utm_zone(v: int | None) -> int | None:
    if v is not None and not isinstance(v, int):
        raise ValueError("Invalid MGRS utm zone: must be None or int")
    if v is not None and v not in UTM_ZONES:
        raise ValueError(f"Invalid MGRS UTM zone: {v} is not in {UTM_ZONES}")
    return v


class MgrsExtension(
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """A concrete implementation of :class:`~pystac.extensions.mgrs.MgrsExtension`
    on an :class:`~pystac.Item`
    that extends the properties of the Item to include properties defined in the
    :stac-ext:`MGRS Extension <mgrs>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`~pystac.extensions.mgrs.MgrsExtension.ext` on an :class:`~pystac.Item`
    to extend it.

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> proj_ext = MgrsExtension.ext(item)
    """

    name: Literal["mgrs"] = "mgrs"
    item: pystac.Item
    """The :class:`~pystac.Item` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemMgrsExtension Item id={self.item.id}>"

    def apply(
        self,
        latitude_band: str,
        grid_square: str,
        utm_zone: int | None = None,
    ) -> None:
        """Applies MGRS extension properties to the extended Item.

        Args:
            latitude_band : REQUIRED. The latitude band of the Item's centroid.
            grid_square : REQUIRED. MGRS grid square of the Item's centroid.
            utm_zone : The UTM Zone of the Item centroid.
        """
        self.latitude_band = validated_latitude_band(latitude_band)
        self.grid_square = validated_grid_square(grid_square)
        self.utm_zone = validated_utm_zone(utm_zone)

    @property
    def latitude_band(self) -> str | None:
        """Get or sets the latitude band of the datasource."""
        return self._get_property(LATITUDE_BAND_PROP, str)

    @latitude_band.setter
    def latitude_band(self, v: str) -> None:
        self._set_property(
            LATITUDE_BAND_PROP, validated_latitude_band(v), pop_if_none=False
        )

    @property
    def grid_square(self) -> str | None:
        """Get or sets the latitude band of the datasource."""
        return self._get_property(GRID_SQUARE_PROP, str)

    @grid_square.setter
    def grid_square(self, v: str) -> None:
        self._set_property(
            GRID_SQUARE_PROP, validated_grid_square(v), pop_if_none=False
        )

    @property
    def utm_zone(self) -> int | None:
        """Get or sets the latitude band of the datasource."""
        return self._get_property(UTM_ZONE_PROP, int)

    @utm_zone.setter
    def utm_zone(self, v: int | None) -> None:
        self._set_property(UTM_ZONE_PROP, validated_utm_zone(v), pop_if_none=True)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: pystac.Item, add_if_missing: bool = False) -> "MgrsExtension":
        """Extends the given STAC Object with properties from the :stac-ext:`MGRS
        Extension <mgrs>`.

        This extension can be applied to instances of :class:`~pystac.Item`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return MgrsExtension(obj)
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))


class MgrsExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: set[str] = set()
    stac_object_types = {pystac.STACObjectType.ITEM}


MGRS_EXTENSION_HOOKS: ExtensionHooks = MgrsExtensionHooks()
