"""
PySTAC-style implementation of the STAC Processing Extension (v1.2.0).

Schema:
- https://stac-extensions.github.io/processing/v1.2.0/schema.json

Applies to:
- Item properties
- Asset extra_fields (owner must implement the extension)
- Collection ItemAssetDefinition properties (owner must implement the extension)
- Collection summaries via ProcessingExtension.summaries(...)
- Provider extra_fields (helper wrapper; Providers do not have stac_extensions)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Literal, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.utils import datetime_to_str, get_required, map_opt, str_to_datetime

# Generalized version of pystac.Item, pystac.Asset, or pystac.ItemAssetDefinition
T = TypeVar("T", pystac.Item, pystac.Asset, pystac.ItemAssetDefinition)

SCHEMA_URI: str = "https://stac-extensions.github.io/processing/v1.2.0/schema.json"
PREFIX: str = "processing:"

# Field names
EXPRESSION_PROP: str = PREFIX + "expression"
LINEAGE_PROP: str = PREFIX + "lineage"
LEVEL_PROP: str = PREFIX + "level"
FACILITY_PROP: str = PREFIX + "facility"
SOFTWARE_PROP: str = PREFIX + "software"
VERSION_PROP: str = PREFIX + "version"
DATETIME_PROP: str = PREFIX + "datetime"


class ProcessingExpression:
    """
    Representation of processing:expression.

    JSON shape (per schema):
      {
        "format": "<string>",
        "expression": <any>
      }
    """

    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]) -> None:
        """
        Initialize a ProcessingExpression with the given properties dictionary.
        """
        self.properties = properties

    @property
    def format(self) -> str:
        """
        Get the format of the processing expression.
        """
        return get_required(self.properties.get("format"), self, "format")

    @format.setter
    def format(self, v: str) -> None:
        """
        Set the format of the processing expression.
        """
        self.properties["format"] = v

    @property
    def expression(self) -> Any:
        """
        Get the expression of the processing expression.
        """
        return get_required(self.properties.get("expression"), self, "expression")

    @expression.setter
    def expression(self, v: Any) -> None:
        """
        Set the expression of the processing expression.
        
        Args:
            v: The expression value to set.
        """
        self.properties["expression"] = v

    def apply(self, format: str, expression: Any) -> None:
        """
        Apply the processing expression.

        Args:
            format: The format of the processing expression.
            expression: The expression value.
        """
        self.format = format
        self.expression = expression

    @classmethod
    def create(cls, format: str, expression: Any) -> "ProcessingExpression":
        """
        Create a new ProcessingExpression.

        Args:
            format: The format of the processing expression.
            expression: The expression value.
        """
        pe = cls({})
        pe.apply(format=format, expression=expression)
        return pe

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the ProcessingExpression to a dictionary.
        """
        return self.properties

    def __repr__(self) -> str:
        """
        Get a string representation of the ProcessingExpression.
        """
        return f"<ProcessingExpression format={self.properties.get('format')!r}>"


class ProcessingExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """
    Implements the STAC Processing Extension for:
    - Items (Item.properties)
    - Assets (Asset.extra_fields; requires owner implements extension)
    - ItemAssetDefinition (ItemAssetDefinition.properties; requires owner implements extension)

    For Collection summaries, use ProcessingExtension.summaries(collection).
    """

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
        """
        Apply the processing extension.
        
        Args:
            expression: The processing expression.
            lineage: The processing lineage.
            level: The processing level.
            facility: The processing facility.
            software: The processing software.
            version: The processing version.
            processing_datetime: The processing datetime.
        """
        self.expression = expression
        self.lineage = lineage
        self.level = level
        self.facility = facility
        self.software = software
        self.version = version
        self.processing_datetime = processing_datetime

    @property
    def expression(self) -> ProcessingExpression | None:
        """
        Get the processing expression.
        """
        return map_opt(
            lambda d: ProcessingExpression(cast(dict[str, Any], d)),
            self._get_property(EXPRESSION_PROP, dict),
        )

    @expression.setter
    def expression(self, v: ProcessingExpression | dict[str, Any] | None) -> None:
        """
        Set the processing expression.
        
        Args:
            v: The processing expression to set.
        """
        if isinstance(v, ProcessingExpression):
            self._set_property(EXPRESSION_PROP, v.to_dict())
        else:
            self._set_property(EXPRESSION_PROP, v)

    @property
    def lineage(self) -> str | None:
        """
        Get the processing lineage.
        """
        return self._get_property(LINEAGE_PROP, str)

    @lineage.setter
    def lineage(self, v: str | None) -> None:
        """
        Set the processing lineage.
        
        Args:
            v: The processing lineage to set.
        """
        self._set_property(LINEAGE_PROP, v)

    @property
    def level(self) -> str | None:
        """
        Get the processing level.
        """
        return self._get_property(LEVEL_PROP, str)

    @level.setter
    def level(self, v: str | None) -> None:
        """
        Set the processing level.

        Args:
            v: The processing level to set.
        """
        self._set_property(LEVEL_PROP, v)

    @property
    def facility(self) -> str | None:
        """
        Get the processing facility.
        """
        return self._get_property(FACILITY_PROP, str)

    @facility.setter
    def facility(self, v: str | None) -> None:
        """
        Set the processing facility.

        Args:
            v: The processing facility to set.
        """
        self._set_property(FACILITY_PROP, v)

    @property
    def software(self) -> dict[str, str] | None:
        """
        Get the processing software.
        """
        return cast(dict[str, str] | None, self._get_property(SOFTWARE_PROP, dict))

    @software.setter
    def software(self, v: dict[str, str] | None) -> None:
        """
        Set the processing software.

        Args:
            v: The processing software to set.
        """
        self._set_property(SOFTWARE_PROP, v)

    @property
    def version(self) -> str | None:
        """
        Get the processing version.
        """
        return self._get_property(VERSION_PROP, str)

    @version.setter
    def version(self, v: str | None) -> None:
        """
        Set the processing version.

        Args:
            v: The processing version to set.
        """
        self._set_property(VERSION_PROP, v)

    @property
    def processing_datetime(self) -> datetime | None:
        """
        Get the processing datetime.
        """
        return map_opt(
            str_to_datetime,
            self._get_property(DATETIME_PROP, str),
        )

    @processing_datetime.setter
    def processing_datetime(self, v: datetime | None) -> None:
        """
        Set the processing datetime.
        """
        self._set_property(DATETIME_PROP, map_opt(datetime_to_str, v))

    @classmethod
    def get_schema_uri(cls) -> str:
        """
        Get the schema URI for the processing extension.
        """
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> "ProcessingExtension[T]":
        """
        Get the ProcessingExtension for the given object.
        """
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
    ) -> "SummariesProcessingExtension":
        """
        Helper wrapper for Collection.summaries.
        """
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesProcessingExtension(obj)

    @classmethod
    def provider(cls, provider: pystac.Provider) -> "ProviderProcessingExtension":
        """
        Helper wrapper for Provider objects (providers do not track stac_extensions).
        """
        return ProviderProcessingExtension(provider)


class ItemProcessingExtension(ProcessingExtension[pystac.Item]):
    """
    Processing extension for Item objects.
    """

    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self, item: pystac.Item):
        """
        Initialize the ItemProcessingExtension with the given Item.
        """
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        """
        Get a string representation of the ItemProcessingExtension.
        """
        return f"<ItemProcessingExtension Item id={self.item.id}>"


class AssetProcessingExtension(ProcessingExtension[pystac.Asset]):
    """
    Processing extension for Asset objects.
    """
    asset_href: str
    properties: dict[str, Any]
    additional_read_properties: list[dict[str, Any]] | None = None

    def __init__(self, asset: pystac.Asset):
        """
        Initialize the AssetProcessingExtension with the given Asset.
        """
        self.asset = asset
        self.asset_href = asset.href
        self.properties = asset.extra_fields

        # Optional: allow reads to fall back to owning Item properties
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        """
        Get a string representation of the AssetProcessingExtension.
        """
        return f"<AssetProcessingExtension Asset href={self.asset_href}>"


