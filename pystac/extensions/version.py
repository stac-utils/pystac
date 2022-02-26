"""Implements the :stac-ext:`Versioning Indicators Extension <version>`."""
from pystac.utils import get_required, map_opt
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union, cast

import pystac
from pystac.utils import StringEnum
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
)
from pystac.extensions.hooks import ExtensionHooks

T = TypeVar("T", pystac.Collection, pystac.Item)

SCHEMA_URI = "https://stac-extensions.github.io/version/v1.0.0/schema.json"

# STAC fields - These are unusual for an extension in that they do not have
# a prefix.  e.g. nothing like "ver:"
VERSION: str = "version"
DEPRECATED: str = "deprecated"


class VersionRelType(StringEnum):
    """A list of rel types defined in the Version Extension.

    See the :stac-ext:`Version Extension Relation types
    <version#relation-types>` documentation
    for details."""

    LATEST = "latest-version"
    """Indicates a link pointing to a resource containing the latest version."""

    PREDECESSOR = "predecessor-version"
    """Indicates a link pointing to a resource containing the predecessor version in the
    version history."""

    SUCCESSOR = "successor-version"
    """Indicates a link pointing to a resource containing the successor version in the
    version history."""


class VersionExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[pystac.Collection, pystac.Item]],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Item` or :class:`~pystac.Collection` with properties from the
    :stac-ext:`Versioning Indicators Extension <version>`. This class is generic over
    the type of STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Collection`).

    To create a concrete instance of :class:`VersionExtension`, use the
    :meth:`VersionExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> version_ext = VersionExtension.ext(item)
    """

    obj: pystac.STACObject

    def __init__(self, obj: pystac.STACObject) -> None:
        self.obj = obj

    def apply(
        self,
        version: str,
        deprecated: Optional[bool] = None,
        latest: Optional[T] = None,
        predecessor: Optional[T] = None,
        successor: Optional[T] = None,
    ) -> None:
        """Applies version extension properties to the extended :class:`~pystac.Item` or
        :class:`~pystac.Collection`.

        Args:
            version : The version string for the item.
            deprecated : Optional flag set to ``True`` if an Item is deprecated with the
                potential to be removed.  Defaults to ``False`` if not present.
            latest : Item representing the latest (e.g., current) version.
            predecessor : Item representing the resource containing the predecessor
                version in the version history.
            successor : Item representing the resource containing the successor version
            in the version history.
        """
        self.version = version
        if deprecated is not None:
            self.deprecated = deprecated
        if latest:
            self.latest = latest
        if predecessor:
            self.predecessor = predecessor
        if successor:
            self.successor = successor

    @property
    def version(self) -> str:
        """Get or sets a version string of the :class:`~pystac.Item` or
        :class:`pystac.Collection`."""
        return get_required(self._get_property(VERSION, str), self, VERSION)

    @version.setter
    def version(self, v: str) -> None:
        self._set_property(VERSION, v, pop_if_none=False)

    @property
    def deprecated(self) -> Optional[bool]:
        """Get or sets whether the item is deprecated.

        A value of ``True`` specifies that the Collection or Item is deprecated with the
        potential to be removed. It should be transitioned out of usage as soon as
        possible and users should refrain from using it in new projects. A link with
        relation type ``latest-version`` SHOULD be added to the links and MUST refer to
        the resource that can be used instead.
        """
        return self._get_property(DEPRECATED, bool)

    @deprecated.setter
    def deprecated(self, v: Optional[bool]) -> None:
        self._set_property(DEPRECATED, v)

    @property
    def latest(self) -> Optional[T]:
        """Gets or sets the :class:`~pystac.Link` to the :class:`~pystac.Item`
        representing the most recent version.
        """
        return map_opt(
            lambda x: cast(T, x),
            next(iter(self.obj.get_stac_objects(VersionRelType.LATEST)), None),
        )

    @latest.setter
    def latest(self, item_or_collection: Optional[T]) -> None:
        self.obj.clear_links(VersionRelType.LATEST)
        if item_or_collection is not None:
            self.obj.add_link(
                pystac.Link(
                    VersionRelType.LATEST, item_or_collection, pystac.MediaType.JSON
                )
            )

    @property
    def predecessor(self) -> Optional[T]:
        """Gets or sets the :class:`~pystac.Link` to the :class:`~pystac.Item`
        representing the resource containing the predecessor version in the version
        history.
        """
        return map_opt(
            lambda x: cast(T, x),
            next(iter(self.obj.get_stac_objects(VersionRelType.PREDECESSOR)), None),
        )

    @predecessor.setter
    def predecessor(self, item_or_collection: Optional[T]) -> None:
        self.obj.clear_links(VersionRelType.PREDECESSOR)
        if item_or_collection is not None:
            self.obj.add_link(
                pystac.Link(
                    VersionRelType.PREDECESSOR,
                    item_or_collection,
                    pystac.MediaType.JSON,
                )
            )

    @property
    def successor(self) -> Optional[T]:
        """Gets or sets the :class:`~pystac.Link` to the :class:`~pystac.Item`
        representing the resource containing the successor version in the version
        history.
        """
        return map_opt(
            lambda x: cast(T, x),
            next(iter(self.obj.get_stac_objects(VersionRelType.SUCCESSOR)), None),
        )

    @successor.setter
    def successor(self, item_or_collection: Optional[T]) -> None:
        self.obj.clear_links(VersionRelType.SUCCESSOR)
        if item_or_collection is not None:
            self.obj.add_link(
                pystac.Link(
                    VersionRelType.SUCCESSOR, item_or_collection, pystac.MediaType.JSON
                )
            )

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> "VersionExtension[T]":
        """Extends the given STAC Object with properties from the :stac-ext:`Versioning
        Indicators Extension <version>`.

        This extension can be applied to instances of :class:`~pystac.Item` or
        :class:`~pystac.Collection`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Collection):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(VersionExtension[T], CollectionVersionExtension(obj))
        if isinstance(obj, pystac.Item):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(VersionExtension[T], ItemVersionExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"Version extension does not apply to type '{type(obj).__name__}'"
            )


class CollectionVersionExtension(VersionExtension[pystac.Collection]):
    """A concrete implementation of :class:`VersionExtension` on a
    :class:`~pystac.Collection` that extends the properties of the Collection to
    include properties defined in the :stac-ext:`Versioning Indicators Extension
    <version>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`VersionExtension.ext` on an :class:`~pystac.Collection` to extend it.
    """

    collection: pystac.Collection
    links: List[pystac.Link]
    properties: Dict[str, Any]

    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields
        self.links = collection.links
        super().__init__(self.collection)

    def __repr__(self) -> str:
        return "<CollectionVersionExtension Item id={}>".format(self.collection.id)


class ItemVersionExtension(VersionExtension[pystac.Item]):
    """A concrete implementation of :class:`VersionExtension` on an
    :class:`~pystac.Item` that extends the properties of the Item to include properties
    defined in the :stac-ext:`Versioning Indicators Extension <version>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`VersionExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    links: List[pystac.Link]
    properties: Dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties
        self.links = item.links
        super().__init__(self.item)

    def __repr__(self) -> str:
        return "<ItemVersionExtension Item id={}>".format(self.item.id)


class VersionExtensionHooks(ExtensionHooks):
    schema_uri = SCHEMA_URI
    prev_extension_ids = {"version"}
    stac_object_types = {pystac.STACObjectType.COLLECTION, pystac.STACObjectType.ITEM}

    def get_object_links(self, so: pystac.STACObject) -> Optional[List[str]]:
        if isinstance(so, pystac.Collection) or isinstance(so, pystac.Item):
            return [
                VersionRelType.LATEST,
                VersionRelType.PREDECESSOR,
                VersionRelType.SUCCESSOR,
            ]
        return None


VERSION_EXTENSION_HOOKS: ExtensionHooks = VersionExtensionHooks()
