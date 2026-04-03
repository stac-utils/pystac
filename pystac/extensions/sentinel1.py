"""Implements the :stac-ext:`Sentinel-1 Extension <sentinel-1>`."""

from __future__ import annotations

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

SCHEMA_URI = "https://stac-extensions.github.io/sentinel-1/v0.2.0/schema.json"

PREFIX = "s1:"
DATATAKE_ID_PROP = PREFIX + "datatake_id"
INSTRUMENT_CONFIGURATION_ID_PROP = PREFIX + "instrument_configuration_ID"
ORBIT_SOURCE_PROP = PREFIX + "orbit_source"
PROCESSING_DATETIME_PROP = PREFIX + "processing_datetime"
PRODUCT_IDENTIFIER_PROP = PREFIX + "product_identifier"
PRODUCT_TIMELINESS_PROP = PREFIX + "product_timeliness"
RESOLUTION_PROP = PREFIX + "resolution"
SLICE_NUMBER_PROP = PREFIX + "slice_number"
TOTAL_SLICES_PROP = PREFIX + "total_slices"
PROCESSING_LEVEL_PROP = PREFIX + "processing_level"
SHAPE_PROP = PREFIX + "shape"


def _validate_shape(v: list[int] | None) -> list[int] | None:
    if v is None:
        return None
    if len(v) < 2:
        raise ValueError(f"{SHAPE_PROP} must contain at least two integers.")
    if not all(isinstance(x, int) for x in v):
        raise ValueError(f"{SHAPE_PROP} must contain only integers.")
    return v


class Sentinel1Extension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """Extension API for the Sentinel-1 extension."""

    name: Literal["s1"] = "s1"

    def apply(
        self,
        datatake_id: str | None = None,
        instrument_configuration_id: str | None = None,
        orbit_source: str | None = None,
        processing_datetime: datetime | None = None,
        product_identifier: str | None = None,
        product_timeliness: str | None = None,
        resolution: str | None = None,
        slice_number: str | None = None,
        total_slices: str | None = None,
        processing_level: str | None = None,
        shape: list[int] | None = None,
    ) -> None:
        self.datatake_id = datatake_id
        self.instrument_configuration_id = instrument_configuration_id
        self.orbit_source = orbit_source
        self.processing_datetime = processing_datetime
        self.product_identifier = product_identifier
        self.product_timeliness = product_timeliness
        self.resolution = resolution
        self.slice_number = slice_number
        self.total_slices = total_slices
        self.processing_level = processing_level
        self.shape = shape

    @property
    def datatake_id(self) -> str | None:
        return self._get_property(DATATAKE_ID_PROP, str)

    @datatake_id.setter
    def datatake_id(self, v: str | None) -> None:
        self._set_property(DATATAKE_ID_PROP, v)

    @property
    def instrument_configuration_id(self) -> str | None:
        return self._get_property(INSTRUMENT_CONFIGURATION_ID_PROP, str)

    @instrument_configuration_id.setter
    def instrument_configuration_id(self, v: str | None) -> None:
        self._set_property(INSTRUMENT_CONFIGURATION_ID_PROP, v)

    @property
    def orbit_source(self) -> str | None:
        return self._get_property(ORBIT_SOURCE_PROP, str)

    @orbit_source.setter
    def orbit_source(self, v: str | None) -> None:
        self._set_property(ORBIT_SOURCE_PROP, v)

    @property
    def processing_datetime(self) -> datetime | None:
        return map_opt(
            str_to_datetime, self._get_property(PROCESSING_DATETIME_PROP, str)
        )

    @processing_datetime.setter
    def processing_datetime(self, v: datetime | None) -> None:
        self._set_property(PROCESSING_DATETIME_PROP, map_opt(datetime_to_str, v))

    @property
    def product_identifier(self) -> str | None:
        return self._get_property(PRODUCT_IDENTIFIER_PROP, str)

    @product_identifier.setter
    def product_identifier(self, v: str | None) -> None:
        self._set_property(PRODUCT_IDENTIFIER_PROP, v)

    @property
    def product_timeliness(self) -> str | None:
        return self._get_property(PRODUCT_TIMELINESS_PROP, str)

    @product_timeliness.setter
    def product_timeliness(self, v: str | None) -> None:
        self._set_property(PRODUCT_TIMELINESS_PROP, v)

    @property
    def resolution(self) -> str | None:
        return self._get_property(RESOLUTION_PROP, str)

    @resolution.setter
    def resolution(self, v: str | None) -> None:
        self._set_property(RESOLUTION_PROP, v)

    @property
    def slice_number(self) -> str | None:
        return self._get_property(SLICE_NUMBER_PROP, str)

    @slice_number.setter
    def slice_number(self, v: str | None) -> None:
        self._set_property(SLICE_NUMBER_PROP, v)

    @property
    def total_slices(self) -> str | None:
        return self._get_property(TOTAL_SLICES_PROP, str)

    @total_slices.setter
    def total_slices(self, v: str | None) -> None:
        self._set_property(TOTAL_SLICES_PROP, v)

    @property
    def processing_level(self) -> str | None:
        return self._get_property(PROCESSING_LEVEL_PROP, str)

    @processing_level.setter
    def processing_level(self, v: str | None) -> None:
        self._set_property(PROCESSING_LEVEL_PROP, v)

    @property
    def shape(self) -> list[int] | None:
        return self._get_property(SHAPE_PROP, list)

    @shape.setter
    def shape(self, v: list[int] | None) -> None:
        self._set_property(SHAPE_PROP, _validate_shape(v))

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> Sentinel1Extension[T]:
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(Sentinel1Extension[T], ItemSentinel1Extension(obj))
        raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesSentinel1Extension:
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesSentinel1Extension(obj)


