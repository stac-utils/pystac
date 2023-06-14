"""Implements the :stac-ext:`Xarray Assets Extension <xarray>`."""

from __future__ import annotations

from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

import pystac
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension
from pystac.extensions.hooks import ExtensionHooks

T = TypeVar("T", pystac.Collection, pystac.Item, pystac.Asset)

SCHEMA_URI = "https://stac-extensions.github.io/xarray-assets/v1.0.0/schema.json"

PREFIX: str = "xarray:"
OPEN_KWARGS_PROP = PREFIX + "open_kwargs"
STORAGE_OPTIONS_PROP = PREFIX + "storage_options"


class XarrayAssetsExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[pystac.Collection, pystac.Item]],
):
    """An abstract class that can be used to extend the properties of a
    :class:`~pystac.Collection`, :class:`~pystac.Item`, or :class:`~pystac.Asset` with
    properties from the :stac-ext:`Datacube Extension <datacube>`. This class is
    generic over the type of STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Asset`).

    To create a concrete instance of :class:`XarrayAssetsExtension`, use the
    :meth:`XarrayAssetsExtension.ext` method. For example:

    .. code-block:: python

        >>> item: pystac.Item = ...
        >>> xr_ext = XarrayAssetsExtension.ext(item)

    """

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> XarrayAssetsExtension[T]:
        """Extend the given STAC Object with properties from the
        :stac-ext:`XarrayAssets Extension <xarray>`.

        This extension can be applied to instances of :class:`~pystac.Collection`,
        :class:`~pystac.Item` or :class:`~pystac.Asset`.

        Raises:
            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Collection):
            cls.validate_has_extension(obj, add_if_missing)
            return CollectionXarrayAssetsExtension(obj)
        if isinstance(obj, pystac.Item):
            cls.validate_has_extension(obj, add_if_missing)
            return ItemXarrayAssetsExtension(obj)
        if isinstance(obj, pystac.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return AssetXarrayAssetsExtension(obj)
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))


class CollectionXarrayAssetsExtension(XarrayAssetsExtension[pystac.Collection]):
    """A concrete implementation of :class:`XarrayAssetsExtension` on a
    :class:`~pystac.Collection` that extends the properties of the Item to include
    properties defined in the :stac-ext:`XarrayAssets Extension <xarray>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`XarrayAssetsExtension.ext` on an :class:`~pystac.Collection` to extend it.
    """

    collection: pystac.Collection
    properties: Dict[str, Any]

    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields

    def __repr__(self) -> str:
        return "<CollectionXarrayAssetsExtension Item id={}>".format(self.collection.id)


class ItemXarrayAssetsExtension(XarrayAssetsExtension[pystac.Item]):
    """A concrete implementation of :class:`XarrayAssetsExtension` on an
    :class:`~pystac.Item` that extends the properties of the Item to include properties
    defined in the :stac-ext:`XarrayAssets Extension <xarray>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`XarrayAssetsExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    properties: Dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemXarrayAssetsExtension Item id={}>".format(self.item.id)


class AssetXarrayAssetsExtension(XarrayAssetsExtension[pystac.Asset]):
    """A concrete implementation of :class:`XarrayAssetsExtension` on an
    :class:`~pystac.Asset` that extends the Asset fields to include properties defined
    in the :stac-ext:`XarrayAssets Extension <xarray>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`XarrayAssetsExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset: pystac.Asset
    properties: Dict[str, Any]
    additional_read_properties: Optional[List[Dict[str, Any]]] = None

    def __init__(self, asset: pystac.Asset):
        self.asset = asset
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    @property
    def storage_options(self) -> Optional[Dict[str, Any]]:
        """Additional keywords for accessing the dataset from remote storage"""
        return self.properties.get(STORAGE_OPTIONS_PROP)

    @storage_options.setter
    def storage_options(self, v: Optional[Dict[str, Any]]) -> Any:
        if v is None:
            self.properties.pop(STORAGE_OPTIONS_PROP, None)
        else:
            self.properties[STORAGE_OPTIONS_PROP] = v

    @property
    def open_kwargs(self) -> Optional[Dict[str, Any]]:
        """Additional keywords for opening the dataset"""
        return self.properties.get(OPEN_KWARGS_PROP)

    @open_kwargs.setter
    def open_kwargs(self, v: Optional[Dict[str, Any]]) -> Any:
        if v is None:
            self.properties.pop(OPEN_KWARGS_PROP, None)
        else:
            self.properties[OPEN_KWARGS_PROP] = v

    def __repr__(self) -> str:
        return "<AssetXarrayAssetsExtension Asset href={}>".format(self.asset.href)

    def open(self, **kwargs: Any) -> Any:
        """Open the asset's data as an xarray object.

        Requires ``xpystac`` to be installed.

        Args:
            **kwargs: All keyword arguments are passed along to ``xarray.open_dataset``

        Returns:
            xarray.Dataset: An ndimentional representation of the data referenced
                by the asset. The data file will be accessed, but the data will not
                necessarily all be eagerly read.
        """
        try:
            from xpystac.core import to_xarray
        except ImportError:
            raise ImportError("Missing optional dependency `xpystac`")

        return to_xarray(self.asset, **kwargs)


class XarrayAssetsExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"xarray"}
    stac_object_types = {pystac.STACObjectType.COLLECTION, pystac.STACObjectType.ITEM}


XARRAY_ASSETS_EXTENSION_HOOKS: ExtensionHooks = XarrayAssetsExtensionHooks()
