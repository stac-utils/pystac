from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Type, cast, TYPE_CHECKING, Union

import pystac
from pystac import STACError
from pystac.link import Link
from pystac.utils import StringEnum, is_absolute_href, make_absolute_href

if TYPE_CHECKING:
    from pystac.catalog import Catalog as Catalog_Type


class STACObjectType(StringEnum):
    CATALOG = "Catalog"
    COLLECTION = "Collection"
    ITEM = "Feature"


class STACObject(ABC):
    """A base class for other PySTAC classes that contains a variety of useful
    methods for dealing with links, copying objects, accessing extensions, and reading
    and writing files. You shouldn't use STACObject directly, but instead access this
    functionality through the implementing classes.
    """

    id: str
    """The ID of the STAC Object."""

    links: List[Link]
    """A list of :class:`~pystac.Link` objects representing all links associated with
    this STAC Object."""

    stac_extensions: List[str]
    """A list of schema URIs for STAC Extensions implemented by this STAC Object."""

    STAC_OBJECT_TYPE: STACObjectType

    def __init__(self, stac_extensions: List[str]) -> None:
        self.links = []
        self.stac_extensions = stac_extensions

    def validate(self) -> List[Any]:
        """Validate this STACObject.

        Returns a list of validation results, which depends on the validation
        implementation. For JSON Schema validation, this will be a list
        of schema URIs that were used during validation.

        Raises:
            STACValidationError
        """
        import pystac.validation

        return pystac.validation.validate(self)

    def add_link(self, link: Link) -> None:
        """Add a link to this object's set of links.

        Args:
             link : The link to add.
        """
        link.set_owner(self)
        self.links.append(link)

    def add_links(self, links: List[Link]) -> None:
        """Add links to this object's set of links.

        Args:
             links : The links to add.
        """

        for link in links:
            self.add_link(link)

    def remove_links(self, rel: Union[str, pystac.RelType]) -> None:
        """Remove links to this object's set of links that match the given ``rel``.

        Args:
             rel : The :class:`~pystac.Link` ``rel`` to match on.
        """

        self.links = [link for link in self.links if link.rel != rel]

    def get_single_link(
        self,
        rel: Union[str, pystac.RelType],
        media_type: Optional[Union[str, pystac.MediaType]] = None,
    ) -> Optional[Link]:
        """Get single link that match the given ``rel`` and, optionally,
        ``media_type``. If ``media_type`` is ``None``, then the link is
        matched only on the ``rel`` value.

        Args:
             rel : The :class:`~pystac.Link` ``rel`` to match on.
             media_type: The :class:`~pystack.MediaType` ``media_type`` to match on
        """

        return next(
            (
                link
                for link in self.links
                if link.rel == rel
                and (media_type is None or link.media_type == media_type)
            ),
            None,
        )

    def get_links(
        self,
        rel: Optional[Union[str, pystac.RelType]] = None,
        media_type: Optional[Union[str, pystac.MediaType]] = None,
    ) -> List[Link]:
        """Gets the :class:`~pystac.Link` instances associated with this object.

        Args:
            rel : If set, filter links such that only those
                matching this relationship are returned.
            media_type: If set, filter the links such that only
                those matching media_type are returned

        Returns:
            List[:class:`~pystac.Link`]: A list of links that match ``rel`` if set,
                or else all links associated with this object.
        """
        if rel is None:
            return self.links
        else:
            return [
                link
                for link in self.links
                if link.rel == rel
                and (media_type is None or link.media_type == media_type)
            ]

    def clear_links(self, rel: Optional[Union[str, pystac.RelType]] = None) -> None:
        """Clears all :class:`~pystac.Link` instances associated with this object.

        Args:
            rel : If set, only clear links that match this relationship.
        """
        if rel is not None:
            self.links = [link for link in self.links if link.rel != rel]
        else:
            self.links = []

    def get_root_link(self) -> Optional[Link]:
        """Get the :class:`~pystac.Link` representing
        the root for this object.

        Returns:
            :class:`~pystac.Link` or None: The root link for this object,
            or ``None`` if no root link is set.
        """
        return self.get_single_link(pystac.RelType.ROOT)

    @property
    def self_href(self) -> str:
        """Gets the absolute HREF that is represented by the ``rel == 'self'``
        :class:`~pystac.Link`.

        Raises:
            ValueError: If the self_href is not set, this method will throw
                a ValueError. Use get_self_href if there may not be an href set.
        """
        result = self.get_self_href()
        if result is None:
            raise ValueError(f"{self} does not have a self_href set.")
        return result

    def get_self_href(self) -> Optional[str]:
        """Gets the absolute HREF that is represented by the ``rel == 'self'``
        :class:`~pystac.Link`.

        Returns:
            str or None: The absolute HREF of this object, or ``None`` if
            there is no self link defined.

        Note:
            A self link can exist for objects, even if the link is not read or
            written to the JSON-serialized version of the object. Any object
            read from :func:`STACObject.from_file <pystac.STACObject.from_file>` will
            have the HREF the file was read from set as it's self HREF. All self
            links have absolute (as opposed to relative) HREFs.
        """
        self_link = self.get_single_link(pystac.RelType.SELF)
        if self_link and self_link.has_target_href():
            return self_link.get_target_str()
        else:
            return None

    def set_self_href(self, href: Optional[str]) -> None:
        """Sets the absolute HREF that is represented by the ``rel == 'self'``
        :class:`~pystac.Link`.

        Args:
            href : The absolute HREF of this object. If the given HREF
                is not absolute, it will be transformed to an absolute
                HREF based on the current working directory. If this is None
                the call will clear the self HREF link.
        """
        root_link = self.get_root_link()
        if root_link is not None and root_link.is_resolved():
            cast(pystac.Catalog, root_link.target)._resolved_objects.remove(self)

        self.remove_links(pystac.RelType.SELF)
        if href is not None:
            self.add_link(Link.self_href(href))

        if root_link is not None and root_link.is_resolved():
            cast(pystac.Catalog, root_link.target)._resolved_objects.cache(self)

    def get_root(self) -> Optional["Catalog_Type"]:
        """Get the :class:`~pystac.Catalog` or :class:`~pystac.Collection` to
        the root for this object. The root is represented by a
        :class:`~pystac.Link` with ``rel == 'root'``.

        Returns:
            Catalog, Collection, or None:
            The root object for this object, or ``None`` if no root link is set.
        """
        root_link = self.get_root_link()
        if root_link:
            if not root_link.is_resolved():
                root_link.resolve_stac_object()
                # Use set_root, so Catalogs can merge ResolvedObjectCache instances.
                self.set_root(cast(pystac.Catalog, root_link.target))
            return cast(pystac.Catalog, root_link.target)
        else:
            return None

    def set_root(self, root: Optional["Catalog_Type"]) -> None:
        """Sets the root :class:`~pystac.Catalog` or :class:`~pystac.Collection`
        for this object.

        Args:
            root : The root
                object to set. Passing in None will clear the root.
        """
        root_link_index = next(
            iter(
                [
                    i
                    for i, link in enumerate(self.links)
                    if link.rel == pystac.RelType.ROOT
                ]
            ),
            None,
        )

        # Remove from old root resolution cache
        if root_link_index is not None:
            root_link = self.links[root_link_index]
            if root_link.is_resolved():
                cast(pystac.Catalog, root_link.target)._resolved_objects.remove(self)

        if root is None:
            self.remove_links(pystac.RelType.ROOT)
        else:
            new_root_link = Link.root(root)
            if root_link_index is not None:
                self.links[root_link_index] = new_root_link
                new_root_link.set_owner(self)
            else:
                self.add_link(new_root_link)
            root._resolved_objects.cache(self)

    def get_parent(self) -> Optional["Catalog_Type"]:
        """Get the :class:`~pystac.Catalog` or :class:`~pystac.Collection` to
        the parent for this object. The root is represented by a
        :class:`~pystac.Link` with ``rel == 'parent'``.

        Returns:
            Catalog, Collection, or None:
                The parent object for this object,
                or ``None`` if no root link is set.
        """
        parent_link = self.get_single_link(pystac.RelType.PARENT)
        if parent_link:
            return cast(pystac.Catalog, parent_link.resolve_stac_object().target)
        else:
            return None

    def set_parent(self, parent: Optional["Catalog_Type"]) -> None:
        """Sets the parent :class:`~pystac.Catalog` or :class:`~pystac.Collection`
        for this object.

        Args:
            parent : The parent
                object to set. Passing in None will clear the parent.
        """

        self.remove_links(pystac.RelType.PARENT)
        if parent is not None:
            self.add_link(Link.parent(parent))

    def get_stac_objects(
        self, rel: Union[str, pystac.RelType], typ: Optional[Type["STACObject"]] = None
    ) -> Iterable["STACObject"]:
        """Gets the :class:`~pystac.STACObject` instances that are linked to
        by links with their ``rel`` property matching the passed in argument.

        Args:
            rel : The relation to match each :class:`~pystac.Link`'s
                ``rel`` property against.
            typ : If not ``None``, objects will only be yielded if they are instances of
                ``typ``.

        Returns:
            Iterable[STACObjects]: A possibly empty iterable of STACObjects that are
            connected to this object through links with the given ``rel`` and are of
            type ``typ`` (if given).
        """
        links = self.links[:]
        for i in range(0, len(links)):
            link = links[i]
            if link.rel == rel:
                link.resolve_stac_object(root=self.get_root())
                if typ is None or isinstance(link.target, typ):
                    yield cast("STACObject", link.target)

    def save_object(
        self,
        include_self_link: bool = True,
        dest_href: Optional[str] = None,
        stac_io: Optional[pystac.StacIO] = None,
    ) -> None:
        """Saves this STAC Object to it's 'self' HREF.

        Args:
            include_self_link : If this is true, include the 'self' link with
                this object. Otherwise, leave out the self link.
            dest_href : Optional HREF to save the file to. If None, the object
                will be saved to the object's self href.
            stac_io: Optional instance of StacIO to use. If not provided, will use the
                instance set on the object's root if available, otherwise will use the
                default instance.


        Raises:
            :class:`~pystac.STACError`: If no self href is set, this error will be
            raised.

        Note:
            When to include a self link is described in the :stac-spec:`Use of Links
            section of the STAC best practices document
            <best-practices.md#use-of-links>`
        """
        if stac_io is None:
            root = self.get_root()
            if root is not None:
                root_stac_io = root._stac_io
                if root_stac_io is not None:
                    stac_io = root_stac_io

            if stac_io is None:
                stac_io = pystac.StacIO.default()

        if dest_href is None:
            self_href = self.get_self_href()
            if self_href is None:
                raise STACError(
                    "Self HREF must be set before saving without an explicit dest_href."
                )
            dest_href = self_href

        stac_io.save_json(dest_href, self.to_dict(include_self_link=include_self_link))

    def full_copy(
        self,
        root: Optional["Catalog_Type"] = None,
        parent: Optional["Catalog_Type"] = None,
    ) -> "STACObject":
        """Create a full copy of this STAC object and any stac objects linked to by
        this object.

        Args:
            root : Optional root to set as the root of the copied object,
                and any other copies that are contained by this object.
            parent : Optional parent to set as the parent of the copy
                of this object.

        Returns:
            STACObject: A full copy of this object, as well as any objects this object
                links to.
        """
        clone = self.clone()

        if root is None and isinstance(clone, pystac.Catalog):
            root = clone

        # Set the root of the STAC Object using the base class,
        # avoiding child class overrides
        # extra logic which can be incompatible with the full copy.
        STACObject.set_root(clone, cast(pystac.Catalog, root))

        if parent:
            clone.set_parent(parent)

        link_rels = set(self._object_links())
        for link in clone.links:
            if link.rel in link_rels:
                link.resolve_stac_object()
                target = cast(STACObject, link.target)
                if root is not None and target in root._resolved_objects:
                    cached_target = root._resolved_objects.get(target)
                    assert cached_target is not None
                    target = cached_target
                else:
                    target_parent = None
                    if link.rel in [
                        pystac.RelType.CHILD,
                        pystac.RelType.ITEM,
                    ] and isinstance(clone, pystac.Catalog):
                        target_parent = clone
                    copied_target = target.full_copy(root=root, parent=target_parent)
                    if root is not None:
                        root._resolved_objects.cache(copied_target)
                    target = copied_target
                if link.rel in [pystac.RelType.CHILD, pystac.RelType.ITEM]:
                    target.set_root(root)
                    if isinstance(clone, pystac.Catalog):
                        target.set_parent(clone)
                link.target = target

        return clone

    def resolve_links(self) -> None:
        """Ensure all STACObjects linked to by this STACObject are
        resolved. This is important for operations such as changing
        HREFs.

        This method mutates the entire catalog tree.
        """
        link_rels = set(self._object_links()) | {
            pystac.RelType.ROOT,
            pystac.RelType.PARENT,
        }

        for link in self.links:
            if link.rel in link_rels:
                if not link.is_resolved():
                    link.resolve_stac_object(root=self.get_root())

    @abstractmethod
    def _object_links(self) -> List[str]:
        """Inherited classes return a list of link 'rel' types that represent
        STACObjects linked to by this object (not including root, parent or self).
        This can include optional relations (which may not be present).
        """
        raise NotImplementedError

    @abstractmethod
    def to_dict(
        self, include_self_link: bool = True, transform_hrefs: bool = True
    ) -> Dict[str, Any]:
        """Generate a dictionary representing the JSON of this serialized object.

        Args:
            include_self_link : If True, the dict will contain a self link
                to this object. If False, the self link will be omitted.
            transform_hrefs: If True, transform the HREF of hierarchical links
                based on the type of catalog this object belongs to (if any).
                I.e. if this object belongs to a root catalog that is
                RELATIVE_PUBLISHED or SELF_CONTAINED,
                hierarchical link HREFs will be transformed to be relative to the
                catalog root.

            dict: A serialization of the object that can be written out as JSON.
        """
        raise NotImplementedError

    @abstractmethod
    def clone(self) -> "STACObject":
        """Clones this object.

        Cloning an object will make a copy of all properties and links of the object;
        however, it will not make copies of the targets of links (i.e. it is not a
        deep copy). To copy a STACObject fully, with all linked elements also copied,
        use :func:`STACObject.full_copy <pystac.STACObject.full_copy>`.

        Returns:
            STACObject: The clone of this object.
        """
        raise NotImplementedError

    @classmethod
    def from_file(
        cls, href: str, stac_io: Optional[pystac.StacIO] = None
    ) -> "STACObject":
        """Reads a STACObject implementation from a file.

        Args:
            href : The HREF to read the object from.
            stac_io: Optional instance of StacIO to use. If not provided, will use the
                default instance.

        Returns:
            The specific STACObject implementation class that is represented
            by the JSON read from the file located at HREF.
        """
        if cls == STACObject:
            return pystac.read_file(href)

        if stac_io is None:
            stac_io = pystac.StacIO.default()

        if not is_absolute_href(href):
            href = make_absolute_href(href)

        d = stac_io.read_json(href)
        o = cls.from_dict(d, href=href, migrate=True, preserve_dict=False)

        # Set the self HREF, if it's not already set to something else.
        if o.get_self_href() is None:
            o.set_self_href(href)

        # If this is a root catalog, set the root to the catalog instance.
        root_link = o.get_root_link()
        if root_link is not None:
            if not root_link.is_resolved():
                if root_link.get_absolute_href() == href:
                    o.set_root(cast(pystac.Catalog, o))
        return o

    @classmethod
    @abstractmethod
    def from_dict(
        cls,
        d: Dict[str, Any],
        href: Optional[str] = None,
        root: Optional["Catalog_Type"] = None,
        migrate: bool = False,
        preserve_dict: bool = True,
    ) -> "STACObject":
        """Parses this STACObject from the passed in dictionary.

        Args:
            d : The dict to parse.
            href : Optional href that is the file location of the object being
                parsed.
            root : Optional root catalog for this object.
                If provided, the root of the returned STACObject will be set
                to this parameter.
            migrate: Use True if this dict represents JSON from an older STAC object,
                so that migrations are run against it.
            preserve_dict: If False, the dict parameter ``d`` may be modified
                during this method call. Otherwise the dict is not mutated.
                Defaults to True, which results results in a deepcopy of the
                parameter. Set to False when possible to avoid the performance
                hit of a deepcopy.

        Returns:
            STACObject: The STACObject parsed from this dict.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def matches_object_type(cls, d: Dict[str, Any]) -> bool:
        """Returns a boolean indicating whether the given dictionary represents a valid
        instance of this :class:`~STACObject` sub-class.

        Args:
            d : A dictionary to identify
        """
        raise NotImplementedError
