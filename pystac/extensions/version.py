"""Implement the version extension.

https://github.com/radiantearth/stac-spec/tree/dev/extensions/version
"""

import pystac
from pystac import collection
from pystac import Extensions
from pystac import item
from pystac import link
from pystac.extensions import base

LATEST = 'latest-version'
PREDECESSOR = 'predecessor-version'
SUCCESSOR = 'successor-version'

# Media type for links.
MEDIA_TYPE = 'application/json'


class VersionItemExt(base.ItemExtension):
    """Add an asset version string to a STAC Item."""
    def __init__(self, an_item):
        self.item = an_item

    def apply(self, version, deprecated=None, latest=None, predecessor=None, successor=None):
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
    def version(self):
        return self.item.properties.get('version')

    @version.setter
    def version(self, v):
        self.item.properties['version'] = v

    @property
    def deprecated(self):
        return bool(self.item.properties.get('deprecated'))

    @deprecated.setter
    def deprecated(self, v):
        if not isinstance(v, bool):
            raise pystac.STACError('deprecated must be a bool')
        self.item.properties['deprecated'] = v

    @property
    def latest(self):
        links = self.item.get_links(LATEST)
        if links:
            return links[0]

    @latest.setter
    def latest(self, source_item):
        self.item.add_link(link.Link(LATEST, source_item, MEDIA_TYPE))

    @property
    def predecessor(self):
        links = self.item.get_links(PREDECESSOR)
        if links:
            return links[0]

    @predecessor.setter
    def predecessor(self, source_item):
        self.item.add_link(link.Link(PREDECESSOR, source_item, MEDIA_TYPE))

    @property
    def successor(self):
        links = self.item.get_links(SUCCESSOR)
        if links:
            return links[0]

    @successor.setter
    def successor(self, source_item):
        self.item.add_link(link.Link(SUCCESSOR, source_item, MEDIA_TYPE))

    @classmethod
    def from_item(cls, an_item):
        return cls(an_item)

    @classmethod
    def _object_links(cls):
        return [LATEST, PREDECESSOR, SUCCESSOR]


class VersionCollectionExt(base.CollectionExtension):
    """Add an asset version string to a STAC Collection."""
    def __init__(self, a_collection):
        self.collection = a_collection

    @property
    def version(self):
        return self.collection.extra_fields.get('version')

    @version.setter
    def version(self, v):
        self.collection.extra_fields['version'] = v

    @property
    def deprecated(self):
        return bool(self.collection.extra_fields.get('deprecated'))

    @deprecated.setter
    def deprecated(self, v):
        if not isinstance(v, bool):
            raise pystac.STACError('deprecated must be a bool')
        self.collection.extra_fields['deprecated'] = v

    @property
    def latest(self):
        links = self.collection.get_links(LATEST)
        if links:
            return links[0]

    @latest.setter
    def latest(self, source_collection):
        self.collection.add_link(link.Link(LATEST, source_collection, MEDIA_TYPE))

    @property
    def predecessor(self):
        links = self.collection.get_links(PREDECESSOR)
        if links:
            return links[0]

    @predecessor.setter
    def predecessor(self, source_collection):
        self.collection.add_link(link.Link(PREDECESSOR, source_collection, MEDIA_TYPE))

    @property
    def successor(self):
        links = self.collection.get_links(SUCCESSOR)
        if links:
            return links[0]

    @successor.setter
    def successor(self, source_collection):
        self.collection.add_link(link.Link(SUCCESSOR, source_collection, MEDIA_TYPE))

    @classmethod
    def from_collection(cls, a_collection):
        return cls(a_collection)

    @classmethod
    def _object_links(cls):
        return [LATEST, PREDECESSOR, SUCCESSOR]

    def apply(self, version, deprecated=None, latest=None, predecessor=None, successor=None):
        self.version = version
        if deprecated is not None:
            self.deprecated = deprecated
        if latest:
            self.latest = latest
        if predecessor:
            self.predecessor = predecessor
        if successor:
            self.successor = successor


VERSION_EXTENSION_DEFINITION = base.ExtensionDefinition(Extensions.VERSION, [
    base.ExtendedObject(item.Item, VersionItemExt),
    base.ExtendedObject(collection.Collection, VersionCollectionExt)
])
