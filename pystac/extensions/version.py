"""Implement the version extension.

https://github.com/radiantearth/stac-spec/tree/dev/extensions/version

Note that the version/schema.json does not know about the links.
"""

from pystac.extensions.hooks import ExtensionHooks
from typing import List, Optional, cast

import pystac as ps
from pystac import STACError

VERSION_EXT_SCHEMA = "https://stac-extensions.github.io/version/v1.0.0/schema.json"

# STAC fields - These are unusual for an extension in that they do not have
# a prefix.  e.g. nothing like "ver:"
VERSION: str = 'version'
DEPRECATED: str = 'deprecated'

# Link "rel" attribute values.
LATEST: str = 'latest-version'
PREDECESSOR: str = 'predecessor-version'
SUCCESSOR: str = 'successor-version'

# Media type for links.
MEDIA_TYPE: str = 'application/json'


class VersionItemExt():
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
    item: ps.Item

    def __init__(self, an_item: ps.Item) -> None:
        self.item = an_item

    def apply(self,
              version: str,
              deprecated: Optional[bool] = None,
              latest: Optional[ps.Item] = None,
              predecessor: Optional[ps.Item] = None,
              successor: Optional[ps.Item] = None) -> None:
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
        result = self.item.properties.get(VERSION)
        if result is None:
            raise STACError(f"Item {self.item.id} has version extension but no version property")
        return result

    @version.setter
    def version(self, v: str) -> None:
        self.item.properties[VERSION] = v

    @property
    def deprecated(self) -> bool:
        """Get or sets is the item is deprecated.

        Returns:
            bool
        """
        return bool(self.item.properties.get(DEPRECATED))

    @deprecated.setter
    def deprecated(self, v: bool) -> None:
        if not isinstance(v, bool):
            raise ps.STACError(DEPRECATED + ' must be a bool')
        self.item.properties[DEPRECATED] = v

    @property
    def latest(self) -> Optional[ps.Item]:
        """Get or sets the most recent item.

        Returns:
            Item or None
        """
        result = next(iter(self.item.get_stac_objects(LATEST)), None)
        if result is None:
            return None
        return cast(ps.Item, result)

    @latest.setter
    def latest(self, source_item: ps.Item) -> None:
        self.item.clear_links(LATEST)
        if source_item:
            self.item.add_link(ps.Link(LATEST, source_item, MEDIA_TYPE))

    @property
    def predecessor(self) -> Optional[ps.Item]:
        """Get or sets the previous item.

        Returns:
            Item or None
        """
        result = next(iter(self.item.get_stac_objects(PREDECESSOR)), None)
        if result is None:
            return None
        return cast(ps.Item, result)

    @predecessor.setter
    def predecessor(self, source_item: ps.Item) -> None:
        self.item.clear_links(PREDECESSOR)
        if source_item:
            self.item.add_link(ps.Link(PREDECESSOR, source_item, MEDIA_TYPE))

    @property
    def successor(self) -> Optional[ps.Item]:
        """Get or sets the next item.

        Returns:
            Item or None
        """
        result = next(iter(self.item.get_stac_objects(SUCCESSOR)), None)
        if result is None:
            return None
        return cast(ps.Item, result)

    @successor.setter
    def successor(self, source_item: ps.Item) -> None:
        self.item.clear_links(SUCCESSOR)
        if source_item:
            self.item.add_link(ps.Link(SUCCESSOR, source_item, MEDIA_TYPE))

    @classmethod
    def from_item(cls, an_item: ps.Item) -> "VersionItemExt":
        return cls(an_item)

    @classmethod
    def _object_links(cls) -> List[str]:
        return [LATEST, PREDECESSOR, SUCCESSOR]


