"""Implements the :stac-ext:`Archive Extension <archive>`."""

from __future__ import annotations

#from abc import ABC
from typing import Any, Generic, Literal, TypeVar, Union, cast

import pystac
from pystac.extensions import item_assets
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension, SummariesExtension
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import StringEnum

T = TypeVar(
    "T",  pystac.Asset, item_assets.AssetDefinition
)

# For time being set the URL to repo location.
# Later to be in standard location like
# "https://stac-extensions.github.io/archive/v1.0.0/schema.json"

SCHEMA_URI = "https://github.com/stac-extensions/archive/blob/main/json-schema/schema.json"
PREFIX: str = "archive:"

# Field names
ARCHIVE_HREF_PROP = PREFIX + "href"
ARCHIVE_FORMAT_PROP = PREFIX + "format"
ARCHIVE_TYPE_PROP = PREFIX + "type"
ARCHIVE_START_PROP = PREFIX + "start"
ARCHIVE_END_PROP = PREFIX + "end"


class ArchiveExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[pystac.Collection, pystac.Item]],
):
    """An abstract class that can be used to extend the properties of a
    :class:`~pystac.Collection`, :class:`~pystac.Item`, or :class:`~pystac.Asset` with
    properties from the :stac-ext:`Archive Extension <archive>`. This class is
    generic over the type of STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Asset`).

    To create a concrete instance of :class:`ArchiveExtension`, use the
    :meth:`ArchiveExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> arch_ext = ArchiveExtension.ext(item)
    """

    name: Literal["archive"] = "archive"

    def apply(
        self,
        href: str |  None = None,
        format: str |  None = None,
        type: str |  None = None,
        start: int |  None = None,
        end: int |  None = None,
    ) -> None:
        """Applies Archive Extension properties to the extended
        :class:`~pystac.Collection`, :class:`~pystac.Item` or :class:`~pystac.Asset`.

        Args:
            href (str) : The location of the file within the archive specified by the href field.
            format (str): The mimetype of the archive format.
            type (str): The mimetype of the file within the archive specified by the href field.
            start (int) : The offset of the first byte of the file within the archive.
            end (int) : The offset of the last byte of the file within the archive.
        """
        self.href = href
        self.format = format
        self.type = type
        self.start = start
        self.end = end

    @property
    def href(self) -> str | None:
        """Get or sets the href,the location of the file within the archive.
        """
        return self._get_property(ARCHIVE_HREF_PROP, str)

    @href.setter
    def href(self, v: str | None) -> None:
        self._set_property(ARCHIVE_HREF_PROP, v)

    @property
    def format(self) -> str | None:
        """Get or sets the format,the mimetype of the archive.
        """
        return self._get_property(ARCHIVE_FORMAT_PROP, str)

    @format.setter
    def format(self, v: str | None) -> None:
        self._set_property(ARCHIVE_FORMAT_PROP, v)

    @property
    def type(self) -> str | None:
        """Get or sets the type,the mimetype of the file within the archive
           specified by the href field.
        """
        return self._get_property(ARCHIVE_TYPE_PROP, str)

    @type.setter
    def type(self, v: str | None) -> None:
        self._set_property(ARCHIVE_TYPE_PROP, v)

    @property
    def start(self) -> int | None:
        """Get or sets the start,the offset of the first byte of the file 
           within the archive.
        """
        return self._get_property(ARCHIVE_START_PROP, int)

    @start.setter
    def start(self, v: int | None) -> None:
        self._set_property(ARCHIVE_START_PROP, v)

    @property
    def end(self) -> int | None:
        """Get or sets the end,the offset of the last byte of the file 
           within the archive.
        """
        return self._get_property(ARCHIVE_END_PROP, int)

    @end.setter
    def start(self, v: int | None) -> None:
        self._set_property(ARCHIVE_END_PROP, v)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> ArchiveExtension[T]:
        """Extends the given STAC Object with properties from the :stac-ext:`Archive
        Extension <archive>`.

        This extension can be applied to instances of :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(ArchiveExtension[T], ItemArchiveExtension(obj))
        if isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(ArchiveExtension[T], AssetArchiveExtension(obj))
        elif isinstance(obj, item_assets.AssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(ArchiveExtension[T], ItemAssetsArchiveExtension(obj))
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesStorageExtension:
        """Returns the extended summaries object for the given collection."""
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesStorageExtension(obj)


#class ItemArchiveExtension(ArchiveExtension[pystac.Item]):
#    """A concrete implementation of :class:`ArchiveExtension` on an
#    :class:`~pystac.Item` that extends the properties of the Item to include properties
#    defined in the :stac-ext:`Archive Extension <archive>`.
#
#    This class should generally not be instantiated directly. Instead, call
#    :meth:`ArchiveExtension.ext` on an :class:`~pystac.Item` to extend it.
#    """
#
#    item: pystac.Item
#    properties: dict[str, Any]
#
#    def __init__(self, item: pystac.Item):
#        self.item = item
#        self.properties = item.properties
#
#    def __repr__(self) -> str:
#        return f"<ItemArchiveExtension Item id={self.item.id}>"


