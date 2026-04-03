"""Implements the :stac-ext:`Sentinel-3 Extension <sentinel-3>`."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Generic, Literal, TypedDict, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.summaries import RangeSummary

T = TypeVar("T", pystac.Item, pystac.Asset, pystac.ItemAssetDefinition)

SCHEMA_URI = "https://stac-extensions.github.io/sentinel-3/v0.2.0/schema.json"

PREFIX = "s3:"
PRODUCT_TYPE_PROP = PREFIX + "product_type"
PRODUCT_NAME_PROP = PREFIX + "product_name"
PROCESSING_TIMELINESS_PROP = PREFIX + "processing_timeliness"
GSD_PROP = PREFIX + "gsd"
LRM_MODE_PROP = PREFIX + "lrm_mode"
SAR_MODE_PROP = PREFIX + "sar_mode"
BRIGHT_PROP = PREFIX + "bright"
CLOSED_SEA_PROP = PREFIX + "closed_sea"
COASTAL_PROP = PREFIX + "coastal"
CONTINENTAL_ICE_PROP = PREFIX + "continental_ice"
COSMETIC_PROP = PREFIX + "cosmetic"
DUBIOUS_SAMPLES_PROP = PREFIX + "dubious_samples"
DUPLICATED_PROP = PREFIX + "duplicated"
FRESH_INLAND_WATER_PROP = PREFIX + "fresh_inland_water"
INVALID_PROP = PREFIX + "invalid"
LAND_PROP = PREFIX + "land"
OPEN_OCEAN_PROP = PREFIX + "open_ocean"
OUT_OF_RANGE_PROP = PREFIX + "out_of_range"
SALINE_WATER_PROP = PREFIX + "saline_water"
SATURATED_PROP = PREFIX + "saturated"
TIDAL_REGION_PROP = PREFIX + "tidal_region"
SNOW_OR_ICE_PROP = PREFIX + "snow_or_ice"

SHAPE_PROP = PREFIX + "shape"
SPATIAL_RESOLUTION_PROP = PREFIX + "spatial_resolution"
ALTIMETRY_BANDS_PROP = PREFIX + "altimetry_bands"


SRALGSD = TypedDict(
    "SRALGSD",
    {
        "along-track": int,
        "across-track": int,
    },
)
"""GSD object for SRAL products."""


SLSTRGSD = TypedDict(
    "SLSTRGSD",
    {
        "S1-S6": int,
        "S7-S9 and F1-F2": int,
    },
)
"""GSD object for SLSTR products."""


class SynergyGSD(TypedDict):
    """GSD object for synergy products."""

    OLCI: int
    SLSTR: SLSTRGSD


class AltimetryBand(TypedDict, total=False):
    """Altimetry band description for Sentinel-3 assets."""

    band_width: float
    description: str
    frequency_band: str
    center_frequency: float


S3GSD = int | SRALGSD | SLSTRGSD | SynergyGSD


def _validate_int_list(prop_name: str, v: list[int] | None) -> list[int] | None:
    if v is None:
        return None
    if not all(isinstance(x, int) for x in v):
        raise ValueError(f"{prop_name} must contain only integers.")
    return v


def _validate_altimetry_bands(
    v: list[AltimetryBand] | None,
) -> list[AltimetryBand] | None:
    if v is None:
        return None
    for i, band in enumerate(v):
        for key in band.keys():
            if key not in {
                "band_width",
                "description",
                "frequency_band",
                "center_frequency",
            }:
                raise ValueError(f"{ALTIMETRY_BANDS_PROP}[{i}] has invalid key {key}.")
    return v


class Sentinel3Extension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """Extension API for the Sentinel-3 extension."""

    name: Literal["s3"] = "s3"

    def apply(
        self,
        product_type: str | None = None,
        product_name: str | None = None,
        processing_timeliness: str | None = None,
        gsd: S3GSD | None = None,
        lrm_mode: float | None = None,
        sar_mode: float | None = None,
        bright: float | None = None,
        closed_sea: float | None = None,
        coastal: float | None = None,
        continental_ice: float | None = None,
        cosmetic: float | None = None,
        dubious_samples: float | None = None,
        duplicated: float | None = None,
        fresh_inland_water: float | None = None,
        invalid: float | None = None,
        land: float | None = None,
        open_ocean: float | None = None,
        out_of_range: float | None = None,
        saline_water: float | None = None,
        saturated: float | None = None,
        tidal_region: float | None = None,
        snow_or_ice: float | None = None,
        shape: list[int] | None = None,
        spatial_resolution: list[int] | None = None,
        altimetry_bands: list[AltimetryBand] | None = None,
    ) -> None:
        self.product_type = product_type
        self.product_name = product_name
        self.processing_timeliness = processing_timeliness
        self.gsd = gsd
        self.lrm_mode = lrm_mode
        self.sar_mode = sar_mode
        self.bright = bright
        self.closed_sea = closed_sea
        self.coastal = coastal
        self.continental_ice = continental_ice
        self.cosmetic = cosmetic
        self.dubious_samples = dubious_samples
        self.duplicated = duplicated
        self.fresh_inland_water = fresh_inland_water
        self.invalid = invalid
        self.land = land
        self.open_ocean = open_ocean
        self.out_of_range = out_of_range
        self.saline_water = saline_water
        self.saturated = saturated
        self.tidal_region = tidal_region
        self.snow_or_ice = snow_or_ice
        self.shape = shape
        self.spatial_resolution = spatial_resolution
        self.altimetry_bands = altimetry_bands

    @property
    def product_type(self) -> str | None:
        return self._get_property(PRODUCT_TYPE_PROP, str)

    @product_type.setter
    def product_type(self, v: str | None) -> None:
        self._set_property(PRODUCT_TYPE_PROP, v)

    @property
    def product_name(self) -> str | None:
        return self._get_property(PRODUCT_NAME_PROP, str)

    @product_name.setter
    def product_name(self, v: str | None) -> None:
        self._set_property(PRODUCT_NAME_PROP, v)

    @property
    def processing_timeliness(self) -> str | None:
        return self._get_property(PROCESSING_TIMELINESS_PROP, str)

    @processing_timeliness.setter
    def processing_timeliness(self, v: str | None) -> None:
        self._set_property(PROCESSING_TIMELINESS_PROP, v)

    @property
    def gsd(self) -> S3GSD | None:
        return self._get_property(GSD_PROP, dict) or self._get_property(GSD_PROP, int)

    @gsd.setter
    def gsd(self, v: S3GSD | None) -> None:
        self._set_property(GSD_PROP, v)

    @property
    def lrm_mode(self) -> float | None:
        return self._get_property(LRM_MODE_PROP, float)

    @lrm_mode.setter
    def lrm_mode(self, v: float | None) -> None:
        self._set_property(LRM_MODE_PROP, v)

    @property
    def sar_mode(self) -> float | None:
        return self._get_property(SAR_MODE_PROP, float)

    @sar_mode.setter
    def sar_mode(self, v: float | None) -> None:
        self._set_property(SAR_MODE_PROP, v)

    @property
    def bright(self) -> float | None:
        return self._get_property(BRIGHT_PROP, float)

    @bright.setter
    def bright(self, v: float | None) -> None:
        self._set_property(BRIGHT_PROP, v)

    @property
    def closed_sea(self) -> float | None:
        return self._get_property(CLOSED_SEA_PROP, float)

    @closed_sea.setter
    def closed_sea(self, v: float | None) -> None:
        self._set_property(CLOSED_SEA_PROP, v)

    @property
    def coastal(self) -> float | None:
        return self._get_property(COASTAL_PROP, float)

    @coastal.setter
    def coastal(self, v: float | None) -> None:
        self._set_property(COASTAL_PROP, v)

    @property
    def continental_ice(self) -> float | None:
        return self._get_property(CONTINENTAL_ICE_PROP, float)

    @continental_ice.setter
    def continental_ice(self, v: float | None) -> None:
        self._set_property(CONTINENTAL_ICE_PROP, v)

    @property
    def cosmetic(self) -> float | None:
        return self._get_property(COSMETIC_PROP, float)

    @cosmetic.setter
    def cosmetic(self, v: float | None) -> None:
        self._set_property(COSMETIC_PROP, v)

    @property
    def dubious_samples(self) -> float | None:
        return self._get_property(DUBIOUS_SAMPLES_PROP, float)

    @dubious_samples.setter
    def dubious_samples(self, v: float | None) -> None:
        self._set_property(DUBIOUS_SAMPLES_PROP, v)

    @property
    def duplicated(self) -> float | None:
        return self._get_property(DUPLICATED_PROP, float)

    @duplicated.setter
    def duplicated(self, v: float | None) -> None:
        self._set_property(DUPLICATED_PROP, v)

    @property
    def fresh_inland_water(self) -> float | None:
        return self._get_property(FRESH_INLAND_WATER_PROP, float)

    @fresh_inland_water.setter
    def fresh_inland_water(self, v: float | None) -> None:
        self._set_property(FRESH_INLAND_WATER_PROP, v)

    @property
    def invalid(self) -> float | None:
        return self._get_property(INVALID_PROP, float)

    @invalid.setter
    def invalid(self, v: float | None) -> None:
        self._set_property(INVALID_PROP, v)

    @property
    def land(self) -> float | None:
        return self._get_property(LAND_PROP, float)

    @land.setter
    def land(self, v: float | None) -> None:
        self._set_property(LAND_PROP, v)

    @property
    def open_ocean(self) -> float | None:
        return self._get_property(OPEN_OCEAN_PROP, float)

    @open_ocean.setter
    def open_ocean(self, v: float | None) -> None:
        self._set_property(OPEN_OCEAN_PROP, v)

    @property
    def out_of_range(self) -> float | None:
        return self._get_property(OUT_OF_RANGE_PROP, float)

    @out_of_range.setter
    def out_of_range(self, v: float | None) -> None:
        self._set_property(OUT_OF_RANGE_PROP, v)

    @property
    def saline_water(self) -> float | None:
        return self._get_property(SALINE_WATER_PROP, float)

    @saline_water.setter
    def saline_water(self, v: float | None) -> None:
        self._set_property(SALINE_WATER_PROP, v)

    @property
    def saturated(self) -> float | None:
        return self._get_property(SATURATED_PROP, float)

    @saturated.setter
    def saturated(self, v: float | None) -> None:
        self._set_property(SATURATED_PROP, v)

    @property
    def tidal_region(self) -> float | None:
        return self._get_property(TIDAL_REGION_PROP, float)

    @tidal_region.setter
    def tidal_region(self, v: float | None) -> None:
        self._set_property(TIDAL_REGION_PROP, v)

    @property
    def snow_or_ice(self) -> float | None:
        return self._get_property(SNOW_OR_ICE_PROP, float)

    @snow_or_ice.setter
    def snow_or_ice(self, v: float | None) -> None:
        self._set_property(SNOW_OR_ICE_PROP, v)

    @property
    def shape(self) -> list[int] | None:
        return self._get_property(SHAPE_PROP, list)

    @shape.setter
    def shape(self, v: list[int] | None) -> None:
        self._set_property(SHAPE_PROP, _validate_int_list(SHAPE_PROP, v))

    @property
    def spatial_resolution(self) -> list[int] | None:
        return self._get_property(SPATIAL_RESOLUTION_PROP, list)

    @spatial_resolution.setter
    def spatial_resolution(self, v: list[int] | None) -> None:
        self._set_property(
            SPATIAL_RESOLUTION_PROP,
            _validate_int_list(SPATIAL_RESOLUTION_PROP, v),
        )

    @property
    def altimetry_bands(self) -> list[AltimetryBand] | None:
        return self._get_property(ALTIMETRY_BANDS_PROP, list)

    @altimetry_bands.setter
    def altimetry_bands(self, v: list[AltimetryBand] | None) -> None:
        self._set_property(ALTIMETRY_BANDS_PROP, _validate_altimetry_bands(v))

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> Sentinel3Extension[T]:
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(Sentinel3Extension[T], ItemSentinel3Extension(obj))
        if isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(Sentinel3Extension[T], AssetSentinel3Extension(obj))
        if isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(Sentinel3Extension[T], ItemAssetsSentinel3Extension(obj))
        raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesSentinel3Extension:
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesSentinel3Extension(obj)


class ItemSentinel3Extension(Sentinel3Extension[pystac.Item]):
    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemSentinel3Extension Item id={self.item.id}>"


class AssetSentinel3Extension(Sentinel3Extension[pystac.Asset]):
    asset_href: str
    properties: dict[str, Any]
    additional_read_properties: Iterable[dict[str, Any]] | None = None

    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return f"<AssetSentinel3Extension Asset href={self.asset_href}>"


class ItemAssetsSentinel3Extension(Sentinel3Extension[pystac.ItemAssetDefinition]):
    properties: dict[str, Any]
    asset_defn: pystac.ItemAssetDefinition

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        self.asset_defn = item_asset
        self.properties = item_asset.properties


class SummariesSentinel3Extension(SummariesExtension):
    @property
    def product_type(self) -> list[str] | None:
        return self.summaries.get_list(PRODUCT_TYPE_PROP)

    @product_type.setter
    def product_type(self, v: list[str] | None) -> None:
        self._set_summary(PRODUCT_TYPE_PROP, v)

    @property
    def product_name(self) -> list[str] | None:
        return self.summaries.get_list(PRODUCT_NAME_PROP)

    @product_name.setter
    def product_name(self, v: list[str] | None) -> None:
        self._set_summary(PRODUCT_NAME_PROP, v)

    @property
    def processing_timeliness(self) -> list[str] | None:
        return self.summaries.get_list(PROCESSING_TIMELINESS_PROP)

    @processing_timeliness.setter
    def processing_timeliness(self, v: list[str] | None) -> None:
        self._set_summary(PROCESSING_TIMELINESS_PROP, v)

    @property
    def gsd(self) -> list[Any] | None:
        return self.summaries.get_list(GSD_PROP)

    @gsd.setter
    def gsd(self, v: list[Any] | None) -> None:
        self._set_summary(GSD_PROP, v)

    @property
    def lrm_mode(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(LRM_MODE_PROP)

    @lrm_mode.setter
    def lrm_mode(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(LRM_MODE_PROP, v)

    @property
    def sar_mode(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(SAR_MODE_PROP)

    @sar_mode.setter
    def sar_mode(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(SAR_MODE_PROP, v)

    @property
    def bright(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(BRIGHT_PROP)

    @bright.setter
    def bright(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(BRIGHT_PROP, v)

    @property
    def closed_sea(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(CLOSED_SEA_PROP)

    @closed_sea.setter
    def closed_sea(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(CLOSED_SEA_PROP, v)

    @property
    def coastal(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(COASTAL_PROP)

    @coastal.setter
    def coastal(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(COASTAL_PROP, v)

    @property
    def continental_ice(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(CONTINENTAL_ICE_PROP)

    @continental_ice.setter
    def continental_ice(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(CONTINENTAL_ICE_PROP, v)

    @property
    def cosmetic(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(COSMETIC_PROP)

    @cosmetic.setter
    def cosmetic(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(COSMETIC_PROP, v)

    @property
    def dubious_samples(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(DUBIOUS_SAMPLES_PROP)

    @dubious_samples.setter
    def dubious_samples(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(DUBIOUS_SAMPLES_PROP, v)

    @property
    def duplicated(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(DUPLICATED_PROP)

    @duplicated.setter
    def duplicated(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(DUPLICATED_PROP, v)

    @property
    def fresh_inland_water(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(FRESH_INLAND_WATER_PROP)

    @fresh_inland_water.setter
    def fresh_inland_water(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(FRESH_INLAND_WATER_PROP, v)

    @property
    def invalid(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(INVALID_PROP)

    @invalid.setter
    def invalid(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(INVALID_PROP, v)

    @property
    def land(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(LAND_PROP)

    @land.setter
    def land(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(LAND_PROP, v)

    @property
    def open_ocean(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(OPEN_OCEAN_PROP)

    @open_ocean.setter
    def open_ocean(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(OPEN_OCEAN_PROP, v)

    @property
    def out_of_range(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(OUT_OF_RANGE_PROP)

    @out_of_range.setter
    def out_of_range(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(OUT_OF_RANGE_PROP, v)

    @property
    def saline_water(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(SALINE_WATER_PROP)

    @saline_water.setter
    def saline_water(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(SALINE_WATER_PROP, v)

    @property
    def saturated(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(SATURATED_PROP)

    @saturated.setter
    def saturated(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(SATURATED_PROP, v)

    @property
    def tidal_region(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(TIDAL_REGION_PROP)

    @tidal_region.setter
    def tidal_region(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(TIDAL_REGION_PROP, v)

    @property
    def snow_or_ice(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(SNOW_OR_ICE_PROP)

    @snow_or_ice.setter
    def snow_or_ice(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(SNOW_OR_ICE_PROP, v)


class Sentinel3ExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"sentinel-3"}
    stac_object_types = {
        pystac.STACObjectType.ITEM,
        pystac.STACObjectType.COLLECTION,
    }


SENTINEL3_EXTENSION_HOOKS: ExtensionHooks = Sentinel3ExtensionHooks()
