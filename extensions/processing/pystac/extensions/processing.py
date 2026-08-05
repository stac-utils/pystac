"""Implements the :stac-ext:`Processing Extension <processing>`."""

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
from pystac.utils import datetime_to_str, get_required, map_opt, str_to_datetime

SCHEMA_URI: str = "https://stac-extensions.github.io/processing/v1.2.0/schema.json"

PREFIX: str = "processing:"
EXPRESSION_PROP: str = PREFIX + "expression"
LINEAGE_PROP: str = PREFIX + "lineage"
LEVEL_PROP: str = PREFIX + "level"
FACILITY_PROP: str = PREFIX + "facility"
SOFTWARE_PROP: str = PREFIX + "software"
VERSION_PROP: str = PREFIX + "version"
DATETIME_PROP: str = PREFIX + "datetime"

T = TypeVar("T", pystac.Item, pystac.Asset, pystac.ItemAssetDefinition)


class ProcessingExpression:
    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]) -> None:
        self.properties = properties

    @property
    def format(self) -> str:
        return cast(str, get_required(self.properties.get("format"), self, "format"))

    @format.setter
    def format(self, v: str) -> None:
        self.properties["format"] = v

    @property
    def expression(self) -> Any:
        return get_required(self.properties.get("expression"), self, "expression")

    @expression.setter
    def expression(self, v: Any) -> None:
        self.properties["expression"] = v

    def apply(self, format: str, expression: Any) -> None:
        self.format = format
        self.expression = expression

    @classmethod
    def create(cls, format: str, expression: Any) -> ProcessingExpression:
        pe = cls({})
        pe.apply(format=format, expression=expression)
        return pe

    def to_dict(self) -> dict[str, Any]:
        return self.properties

    def __repr__(self) -> str:
        return f"<ProcessingExpression format={self.properties.get('format')!r}>"


class ProcessingExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    name: Literal["processing"] = "processing"

    def apply(
        self,
        expression: ProcessingExpression | dict[str, Any] | None = None,
        lineage: str | None = None,
        level: str | None = None,
        facility: str | None = None,
        software: dict[str, str] | None = None,
        version: str | None = None,
        processing_datetime: datetime | None = None,
    ) -> None:
        self.expression = expression
        self.lineage = lineage
        self.level = level
        self.facility = facility
        self.software = software
        self.version = version
        self.processing_datetime = processing_datetime

    @property
    def expression(self) -> ProcessingExpression | None:
        return map_opt(
            lambda d: ProcessingExpression(cast(dict[str, Any], d)),
            self._get_property(EXPRESSION_PROP, dict),
        )

    @expression.setter
    def expression(self, v: ProcessingExpression | dict[str, Any] | None) -> None:
        if isinstance(v, ProcessingExpression):
            self._set_property(EXPRESSION_PROP, v.to_dict())
            return
        self._set_property(EXPRESSION_PROP, v)

    @property
    def lineage(self) -> str | None:
        return self._get_property(LINEAGE_PROP, str)

    @lineage.setter
    def lineage(self, v: str | None) -> None:
        self._set_property(LINEAGE_PROP, v)

    @property
    def level(self) -> str | None:
        return self._get_property(LEVEL_PROP, str)

    @level.setter
    def level(self, v: str | None) -> None:
        self._set_property(LEVEL_PROP, v)

    @property
    def facility(self) -> str | None:
        return self._get_property(FACILITY_PROP, str)

    @facility.setter
    def facility(self, v: str | None) -> None:
        self._set_property(FACILITY_PROP, v)

    @property
    def software(self) -> dict[str, str] | None:
        return cast(dict[str, str] | None, self._get_property(SOFTWARE_PROP, dict))

    @software.setter
    def software(self, v: dict[str, str] | None) -> None:
        self._set_property(SOFTWARE_PROP, v)

    @property
    def version(self) -> str | None:
        return self._get_property(VERSION_PROP, str)

    @version.setter
    def version(self, v: str | None) -> None:
        self._set_property(VERSION_PROP, v)

    @property
    def processing_datetime(self) -> datetime | None:
        return map_opt(str_to_datetime, self._get_property(DATETIME_PROP, str))

    @processing_datetime.setter
    def processing_datetime(self, v: datetime | None) -> None:
        self._set_property(DATETIME_PROP, map_opt(datetime_to_str, v))

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> ProcessingExtension[T]:
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(ProcessingExtension[T], ItemProcessingExtension(obj))
        if isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(ProcessingExtension[T], AssetProcessingExtension(obj))
        if isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(ProcessingExtension[T], ItemAssetsProcessingExtension(obj))
        raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesProcessingExtension:
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesProcessingExtension(obj)

    @classmethod
    def provider(cls, provider: pystac.Provider) -> ProviderProcessingExtension:
        return ProviderProcessingExtension(provider)


class ItemProcessingExtension(ProcessingExtension[pystac.Item]):
    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemProcessingExtension Item id={self.item.id}>"


class AssetProcessingExtension(ProcessingExtension[pystac.Asset]):
    asset_href: str
    properties: dict[str, Any]
    additional_read_properties: list[dict[str, Any]] | None = None

    def __init__(self, asset: pystac.Asset):
        self.asset = asset
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return f"<AssetProcessingExtension Asset href={self.asset_href}>"