class VersionCollectionExt():
    """VersionCollectionExt extends Collection to add version and deprecated properties
    along with links to the latest, predecessor, and successor Collections.

    Args:
        a_collection (Collection): The collection to be extended.

    Attributes:
        collection (Collection): The collection that is being extended.

    Note:
        Using VersionCollectionExt to directly wrap a collection will add the
        'version' extension ID to the collections's stac_extensions.
    """
    collection: ps.Collection

    def __init__(self, a_collection: ps.Collection) -> None:
        self.collection = a_collection

    @property
    def version(self) -> str:
        """Get or sets a version string of the collection.

        Returns:
            str
        """
        result = self.collection.extra_fields.get(VERSION)
        if result is None:
            raise STACError(f"Collection {self.collection.id} does not have property {VERSION}")
        return result

    @version.setter
    def version(self, v: str) -> None:
        self.collection.extra_fields[VERSION] = v

    @property
    def deprecated(self) -> bool:
        """Get or sets is the collection is deprecated.

        Returns:
            bool
        """
        return bool(self.collection.extra_fields.get(DEPRECATED))

    @deprecated.setter
    def deprecated(self, v: bool) -> None:
        if not isinstance(v, bool):
            raise ps.STACError(DEPRECATED + ' must be a bool')
        self.collection.extra_fields[DEPRECATED] = v

    @property
    def latest(self) -> Optional[ps.Collection]:
        """Get or sets the most recent collection.

        Returns:
            Collection or None
        """
        result = next(iter(self.collection.get_stac_objects(LATEST)), None)
        if result is None:
            return None
        return cast(ps.Collection, result)

    @latest.setter
    def latest(self, source_collection: ps.Collection) -> None:
        self.collection.clear_links(LATEST)
        if source_collection:
            self.collection.add_link(ps.Link(LATEST, source_collection, MEDIA_TYPE))

    @property
    def predecessor(self) -> Optional[ps.Collection]:
        """Get or sets the previous collection.

        Returns:
            Collection or None
        """
        result = next(iter(self.collection.get_stac_objects(PREDECESSOR)), None)
        if result is None:
            return None
        return cast(ps.Collection, result)

    @predecessor.setter
    def predecessor(self, source_collection: ps.Collection) -> None:
        self.collection.clear_links(PREDECESSOR)
        if source_collection:
            self.collection.add_link(ps.Link(PREDECESSOR, source_collection, MEDIA_TYPE))

    @property
    def successor(self) -> Optional[ps.Collection]:
        """Get or sets the next collection.

        Returns:
            Collection or None
        """
        result = next(iter(self.collection.get_stac_objects(SUCCESSOR)), None)
        if result is None:
            return None
        return cast(ps.Collection, result)

    @successor.setter
    def successor(self, source_collection: ps.Collection) -> None:
        self.collection.clear_links(SUCCESSOR)
        if source_collection:
            self.collection.add_link(ps.Link(SUCCESSOR, source_collection, MEDIA_TYPE))

    @classmethod
    def from_collection(cls, a_collection: ps.Collection) -> "VersionCollectionExt":
        return cls(a_collection)

    @classmethod
    def _object_links(cls) -> List[str]:
        return [LATEST, PREDECESSOR, SUCCESSOR]

    def apply(self,
              version: str,
              deprecated: Optional[bool] = None,
              latest: Optional[ps.Collection] = None,
              predecessor: Optional[ps.Collection] = None,
              successor: Optional[ps.Collection] = None) -> None:
        """Applies version extension properties to the extended Collection.

        Args:
            version (str): The version string for the collection.
            deprecated (bool): Optional flag set to True if an Collection is
                deprecated with the potential to be removed.  Defaults to false
                if not present.
            latest (Collection): Collection with the latest (e.g., current) version.
            predecessor (Collection): Collection with the previous version.
            successor (Collection): Collection with the next most recent version.
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


class VersionExtensionHooks(ExtensionHooks):
    schema_uri = VERSION_EXT_SCHEMA

    def get_object_links(self, so: ps.STACObject) -> Optional[List[str]]:
        if isinstance(so, ps.Collection) or isinstance(so, ps.Item):
            return [LATEST, PREDECESSOR, SUCCESSOR]
        return None


VERSION_EXTENSION_HOOKS: ExtensionHooks = VersionExtensionHooks()