class ItemSentinel1Extension(Sentinel1Extension[pystac.Item]):
    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemSentinel1Extension Item id={self.item.id}>"


class SummariesSentinel1Extension(SummariesExtension):
    @property
    def datatake_id(self) -> list[str] | None:
        return self.summaries.get_list(DATATAKE_ID_PROP)

    @datatake_id.setter
    def datatake_id(self, v: list[str] | None) -> None:
        self._set_summary(DATATAKE_ID_PROP, v)

    @property
    def instrument_configuration_id(self) -> list[str] | None:
        return self.summaries.get_list(INSTRUMENT_CONFIGURATION_ID_PROP)

    @instrument_configuration_id.setter
    def instrument_configuration_id(self, v: list[str] | None) -> None:
        self._set_summary(INSTRUMENT_CONFIGURATION_ID_PROP, v)

    @property
    def orbit_source(self) -> list[str] | None:
        return self.summaries.get_list(ORBIT_SOURCE_PROP)

    @orbit_source.setter
    def orbit_source(self, v: list[str] | None) -> None:
        self._set_summary(ORBIT_SOURCE_PROP, v)

    @property
    def processing_datetime(self) -> RangeSummary[datetime] | None:
        return map_opt(
            lambda s: RangeSummary(
                str_to_datetime(s.minimum), str_to_datetime(s.maximum)
            ),
            self.summaries.get_range(PROCESSING_DATETIME_PROP),
        )

    @processing_datetime.setter
    def processing_datetime(self, v: RangeSummary[datetime] | None) -> None:
        self._set_summary(
            PROCESSING_DATETIME_PROP,
            map_opt(
                lambda s: RangeSummary(
                    datetime_to_str(s.minimum), datetime_to_str(s.maximum)
                ),
                v,
            ),
        )

    @property
    def product_identifier(self) -> list[str] | None:
        return self.summaries.get_list(PRODUCT_IDENTIFIER_PROP)

    @product_identifier.setter
    def product_identifier(self, v: list[str] | None) -> None:
        self._set_summary(PRODUCT_IDENTIFIER_PROP, v)

    @property
    def product_timeliness(self) -> list[str] | None:
        return self.summaries.get_list(PRODUCT_TIMELINESS_PROP)

    @product_timeliness.setter
    def product_timeliness(self, v: list[str] | None) -> None:
        self._set_summary(PRODUCT_TIMELINESS_PROP, v)

    @property
    def resolution(self) -> list[str] | None:
        return self.summaries.get_list(RESOLUTION_PROP)

    @resolution.setter
    def resolution(self, v: list[str] | None) -> None:
        self._set_summary(RESOLUTION_PROP, v)

    @property
    def slice_number(self) -> list[str] | None:
        return self.summaries.get_list(SLICE_NUMBER_PROP)

    @slice_number.setter
    def slice_number(self, v: list[str] | None) -> None:
        self._set_summary(SLICE_NUMBER_PROP, v)

    @property
    def total_slices(self) -> list[str] | None:
        return self.summaries.get_list(TOTAL_SLICES_PROP)

    @total_slices.setter
    def total_slices(self, v: list[str] | None) -> None:
        self._set_summary(TOTAL_SLICES_PROP, v)

    @property
    def processing_level(self) -> list[str] | None:
        return self.summaries.get_list(PROCESSING_LEVEL_PROP)

    @processing_level.setter
    def processing_level(self, v: list[str] | None) -> None:
        self._set_summary(PROCESSING_LEVEL_PROP, v)

    @property
    def shape(self) -> list[list[int]] | None:
        return self.summaries.get_list(SHAPE_PROP)

    @shape.setter
    def shape(self, v: list[list[int]] | None) -> None:
        self._set_summary(SHAPE_PROP, v)


class Sentinel1ExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"sentinel-1"}
    stac_object_types = {
        pystac.STACObjectType.ITEM,
        pystac.STACObjectType.COLLECTION,
    }


SENTINEL1_EXTENSION_HOOKS: ExtensionHooks = Sentinel1ExtensionHooks()
