"""Implements the :stac-ext:`Sentinel-2 Extension <sentinel-2>`."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Generic, Literal, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.summaries import RangeSummary
from pystac.utils import datetime_to_str, map_opt, str_to_datetime

T = TypeVar("T", bound=pystac.Item)

SCHEMA_URI = "https://stac-extensions.github.io/sentinel-2/v1.0.0/schema.json"

PREFIX = "s2:"
TILE_ID_PROP = PREFIX + "tile_id"
GRANULE_ID_PROP = PREFIX + "granule_id"
DATATAKE_ID_PROP = PREFIX + "datatake_id"
PRODUCT_URI_PROP = PREFIX + "product_uri"
DATASTRIP_ID_PROP = PREFIX + "datastrip_id"
PRODUCT_TYPE_PROP = PREFIX + "product_type"
DATATAKE_TYPE_PROP = PREFIX + "datatake_type"
GENERATION_TIME_PROP = PREFIX + "generation_time"
PROCESSING_BASELINE_PROP = PREFIX + "processing_baseline"
WATER_PERCENTAGE_PROP = PREFIX + "water_percentage"
MEAN_SOLAR_ZENITH_PROP = PREFIX + "mean_solar_zenith"
MEAN_SOLAR_AZIMUTH_PROP = PREFIX + "mean_solar_azimuth"
SNOW_ICE_PERCENTAGE_PROP = PREFIX + "snow_ice_percentage"
VEGETATION_PERCENTAGE_PROP = PREFIX + "vegetation_percentage"
THIN_CIRRUS_PERCENTAGE_PROP = PREFIX + "thin_cirrus_percentage"
CLOUD_SHADOW_PERCENTAGE_PROP = PREFIX + "cloud_shadow_percentage"
NODATA_PIXEL_PERCENTAGE_PROP = PREFIX + "nodata_pixel_percentage"
UNCLASSIFIED_PERCENTAGE_PROP = PREFIX + "unclassified_percentage"
DARK_FEATURES_PERCENTAGE_PROP = PREFIX + "dark_features_percentage"
NOT_VEGETATED_PERCENTAGE_PROP = PREFIX + "not_vegetated_percentage"
DEGRADED_MSI_DATA_PERCENTAGE_PROP = PREFIX + "degraded_msi_data_percentage"
HIGH_PROBA_CLOUDS_PERCENTAGE_PROP = PREFIX + "high_proba_clouds_percentage"
MEDIUM_PROBA_CLOUDS_PERCENTAGE_PROP = PREFIX + "medium_proba_clouds_percentage"
SATURATED_DEFECTIVE_PIXEL_PERCENTAGE_PROP = (
    PREFIX + "saturated_defective_pixel_percentage"
)
REFLECTANCE_CONVERSION_FACTOR_PROP = PREFIX + "reflectance_conversion_factor"
MGRS_TILE_PROP = PREFIX + "mgrs_tile"

PROCESSING_BASELINE_RE = re.compile(r"^\d\d\.\d\d$")
MGRS_TILE_RE = re.compile(
    r"^\d\d?[CDEFGHJKLMNPQRSTUVWX][ABCDEFGHJKLMNPQRSTUVWXYZ][ABCDEFGHJKLMNPQRSTUV]$"
)


def _validate_range(
    prop_name: str, v: float | None, minimum: float, maximum: float
) -> float | None:
    if v is None:
        return None
    if not minimum <= v <= maximum:
        raise ValueError(f"{prop_name} must be in [{minimum}, {maximum}]. Got: {v}")
    return float(v)


def _validate_processing_baseline(v: str | None) -> str | None:
    if v is None:
        return None
    if not PROCESSING_BASELINE_RE.match(v):
        raise ValueError(
            f"{PROCESSING_BASELINE_PROP} must match NN.NN. Got: {v}"
        )
    return v


def _validate_mgrs_tile(v: str | None) -> str | None:
    if v is None:
        return None
    if not MGRS_TILE_RE.match(v):
        raise ValueError(f"{MGRS_TILE_PROP} is not a valid Sentinel-2 MGRS tile: {v}")
    return v


class Sentinel2Extension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """Extension API for the Sentinel-2 extension."""

    name: Literal["s2"] = "s2"

    def apply(
        self,
        tile_id: str | None = None,
        granule_id: str | None = None,
        datatake_id: str | None = None,
        product_uri: str | None = None,
        datastrip_id: str | None = None,
        product_type: str | None = None,
        datatake_type: str | None = None,
        generation_time: datetime | None = None,
        processing_baseline: str | None = None,
        water_percentage: float | None = None,
        mean_solar_zenith: float | None = None,
        mean_solar_azimuth: float | None = None,
        snow_ice_percentage: float | None = None,
        vegetation_percentage: float | None = None,
        thin_cirrus_percentage: float | None = None,
        cloud_shadow_percentage: float | None = None,
        nodata_pixel_percentage: float | None = None,
        unclassified_percentage: float | None = None,
        dark_features_percentage: float | None = None,
        not_vegetated_percentage: float | None = None,
        degraded_msi_data_percentage: float | None = None,
        high_proba_clouds_percentage: float | None = None,
        medium_proba_clouds_percentage: float | None = None,
        saturated_defective_pixel_percentage: float | None = None,
        reflectance_conversion_factor: float | None = None,
        mgrs_tile: str | None = None,
    ) -> None:
        self.tile_id = tile_id
        self.granule_id = granule_id
        self.datatake_id = datatake_id
        self.product_uri = product_uri
        self.datastrip_id = datastrip_id
        self.product_type = product_type
        self.datatake_type = datatake_type
        self.generation_time = generation_time
        self.processing_baseline = processing_baseline
        self.water_percentage = water_percentage
        self.mean_solar_zenith = mean_solar_zenith
        self.mean_solar_azimuth = mean_solar_azimuth
        self.snow_ice_percentage = snow_ice_percentage
        self.vegetation_percentage = vegetation_percentage
        self.thin_cirrus_percentage = thin_cirrus_percentage
        self.cloud_shadow_percentage = cloud_shadow_percentage
        self.nodata_pixel_percentage = nodata_pixel_percentage
        self.unclassified_percentage = unclassified_percentage
        self.dark_features_percentage = dark_features_percentage
        self.not_vegetated_percentage = not_vegetated_percentage
        self.degraded_msi_data_percentage = degraded_msi_data_percentage
        self.high_proba_clouds_percentage = high_proba_clouds_percentage
        self.medium_proba_clouds_percentage = medium_proba_clouds_percentage
        self.saturated_defective_pixel_percentage = (
            saturated_defective_pixel_percentage
        )
        self.reflectance_conversion_factor = reflectance_conversion_factor
        self.mgrs_tile = mgrs_tile

    @property
    def tile_id(self) -> str | None:
        return self._get_property(TILE_ID_PROP, str)

    @tile_id.setter
    def tile_id(self, v: str | None) -> None:
        self._set_property(TILE_ID_PROP, v)

    @property
    def granule_id(self) -> str | None:
        return self._get_property(GRANULE_ID_PROP, str)

    @granule_id.setter
    def granule_id(self, v: str | None) -> None:
        self._set_property(GRANULE_ID_PROP, v)

    @property
    def datatake_id(self) -> str | None:
        return self._get_property(DATATAKE_ID_PROP, str)

    @datatake_id.setter
    def datatake_id(self, v: str | None) -> None:
        self._set_property(DATATAKE_ID_PROP, v)

    @property
    def product_uri(self) -> str | None:
        return self._get_property(PRODUCT_URI_PROP, str)

    @product_uri.setter
    def product_uri(self, v: str | None) -> None:
        self._set_property(PRODUCT_URI_PROP, v)

    @property
    def datastrip_id(self) -> str | None:
        return self._get_property(DATASTRIP_ID_PROP, str)

    @datastrip_id.setter
    def datastrip_id(self, v: str | None) -> None:
        self._set_property(DATASTRIP_ID_PROP, v)

    @property
    def product_type(self) -> str | None:
        return self._get_property(PRODUCT_TYPE_PROP, str)

    @product_type.setter
    def product_type(self, v: str | None) -> None:
        self._set_property(PRODUCT_TYPE_PROP, v)

    @property
    def datatake_type(self) -> str | None:
        return self._get_property(DATATAKE_TYPE_PROP, str)

    @datatake_type.setter
    def datatake_type(self, v: str | None) -> None:
        self._set_property(DATATAKE_TYPE_PROP, v)

    @property
    def generation_time(self) -> datetime | None:
        return map_opt(str_to_datetime, self._get_property(GENERATION_TIME_PROP, str))

    @generation_time.setter
    def generation_time(self, v: datetime | None) -> None:
        self._set_property(GENERATION_TIME_PROP, map_opt(datetime_to_str, v))

    @property
    def processing_baseline(self) -> str | None:
        return self._get_property(PROCESSING_BASELINE_PROP, str)

    @processing_baseline.setter
    def processing_baseline(self, v: str | None) -> None:
        self._set_property(PROCESSING_BASELINE_PROP, _validate_processing_baseline(v))

    @property
    def water_percentage(self) -> float | None:
        return self._get_property(WATER_PERCENTAGE_PROP, float)

    @water_percentage.setter
    def water_percentage(self, v: float | None) -> None:
        self._set_property(
            WATER_PERCENTAGE_PROP,
            _validate_range(WATER_PERCENTAGE_PROP, v, 0, 100),
        )

    @property
    def mean_solar_zenith(self) -> float | None:
        return self._get_property(MEAN_SOLAR_ZENITH_PROP, float)

    @mean_solar_zenith.setter
    def mean_solar_zenith(self, v: float | None) -> None:
        self._set_property(
            MEAN_SOLAR_ZENITH_PROP,
            _validate_range(MEAN_SOLAR_ZENITH_PROP, v, 0, 180),
        )

    @property
    def mean_solar_azimuth(self) -> float | None:
        return self._get_property(MEAN_SOLAR_AZIMUTH_PROP, float)

    @mean_solar_azimuth.setter
    def mean_solar_azimuth(self, v: float | None) -> None:
        self._set_property(
            MEAN_SOLAR_AZIMUTH_PROP,
            _validate_range(MEAN_SOLAR_AZIMUTH_PROP, v, 0, 180),
        )

    @property
    def snow_ice_percentage(self) -> float | None:
        return self._get_property(SNOW_ICE_PERCENTAGE_PROP, float)

    @snow_ice_percentage.setter
    def snow_ice_percentage(self, v: float | None) -> None:
        self._set_property(
            SNOW_ICE_PERCENTAGE_PROP,
            _validate_range(SNOW_ICE_PERCENTAGE_PROP, v, 0, 100),
        )

    @property
    def vegetation_percentage(self) -> float | None:
        return self._get_property(VEGETATION_PERCENTAGE_PROP, float)

    @vegetation_percentage.setter
    def vegetation_percentage(self, v: float | None) -> None:
        self._set_property(
            VEGETATION_PERCENTAGE_PROP,
            _validate_range(VEGETATION_PERCENTAGE_PROP, v, 0, 100),
        )

    @property
    def thin_cirrus_percentage(self) -> float | None:
        return self._get_property(THIN_CIRRUS_PERCENTAGE_PROP, float)

    @thin_cirrus_percentage.setter
    def thin_cirrus_percentage(self, v: float | None) -> None:
        self._set_property(
            THIN_CIRRUS_PERCENTAGE_PROP,
            _validate_range(THIN_CIRRUS_PERCENTAGE_PROP, v, 0, 100),
        )

    @property
    def cloud_shadow_percentage(self) -> float | None:
        return self._get_property(CLOUD_SHADOW_PERCENTAGE_PROP, float)

    @cloud_shadow_percentage.setter
    def cloud_shadow_percentage(self, v: float | None) -> None:
        self._set_property(
            CLOUD_SHADOW_PERCENTAGE_PROP,
            _validate_range(CLOUD_SHADOW_PERCENTAGE_PROP, v, 0, 100),
        )

    @property
    def nodata_pixel_percentage(self) -> float | None:
        return self._get_property(NODATA_PIXEL_PERCENTAGE_PROP, float)

    @nodata_pixel_percentage.setter
    def nodata_pixel_percentage(self, v: float | None) -> None:
        self._set_property(
            NODATA_PIXEL_PERCENTAGE_PROP,
            _validate_range(NODATA_PIXEL_PERCENTAGE_PROP, v, 0, 100),
        )

    @property
    def unclassified_percentage(self) -> float | None:
        return self._get_property(UNCLASSIFIED_PERCENTAGE_PROP, float)

    @unclassified_percentage.setter
    def unclassified_percentage(self, v: float | None) -> None:
        self._set_property(
            UNCLASSIFIED_PERCENTAGE_PROP,
            _validate_range(UNCLASSIFIED_PERCENTAGE_PROP, v, 0, 100),
        )

    @property
    def dark_features_percentage(self) -> float | None:
        return self._get_property(DARK_FEATURES_PERCENTAGE_PROP, float)

    @dark_features_percentage.setter
    def dark_features_percentage(self, v: float | None) -> None:
        self._set_property(
            DARK_FEATURES_PERCENTAGE_PROP,
            _validate_range(DARK_FEATURES_PERCENTAGE_PROP, v, 0, 100),
        )

    @property
    def not_vegetated_percentage(self) -> float | None:
        return self._get_property(NOT_VEGETATED_PERCENTAGE_PROP, float)

    @not_vegetated_percentage.setter
    def not_vegetated_percentage(self, v: float | None) -> None:
        self._set_property(
            NOT_VEGETATED_PERCENTAGE_PROP,
            _validate_range(NOT_VEGETATED_PERCENTAGE_PROP, v, 0, 100),
        )

    @property
    def degraded_msi_data_percentage(self) -> float | None:
        return self._get_property(DEGRADED_MSI_DATA_PERCENTAGE_PROP, float)

    @degraded_msi_data_percentage.setter
    def degraded_msi_data_percentage(self, v: float | None) -> None:
        self._set_property(
            DEGRADED_MSI_DATA_PERCENTAGE_PROP,
            _validate_range(DEGRADED_MSI_DATA_PERCENTAGE_PROP, v, 0, 100),
        )

    @property
    def high_proba_clouds_percentage(self) -> float | None:
        return self._get_property(HIGH_PROBA_CLOUDS_PERCENTAGE_PROP, float)

    @high_proba_clouds_percentage.setter
    def high_proba_clouds_percentage(self, v: float | None) -> None:
        self._set_property(
            HIGH_PROBA_CLOUDS_PERCENTAGE_PROP,
            _validate_range(HIGH_PROBA_CLOUDS_PERCENTAGE_PROP, v, 0, 100),
        )

    @property
    def medium_proba_clouds_percentage(self) -> float | None:
        return self._get_property(MEDIUM_PROBA_CLOUDS_PERCENTAGE_PROP, float)

    @medium_proba_clouds_percentage.setter
    def medium_proba_clouds_percentage(self, v: float | None) -> None:
        self._set_property(
            MEDIUM_PROBA_CLOUDS_PERCENTAGE_PROP,
            _validate_range(MEDIUM_PROBA_CLOUDS_PERCENTAGE_PROP, v, 0, 100),
        )

    @property
    def saturated_defective_pixel_percentage(self) -> float | None:
        return self._get_property(SATURATED_DEFECTIVE_PIXEL_PERCENTAGE_PROP, float)

    @saturated_defective_pixel_percentage.setter
    def saturated_defective_pixel_percentage(self, v: float | None) -> None:
        self._set_property(
            SATURATED_DEFECTIVE_PIXEL_PERCENTAGE_PROP,
            _validate_range(SATURATED_DEFECTIVE_PIXEL_PERCENTAGE_PROP, v, 0, 100),
        )

    @property
    def reflectance_conversion_factor(self) -> float | None:
        return self._get_property(REFLECTANCE_CONVERSION_FACTOR_PROP, float)

    @reflectance_conversion_factor.setter
    def reflectance_conversion_factor(self, v: float | None) -> None:
        self._set_property(REFLECTANCE_CONVERSION_FACTOR_PROP, v)

    @property
    def mgrs_tile(self) -> str | None:
        return self._get_property(MGRS_TILE_PROP, str)

    @mgrs_tile.setter
    def mgrs_tile(self, v: str | None) -> None:
        self._set_property(MGRS_TILE_PROP, _validate_mgrs_tile(v))

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> Sentinel2Extension[T]:
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(Sentinel2Extension[T], ItemSentinel2Extension(obj))
        raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesSentinel2Extension:
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesSentinel2Extension(obj)


class ItemSentinel2Extension(Sentinel2Extension[pystac.Item]):
    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemSentinel2Extension Item id={self.item.id}>"


class SummariesSentinel2Extension(SummariesExtension):
    @property
    def tile_id(self) -> list[str] | None:
        return self.summaries.get_list(TILE_ID_PROP)

    @tile_id.setter
    def tile_id(self, v: list[str] | None) -> None:
        self._set_summary(TILE_ID_PROP, v)

    @property
    def granule_id(self) -> list[str] | None:
        return self.summaries.get_list(GRANULE_ID_PROP)

    @granule_id.setter
    def granule_id(self, v: list[str] | None) -> None:
        self._set_summary(GRANULE_ID_PROP, v)

    @property
    def datatake_id(self) -> list[str] | None:
        return self.summaries.get_list(DATATAKE_ID_PROP)

    @datatake_id.setter
    def datatake_id(self, v: list[str] | None) -> None:
        self._set_summary(DATATAKE_ID_PROP, v)

    @property
    def product_uri(self) -> list[str] | None:
        return self.summaries.get_list(PRODUCT_URI_PROP)

    @product_uri.setter
    def product_uri(self, v: list[str] | None) -> None:
        self._set_summary(PRODUCT_URI_PROP, v)

    @property
    def datastrip_id(self) -> list[str] | None:
        return self.summaries.get_list(DATASTRIP_ID_PROP)

    @datastrip_id.setter
    def datastrip_id(self, v: list[str] | None) -> None:
        self._set_summary(DATASTRIP_ID_PROP, v)

    @property
    def product_type(self) -> list[str] | None:
        return self.summaries.get_list(PRODUCT_TYPE_PROP)

    @product_type.setter
    def product_type(self, v: list[str] | None) -> None:
        self._set_summary(PRODUCT_TYPE_PROP, v)

    @property
    def datatake_type(self) -> list[str] | None:
        return self.summaries.get_list(DATATAKE_TYPE_PROP)

    @datatake_type.setter
    def datatake_type(self, v: list[str] | None) -> None:
        self._set_summary(DATATAKE_TYPE_PROP, v)

    @property
    def generation_time(self) -> RangeSummary[datetime] | None:
        return map_opt(
            lambda s: RangeSummary(
                str_to_datetime(s.minimum), str_to_datetime(s.maximum)
            ),
            self.summaries.get_range(GENERATION_TIME_PROP),
        )

    @generation_time.setter
    def generation_time(self, v: RangeSummary[datetime] | None) -> None:
        self._set_summary(
            GENERATION_TIME_PROP,
            map_opt(
                lambda s: RangeSummary(
                    datetime_to_str(s.minimum), datetime_to_str(s.maximum)
                ),
                v,
            ),
        )

    @property
    def processing_baseline(self) -> list[str] | None:
        return self.summaries.get_list(PROCESSING_BASELINE_PROP)

    @processing_baseline.setter
    def processing_baseline(self, v: list[str] | None) -> None:
        self._set_summary(PROCESSING_BASELINE_PROP, v)

    @property
    def water_percentage(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(WATER_PERCENTAGE_PROP)

    @water_percentage.setter
    def water_percentage(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(WATER_PERCENTAGE_PROP, v)

    @property
    def mean_solar_zenith(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(MEAN_SOLAR_ZENITH_PROP)

    @mean_solar_zenith.setter
    def mean_solar_zenith(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(MEAN_SOLAR_ZENITH_PROP, v)

    @property
    def mean_solar_azimuth(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(MEAN_SOLAR_AZIMUTH_PROP)

    @mean_solar_azimuth.setter
    def mean_solar_azimuth(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(MEAN_SOLAR_AZIMUTH_PROP, v)

    @property
    def snow_ice_percentage(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(SNOW_ICE_PERCENTAGE_PROP)

    @snow_ice_percentage.setter
    def snow_ice_percentage(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(SNOW_ICE_PERCENTAGE_PROP, v)

    @property
    def vegetation_percentage(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(VEGETATION_PERCENTAGE_PROP)

    @vegetation_percentage.setter
    def vegetation_percentage(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(VEGETATION_PERCENTAGE_PROP, v)

    @property
    def thin_cirrus_percentage(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(THIN_CIRRUS_PERCENTAGE_PROP)

    @thin_cirrus_percentage.setter
    def thin_cirrus_percentage(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(THIN_CIRRUS_PERCENTAGE_PROP, v)

    @property
    def cloud_shadow_percentage(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(CLOUD_SHADOW_PERCENTAGE_PROP)

    @cloud_shadow_percentage.setter
    def cloud_shadow_percentage(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(CLOUD_SHADOW_PERCENTAGE_PROP, v)

    @property
    def nodata_pixel_percentage(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(NODATA_PIXEL_PERCENTAGE_PROP)

    @nodata_pixel_percentage.setter
    def nodata_pixel_percentage(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(NODATA_PIXEL_PERCENTAGE_PROP, v)

    @property
    def unclassified_percentage(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(UNCLASSIFIED_PERCENTAGE_PROP)

    @unclassified_percentage.setter
    def unclassified_percentage(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(UNCLASSIFIED_PERCENTAGE_PROP, v)

    @property
    def dark_features_percentage(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(DARK_FEATURES_PERCENTAGE_PROP)

    @dark_features_percentage.setter
    def dark_features_percentage(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(DARK_FEATURES_PERCENTAGE_PROP, v)

    @property
    def not_vegetated_percentage(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(NOT_VEGETATED_PERCENTAGE_PROP)

    @not_vegetated_percentage.setter
    def not_vegetated_percentage(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(NOT_VEGETATED_PERCENTAGE_PROP, v)

    @property
    def degraded_msi_data_percentage(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(DEGRADED_MSI_DATA_PERCENTAGE_PROP)

    @degraded_msi_data_percentage.setter
    def degraded_msi_data_percentage(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(DEGRADED_MSI_DATA_PERCENTAGE_PROP, v)

    @property
    def high_proba_clouds_percentage(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(HIGH_PROBA_CLOUDS_PERCENTAGE_PROP)

    @high_proba_clouds_percentage.setter
    def high_proba_clouds_percentage(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(HIGH_PROBA_CLOUDS_PERCENTAGE_PROP, v)

    @property
    def medium_proba_clouds_percentage(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(MEDIUM_PROBA_CLOUDS_PERCENTAGE_PROP)

    @medium_proba_clouds_percentage.setter
    def medium_proba_clouds_percentage(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(MEDIUM_PROBA_CLOUDS_PERCENTAGE_PROP, v)

    @property
    def saturated_defective_pixel_percentage(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(SATURATED_DEFECTIVE_PIXEL_PERCENTAGE_PROP)

    @saturated_defective_pixel_percentage.setter
    def saturated_defective_pixel_percentage(
        self, v: RangeSummary[float] | None
    ) -> None:
        self._set_summary(SATURATED_DEFECTIVE_PIXEL_PERCENTAGE_PROP, v)

    @property
    def reflectance_conversion_factor(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(REFLECTANCE_CONVERSION_FACTOR_PROP)

    @reflectance_conversion_factor.setter
    def reflectance_conversion_factor(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(REFLECTANCE_CONVERSION_FACTOR_PROP, v)

    @property
    def mgrs_tile(self) -> list[str] | None:
        return self.summaries.get_list(MGRS_TILE_PROP)

    @mgrs_tile.setter
    def mgrs_tile(self, v: list[str] | None) -> None:
        self._set_summary(MGRS_TILE_PROP, v)


class Sentinel2ExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"sentinel-2"}
    stac_object_types = {
        pystac.STACObjectType.ITEM,
        pystac.STACObjectType.COLLECTION,
    }


SENTINEL2_EXTENSION_HOOKS: ExtensionHooks = Sentinel2ExtensionHooks()
