import os
from copy import copy
from urllib.parse import urlparse

from pystac import STACError
from pystac.io import STAC_IO
from pystac.utils import (make_absolute_href, make_relative_href, is_absolute_href)

class LinkType:
    ABSOLUTE = 'ABSOLUTE'
    RELATIVE = 'RELATIVE'

class Link:
    def __init__(self,
                 rel,
                 target,
                 media_type=None,
                 title=None,
                 properties=None,
                 link_type=LinkType.ABSOLUTE):
        self.rel = rel
        self.target = target # An object or an href
        self.media_type = media_type
        self.title = title
        self.properties = properties
        self.link_type = link_type
        self.owner = None

    def set_owner(self, owner):
        self.owner = owner
        return self

    def make_absolute(self):
        self.link_type = LinkType.ABSOLUTE
        return self

    def make_relative(self):
        self.link_type = LinkType.RELATIVE
        return self

    def get_href(self):
        """Gets the HREF for this link.

        If the link is relative and has an owner, will return a relative HREF, otherwise
        will return the absolute href.
        """
        href = self.get_absolute_href()
        if self.link_type == LinkType.RELATIVE:
            if self.owner is not None:
                href = make_relative_href(href, self.owner.get_self_href())

        return href

    def get_absolute_href(self):
        """Gets the aboslute href for this link, if possible.

        If this link has no owner, this will return whatever the
        target is (as it cannot determine the absolute path, if the link
        href is relative)."""
        if self.is_resolved():
            href = self.target.get_self_href()
        else:
            href = self.target

        if self.owner is not None:
            href = make_absolute_href(href, self.owner.get_self_href())

        return href

    def __repr__(self):
        return '<Link rel={} target={}>'.format(self.rel, self.target)

    def resolve_stac_object(self, root=None):
        """Resolves a STAC object from the HREF of this link, if the link is not
        already resolved.

        Params:
          root -    The root of the catalog for this link. This root's resolved object cache is used
                    to search for previously resolved instances of the STAC object.
        """
        if isinstance(self.target, str):
            # If it's a relative link, base it off the parent.
            target_path = self.target
            parsed = urlparse(self.target)
            if parsed.scheme == '':
                if not os.path.isabs(parsed.path):
                    if self.owner is None:
                        raise STACError('Relative path {} encountered '
                                        'without owner.'.format(target_path))
                    owner_href = self.owner.get_self_href()
                    if owner_href is None:
                        raise STACError('Relative path {} encountered '
                                        'without owner "self" link set.'.format(target_path))
                    target_path = make_absolute_href(self.target, owner_href)

            obj = STAC_IO.read_stac_object(target_path)
            obj.set_self_href(target_path)
        else:
            obj = self.target

        if root is not None:
            self.target = root._resolved_objects.get_or_set(obj)
            self.target.set_root(root, link_type=self.link_type)
        else:
            self.target = obj

        if self.owner and self.rel in ['child', 'item']:
            self.target.set_parent(self.owner, link_type=self.link_type)

        return self

    def is_resolved(self):
        return not isinstance(self.target, str)

    def to_dict(self):
        d = { 'rel': self.rel }

        d['href'] = self.get_href()

        if self.media_type is not None:
            d['type'] = self.media_type

        if self.title is not None:
            d['title'] = self.title

        if self.properties:
            for k, v in self.properties.items():
                d[k] = v

        return d

    def clone(self):
        return Link(rel=self.rel,
                    target=self.target,
                    media_type=self.media_type,
                    title=self.title,
                    link_type=self.link_type)

    @staticmethod
    def from_dict(d):
        d = copy(d)
        rel = d.pop('rel')
        href = d.pop('href')
        media_type = d.pop('type', None)
        title = d.pop('title', None)

        properties = None
        if any(d):
            properties = d

        if rel == 'self' or is_absolute_href(href):
            link_type = LinkType.ABSOLUTE
        else:
            link_type = LinkType.RELATIVE

        return Link(rel=rel,
                    target=href,
                    media_type=media_type,
                    title=title,
                    properties=properties,
                    link_type=link_type)

    @staticmethod
    def root(c, link_type=LinkType.ABSOLUTE):
        """Creates a link to a root Catalog or Collection."""
        return Link('root', c, media_type='application/json', link_type=link_type)

    @staticmethod
    def parent(c, link_type=LinkType.ABSOLUTE):
        """Creates a link to a parent Catalog or Collection."""
        return Link('parent', c, media_type='application/json', link_type=link_type)

    @staticmethod
    def collection(c, link_type=LinkType.ABSOLUTE):
        """Creates a link to an item's Collection."""
        return Link('collection', c, media_type='application/json', link_type=link_type)

    @staticmethod
    def self_href(href):
        """Creates a self link to the file's location."""
        return Link('self', href, media_type='application/json')

    @staticmethod
    def child(c, title=None, link_type=LinkType.ABSOLUTE):
        """Creates a link to a child Catalog or Collection."""
        return Link('child', c, title=title, media_type='application/json', link_type=link_type)

    @staticmethod
    def item(item, title=None, link_type=LinkType.ABSOLUTE):
        """Creates a link to an Item."""
        return Link('item', item, title=title, media_type='application/json', link_type=link_type)
