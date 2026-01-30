"""
Implements the STAC :stac-ext:`Order Extension <order>`.

Schema: https://stac-extensions.github.io/order/v1.1.0/schema.json
"""

from __future__ import annotations

import warnings
from datetime import datetime
from typing import Any, Generic, Iterable, Literal, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.utils import (
    StringEnum,
    datetime_to_str,
    get_required,
    map_opt,
    str_to_datetime,
)

#: Generalized version of supported extended objects
T = TypeVar(
    "T",
    pystac.Item,
    pystac.Collection,
    pystac.Asset,
    pystac.ItemAssetDefinition,
)

SCHEMA_URI: str = "https://stac-extensions.github.io/order/v1.1.0/schema.json"
PREFIX: str = "order:"

STATUS_PROP: str = PREFIX + "status"  # required on Items; required top-level on Collections (per schema)
ID_PROP: str = PREFIX + "id"
DATE_PROP: str = PREFIX + "date"
EXPIRATION_DATE_PROP: str = PREFIX + "expiration_date"  # deprecated in schema


class OrderStatus(StringEnum):
    """
    Enumeration of order statuses.
    """
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
    """
    An abstract class that can be used to extend the fields of:

    - :class:`~pystac.Item` (Item properties)
    - :class:`~pystac.Collection` (top-level extra_fields)
    - :class:`~pystac.Asset` (asset extra_fields; for both Item and Collection assets)
    - :class:`~pystac.ItemAssetDefinition` (item asset definition properties)

    To create a concrete instance, use :meth:`OrderExtension.ext`.
    """

    name: Literal["order"] = "order"

    def apply(
        self,
        status: OrderStatus,
        order_id: str | None = None,
        date: datetime | None = None,
        expiration_date: datetime | None = None,
    ) -> None:
        """
        Applies order extension fields to the extended object.

        Args:
            status: Required order status.
            order_id: Optional order identifier.
            date: Optional order datetime (serialized as RFC3339/ISO8601 in UTC).
            expiration_date: Deprecated in the schema; preserved for compatibility.
        """
        self.status = status
        self.order_id = order_id
        self.date = date
        self.expiration_date = expiration_date

    @classmethod
    def get_schema_uri(cls) -> str:
        """
        Get the schema URI for the Order Extension.
        """
        return SCHEMA_URI

    @property
    def status(self) -> OrderStatus:
        """
        Get the order status.
        """
        return get_required(
            map_opt(lambda x: OrderStatus(x), self._get_property(STATUS_PROP, str)),
            self,
            STATUS_PROP,
        )

    @status.setter
    def status(self, v: OrderStatus) -> None:
        """
        Set the order status.

        Args:
            v: The order status to set.
        """
        self._set_property(STATUS_PROP, v.value, pop_if_none=False)

    @property
    def order_id(self) -> str | None:
        """
        Get the order identifier.
        """
        return self._get_property(ID_PROP, str)

    @order_id.setter
    def order_id(self, v: str | None) -> None:
        """
        Set the order identifier.

        Args:
            v: The order identifier to set.
        """
        self._set_property(ID_PROP, v, pop_if_none=True)

    @property
    def date(self) -> datetime | None:
        """
        Get the order datetime.
        """
        return map_opt(lambda s: str_to_datetime(s), self._get_property(DATE_PROP, str))

    @date.setter
    def date(self, v: datetime | None) -> None:
        """
        Set the order datetime.

        Args:
            v: The order datetime to set.
        """
        self._set_property(DATE_PROP, map_opt(datetime_to_str, v), pop_if_none=True)

    @property
    def expiration_date(self) -> datetime | None:
        """
        Get the expiration date.
        """
        warnings.warn(
            f"'{EXPIRATION_DATE_PROP}' is deprecated in the Order Extension schema.",
            DeprecationWarning,
            stacklevel=2,
        )
        return map_opt(
            lambda s: str_to_datetime(s), self._get_property(EXPIRATION_DATE_PROP, str)
        )

    @expiration_date.setter
    def expiration_date(self, v: datetime | None) -> None:
        """
        Set the expiration date.

        Args:
            v: The expiration date to set.
        """
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
        """
        Extends the given object with properties from the Order Extension.

        Supported:
            - pystac.Item
            - pystac.Collection
            - pystac.Asset (Item or Collection assets)
            - pystac.ItemAssetDefinition

        Raises:
            pystac.ExtensionTypeError: if an unsupported object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(OrderExtension[T], ItemOrderExtension(obj))

        if isinstance(obj, pystac.Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(OrderExtension[T], CollectionOrderExtension(obj))

        if isinstance(obj, pystac.Asset):
            # Allow both Item assets and Collection assets; validate owner type if present.
            if obj.owner is not None and not isinstance(obj.owner, (pystac.Item, pystac.Collection)):
                raise pystac.ExtensionTypeError(
                    "Order extension only applies to Assets owned by Item or Collection."
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
    ) -> "SummariesOrderExtension":
        """Returns the extended summaries object for the given collection."""
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesOrderExtension(obj)


class ItemOrderExtension(OrderExtension[pystac.Item]):
    """Concrete implementation on :class:`~pystac.Item`."""

    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self, item: pystac.Item):
        """
        Initialize the ItemOrderExtension.
        """
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemOrderExtension Item id={self.item.id}>"


class CollectionOrderExtension(OrderExtension[pystac.Collection]):
    """
    Concrete implementation on :class:`~pystac.Collection`.

    Note: Collection extension fields defined as "top-level fields" are stored in
    ``collection.extra_fields`` (not in ``collection.summaries``).
    """

    collection: pystac.Collection
    properties: dict[str, Any]

    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields

    def __repr__(self) -> str:
        return f"<CollectionOrderExtension Collection id={self.collection.id}>"


class AssetOrderExtension(OrderExtension[pystac.Asset]):
    """Concrete implementation on :class:`~pystac.Asset`."""

    asset_href: str
    properties: dict[str, Any]
    additional_read_properties: Iterable[dict[str, Any]] | None = None

    def __init__(self, asset: pystac.Asset):
        """
        Initialize the AssetOrderExtension.
        """
        self.asset_href = asset.href
        self.properties = asset.extra_fields

        # Expose owner properties as read-only fallback (mirrors core PySTAC pattern).
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]
        elif asset.owner and isinstance(asset.owner, pystac.Collection):
            self.additional_read_properties = [asset.owner.extra_fields]

    def __repr__(self) -> str:
        """
        Get a string representation of the AssetOrderExtension.
        """
        return f"<AssetOrderExtension Asset href={self.asset_href}>"


class ItemAssetsOrderExtension(OrderExtension[pystac.ItemAssetDefinition]):
    """Concrete implementation on :class:`~pystac.ItemAssetDefinition`."""

    asset_defn: pystac.ItemAssetDefinition
    properties: dict[str, Any]

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        """
        Initialize the ItemAssetsOrderExtension.
        """
        self.asset_defn = item_asset
        self.properties = item_asset.properties

    def __repr__(self) -> str:
        """
        Get a string representation of the ItemAssetsOrderExtension.
        """
        return "<ItemAssetsOrderExtension ItemAssetDefinition>"


class SummariesOrderExtension(SummariesExtension):
    """Concrete implementation extending :attr:`pystac.Collection.summaries`."""

    @property
    def status(self) -> list[OrderStatus] | None:
        """
        Get the order status.
        """
        return self.summaries.get_list(STATUS_PROP)

    @status.setter
    def status(self, v: list[OrderStatus] | None) -> None:
        """
        Set the order status.
        
        Args:
            v: The order status to set.
        """
        self._set_summary(STATUS_PROP, v)

    @property
    def order_id(self) -> list[str] | None:
        """
        Get the order ID.
        """
        return self.summaries.get_list(ID_PROP)

    @order_id.setter
    def order_id(self, v: list[str] | None) -> None:
        """
        Set the order ID.

        Args:
            v: The order ID to set.
        """
        self._set_summary(ID_PROP, v)

    @property
    def date(self) -> list[str] | None:
        """
        Get the expiration date.
        """
        # Summaries commonly store datetimes as strings (STAC JSON), so keep as-is.
        return self.summaries.get_list(DATE_PROP)

    @date.setter
    def date(self, v: list[str] | None) -> None:
        """
        Set the expiration date.

        Args:
            v: The expiration date to set.
        """
        self._set_summary(DATE_PROP, v)