class ItemAssetsProcessingExtension(ProcessingExtension[pystac.ItemAssetDefinition]):
    """
    Processing extension for ItemAssetDefinition objects.
    """
    asset_defn: pystac.ItemAssetDefinition
    properties: dict[str, Any]

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        """
        Initialize the ItemAssetsProcessingExtension with the given ItemAssetDefinition.
        """
        self.asset_defn = item_asset
        self.properties = item_asset.properties

    def __repr__(self) -> str:
        """
        Get a string representation of the ItemAssetsProcessingExtension.
        """
        return "<ItemAssetsProcessingExtension ItemAssetDefinition>"


class SummariesProcessingExtension(SummariesExtension):
    """
    Extends Collection.summaries for processing:* fields.

    Notes:
    - Strings are typically stored as lists in summaries.
    - Dict-shaped summaries (e.g., processing:software) are accessible via get_schema.
    """

    @property
    def expression(self) -> dict[str, Any] | None:
        """
        Get the processing expression summary.
        """
        return self.summaries.get_schema(EXPRESSION_PROP)

    @expression.setter
    def expression(self, v: dict[str, Any] | None) -> None:
        """
        Set the processing expression summary.
        
        Args:
            v: The processing expression summary to set.
        """
        self._set_summary(EXPRESSION_PROP, v)

    @property
    def lineage(self) -> list[Any] | None:
        """
        Get the processing lineage summary.
        """
        return self.summaries.get_list(LINEAGE_PROP)

    @lineage.setter
    def lineage(self, v: list[Any] | None) -> None:
        """
        Set the processing lineage summary.

        Args:
            v: The processing lineage summary to set.
        """
        self._set_summary(LINEAGE_PROP, v)

    @property
    def level(self) -> list[Any] | None:
        """
        Get the processing level summary.
        """
        return self.summaries.get_list(LEVEL_PROP)

    @level.setter
    def level(self, v: list[Any] | None) -> None:
        """
        Set the processing level summary.

        Args:
            v: The processing level summary to set.
        """
        self._set_summary(LEVEL_PROP, v)

    @property
    def facility(self) -> list[Any] | None:
        """
        Get the processing facility summary.
        """
        return self.summaries.get_list(FACILITY_PROP)

    @facility.setter
    def facility(self, v: list[Any] | None) -> None:
        """
        Set the processing facility summary.

        Args:
            v: The processing facility summary to set.
        """
        self._set_summary(FACILITY_PROP, v)

    @property
    def software(self) -> dict[str, Any] | None:
        """
        Get the processing software summary.
        """
        return self.summaries.get_schema(SOFTWARE_PROP)

    @software.setter
    def software(self, v: dict[str, Any] | None) -> None:
        """
        Set the processing software summary.

        Args:
            v: The processing software summary to set.
        """
        self._set_summary(SOFTWARE_PROP, v)

    @property
    def version(self) -> list[Any] | None:
        """
        Get the processing version summary.
        """
        return self.summaries.get_list(VERSION_PROP)

    @version.setter
    def version(self, v: list[Any] | None) -> None:
        """
        Set the processing version summary.

        Args:
            v: The processing version summary to set.
        """
        self._set_summary(VERSION_PROP, v)

    @property
    def processing_datetime(self) -> list[Any] | None:
        """
        Get the processing datetime summary.
        """
        return self.summaries.get_list(DATETIME_PROP)

    @processing_datetime.setter
    def processing_datetime(self, v: list[Any] | None) -> None:
        """
        Set the processing datetime summary.

        Args:
            v: The processing datetime summary to set.
        """
        self._set_summary(DATETIME_PROP, v)


