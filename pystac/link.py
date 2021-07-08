from copy import copy
from typing import Any, Dict, Optional, TYPE_CHECKING, Union, cast

import pystac
from pystac.utils import make_absolute_href, make_relative_href, is_absolute_href

if TYPE_CHECKING:
    from pystac.stac_object import STACObject as STACObject_Type
    from pystac.item import Item as Item_Type
    from pystac.catalog import Catalog as Catalog_Type
    from pystac.collection import Collection as Collection_Type

HIERARCHICAL_LINKS = [
    pystac.RelType.ROOT,
    pystac.RelType.CHILD,
    pystac.RelType.PARENT,
    pystac.RelType.COLLECTION,
    pystac.RelType.ITEM,
    pystac.RelType.ITEMS,
]


class Link:
    """A link connects a :class:`~pystac.STACObject` to another entity.

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
        rel : The relation of the link (e.g. 'child', 'item'). Registered rel Types
            are preferred. See :class:`~pystac.RelType` for common media types.
        target : The target of the link. If the link is
            unresolved, or the link is to something that is not a STACObject,
            the target is an HREF. If resolved, the target is a STACObject.
        media_type : Optional description of the media type. Registered Media Types
            are preferred. See :class:`~pystac.MediaType` for common media types.
        title : Optional title for this link.
        extra_fields : Optional, additional fields for this link. This is used
            by extensions as a way to serialize and deserialize properties on link
            object JSON.
    """

    rel: Union[str, pystac.RelType]
    """The relation of the link (e.g. 'child', 'item'). Registered rel Types are
    preferred. See :class:`~pystac.RelType` for common media types."""

    target: Union[str, "STACObject_Type"]
    """The target of the link. If the link is unresolved, or the link is to something
    that is not a STACObject, the target is an HREF. If resolved, the target is a
    STACObject."""

    media_type: Optional[str]
    """Optional description of the media type. Registered Media Types are preferred.
    See :class:`~pystac.MediaType` for common media types."""

    title: Optional[str]
    """Optional title for this link."""

    extra_fields: Dict[str, Any]
    """Optional, additional fields for this link. This is used by extensions as a
    way to serialize and deserialize properties on link object JSON."""

    owner: Optional["STACObject_Type"]
    """The owner of this link. The link will use its owner's root catalog
    :class:`~pystac.resolved_object_cache.ResolvedObjectCache` to resolve objects, and
    will create absolute HREFs from relative HREFs against the owner's self HREF."""

    def __init__(
        self,
        rel: Union[str, pystac.RelType],
        target: Union[str, "STACObject_Type"],
        media_type: Optional[str] = None,
        title: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.rel = rel
        self.target = target
        self.media_type = media_type
        self.title = title
        self.extra_fields = extra_fields or {}
        self.owner = None

    def set_owner(self, owner: Optional["STACObject_Type"]) -> "Link":
        """Sets the owner of this link.

        Args:
            owner: The owner of this link. Pass None to clear.
        """
        self.owner = owner
        return self

    @property
    def href(self) -> str:
        """Returns the HREF for this link.

        If the href is None, this will throw an exception.
        Use get_href if there may not be an href.
        """
        result = self.get_href()
        if result is None:
            raise ValueError(f"{self} does not have an HREF set.")
        return result

    def get_href(self) -> Optional[str]:
        """Gets the HREF for this link.

        Returns:
            str: Returns this link's HREF. If there is an owner of the link and
            the root catalog (if there is one) is of type RELATIVE_PUBLISHED,
            then the HREF returned will be relative.
            In all other cases, this method will return an absolute HREF.
        """
        # get the self href
        if self.is_resolved():
            href = cast(pystac.STACObject, self.target).get_self_href()
        else:
            href = cast(Optional[str], self.target)

        if href and is_absolute_href(href) and self.owner and self.owner.get_root():
            root = self.owner.get_root()
            rel_links = [
                *HIERARCHICAL_LINKS,
                *pystac.EXTENSION_HOOKS.get_extended_object_links(self.owner),
            ]
            # if a hierarchical link with an owner and root, and relative catalog
            if root and root.is_relative() and self.rel in rel_links:
                owner_href = self.owner.get_self_href()
                if owner_href is not None:
                    href = make_relative_href(href, owner_href)

        return href

    @property
    def absolute_href(self) -> str:
        """Returns the absolute HREF for this link.

        If the href is None, this will throw an exception.
        Use get_absolute_href if there may not be an href set.
        """
        result = self.get_absolute_href()
        if result is None:
            raise ValueError(f"{self} does not have an HREF set.")
        return result

    def get_absolute_href(self) -> Optional[str]:
        """Gets the absolute href for this link, if possible.

        Returns:
            str: Returns this link's HREF. It attempts to derive an absolute HREF
            from this link; however, if the link is relative, has no owner,
            and has an unresolved target, this will return a relative HREF.
        """
        if self.is_resolved():
            href = cast(pystac.STACObject, self.target).get_self_href()
        else:
            href = cast(Optional[str], self.target)

        if href is not None and self.owner is not None:
            href = make_absolute_href(href, self.owner.get_self_href())

        return href

    def __repr__(self) -> str:
        return "<Link rel={} target={}>".format(self.rel, self.target)

    def resolve_stac_object(self, root: Optional["Catalog_Type"] = None) -> "Link":
        """Resolves a STAC object from the HREF of this link, if the link is not
        already resolved.

        Args:
            root : Optional root of the catalog for this link.
                If provided, the root's resolved object cache is used to search for
                previously resolved instances of the STAC object.
        """
        if isinstance(self.target, str):
            target_href = self.target

            # If it's a relative link, base it off the parent.
            if not is_absolute_href(target_href):
                if self.owner is None:
                    raise pystac.STACError(
                        "Relative path {} encountered "
                        "without owner or start_href.".format(target_href)
                    )
                start_href = self.owner.get_self_href()

                if start_href is None:
                    raise pystac.STACError(
                        "Relative path {} encountered "
                        'without owner "self" link set.'.format(target_href)
                    )

                target_href = make_absolute_href(target_href, start_href)
            obj = None

            stac_io: Optional[pystac.StacIO] = None

            if root is not None:
                obj = root._resolved_objects.get_by_href(target_href)
                stac_io = root._stac_io

            if obj is None:

                if stac_io is None:
                    if self.owner is not None:
                        if isinstance(self.owner, pystac.Catalog):
                            stac_io = self.owner._stac_io
                    if stac_io is None:
                        stac_io = pystac.StacIO.default()

                obj = stac_io.read_stac_object(target_href, root=root)
                obj.set_self_href(target_href)
                if root is not None:
                    obj = root._resolved_objects.get_or_cache(obj)
                    obj.set_root(root)
        else:
            obj = self.target

        self.target = obj

        if (
            self.owner
            and self.rel in [pystac.RelType.CHILD, pystac.RelType.ITEM]
            and isinstance(self.owner, pystac.Catalog)
        ):
            self.target.set_parent(self.owner)

        return self

    def is_resolved(self) -> bool:
        """Determines if the link's target is a resolved STACObject.

        Returns:
            bool: True if this link is resolved.
        """
        return not isinstance(self.target, str)

    def to_dict(self) -> Dict[str, Any]:
        """Generate a dictionary representing the JSON of this serialized Link.

        Returns:
            dict: A serialization of the Link that can be written out as JSON.
        """

        d: Dict[str, Any] = {"rel": self.rel, "href": self.get_href()}

        if self.media_type is not None:
            d["type"] = self.media_type

        if self.title is not None:
            d["title"] = self.title

        for k, v in self.extra_fields.items():
            d[k] = v

        return d

    def clone(self) -> "Link":
        """Clones this link.

        This makes a copy of all link information, but does not clone a STACObject
        if one is the target of this link.

        Returns:
            Link: The cloned link.
        """
        cls = self.__class__
        return cls(
            rel=self.rel,
            target=self.target,
            media_type=self.media_type,
            title=self.title,
        )

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Link":
        """Deserializes a Link from a dict.

        Args:
            d : The dict that represents the Link in JSON

        Returns:
            Link: Link instance constructed from the dict.
        """
        d = copy(d)
        rel = d.pop("rel")
        href = d.pop("href")
        media_type = d.pop("type", None)
        title = d.pop("title", None)

        extra_fields = None
        if any(d):
            extra_fields = d

        return cls(
            rel=rel,
            target=href,
            media_type=media_type,
            title=title,
            extra_fields=extra_fields,
        )

    @classmethod
    def root(cls, c: "Catalog_Type") -> "Link":
        """Creates a link to a root Catalog or Collection."""
        return cls(pystac.RelType.ROOT, c, media_type=pystac.MediaType.JSON)

    @classmethod
    def parent(cls, c: "Catalog_Type") -> "Link":
        """Creates a link to a parent Catalog or Collection."""
        return cls(pystac.RelType.PARENT, c, media_type=pystac.MediaType.JSON)

    @classmethod
    def collection(cls, c: "Collection_Type") -> "Link":
        """Creates a link to an item's Collection."""
        return cls(pystac.RelType.COLLECTION, c, media_type=pystac.MediaType.JSON)

    @classmethod
    def self_href(cls, href: str) -> "Link":
        """Creates a self link to a file's location."""
        return cls(pystac.RelType.SELF, href, media_type=pystac.MediaType.JSON)

    @classmethod
    def child(cls, c: "Catalog_Type", title: Optional[str] = None) -> "Link":
        """Creates a link to a child Catalog or Collection."""
        return cls(
            pystac.RelType.CHILD, c, title=title, media_type=pystac.MediaType.JSON
        )

    @classmethod
    def item(cls, item: "Item_Type", title: Optional[str] = None) -> "Link":
        """Creates a link to an Item."""
        return cls(
            pystac.RelType.ITEM, item, title=title, media_type=pystac.MediaType.JSON
        )

    @classmethod
    def canonical(
        cls,
        item_or_collection: Union["Item_Type", "Collection_Type"],
        title: Optional[str] = None,
    ) -> "Link":
        """Creates a canonical link to an Item or Collection."""
        return cls(
            pystac.RelType.CANONICAL,
            item_or_collection,
            title=title,
            media_type=pystac.MediaType.JSON,
        )
