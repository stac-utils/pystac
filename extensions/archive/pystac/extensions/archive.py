"""Implements the :stac-ext:`Archive Extension <archive>`."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Generic, Literal, TypeVar, cast

# import pystac
from pystac import (
    Asset,
    Collection,
    ExtensionTypeError,
    Item,
    Link,
    STACObjectType,
)
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
)
from pystac.extensions.hooks import ExtensionHooks

#: Generalized version of :class:`~pystac.Asset`, :class:`~pystac.Link`,
T = TypeVar("T", Asset, Link)

SCHEMA_URI = "https://stac-extensions.github.io/archive/v1.0.0/schema.json"
PREFIX: str = "archive:"

# Field names
ARCHIVE_HREF_PROP = PREFIX + "href"
ARCHIVE_TYPE_PROP = PREFIX + "type"
ARCHIVE_ROLES_PROP = PREFIX + "roles"
ARCHIVE_RANGE_PROP = PREFIX + "range"
ARCHIVE_TITLE_PROP = PREFIX + "title"
ARCHIVE_DESCRIPTION_PROP = PREFIX + "description"


class ArchiveExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Collection | Item],
):
    """A class that can be used to extend the properties of an :class:`~pystac.Asset`
    or :class:`~pystac.Link` with properties from the
    :stac-ext:`Archive Extension <archive>`.

    To create a concrete instance of :class:`ArchiveExtension`, use the
    :meth:`ArchiveExtension.ext` method. For example:

    .. code-block:: python

       >>> asset: pystac.Asset = ...
       >>> archive_ext =ArchiveExtension.ext(asset)
    """

    name: Literal["archive"] = "archive"

    def apply(
        self,
        href: str | None = None,
        type: str | None = None,
        roles: list[str] | None = None,
        range: list[int] | None = None,
        title: str | None = None,
        description: str | None = None,
    ) -> None:
        """Applies Archive Extension properties to the extended
        :class:`~pystac.Asset`.

        Args:
            href (str) : The location of the file within the archive specified by the
                         href field.
            type (str): The mimetype of the file within the archive specified by the
                        href field.
            roles [str] : The roles of the file within the archive.
            range [int] : The first and last byte of the file within the archive.
            title (str) : The title of the archive file.
            description (str) : The description of the archive file.
        """
        self.href = href
        self.type = type
        self.roles = roles
        self.range = range
        self.title = title
        self.description = description

    @property
    def href(self) -> str | None:
        """Get or sets the href,the location of the file within the archive."""
        return self._get_property(ARCHIVE_HREF_PROP, str)

    @href.setter
    def href(self, v: str | None) -> None:
        self._set_property(ARCHIVE_HREF_PROP, v)

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
    def roles(self) -> list[str] | None:
        """Get or sets the roles of the file
        within the archive.
        """
        return self._get_property(ARCHIVE_ROLES_PROP, list[str])

    @roles.setter
    def roles(self, v: list[str] | None) -> None:
        self._set_property(ARCHIVE_ROLES_PROP, v)

    @property
    def range(self) -> list[int] | None:
        """Get or sets the start,end offset of the first and last byte of the file
        within the archive.
        """
        return self._get_property(ARCHIVE_RANGE_PROP, list[int])

    @range.setter
    def range(self, v: list[int] | None) -> None:
        self._set_property(ARCHIVE_RANGE_PROP, v)

    @property
    def title(self) -> str | None:
        """Detailed multi-line title to name the archive. `CommonMark 0.29
        <http://commonmark.org/>`__ syntax MAY be used for rich text representation."""
        return self.properties.get(ARCHIVE_TITLE_PROP)

    @title.setter
    def title(self, v: str | None) -> None:
        if v is None:
            self.properties.pop(ARCHIVE_TITLE_PROP, None)
        else:
            self.properties[ARCHIVE_TITLE_PROP] = v

    @property
    def description(self) -> str | None:
        """Detailed multi-line description to explain the archive. `CommonMark 0.29
        <http://commonmark.org/>`__ syntax MAY be used for rich text representation."""
        return self.properties.get(ARCHIVE_DESCRIPTION_PROP)

    @description.setter
    def description(self, v: str | None) -> None:
        if v is None:
            self.properties.pop(ARCHIVE_DESCRIPTION_PROP, None)
        else:
            self.properties[ARCHIVE_DESCRIPTION_PROP] = v

    def to_dict(self) -> dict[str, Any]:
        """Returns a dictionary representing this ``Archive``."""
        return self.properties

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(
        cls, obj: Asset | Link, add_if_missing: bool = False
    ) -> ArchiveExtension[T]:
        """Extends the given STAC Object with properties from the 
        :stac-ext:`Archive Extension <archive>`.

        This extension can be applied to instances of :class:`~pystac.Asset` or
        :class:`~pystac.Link`
        """
        if isinstance(obj, Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(ArchiveExtension[T], AssetArchiveExtension(obj))
        elif isinstance(obj, Link):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(ArchiveExtension[T], LinkArchiveExtension(obj))
        else:
            raise ExtensionTypeError(cls._ext_error_message(obj))


class AssetArchiveExtension(ArchiveExtension[Asset]):
    """A concrete implementation of :class:`ArchiveExtension` on an
    :class:`~pystac.Asset` that extends the Asset fields to include properties
    defined in the :stac-ext:`Archive Extension <archive>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`ArchiveExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset: Asset

    asset_href: str
    """The ``href`` value of the :class:`~pystac.Asset` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Asset` fields, including extension properties."""

    additional_read_properties: Iterable[dict[str, Any]] | None = None
    """If present, this will be a list containing 1 dictionary representing the
    properties of the owner."""

    def __init__(self, asset: Asset):
        self.asset = asset
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and hasattr(asset.owner, "properties"):
            self.additional_read_properties = [asset.owner.properties]
        else:
            self.additional_read_properties = None

    def __repr__(self) -> str:
        return f"<AssetArchiveExtension Asset href={self.asset_href}>"


class LinkArchiveExtension(ArchiveExtension[Link]):
    """A concrete implementation of :class:`ArchiveExtension` on an
    :class:`~pystac.Link` that extends the Link fields to include properties defined
    in the :stac-ext:`Archive Extension <archive>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`ArchiveExtension.ext` on an :class:`~pystac.Link` to extend it.
    """

    link_href: str
    """The ``href`` value of the :class:`~pystac.Link` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Link` fields, including extension properties."""

    additional_read_properties: Iterable[dict[str, Any]] | None = None
    """If present, this will be a list containing 1 dictionary representing the
    properties of the owner."""

    def __init__(self, link: Link):
        self.link_href = link.href
        self.properties = link.extra_fields
        if link.owner and hasattr(link.owner, "properties"):
            self.additional_read_properties = [link.owner.properties]

    def __repr__(self) -> str:
        return f"<LinkArchiveExtension Link href={self.link_href}>"


class ArchiveExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI

    # For time being empty set
    # prev_extension_ids: set[str] = set()
    prev_extension_ids = {
        "archive",
    }
    stac_object_types = {STACObjectType.COLLECTION, STACObjectType.ITEM}


ARCHIVE_EXTENSION_HOOKS: ExtensionHooks = ArchiveExtensionHooks()
