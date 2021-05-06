"""Implements the Version extension.

https://github.com/stac-extensions/version
"""

from pystac.utils import get_required, map_opt
from typing import Generic, List, Optional, Set, TypeVar, Union, cast

import pystac
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

# Link "rel" attribute values.
LATEST: str = "latest-version"
PREDECESSOR: str = "predecessor-version"
SUCCESSOR: str = "successor-version"

# Media type for links.
MEDIA_TYPE: str = "application/json"


class VersionExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[pystac.Collection, pystac.Item]],
):
    """VersionItemExt extends Item to add version and deprecated properties
    along with links to the latest, predecessor, and successor Items.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The item that is being extended.

    Note:
        Using VersionItemExt to directly wrap an item will add the 'version'
        extension ID to the item's stac_extensions.
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
        """Applies version extension properties to the extended Item.

        Args:
            version (str): The version string for the item.
            deprecated (bool): Optional flag set to True if an Item is
                deprecated with the potential to be removed.  Defaults to false
                if not present.
            latest (Item): Item with the latest (e.g., current) version.
            predecessor (Item): Item with the previous version.
            successor (Item): Item with the next most recent version.
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
        """Get or sets a version string of the item.

        Returns:
            str
        """
        return get_required(self._get_property(VERSION, str), self, VERSION)

    @version.setter
    def version(self, v: str) -> None:
        self._set_property(VERSION, v, pop_if_none=False)

    @property
    def deprecated(self) -> Optional[bool]:
        """Get or sets is the item is deprecated."""
        return self._get_property(DEPRECATED, bool)

    @deprecated.setter
    def deprecated(self, v: Optional[bool]) -> None:
        self._set_property(DEPRECATED, v)

    @property
    def latest(self) -> Optional[T]:
        """Get or sets the most recent version."""
        return map_opt(
            lambda x: cast(T, x), next(iter(self.obj.get_stac_objects(LATEST)), None)
        )

    @latest.setter
    def latest(self, item: Optional[T]) -> None:
        self.obj.clear_links(LATEST)
        if item is not None:
            self.obj.add_link(pystac.Link(LATEST, item, MEDIA_TYPE))

    @property
    def predecessor(self) -> Optional[T]:
        """Get or sets the previous item."""
        return map_opt(
            lambda x: cast(T, x),
            next(iter(self.obj.get_stac_objects(PREDECESSOR)), None),
        )

    @predecessor.setter
    def predecessor(self, item: Optional[T]) -> None:
        self.obj.clear_links(PREDECESSOR)
        if item is not None:
            self.obj.add_link(pystac.Link(PREDECESSOR, item, MEDIA_TYPE))

    @property
    def successor(self) -> Optional[T]:
        """Get or sets the next item."""
        return map_opt(
            lambda x: cast(T, x), next(iter(self.obj.get_stac_objects(SUCCESSOR)), None)
        )

    @successor.setter
    def successor(self, item: Optional[T]) -> None:
        self.obj.clear_links(SUCCESSOR)
        if item is not None:
            self.obj.add_link(pystac.Link(SUCCESSOR, item, MEDIA_TYPE))

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @staticmethod
    def ext(obj: T) -> "VersionExtension[T]":
        if isinstance(obj, pystac.Collection):
            return cast(VersionExtension[T], CollectionVersionExtension(obj))
        if isinstance(obj, pystac.Item):
            return cast(VersionExtension[T], ItemVersionExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"File extension does not apply to type {type(obj)}"
            )


class CollectionVersionExtension(VersionExtension[pystac.Collection]):
    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields
        self.links = collection.links
        super().__init__(self.collection)

    def __repr__(self) -> str:
        return "<CollectionVersionExtension Item id={}>".format(self.collection.id)


class ItemVersionExtension(VersionExtension[pystac.Item]):
    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties
        self.links = item.links
        super().__init__(self.item)

    def __repr__(self) -> str:
        return "<ItemVersionExtension Item id={}>".format(self.item.id)


class VersionExtensionHooks(ExtensionHooks):
    schema_uri = SCHEMA_URI
    prev_extension_ids: Set[str] = set(["version"])
    stac_object_types: Set[pystac.STACObjectType] = set(
        [pystac.STACObjectType.COLLECTION, pystac.STACObjectType.ITEM]
    )

    def get_object_links(self, so: pystac.STACObject) -> Optional[List[str]]:
        if isinstance(so, pystac.Collection) or isinstance(so, pystac.Item):
            return [LATEST, PREDECESSOR, SUCCESSOR]
        return None


VERSION_EXTENSION_HOOKS: ExtensionHooks = VersionExtensionHooks()
