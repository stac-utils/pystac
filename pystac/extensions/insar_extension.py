from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Literal, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.utils import datetime_to_str, map_opt, str_to_datetime


SCHEMA_URI: str = "https://stac-extensions.github.io/insar/v1.0.0/schema.json"
PREFIX: str = "insar:"

PERP_BASELINE_PROP: str = PREFIX + "perpendicular_baseline"
TEMP_BASELINE_PROP: str = PREFIX + "temporal_baseline"
HOA_PROP: str = PREFIX + "height_of_ambiguity"
REF_DT_PROP: str = PREFIX + "reference_datetime"
SEC_DT_PROP: str = PREFIX + "secondary_datetime"
PROC_DEM_PROP: str = PREFIX + "processing_dem"
GEOC_DEM_PROP: str = PREFIX + "geocoding_dem"

T = TypeVar("T", pystac.Item, pystac.Asset, pystac.ItemAssetDefinition)


def _validated_number(v: float | int | None, field: str) -> float | None:
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"Invalid {field}: expected a number, got {type(v).__name__}")
    return float(v)


def _validated_str(v: str | None, field: str) -> str | None:
    if v is None:
        return None
    if not isinstance(v, str):
        raise ValueError(f"Invalid {field}: expected a string, got {type(v).__name__}")
    return v


class InsarExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """
    Item/Asset/ItemAssetDefinition InSAR properties.
    For Collection-level support, use InsarExtension.summaries(collection, ...).
    """

    name: Literal["insar"] = "insar"

    # ---------------- schema plumbing ----------------

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    # ---------------- factories ----------------

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> "InsarExtension[T]":
        """
        Applies to:
          - Item (properties)
          - Asset (extra_fields) [Item assets AND Collection assets are allowed by schema]  :contentReference[oaicite:2]{index=2}
          - ItemAssetDefinition (collection.item_assets[*].properties)
        """
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(InsarExtension[T], ItemInsarExtension(obj))

        if isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(InsarExtension[T], AssetInsarExtension(obj))

        if isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(InsarExtension[T], ItemAssetsInsarExtension(obj))

        # Keep the same user experience as SAR: Collection uses .summaries(...) instead. :contentReference[oaicite:3]{index=3}
        if isinstance(obj, pystac.Collection):  # type: ignore[unreachable]
            raise pystac.ExtensionTypeError(
                "InSAR extension does not apply to type 'Collection'. "
                "Hint: Did you mean to use `InsarExtension.summaries` instead?"
            )

        raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> "SummariesInsarExtension":
        """
        Collection-level InSAR lives under `collection.summaries` per updated schema. :contentReference[oaicite:4]{index=4}
        """
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesInsarExtension(obj)

    # ---------------- item/asset properties ----------------

    def apply(
        self,
        *,
        perpendicular_baseline: float | int | None = None,
        temporal_baseline: float | int | None = None,
        height_of_ambiguity: float | int | None = None,
        reference_datetime: datetime | None = None,
        secondary_datetime: datetime | None = None,
        processing_dem: str | None = None,
        geocoding_dem: str | None = None,
    ) -> None:
        self.perpendicular_baseline = perpendicular_baseline
        self.temporal_baseline = temporal_baseline
        self.height_of_ambiguity = height_of_ambiguity
        self.reference_datetime = reference_datetime
        self.secondary_datetime = secondary_datetime
        self.processing_dem = processing_dem
        self.geocoding_dem = geocoding_dem

    @property
    def perpendicular_baseline(self) -> float | None:
        return self._get_property(PERP_BASELINE_PROP, float)

    @perpendicular_baseline.setter
    def perpendicular_baseline(self, v: float | int | None) -> None:
        self._set_property(
            PERP_BASELINE_PROP, _validated_number(v, PERP_BASELINE_PROP), pop_if_none=True
        )

    @property
    def temporal_baseline(self) -> float | None:
        return self._get_property(TEMP_BASELINE_PROP, float)

    @temporal_baseline.setter
    def temporal_baseline(self, v: float | int | None) -> None:
        self._set_property(
            TEMP_BASELINE_PROP, _validated_number(v, TEMP_BASELINE_PROP), pop_if_none=True
        )

    @property
    def height_of_ambiguity(self) -> float | None:
        return self._get_property(HOA_PROP, float)

    @height_of_ambiguity.setter
    def height_of_ambiguity(self, v: float | int | None) -> None:
        self._set_property(HOA_PROP, _validated_number(v, HOA_PROP), pop_if_none=True)

    @property
    def reference_datetime(self) -> datetime | None:
        return map_opt(str_to_datetime, self._get_property(REF_DT_PROP, str))

    @reference_datetime.setter
    def reference_datetime(self, v: datetime | None) -> None:
        self._set_property(REF_DT_PROP, map_opt(datetime_to_str, v), pop_if_none=True)

    @property
    def secondary_datetime(self) -> datetime | None:
        return map_opt(str_to_datetime, self._get_property(SEC_DT_PROP, str))

    @secondary_datetime.setter
    def secondary_datetime(self, v: datetime | None) -> None:
        self._set_property(SEC_DT_PROP, map_opt(datetime_to_str, v), pop_if_none=True)

    @property
    def processing_dem(self) -> str | None:
        return self._get_property(PROC_DEM_PROP, str)

    @processing_dem.setter
    def processing_dem(self, v: str | None) -> None:
        self._set_property(PROC_DEM_PROP, _validated_str(v, PROC_DEM_PROP), pop_if_none=True)

    @property
    def geocoding_dem(self) -> str | None:
        return self._get_property(GEOC_DEM_PROP, str)

    @geocoding_dem.setter
    def geocoding_dem(self, v: str | None) -> None:
        self._set_property(GEOC_DEM_PROP, _validated_str(v, GEOC_DEM_PROP), pop_if_none=True)


