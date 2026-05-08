"""Implements the :stac-ext:`Order Extension <order>`."""

from __future__ import annotations

import warnings
from collections.abc import Iterable
from datetime import datetime
from typing import Any, Generic, Literal, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import StringEnum, datetime_to_str, get_required, map_opt
from pystac.utils import str_to_datetime

T = TypeVar(
    "T",
    pystac.Item,
    pystac.Collection,
    pystac.Asset,
    pystac.ItemAssetDefinition,
)

SCHEMA_URI: str = "https://stac-extensions.github.io/order/v1.1.0/schema.json"

PREFIX: str = "order:"
STATUS_PROP: str = PREFIX + "status"
ID_PROP: str = PREFIX + "id"
DATE_PROP: str = PREFIX + "date"
EXPIRATION_DATE_PROP: str = PREFIX + "expiration_date"


class OrderStatus(StringEnum):
    ORDERABLE = "orderable"
    ORDERED = "ordered"
    PENDING = "pending"
    SHIPPING = "shipping"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class OrderExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """Extension API for the STAC Order Extension."""

    name: Literal["order"] = "order"

    def apply(
        self,
        status: OrderStatus,
        order_id: str | None = None,
        date: datetime | None = None,
        expiration_date: datetime | None = None,
    ) -> None:
        self.status = status
        self.order_id = order_id
        self.date = date
        if expiration_date is not None:
            self.expiration_date = expiration_date

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @property
    def status(self) -> OrderStatus:
        return get_required(
            map_opt(
                lambda x: OrderStatus(x), self._get_property(STATUS_PROP, str)
            ),
            self,
            STATUS_PROP,
        )

    @status.setter
    def status(self, v: OrderStatus) -> None:
        self._set_property(STATUS_PROP, v.value, pop_if_none=False)

    @property
    def order_id(self) -> str | None:
        return self._get_property(ID_PROP, str)

    @order_id.setter
    def order_id(self, v: str | None) -> None:
        self._set_property(ID_PROP, v, pop_if_none=True)

    @property
    def date(self) -> datetime | None:
        return map_opt(lambda s: str_to_datetime(s), self._get_property(DATE_PROP, str))

    @date.setter
    def date(self, v: datetime | None) -> None:
        self._set_property(DATE_PROP, map_opt(datetime_to_str, v), pop_if_none=True)

    @property
    def expiration_date(self) -> datetime | None:
        warnings.warn(
            f"'{EXPIRATION_DATE_PROP}' is deprecated in the Order Extension schema.",
            DeprecationWarning,
            stacklevel=2,
        )
        return map_opt(
            lambda s: str_to_datetime(s),
            self._get_property(EXPIRATION_DATE_PROP, str),
        )

    @expiration_date.setter
    def expiration_date(self, v: datetime | None) -> None:
        warnings.warn(
            f"'{EXPIRATION_DATE_PROP}' is deprecated in the Order Extension schema.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._set_property(
            EXPIRATION_DATE_PROP, map_opt(datetime_to_str, v), pop_if_none=True
        )

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> OrderExtension[T]:
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(OrderExtension[T], ItemOrderExtension(obj))
        if isinstance(obj, pystac.Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(OrderExtension[T], CollectionOrderExtension(obj))
        if isinstance(obj, pystac.Asset):
            if obj.owner is not None and not isinstance(
                obj.owner, (pystac.Item, pystac.Collection)
            ):
                raise pystac.ExtensionTypeError(
                    "Order extension only applies to Assets owned by Item or "
                    "Collection."
                )
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(OrderExtension[T], AssetOrderExtension(obj))
        if isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(OrderExtension[T], ItemAssetsOrderExtension(obj))
        raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesOrderExtension:
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesOrderExtension(obj)


class ItemOrderExtension(OrderExtension[pystac.Item]):
    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemOrderExtension Item id={self.item.id}>"


class CollectionOrderExtension(OrderExtension[pystac.Collection]):
    collection: pystac.Collection
    properties: dict[str, Any]

    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields

    def __repr__(self) -> str:
        return f"<CollectionOrderExtension Collection id={self.collection.id}>"


class AssetOrderExtension(OrderExtension[pystac.Asset]):
    asset_href: str
    properties: dict[str, Any]
    additional_read_properties: Iterable[dict[str, Any]] | None = None

    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]
        elif asset.owner and isinstance(asset.owner, pystac.Collection):
            self.additional_read_properties = [asset.owner.extra_fields]

    def __repr__(self) -> str:
        return f"<AssetOrderExtension Asset href={self.asset_href}>"


class ItemAssetsOrderExtension(OrderExtension[pystac.ItemAssetDefinition]):
    asset_defn: pystac.ItemAssetDefinition
    properties: dict[str, Any]

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        self.asset_defn = item_asset
        self.properties = item_asset.properties

    def __repr__(self) -> str:
        return "<ItemAssetsOrderExtension ItemAssetDefinition>"


class SummariesOrderExtension(SummariesExtension):
    @property
    def status(self) -> list[OrderStatus] | None:
        return self.summaries.get_list(STATUS_PROP)

    @status.setter
    def status(self, v: list[OrderStatus] | None) -> None:
        self._set_summary(STATUS_PROP, v)

    @property
    def order_id(self) -> list[str] | None:
        return self.summaries.get_list(ID_PROP)

    @order_id.setter
    def order_id(self, v: list[str] | None) -> None:
        self._set_summary(ID_PROP, v)

    @property
    def date(self) -> list[str] | None:
        return self.summaries.get_list(DATE_PROP)

    @date.setter
    def date(self, v: list[str] | None) -> None:
        self._set_summary(DATE_PROP, v)


class OrderExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"order"}
    stac_object_types = {pystac.STACObjectType.COLLECTION, pystac.STACObjectType.ITEM}


ORDER_EXTENSION_HOOKS: ExtensionHooks = OrderExtensionHooks()
