from copy import copy

import pystac
from pystac import STACError
from pystac.stac_io import STAC_IO
from pystac.utils import (make_absolute_href, make_relative_href, is_absolute_href)

HIERARCHICAL_LINKS = ['root', 'child', 'parent', 'collection', 'item', 'items']


class Link:
    """A link is connects a :class:`~pystac.STACObject` to another entity.

    The target of a link can be either another STACObject, or
    an HREF. When serialized, links always refer to the HREF of the target.
    Links are lazily deserialized - this is, when you read in a link, it does
    not automatically load in the STACObject that is the target
    (if the link is pointing to a STACObject). When a user is crawling
    through a catalog or when additional metadata is required, PySTAC uses the
    :func:`Link.resolve_stac_object <pystac.Link.resolve_stac_object>` method
    to load in and deserialize STACObjects. This mechanism is used within
    the PySTAC codebase and normally does not need to be considered by the user -
    ideally the lazy deserialization of STACObjects is transparent to clients of PySTAC.

    Args:
        rel (str): The relation of the link (e.g. 'child', 'item')
        target (str or STACObject): The target of the link. If the link is
            unresolved, or the link is to something that is not a STACObject,
            the target is an HREF. If resolved, the target is a STACObject.
        media_type (str): Optional description of the media type. Registered Media Types
            are preferred. See :class:`~pystac.MediaType` for common media types.
        title (str): Optional title for this link.
        properties (dict): Optional, additional properties for this link. This is used by
            extensions as a way to serialize and deserialize properties on link
            object JSON.

    Attributes:
        rel (str): The relation of the link (e.g. 'child', 'item')
        target (str or STACObject): The target of the link. If the link is
            unresolved, or the link is to something that is not a STACObject,
            the target is an HREF. If resolved, the target is a STACObject.
        media_type (str or None): Optional description of the media type. Registered Media Types
            are preferred. See :class:`~pystac.MediaType` for common media types.
        title (str or None): Optional title for this link.
        properties (dict or None): Optional, additional properties for this link.
            This is used by extensions as a way to serialize and deserialize properties
            on link object JSON.
        owner (STACObject or None): The owner of this link. The link will use
            its owner's root catalog :class:`~pystac.resolved_object_cache.ResolvedObjectCache`
            to resolve objects, and will create absolute HREFs from relative HREFs against
            the owner's self HREF.
    """
    def __init__(self, rel, target, media_type=None, title=None, properties=None):
        self.rel = rel
        self.target = target  # An object or an href
        self.media_type = media_type
        self.title = title
        self.properties = properties
        self.owner = None

    def set_owner(self, owner):
        """Sets the owner of this link.

        Args:
            owner (STACObject): The owner of this link.
        """
        self.owner = owner
        return self

    def get_href(self):
        """Gets the HREF for this link.

        Returns:
            str: Returns this link's HREF. If there is an owner of the link and
            the root catalog (if there is one) is of type RELATIVE_PUBLISHED,
            then the HREF returned will be relative.
            In all other cases, this method will return an absolute HREF.
        """
        # get the self href
        if self.is_resolved():
            href = self.target.get_self_href()
        else:
            href = self.target

        if href and is_absolute_href(href) and self.owner and self.owner.get_root():
            root = self.owner.get_root()
            rel_links = HIERARCHICAL_LINKS + \
                pystac.STAC_EXTENSIONS.get_extended_object_links(self.owner)
            # if a hierarchical link with an owner and root, and relative catalog
            if root.is_relative() and self.rel in rel_links:
                href = make_relative_href(href, self.owner.get_self_href())

        return href

    def get_absolute_href(self):
        """Gets the absolute href for this link, if possible.

        Returns:
            str: Returns this link's HREF. It attempts to derive an absolute HREF
            from this link; however, if the link is relative, has no owner,
            and has an unresolved target, this will return a relative HREF.
        """
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

        Args:
            root (Catalog or Collection): Optional root of the catalog for this link.
                If provided, the root's resolved object cache is used to search for
                previously resolved instances of the STAC object.
        """
        if isinstance(self.target, str):
            target_href = self.target

            # If it's a relative link, base it off the parent.
            if not is_absolute_href(target_href):
                if self.owner is None:
                    raise STACError('Relative path {} encountered '
                                    'without owner or start_href.'.format(target_href))
                start_href = self.owner.get_self_href()

                if start_href is None:
                    raise STACError('Relative path {} encountered '
                                    'without owner "self" link set.'.format(target_href))

                target_href = make_absolute_href(target_href, start_href)
            obj = None

            if root is not None:
                obj = root._resolved_objects.get_by_href(target_href)

            if obj is None:
                obj = STAC_IO.read_stac_object(target_href, root=root)
                obj.set_self_href(target_href)
                if root is not None:
                    obj = root._resolved_objects.get_or_cache(obj)
                    obj.set_root(root)
        else:
            obj = self.target

        self.target = obj

        if self.owner and self.rel in ['child', 'item']:
            self.target.set_parent(self.owner)

        return self

    def is_resolved(self):
        """Determines if the link's target is a resolved STACObject.

        Returns:
            bool: True if this link is resolved.
        """
        return not isinstance(self.target, str)

    def to_dict(self):
        """Generate a dictionary representing the JSON of this serialized Link.

        Returns:
            dict: A serializion of the Link that can be written out as JSON.
        """

        d = {'rel': self.rel}

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
        """Clones this link.

        This makes a copy of all link information, but does not clone a STACObject
        if one is the target of this link.

        Returns:
            Link: The cloned link.
        """

        return Link(rel=self.rel, target=self.target, media_type=self.media_type, title=self.title)

    @staticmethod
    def from_dict(d):
        """Deserializes a Link from a dict.

        Args:
            d (dict): The dict that represents the Link in JSON

        Returns:
            Link: Link instance constructed from the dict.
        """
        d = copy(d)
        rel = d.pop('rel')
        href = d.pop('href')
        media_type = d.pop('type', None)
        title = d.pop('title', None)

        properties = None
        if any(d):
            properties = d

        return Link(rel=rel, target=href, media_type=media_type, title=title, properties=properties)

    @staticmethod
    def root(c):
        """Creates a link to a root Catalog or Collection."""
        return Link('root', c, media_type='application/json')

    @staticmethod
    def parent(c):
        """Creates a link to a parent Catalog or Collection."""
        return Link('parent', c, media_type='application/json')

    @staticmethod
    def collection(c):
        """Creates a link to an item's Collection."""
        return Link('collection', c, media_type='application/json')

    @staticmethod
    def self_href(href):
        """Creates a self link to a file's location."""
        return Link('self', href, media_type='application/json')

    @staticmethod
    def child(c, title=None):
        """Creates a link to a child Catalog or Collection."""
        return Link('child', c, title=title, media_type='application/json')

    @staticmethod
    def item(item, title=None):
        """Creates a link to an Item."""
        return Link('item', item, title=title, media_type='application/json')