class ItemInsarExtension(InsarExtension[pystac.Item]):
    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemInsarExtension Item id={self.item.id}>"


class AssetInsarExtension(InsarExtension[pystac.Asset]):
    asset_href: str
    properties: dict[str, Any]

    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields

    def __repr__(self) -> str:
        return f"<AssetInsarExtension Asset href={self.asset_href}>"


class ItemAssetsInsarExtension(InsarExtension[pystac.ItemAssetDefinition]):
    asset_defn: pystac.ItemAssetDefinition
    properties: dict[str, Any]

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        self.asset_defn = item_asset
        self.properties = item_asset.properties

    def __repr__(self) -> str:
        return "<ItemAssetsInsarExtension ItemAssetDefinition>"


class SummariesInsarExtension(SummariesExtension):
    """
    Collection summaries InSAR: supports
      - insar:reference_datetime
      - insar:processing_dem
      - insar:geocoding_dem

    IMPORTANT: STAC core requires summaries values to be array/range/schema.
    We therefore store singleton values as 1-element arrays.
    """

    def _get_singleton_list_value(self, key: str) -> Any | None:
        lst = self.summaries.get_list(key)
        if lst is None:
            return None
        if len(lst) == 0:
            return None
        # If multiple values exist, you can decide whether to raise or return first.
        return lst[0]

    def _set_singleton_list_value(self, key: str, value: Any | None) -> None:
        if value is None:
            self.summaries.remove(key)
            return
        # Store as "Set of values" (array) to satisfy core Collection schema
        self.summaries.add(key, [value])

    def apply(
        self,
        *,
        reference_datetime: datetime | None = None,
        processing_dem: str | None = None,
        geocoding_dem: str | None = None,
    ) -> None:
        self.reference_datetime = reference_datetime
        self.processing_dem = processing_dem
        self.geocoding_dem = geocoding_dem

    @property
    def reference_datetime(self) -> datetime | None:
        raw = self._get_singleton_list_value(REF_DT_PROP)
        if raw is None:
            return None
        if isinstance(raw, str):
            return str_to_datetime(raw)
        raise ValueError(
            f"Invalid {REF_DT_PROP} summary: expected RFC3339 string in list, got {type(raw).__name__}"
        )

    @reference_datetime.setter
    def reference_datetime(self, v: datetime | None) -> None:
        self._set_singleton_list_value(REF_DT_PROP, map_opt(datetime_to_str, v))

    @property
    def processing_dem(self) -> str | None:
        raw = self._get_singleton_list_value(PROC_DEM_PROP)
        if raw is None:
            return None
        if isinstance(raw, str):
            return raw
        raise ValueError(
            f"Invalid {PROC_DEM_PROP} summary: expected string in list, got {type(raw).__name__}"
        )

    @processing_dem.setter
    def processing_dem(self, v: str | None) -> None:
        self._set_singleton_list_value(PROC_DEM_PROP, _validated_str(v, PROC_DEM_PROP))

    @property
    def geocoding_dem(self) -> str | None:
        raw = self._get_singleton_list_value(GEOC_DEM_PROP)
        if raw is None:
            return None
        if isinstance(raw, str):
            return raw
        raise ValueError(
            f"Invalid {GEOC_DEM_PROP} summary: expected string in list, got {type(raw).__name__}"
        )

    @geocoding_dem.setter
    def geocoding_dem(self, v: str | None) -> None:
        self._set_singleton_list_value(GEOC_DEM_PROP, _validated_str(v, GEOC_DEM_PROP))