class AssetArchiveExtension(ArchiveExtension[pystac.Asset]):
    """A concrete implementation of :class:`ArchiveExtension` on an
    :class:`~pystac.Asset` that extends the Asset fields to include properties defined
    in the :stac-ext:`Archive Extension <archive>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`ArchiveExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset_href: str
    properties: dict[str, Any]
    additional_read_properties: list[dict[str, Any]] | None

    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]
        else:
            self.additional_read_properties = None

    def __repr__(self) -> str:
        return f"<AssetArchiveExtension Item id={self.asset_href}>"


class ItemAssetsArchiveExtension(ArchiveExtension[item_assets.AssetDefinition]):
    properties: dict[str, Any]
    asset_defn: item_assets.AssetDefinition

    def __init__(self, item_asset: item_assets.AssetDefinition):
        self.asset_defn = item_asset
        self.properties = item_asset.properties


class SummariesArchiveExtension(SummariesExtension):
    """A concrete implementation of :class:`~SummariesExtension` that extends
    the ``summaries`` field of a :class:`~pystac.Collection` to include properties
    defined in the :stac-ext:`Archive Extension <storage>`.
    """

    @property
    def href(self) -> list[str] | None:
        """Get or sets the summary of :attr:`ArchiveExtension.href` values
        for this Collection.
        """
        return self.summaries.get_list(ARCHIVE_HREF_PROP)

    @href.setter
    def href(self, v: list[str] | None) -> None:
        self._set_summary(ARCHIVE_HREF_PROP, v)

    @property
    def format(self) -> list[str] | None:
        """Get or sets the summary of :attr:`ArchiveExtension.format` values
        for this Collection.
        """
        return self.summaries.get_list(ARCHIVE_FORMAT_PROP)

    @format.setter
    def format(self, v: list[str] | None) -> None:
        self._set_summary(ARCHIVE_FORMAT_PROP, v)

    @property
    def type(self) -> list[str] | None:
        """Get or sets the summary of :attr:`ArchiveExtension.type` values
        for this Collection.
        """
        return self.summaries.get_list(ARCHIVE_TYPE_PROP)

    @type.setter
    def type(self, v: list[str] | None) -> None:
        self._set_summary(ARCHIVE_TYPE_PROP, v)

    @property
    def start(self) -> list[int] | None:
        """Get or sets the summary of :attr:`ArchiveExtension.start` values
        for this Collection.
        """
        return self.summaries.get_list(ARCHIVE_START_PROP)

    @start.setter
    def start(self, v: list[int] | None) -> None:
        self._set_summary(ARCHIVE_START_PROP, v)

    @property
    def end(self) -> list[int] | None:
        """Get or sets the summary of :attr:`ArchiveExtension.end` values
        for this Collection.
        """
        return self.summaries.get_list(ARCHIVE_END_PROP)

    @end.setter
    def end(self, v: list[int] | None) -> None:
        self._set_summary(ARCHIVE_END_PROP, v)


class ArchiveExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI

    #For time being empty set 
    prev_extension_ids: set[str] = set()
    stac_object_types = {
        pystac.STACObjectType.COLLECTION,
        pystac.STACObjectType.ITEM,
    }


ARCHIVE_EXTENSION_HOOKS: ExtensionHooks = ArchiveExtensionHooks()
