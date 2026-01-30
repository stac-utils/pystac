from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Generic, Literal, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import StringEnum

T = TypeVar("T", pystac.Collection, pystac.Item, pystac.Asset, pystac.ItemAssetDefinition)

SCHEMA_URI: str = "https://stac-extensions.github.io/product/v1.0.0/schema.json"
PREFIX: str = "product:"

TYPE_PROP: str = PREFIX + "type"
TIMELINESS_PROP: str = PREFIX + "timeliness"
TIMELINESS_CATEGORY_PROP: str = PREFIX + "timeliness_category"
ACQUISITION_TYPE_PROP: str = PREFIX + "acquisition_type"


class AcquisitionType(StringEnum):
    """Allowed values for product:acquisition_type."""
    NOMINAL = "nominal"
    CALIBRATION = "calibration"
    OTHER = "other"


class ProductExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """
    Implements the STAC Product Extension (v1.0.0) for:
      - Item properties
      - Collection top-level extra_fields
      - Asset extra_fields (Item/Collection assets)
      - ItemAssetDefinition properties (collection/item_assets)

    For Collection summaries, use ProductExtension.summaries(collection).
    """

    name: Literal["product"] = "product"

    def apply(
        self,
        *,
        product_type: str | None = None,
        timeliness: str | None = None,
        timeliness_category: str | None = None,
        acquisition_type: AcquisitionType | str | None = None,
    ) -> None:
        """
        Apply the Product Extension properties to the owning object.

        Args:
            product_type: The product type.
            timeliness: The timeliness as an ISO 8601 duration string (e.g. "PT3H", "P1M").
            timeliness_category: The timeliness category.
            acquisition_type: The acquisition type.
        """
        # Enforce the schema dependency: timeliness_category => timeliness
        if timeliness_category is not None and timeliness is None and self.timeliness is None:
            raise ValueError(
                f"'{TIMELINESS_CATEGORY_PROP}' requires '{TIMELINESS_PROP}' to be set."
            )

        self.product_type = product_type
        if timeliness is not None:
            self.timeliness = timeliness
        if timeliness_category is not None:
            self.timeliness_category = timeliness_category
        self.acquisition_type = acquisition_type

    @property
    def product_type(self) -> str | None:
        """
        Gets the product type.
        """
        return self._get_property(TYPE_PROP, str)

    @product_type.setter
    def product_type(self, v: str | None) -> None:
        """Sets the product type.

        Args:
            v: The product type.
        """
        self._set_property(TYPE_PROP, v)

    @property
    def timeliness(self) -> str | None:
        """
        Gets the timeliness as an ISO 8601 duration string (e.g. "PT3H", "P1M").
        """
        # ISO 8601 duration string (e.g. "PT3H", "P1M")
        return self._get_property(TIMELINESS_PROP, str)

    @timeliness.setter
    def timeliness(self, v: str | None) -> None:
        """Sets the timeliness.

        Args:
            v: The timeliness as an ISO 8601 duration string (e.g. "PT3H", "P1M").
        """
        self._set_property(TIMELINESS_PROP, v)

    @property
    def timeliness_category(self) -> str | None:
        """
        Gets the timeliness category.
        """
        return self._get_property(TIMELINESS_CATEGORY_PROP, str)

    @timeliness_category.setter
    def timeliness_category(self, v: str | None) -> None:
        """Sets the timeliness category.

        Args:
            v: The timeliness category.
        """
        if v is not None and (self.timeliness is None):
            raise ValueError(
                f"'{TIMELINESS_CATEGORY_PROP}' requires '{TIMELINESS_PROP}' to be set."
            )
        self._set_property(TIMELINESS_CATEGORY_PROP, v)

    @property
    def acquisition_type(self) -> AcquisitionType | str | None:
        """
        Gets the acquisition type.
        """
        raw = self._get_property(ACQUISITION_TYPE_PROP, str)
        if raw is None:
            return None
        try:
            return AcquisitionType(raw)
        except Exception:
            # Keep unknown strings if encountered in the wild
            return raw

    @acquisition_type.setter
    def acquisition_type(self, v: AcquisitionType | str | None) -> None:
        """Sets the acquisition type.

        Args:
            v: The acquisition type.
        """
        self._set_property(ACQUISITION_TYPE_PROP, None if v is None else str(v))

    @classmethod
    def get_schema_uri(cls) -> str:
        """
        Gets the schema URI for the extension.
        """
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> ProductExtension[T]:
        """
        Attach ProductExtension to an Item, Collection, Asset, or ItemAssetDefinition.

        Use add_if_missing=True to append SCHEMA_URI to stac_extensions
        on the owning Item/Collection when needed.
        """
        if isinstance(obj, pystac.Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(ProductExtension[T], CollectionProductExtension(obj))
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(ProductExtension[T], ItemProductExtension(obj))
        if isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(ProductExtension[T], AssetProductExtension(obj))
        if isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(ProductExtension[T], ItemAssetsProductExtension(obj))

        raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> "SummariesProductExtension":
        """
        Attach SummariesProductExtension to a Collection.

        Use add_if_missing=True to append SCHEMA_URI to stac_extensions
        on the owning Collection when needed.
        """
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesProductExtension(obj)


class CollectionProductExtension(ProductExtension[pystac.Collection]):
    """
    Attach ProductExtension to a Collection.
    """

    collection: pystac.Collection
    properties: dict[str, Any]

    def __init__(self, collection: pystac.Collection):
        """
        Args:
            collection: The Collection to extend.
        """

        self.collection = collection
        # Product fields live at top-level in Collections (extra_fields)
        self.properties = collection.extra_fields

    def __repr__(self) -> str:
        return f"<CollectionProductExtension Collection id={self.collection.id}>"


class ItemProductExtension(ProductExtension[pystac.Item]):
    """
    Attach ProductExtension to an Item.
    """

    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemProductExtension Item id={self.item.id}>"


class AssetProductExtension(ProductExtension[pystac.Asset]):
    """
    Attach ProductExtension to an Asset.
    """

    asset: pystac.Asset
    asset_href: str
    properties: dict[str, Any]
    additional_read_properties: Iterable[dict[str, Any]] | None

    def __init__(self, asset: pystac.Asset):
        """
        Args:
            asset: The Asset to extend.
        """
        self.asset = asset
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        # Allow reads to fall back to owning Item properties (common PySTAC pattern)
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]
        else:
            self.additional_read_properties = None

    def __repr__(self) -> str:
        """
        Get a string representation of the extension.
        """
        return f"<AssetProductExtension Asset href={self.asset_href}>"


