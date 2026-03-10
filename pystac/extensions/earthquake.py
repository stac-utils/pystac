"""Implementation of the STAC :stac-ext:`Earthquake Extension <earthquake>`."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Generic, Literal, TypedDict, TypeVar, cast

import pystac
from pystac.errors import ExtensionTypeError
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension
from pystac.extensions.hooks import ExtensionHooks

# ----------------------------
# STAC Earthquake extension
# ----------------------------

SCHEMA_URI: str = "https://stac-extensions.github.io/earthquake/v1.0.0/schema.json"

MAGNITUDE_PROP = "eq:magnitude"
MAGNITUDE_TYPE_PROP = "eq:magnitude_type"
FELT_PROP = "eq:felt"
STATUS_PROP = "eq:status"
TSUNAMI_PROP = "eq:tsunami"
SOURCES_PROP = "eq:sources"
DEPTH_PROP = "eq:depth"

MagnitudeType = Literal[
    "mww",
    "mwc",
    "mwb",
    "ms",
    "mb",
    "mfa",
    "ml",
    "mlg",
    "md",
    "mwp",
    "me",
    "mh",
]
StatusType = Literal["automatic", "reviewed", "deleted"]


class EarthquakeSource(TypedDict, total=False):
    """A single source entry stored in :data:`eq:sources <SOURCES_PROP>`."""

    name: str  # required by schema
    code: str  # required by schema
    catalog: str  # optional by schema


def _validate_magnitude(v: float | None) -> float | None:
    if v is None:
        return None
    if not (0 <= v <= 20):
        raise ValueError(f"{MAGNITUDE_PROP} must be in [0, 20]. Got: {v}")
    return float(v)


def _validate_felt(v: int | None) -> int | None:
    if v is None:
        return None
    if v < 0:
        raise ValueError(f"{FELT_PROP} must be >= 0. Got: {v}")
    return int(v)


def _validate_sources(
    v: list[EarthquakeSource] | None,
) -> list[EarthquakeSource] | None:
    if v is None:
        return None
    if len(v) < 1:
        raise ValueError(f"{SOURCES_PROP} must have at least 1 source.")
    for i, s in enumerate(v):
        if "name" not in s or "code" not in s:
            raise ValueError(
                f"{SOURCES_PROP}[{i}] must include required keys "
                f"'name' and 'code'. Got: {s}"
            )
        if not isinstance(s["name"], str) or not s["name"]:
            raise ValueError(f"{SOURCES_PROP}[{i}].name must be a non-empty string.")
        if not isinstance(s["code"], str) or not s["code"]:
            raise ValueError(f"{SOURCES_PROP}[{i}].code must be a non-empty string.")
        if "catalog" in s and (not isinstance(s["catalog"], str) or not s["catalog"]):
            raise ValueError(
                f"{SOURCES_PROP}[{i}].catalog must be a non-empty string if set."
            )
    return v


T = TypeVar("T", pystac.Item, pystac.Asset, pystac.ItemAssetDefinition)


class EarthquakeExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """
    Implements the STAC Earthquake Extension for Items and also supports reading/writing
    extension fields on Assets and Collection Item Asset Definitions.

    Schema: https://stac-extensions.github.io/earthquake/v1.0.0/schema.json
    """

    # Use the extension's field prefix as the name to match existing PySTAC patterns.
    name: Literal["eq"] = "eq"

    # ---- schema hooks ----
    @classmethod
    def get_schema_uri(cls) -> str:
        """Return the published schema URI for this extension."""
        return SCHEMA_URI

    # ---- factory ----
    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> EarthquakeExtension[T]:
        """
        Extend an Item, Asset, or ItemAssetDefinition with earthquake fields.

        Args:
            obj: The PySTAC object to wrap.
            add_if_missing: If ``True``, add the earthquake schema URI to the owning
                Item or Collection before returning the extension wrapper.
        """
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(EarthquakeExtension[T], ItemEarthquakeExtension(obj))
        if isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(EarthquakeExtension[T], AssetEarthquakeExtension(obj))
        if isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(EarthquakeExtension[T], ItemAssetsEarthquakeExtension(obj))

        raise ExtensionTypeError(cls._ext_error_message(obj))

    # ---- convenience ----
    def apply(
        self,
        *,
        magnitude: float,
        sources: list[EarthquakeSource],
        magnitude_type: MagnitudeType | None = None,
        felt: int | None = None,
        status: StatusType | None = None,
        tsunami: bool | None = None,
        depth: float | None = None,
    ) -> None:
        """
        Apply earthquake fields to the wrapped object.

        Note: schema marks `eq:magnitude` and `eq:sources` as required.
        """
        self.magnitude = magnitude
        self.sources = sources
        self.magnitude_type = magnitude_type
        self.felt = felt
        self.status = status
        self.tsunami = tsunami
        self.depth = depth

    # ---- properties ----
    @property
    def magnitude(self) -> float | None:
        """Magnitude of the earthquake event."""
        return self._get_property(MAGNITUDE_PROP, float)

    @magnitude.setter
    def magnitude(self, v: float | None) -> None:
        self._set_property(MAGNITUDE_PROP, _validate_magnitude(v), pop_if_none=True)

    @property
    def magnitude_type(self) -> MagnitudeType | None:
        """Magnitude scale used to compute :attr:`magnitude`."""
        return cast(
            MagnitudeType | None,
            self._get_property(MAGNITUDE_TYPE_PROP, str),
        )

    @magnitude_type.setter
    def magnitude_type(self, v: MagnitudeType | None) -> None:
        self._set_property(MAGNITUDE_TYPE_PROP, v, pop_if_none=True)

    @property
    def felt(self) -> int | None:
        """Reported number of people who felt the event."""
        return self._get_property(FELT_PROP, int)

    @felt.setter
    def felt(self, v: int | None) -> None:
        self._set_property(FELT_PROP, _validate_felt(v), pop_if_none=True)

    @property
    def status(self) -> StatusType | None:
        """Review status of the event metadata."""
        return cast(StatusType | None, self._get_property(STATUS_PROP, str))

    @status.setter
    def status(self, v: StatusType | None) -> None:
        self._set_property(STATUS_PROP, v, pop_if_none=True)

    @property
    def tsunami(self) -> bool | None:
        """Whether the event was associated with a tsunami."""
        return self._get_property(TSUNAMI_PROP, bool)

    @tsunami.setter
    def tsunami(self, v: bool | None) -> None:
        self._set_property(TSUNAMI_PROP, v, pop_if_none=True)

    @property
    def depth(self) -> float | None:
        """Depth of the event in kilometers."""
        return self._get_property(DEPTH_PROP, float)

    @depth.setter
    def depth(self, v: float | None) -> None:
        # schema only says "number" (no range); keep permissive
        self._set_property(
            DEPTH_PROP,
            None if v is None else float(v),
            pop_if_none=True,
        )

    @property
    def sources(self) -> list[EarthquakeSource] | None:
        """Provider-specific source records associated with this event."""
        return self._get_property(SOURCES_PROP, list[dict[str, Any]])  # type: ignore[return-value]

    @sources.setter
    def sources(self, v: list[EarthquakeSource] | None) -> None:
        self._set_property(SOURCES_PROP, _validate_sources(v), pop_if_none=True)


class ItemEarthquakeExtension(EarthquakeExtension[pystac.Item]):
    """Concrete earthquake implementation for :class:`~pystac.Item` objects."""

    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemEarthquakeExtension Item id={self.item.id}>"


class AssetEarthquakeExtension(EarthquakeExtension[pystac.Asset]):
    """Concrete earthquake implementation for :class:`~pystac.Asset` objects."""

    asset_href: str
    properties: dict[str, Any]
    additional_read_properties: Iterable[dict[str, Any]] | None = None

    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        # allow reads to fall back to Item properties (common PySTAC pattern)
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return f"<AssetEarthquakeExtension Asset href={self.asset_href}>"


class ItemAssetsEarthquakeExtension(EarthquakeExtension[pystac.ItemAssetDefinition]):
    """Concrete earthquake implementation for item asset definitions."""

    asset_defn: pystac.ItemAssetDefinition
    properties: dict[str, Any]

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        self.asset_defn = item_asset
        self.properties = item_asset.properties


class EarthquakeExtensionHooks(ExtensionHooks):
    """Hook registration used when reading or migrating STAC objects."""

    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"earthquake", "eq"}
    stac_object_types = {
        pystac.STACObjectType.COLLECTION,
        pystac.STACObjectType.ITEM,
    }


EARTHQUAKE_EXTENSION_HOOKS: ExtensionHooks = EarthquakeExtensionHooks()
