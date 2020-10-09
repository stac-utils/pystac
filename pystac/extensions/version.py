"""Implement the version extension.

https://github.com/radiantearth/stac-spec/tree/dev/extensions/version
"""

import pystac
from pystac import Extensions
from pystac import item
from pystac import link
from pystac.extensions import base

LATEST_VERSION = 'latest-version'
PREDECESSOR_VERSION = 'predecessor-version'
SUCCESSOR_VERSION = 'successor-version'

# Media type for links.
MEDIA_TYPE = 'application/json'


class VersionItemExt(base.ItemExtension):
    """Add an asset version string to a STAC Item."""

    def __init__(self, an_item):
      self.item = an_item

    def apply(self, version,
              deprecated=None, latest=None, predecessor=None, successor=None):
        self.version = version
        if deprecated is not None:
            self.deprecated = deprecated
        if latest:
            self.latest_link = latest
        if predecessor:
            self.predecessor_link = predecessor
        if successor:
            self.successor_link = successor

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
    def latest_link(self):
        links = self.item.get_links(LATEST_VERSION)
        if links:
            return links[0]

    @latest_link.setter
    def latest_link(self, source_item):
        self.item.add_link(link.Link(LATEST_VERSION, source_item, MEDIA_TYPE))

    @property
    def predecessor_link(self):
        links = self.item.get_links(PREDECESSOR_VERSION)
        if links:
            return links[0]

    @predecessor_link.setter
    def predecessor_link(self, source_item):
        self.item.add_link(link.Link(PREDECESSOR_VERSION, source_item, MEDIA_TYPE))

    @property
    def successor_link(self):
        links = self.item.get_links(SUCCESSOR_VERSION)
        if links:
            return links[0]

    @successor_link.setter
    def successor_link(self, source_item):
        self.item.add_link(link.Link(SUCCESSOR_VERSION, source_item, MEDIA_TYPE))

    @classmethod
    def from_item(cls, an_item):
        return cls(an_item)

    @classmethod
    def _object_links(cls):
        return []  # TODO(schwehr): What should this return?


# TODO(schwehr): class VersionCollectionExt(base.CollectionExtension):

VERSION_EXTENSION_DEFINITION = base.ExtensionDefinition(
    Extensions.VERSION, [base.ExtendedObject(item.Item, VersionItemExt)])