class ItemAssetsProcessingExtension(ProcessingExtension[pystac.ItemAssetDefinition]):
    asset_defn: pystac.ItemAssetDefinition
    properties: dict[str, Any]

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        self.asset_defn = item_asset
        self.properties = item_asset.properties

    def __repr__(self) -> str:
        return "<ItemAssetsProcessingExtension ItemAssetDefinition>"


class SummariesProcessingExtension(SummariesExtension):
    @property
    def expression(self) -> dict[str, Any] | None:
        return self.summaries.get_schema(EXPRESSION_PROP)

    @expression.setter
    def expression(self, v: dict[str, Any] | None) -> None:
        self._set_summary(EXPRESSION_PROP, v)

    @property
    def lineage(self) -> list[Any] | None:
        return self.summaries.get_list(LINEAGE_PROP)

    @lineage.setter
    def lineage(self, v: list[Any] | None) -> None:
        self._set_summary(LINEAGE_PROP, v)

    @property
    def level(self) -> list[Any] | None:
        return self.summaries.get_list(LEVEL_PROP)

    @level.setter
    def level(self, v: list[Any] | None) -> None:
        self._set_summary(LEVEL_PROP, v)

    @property
    def facility(self) -> list[Any] | None:
        return self.summaries.get_list(FACILITY_PROP)

    @facility.setter
    def facility(self, v: list[Any] | None) -> None:
        self._set_summary(FACILITY_PROP, v)

    @property
    def software(self) -> dict[str, Any] | None:
        return self.summaries.get_schema(SOFTWARE_PROP)

    @software.setter
    def software(self, v: dict[str, Any] | None) -> None:
        self._set_summary(SOFTWARE_PROP, v)

    @property
    def version(self) -> list[Any] | None:
        return self.summaries.get_list(VERSION_PROP)

    @version.setter
    def version(self, v: list[Any] | None) -> None:
        self._set_summary(VERSION_PROP, v)

    @property
    def processing_datetime(self) -> list[Any] | None:
        return self.summaries.get_list(DATETIME_PROP)

    @processing_datetime.setter
    def processing_datetime(self, v: list[Any] | None) -> None:
        self._set_summary(DATETIME_PROP, v)


class ProviderProcessingExtension(PropertiesExtension):
    provider: pystac.Provider
    properties: dict[str, Any]

    def __init__(self, provider: pystac.Provider):
        self.provider = provider
        self.properties = provider.extra_fields

    def apply(
        self,
        expression: ProcessingExpression | dict[str, Any] | None = None,
        lineage: str | None = None,
        level: str | None = None,
        facility: str | None = None,
        software: dict[str, str] | None = None,
        version: str | None = None,
        processing_datetime: datetime | None = None,
    ) -> None:
        self.expression = expression
        self.lineage = lineage
        self.level = level
        self.facility = facility
        self.software = software
        self.version = version
        self.processing_datetime = processing_datetime

    @property
    def expression(self) -> ProcessingExpression | None:
        return map_opt(
            lambda d: ProcessingExpression(cast(dict[str, Any], d)),
            self._get_property(EXPRESSION_PROP, dict),
        )

    @expression.setter
    def expression(self, v: ProcessingExpression | dict[str, Any] | None) -> None:
        if isinstance(v, ProcessingExpression):
            self._set_property(EXPRESSION_PROP, v.to_dict())
            return
        self._set_property(EXPRESSION_PROP, v)

    @property
    def lineage(self) -> str | None:
        return self._get_property(LINEAGE_PROP, str)

    @lineage.setter
    def lineage(self, v: str | None) -> None:
        self._set_property(LINEAGE_PROP, v)

    @property
    def level(self) -> str | None:
        return self._get_property(LEVEL_PROP, str)

    @level.setter
    def level(self, v: str | None) -> None:
        self._set_property(LEVEL_PROP, v)

    @property
    def facility(self) -> str | None:
        return self._get_property(FACILITY_PROP, str)

    @facility.setter
    def facility(self, v: str | None) -> None:
        self._set_property(FACILITY_PROP, v)

    @property
    def software(self) -> dict[str, str] | None:
        return cast(dict[str, str] | None, self._get_property(SOFTWARE_PROP, dict))

    @software.setter
    def software(self, v: dict[str, str] | None) -> None:
        self._set_property(SOFTWARE_PROP, v)

    @property
    def version(self) -> str | None:
        return self._get_property(VERSION_PROP, str)

    @version.setter
    def version(self, v: str | None) -> None:
        self._set_property(VERSION_PROP, v)

    @property
    def processing_datetime(self) -> datetime | None:
        return map_opt(str_to_datetime, self._get_property(DATETIME_PROP, str))

    @processing_datetime.setter
    def processing_datetime(self, v: datetime | None) -> None:
        self._set_property(DATETIME_PROP, map_opt(datetime_to_str, v))

    def __repr__(self) -> str:
        return f"<ProviderProcessingExtension Provider name={self.provider.name!r}>"


class ProcessingExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"processing"}
    stac_object_types = {pystac.STACObjectType.COLLECTION, pystac.STACObjectType.ITEM}


PROCESSING_EXTENSION_HOOKS: ExtensionHooks = ProcessingExtensionHooks()
