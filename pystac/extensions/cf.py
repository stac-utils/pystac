"""CF Extension Module."""

from __future__ import annotations

import copy
from collections.abc import Iterable
from typing import (
    Any,
    Generic,
    Literal,
    TypeVar,
    cast,
)

import pystac
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension
from pystac.utils import map_opt

#: Generalized version of :class:`~pystac.Collection`, `:class:`~pystac.Item`,
#: :class:`~pystac.Asset`, or :class:`~pystac.ItemAssetDefinition`
T = TypeVar(
    "T", pystac.Collection, pystac.Item, pystac.Asset, pystac.ItemAssetDefinition
)

SCHEMA_URI = "https://stac-extensions.github.io/cf/v0.2.0/schema.json"
PREFIX: str = "cf:"

# Field names
PARAMETER_PROP = PREFIX + "parameter"


class Parameter:
    """Helper for Parameter entries."""

    name: str
    unit: str | None

    def __init__(self, name: str, unit: str | None):
        self.name = name
        self.unit = unit

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Parameter):
            return NotImplemented
        return self.name == other.name and self.unit == other.unit

    def __repr__(self) -> str:
        """Return string repr."""
        return f"<Parameter name={self.name} unit={self.unit}>"

    def to_dict(self) -> dict[str, str | None]:
        return copy.deepcopy({"name": self.name, "unit": self.unit})

    @staticmethod
    def from_dict(d: dict[str, str]) -> Parameter:
        name = d.get("name")
        if name is None:
            raise ValueError("name must be a valid string.")
        return Parameter(name, d.get("unit"))


class CFExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Asset`, :class:`~pystac.Item`, or a :class:`pystac.Collection`
    with properties from the :stac-ext:`CF Extension <cf>`.
    This class is generic over the type of STAC Object to be extended
    (e.g. :class:`~pystac.Item`, :class:`~pystac.Collection`).

    To create a concrete instance of :class:`CFExtension`, use the
    :meth:`CFExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> cf_ext = CFExtension.ext(item)
    """

    name: Literal["cf"] = "cf"

    def apply(
        self,
        parameters: list[Parameter] | None = None,
    ) -> None:
        """Apply CF Extension properties to the extended :class:`~pystac.Asset`,
        :class:`~pystac.Item`, or :class:`~pystac.Collection`.
        """
        self.parameters = parameters

    @property
    def parameters(self) -> list[Parameter] | None:
        """Get or set the CF parameter(s)."""
        return map_opt(
            lambda params: [Parameter.from_dict(param) for param in params],
            self._get_property(PARAMETER_PROP, list[dict[str, Any]]),
        )

    @parameters.setter
    def parameters(self, v: list[Parameter] | None) -> None:
        self._set_property(
            PARAMETER_PROP,
            map_opt(lambda params: [param.to_dict() for param in params], v),
        )

    @classmethod
    def get_schema_uri(cls) -> str:
        """Return this extension's schema URI."""
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> CFExtension[T]:
        """Extend the given STAC Object with properties from the
        :stac-ext:`CF Extension <cf>`.

        This extension can be applied to instances of :class:`~pystac.Item`,
        :class:`~pystac.Asset`, or  :class:`~pystac.Collection`.

        Raises
        ------
            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(CFExtension[T], CollectionCFExtension(obj))
        elif isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(CFExtension[T], ItemCFExtension(obj))
        elif isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(CFExtension[T], AssetCFExtension(obj))
        elif isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(CFExtension[T], ItemAssetsCFExtension(obj))
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))


class ItemCFExtension(CFExtension[pystac.Item]):
    """
    A concrete implementation of :class:`CFExtension` on an :class:`~pystac.Item`.

    Extends the properties of the Item to include properties defined in the
    :stac-ext:`CF Extension <cf>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`CFExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self, item: pystac.Item) -> None:
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        """Return repr."""
        return f"<ItemCFExtension Item id={self.item.id}>"


class ItemAssetsCFExtension(CFExtension[pystac.ItemAssetDefinition]):
    """Extension for CF item assets."""

    asset_defn: pystac.ItemAssetDefinition
    properties: dict[str, Any]

    def __init__(self, item_asset: pystac.ItemAssetDefinition) -> None:
        self.asset_defn = item_asset
        self.properties = item_asset.properties


class AssetCFExtension(CFExtension[pystac.Asset]):
    """
    A concrete implementation of :class:`CFExtension` on an :class:`~pystac.Asset`.

    Extends the Asset fields to include properties defined in the
    :stac-ext:`CF Extension <cf>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`CFExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset_href: str
    """The ``href`` value of the :class:`~pystac.Asset` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Asset` fields, including extension properties."""

    additional_read_properties: Iterable[dict[str, Any]] | None = None
    """If present, this will be a list containing 1 dictionary representing the
    properties of the owning :class:`~pystac.Item`."""

    def __init__(self, asset: pystac.Asset) -> None:
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        """Return repr."""
        return f"<AssetCFExtension Asset href={self.asset_href}>"


class CollectionCFExtension(CFExtension[pystac.Collection]):
    """Extension for CF data."""

    collection: pystac.Collection
    properties: dict[str, Any]

    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields

    def __repr__(self) -> str:
        return f"<CollectionCFExtension Item id={self.collection.id}>"