class ItemAssetsProductExtension(ProductExtension[pystac.ItemAssetDefinition]):
    """
    Attach ProductExtension to an ItemAssetDefinition.
    """

    asset_defn: pystac.ItemAssetDefinition
    properties: dict[str, Any]

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        """
        Args:
            item_asset: The ItemAssetDefinition to extend.
        """
        self.asset_defn = item_asset
        self.properties = item_asset.properties

    def __repr__(self) -> str:
        """
        Get a string representation of the extension.
        """
        return "<ItemAssetsProductExtension ItemAssetDefinition>"


class SummariesProductExtension(SummariesExtension):
    @property
    def product_type(self) -> list[str] | None:
        """
        Get the product type from the summaries.
        """
        return self.summaries.get_list(TYPE_PROP)

    @product_type.setter
    def product_type(self, v: list[str] | None) -> None:
        """
        Set the product type in the summaries.
        
        Args:
            v: The product type.
        """
        self._set_summary(TYPE_PROP, v)

    @property
    def timeliness(self) -> list[str] | None:
        """
        Get the timeliness from the summaries.
        """
        return self.summaries.get_list(TIMELINESS_PROP)

    @timeliness.setter
    def timeliness(self, v: list[str] | None) -> None:
        """
        Set the timeliness in the summaries.

        Args:
            v: The timeliness.
        """
        self._set_summary(TIMELINESS_PROP, v)

    @property
    def timeliness_category(self) -> list[str] | None:
        """
        Get the timeliness category from the summaries.
        """
        return self.summaries.get_list(TIMELINESS_CATEGORY_PROP)

    @timeliness_category.setter
    def timeliness_category(self, v: list[str] | None) -> None:
        """
        Set the timeliness category in the summaries.

        Args:
            v: The timeliness category.
        """
        self._set_summary(TIMELINESS_CATEGORY_PROP, v)

    @property
    def acquisition_type(self) -> list[str] | None:
        """
        Get the acquisition type from the summaries.
        """
        return self.summaries.get_list(ACQUISITION_TYPE_PROP)

    @acquisition_type.setter
    def acquisition_type(self, v: list[str] | None) -> None:
        """
        Set the acquisition type in the summaries.

        Args:
            v: The acquisition type.
        """
        self._set_summary(ACQUISITION_TYPE_PROP, v)


class ProductExtensionHooks(ExtensionHooks):
    """
    Hooks for the Product extension.
    """
    schema_uri: str = SCHEMA_URI
    # Helpful for discovery/migration if you later add older schema URIs here
    prev_extension_ids = {"product"}
    stac_object_types = {pystac.STACObjectType.COLLECTION, pystac.STACObjectType.ITEM}


PRODUCT_EXTENSION_HOOKS: ExtensionHooks = ProductExtensionHooks()