class ProviderProcessingExtension(PropertiesExtension):
    """
    Provider helper wrapper: applies processing:* fields to Provider.extra_fields.

    This does NOT manage stac_extensions, because Provider objects do not carry
    that field in STAC.
    """

    provider: pystac.Provider
    properties: dict[str, Any]

    def __init__(self, provider: pystac.Provider):
        """
        Initialize the ProviderProcessingExtension.

        Args:
            provider: The provider to wrap.
        """
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
        """
        Apply the processing extension properties to the provider.

        Args:
            expression: The processing expression to set.
            lineage: The processing lineage to set.
            level: The processing level to set.
            facility: The processing facility to set.
            software: The processing software to set.
            version: The processing version to set.
            processing_datetime: The processing datetime to set.
        """
        self.expression = expression
        self.lineage = lineage
        self.level = level
        self.facility = facility
        self.software = software
        self.version = version
        self.processing_datetime = processing_datetime

    @property
    def expression(self) -> ProcessingExpression | None:
        """
        Get the processing expression summary.
        """
        return map_opt(
            lambda d: ProcessingExpression(cast(dict[str, Any], d)),
            self._get_property(EXPRESSION_PROP, dict),
        )

    @expression.setter
    def expression(self, v: ProcessingExpression | dict[str, Any] | None) -> None:
        """
        Set the processing expression summary.

        Args:
            v: The processing expression summary to set.
        """
        if isinstance(v, ProcessingExpression):
            self._set_property(EXPRESSION_PROP, v.to_dict())
        else:
            self._set_property(EXPRESSION_PROP, v)

    @property
    def lineage(self) -> str | None:
        """
        Get the processing lineage summary.
        """
        return self._get_property(LINEAGE_PROP, str)

    @lineage.setter
    def lineage(self, v: str | None) -> None:
        """
        Set the processing lineage summary.

        Args:
            v: The processing lineage summary to set.
        """
        self._set_property(LINEAGE_PROP, v)

    @property
    def level(self) -> str | None:
        """
        Get the processing level summary.
        """
        return self._get_property(LEVEL_PROP, str)

    @level.setter
    def level(self, v: str | None) -> None:
        """
        Set the processing level summary.

        Args:
            v: The processing level summary to set.
        """
        self._set_property(LEVEL_PROP, v)

    @property
    def facility(self) -> str | None:
        """
        Get the processing facility summary.
        """
        return self._get_property(FACILITY_PROP, str)

    @facility.setter
    def facility(self, v: str | None) -> None:
        """
        Set the processing facility summary.

        Args:
            v: The processing facility summary to set.
        """
        self._set_property(FACILITY_PROP, v)

    @property
    def software(self) -> dict[str, str] | None:
        """
        Get the processing software summary.
        """
        return cast(dict[str, str] | None, self._get_property(SOFTWARE_PROP, dict))

    @software.setter
    def software(self, v: dict[str, str] | None) -> None:
        """
        Set the processing software summary.

        Args:
            v: The processing software summary to set.
        """
        self._set_property(SOFTWARE_PROP, v)

    @property
    def version(self) -> str | None:
        """
        Get the processing version summary.
        """
        return self._get_property(VERSION_PROP, str)

    @version.setter
    def version(self, v: str | None) -> None:
        """
        Set the processing version summary.

        Args:
            v: The processing version summary to set.
        """
        self._set_property(VERSION_PROP, v)

    @property
    def processing_datetime(self) -> datetime | None:
        """
        Get the processing datetime summary.
        """
        return map_opt(
            str_to_datetime,
            self._get_property(DATETIME_PROP, str),
        )

    @processing_datetime.setter
    def processing_datetime(self, v: datetime | None) -> None:
        """
        Set the processing datetime summary.
        """
        self._set_property(DATETIME_PROP, map_opt(datetime_to_str, v))

    def __repr__(self) -> str:
        """
        Get a string representation of the processing extension.
        """
        return f"<ProviderProcessingExtension Provider name={self.provider.name!r}>"
