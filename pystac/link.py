from copy import (copy, deepcopy)

from pystac import STACError
from pystac.stac_io import STAC_IO
from pystac.utils import (make_absolute_href, make_relative_href, is_absolute_href)


class LinkType:
    """Enumerates link types; used to determine if a link is absolute or relative."""
    ABSOLUTE = 'ABSOLUTE'
    RELATIVE = 'RELATIVE'


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
        link_type (str): The link type, either relative or absolute. Use one of
            :class:`~pystac.LinkType`.

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
        link_type (str): The link type, either relative or absolute. Use one of
            :class:`~pystac.LinkType`.
        owner (STACObject or None): The owner of this link. The link will use
            its owner's root catalog :class:`~pystac.resolved_object_cache.ResolvedObjectCache`
            to resolve objects, and will create absolute HREFs from relative HREFs against
            the owner's self HREF.
    """
    def __init__(self,
                 rel,
                 target,
                 media_type=None,
                 title=None,
                 properties=None,
                 link_type=LinkType.ABSOLUTE):
        self.rel = rel
        self.target = target  # An object or an href
        self.media_type = media_type
        self.title = title
        self.properties = properties
        self.link_type = link_type
        self.owner = None

    def set_owner(self, owner):
        """Sets the owner of this link.

        Args:
            owner (STACObject): The owner of this link.
        """
        self.owner = owner
        return self

    def make_absolute(self):
        """Sets the link type of this link to absolute"""
        self.link_type = LinkType.ABSOLUTE
        return self

    def make_relative(self):
        """Sets the link type of this link to relative"""
        self.link_type = LinkType.RELATIVE
        return self

    def get_href(self):
        """Gets the HREF for this link.

        Returns:
            str: Returns this link's HREF. If the link type is LinkType.RELATIVE,
            and there is an owner of the link, then the HREF returned will be
            relative. In all other cases, this method will return an absolute HREF.
        """
        if self.link_type == LinkType.RELATIVE:
            if self.is_resolved():
                href = self.target.get_self_href()
            else:
                href = self.target

            if href and is_absolute_href(href) and self.owner is not None:
                href = make_relative_href(href, self.owner.get_self_href())
        else:
            href = self.get_absolute_href()

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
                    obj.set_root(root, link_type=self.link_type)
        else:
            obj = self.target

        self.target = obj

        if self.owner and self.rel in ['child', 'item']:
            self.target.set_parent(self.owner, link_type=self.link_type)

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

        return deepcopy(d)

    def clone(self):
        """Clones this link.

        This makes a copy of all link information, but does not clone a STACObject
        if one is the target of this link.

        Returns:
            Link: The cloned link.
        """

        return Link(rel=self.rel,
                    target=self.target,
                    media_type=self.media_type,
                    title=self.title,
                    link_type=self.link_type)

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
        """Creates a self link to a file's location."""
        return Link('self', href, media_type='application/json', link_type=LinkType.ABSOLUTE)

    @staticmethod
    def child(c, title=None, link_type=LinkType.ABSOLUTE):
        """Creates a link to a child Catalog or Collection."""
        return Link('child', c, title=title, media_type='application/json', link_type=link_type)

    @staticmethod
    def item(item, title=None, link_type=LinkType.ABSOLUTE):
        """Creates a link to an Item."""
        return Link('item', item, title=title, media_type='application/json', link_type=link_type)
