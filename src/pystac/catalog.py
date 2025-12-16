from __future__ import annotations

import os
import warnings
from collections.abc import Callable, Iterable, Iterator
from copy import deepcopy
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    cast,
)

import pystac
import pystac.media_type
from pystac.cache import ResolvedObjectCache
from pystac.errors import STACError, STACTypeError
from pystac.layout import (
    APILayoutStrategy,
    BestPracticesLayoutStrategy,
    HrefLayoutStrategy,
    LayoutTemplate,
)
from pystac.link import Link
from pystac.serialization import (
    identify_stac_object,
    identify_stac_object_type,
    migrate_to_latest,
)
from pystac.stac_object import STACObject, STACObjectType
from pystac.utils import (
    HREF,
    StringEnum,
    _is_url,
    is_absolute_href,
    make_absolute_href,
    make_relative_href,
)

if TYPE_CHECKING:
    from pystac.asset import Asset
    from pystac.collection import Collection
    from pystac.extensions.ext import CatalogExt
    from pystac.item import Item

#: Generalized version of :class:`Catalog`
C = TypeVar("C", bound="Catalog")


class CatalogType(StringEnum):
    SELF_CONTAINED = "SELF_CONTAINED"
    """A 'self-contained catalog' is one that is designed for portability.
    Users may want to download an online catalog from and be able to use it on their
    local computer, so all links need to be relative.

    See:
        :stac-spec:`The best practices documentation on self-contained catalogs
        <best-practices.md#self-contained-catalogs>`
    """

    ABSOLUTE_PUBLISHED = "ABSOLUTE_PUBLISHED"
    """
    Absolute Published Catalog is a catalog that uses absolute links for everything,
    both in the links objects and in the asset hrefs.

    See:
        :stac-spec:`The best practices documentation on published catalogs
        <best-practices.md#published-catalogs>`
    """

    RELATIVE_PUBLISHED = "RELATIVE_PUBLISHED"
    """
    Relative Published Catalog is a catalog that uses relative links for everything, but
    includes an absolute self link at the root catalog, to identify its online location.

    See:
        :stac-spec:`The best practices documentation on published catalogs
        <best-practices.md#published-catalogs>`
    """

    @classmethod
    def determine_type(cls, stac_json: dict[str, Any]) -> CatalogType | None:
        """Determines the catalog type based on a STAC JSON dict.

        Only applies to Catalogs or Collections

        Args:
            stac_json : The STAC JSON dict to determine the catalog type

        Returns:
            Optional[CatalogType]: The catalog type of the catalog or collection.
            Will return None if it cannot be determined.
        """
        self_link = None
        relative = False
        for link in stac_json["links"]:
            if link["rel"] == pystac.RelType.SELF:
                self_link = link
            else:
                relative |= not is_absolute_href(link["href"])

        if self_link:
            if relative:
                return cls.RELATIVE_PUBLISHED
            else:
                return cls.ABSOLUTE_PUBLISHED
        else:
            if relative:
                return cls.SELF_CONTAINED
            else:
                return None


class Catalog(STACObject):
    """A PySTAC Catalog represents a STAC catalog in memory.

    A Catalog is a :class:`~pystac.STACObject` that may contain children,
    which are instances of :class:`~pystac.Catalog` or :class:`~pystac.Collection`,
    as well as :class:`~pystac.Item` s.

    Args:
        id : Identifier for the catalog. Must be unique within the STAC.
        description : Detailed multi-line description to fully explain the catalog.
            `CommonMark 0.29 syntax <https://commonmark.org/>`_ MAY be used for rich
            text representation.
        title : Optional short descriptive one-line title for the catalog.
        stac_extensions : Optional list of extensions the Catalog implements.
        href : Optional HREF for this catalog, which be set as the
            catalog's self link's HREF.
        catalog_type : Optional catalog type for this catalog. Must
            be one of the values in :class:`~pystac.CatalogType`.
        strategy : The layout strategy to use for setting the
            HREFs of the catalog child objects and items.
            If not provided, it will default to the strategy of the root and fallback to
            :class:`~pystac.layout.BestPracticesLayoutStrategy`.
    """

    catalog_type: CatalogType
    """The catalog type. Defaults to :attr:`CatalogType.ABSOLUTE_PUBLISHED`."""

    description: str
    """Detailed multi-line description to fully explain the catalog."""

    extra_fields: dict[str, Any]
    """Extra fields that are part of the top-level JSON properties of the Catalog."""

    id: str
    """Identifier for the catalog."""

    links: list[Link]
    """A list of :class:`~pystac.Link` objects representing all links associated with
    this Catalog."""

    title: str | None
    """Optional short descriptive one-line title for the catalog."""

    stac_extensions: list[str]
    """List of extensions the Catalog implements."""

    _resolved_objects: ResolvedObjectCache

    STAC_OBJECT_TYPE = pystac.STACObjectType.CATALOG

    _stac_io: pystac.StacIO | None = None
    """Optional instance of StacIO that will be used by default
    for any IO operations on objects contained by this catalog.
    Set while reading in a catalog. This is set when a catalog
    is read by a StacIO instance."""

    DEFAULT_FILE_NAME = "catalog.json"
    """Default file name that will be given to this STAC object in
    a canonical format.
    """

    _fallback_strategy: HrefLayoutStrategy = BestPracticesLayoutStrategy()
    """Fallback layout strategy"""

    def __init__(
        self,
        id: str,
        description: str,
        title: str | None = None,
        stac_extensions: list[str] | None = None,
        extra_fields: dict[str, Any] | None = None,
        href: str | None = None,
        catalog_type: CatalogType = CatalogType.ABSOLUTE_PUBLISHED,
        strategy: HrefLayoutStrategy | None = None,
    ):
        super().__init__(stac_extensions or [])

        self.id = id
        self.description = description
        self.title = title
        if extra_fields is None:
            self.extra_fields = {}
        else:
            self.extra_fields = extra_fields

        self._resolved_objects = ResolvedObjectCache()

        self.add_link(Link.root(self))

        if href is not None:
            self.set_self_href(href)

        self.catalog_type: CatalogType = catalog_type

        self.strategy: HrefLayoutStrategy | None = strategy

        self._resolved_objects.cache(self)

    def __repr__(self) -> str:
        return f"<Catalog id={self.id}>"

    def set_root(self, root: Catalog | None) -> None:
        STACObject.set_root(self, root)
        if root is not None:
            root._resolved_objects = ResolvedObjectCache.merge(
                root._resolved_objects, self._resolved_objects
            )

            # Walk through resolved object links and update the root
            for link in self.links:
                if link.rel == pystac.RelType.CHILD or link.rel == pystac.RelType.ITEM:
                    target = link.target
                    if isinstance(target, STACObject):
                        target.set_root(root)

    def is_relative(self) -> bool:
        return self.catalog_type in [
            CatalogType.RELATIVE_PUBLISHED,
            CatalogType.SELF_CONTAINED,
        ]

    def _get_strategy(self, strategy: HrefLayoutStrategy | None) -> HrefLayoutStrategy:
        if strategy is not None:
            return strategy
        elif self.strategy is not None:
            return self.strategy
        elif root := self.get_root():
            if root.strategy is not None:
                return root.strategy
            else:
                return root._fallback_strategy
        else:
            return self._fallback_strategy

    def add_child(
        self,
        child: Catalog | Collection,
        title: str | None = None,
        strategy: HrefLayoutStrategy | None = None,
        set_parent: bool = True,
    ) -> Link:
        """Adds a link to a child :class:`~pystac.Catalog` or
        :class:`~pystac.Collection`.

        This method will set the child's parent to this object and potentially
        override its self_link (unless ``set_parent`` is False).

        It will always set its root to this Catalog's root.

        Args:
            child : The child to add.
            title : Optional title to give to the :class:`~pystac.Link`
            strategy : The layout strategy to use for setting the
                self href of the child. If not provided, defaults to
                the layout strategy of the parent or root and falls back to
                :class:`~pystac.layout.BestPracticesLayoutStrategy`.
            set_parent : Whether to set the parent on the child as well.
                Defaults to True.

        Returns:
            Link: The link created for the child
        """

        # Prevent typo confusion
        if isinstance(child, pystac.Item):
            raise pystac.STACError("Cannot add item as child. Use add_item instead.")

        strategy = self._get_strategy(strategy)

        child.set_root(self.get_root())
        if set_parent:
            child.set_parent(self)
        else:
            child._allow_parent_to_override_href = False

        # set self link
        self_href = self.get_self_href()
        if self_href and set_parent:
            child_href = strategy.get_href(child, self_href)
            child.set_self_href(child_href)

        child_link = Link.child(child, title=title)
        self.add_link(child_link)
        return child_link

    def add_children(
        self,
        children: Iterable[Catalog | Collection],
        strategy: HrefLayoutStrategy | None = None,
    ) -> list[Link]:
        """Adds links to multiple :class:`~pystac.Catalog` or `~pystac.Collection`
        objects. This method will set each child's parent to this object, and their
        root to this Catalog's root.

        Args:
            children : The children to add.
            strategy : The layout strategy to use for setting the
                self href of the children. If not provided, defaults to
                the layout strategy of the parent or root and falls back to
                :class:`~pystac.layout.BestPracticesLayoutStrategy`.

        Returns:
            List[Link]: An array of links created for the children
        """
        return [self.add_child(child, strategy=strategy) for child in children]

    def add_item(
        self,
        item: Item,
        title: str | None = None,
        strategy: HrefLayoutStrategy | None = None,
        set_parent: bool = True,
    ) -> Link:
        """Adds a link to an :class:`~pystac.Item`.

        This method will set the item's parent to this object and potentially
        override its self_link (unless ``set_parent`` is False)

        It will always set its root to this Catalog's root.

        Args:
            item : The item to add.
            title : Optional title to give to the :class:`~pystac.Link`
            strategy : The layout strategy to use for setting the
                self href of the item. If not provided, defaults to
                the layout strategy of the parent or root and falls back to
                :class:`~pystac.layout.BestPracticesLayoutStrategy`.
            set_parent : Whether to set the parent on the item as well.
                Defaults to True.

        Returns:
            Link: The link created for the item
        """

        # Prevent typo confusion
        if isinstance(item, pystac.Catalog):
            raise pystac.STACError("Cannot add catalog as item. Use add_child instead.")

        strategy = self._get_strategy(strategy)

        item.set_root(self.get_root())
        if set_parent:
            item.set_parent(self)
        else:
            item._allow_parent_to_override_href = False

        # set self link
        self_href = self.get_self_href()
        if self_href and set_parent:
            item_href = strategy.get_href(item, self_href)
            item.set_self_href(item_href)

        item_link = Link.item(item, title=title)
        self.add_link(item_link)
        return item_link

    def add_items(
        self,
        items: Iterable[Item],
        strategy: HrefLayoutStrategy | None = None,
    ) -> list[Link]:
        """Adds links to multiple :class:`Items <pystac.Item>`.

        This method will set each item's parent to this object, and their root to
        this Catalog's root.

        Args:
            items : The items to add.
            strategy : The layout strategy to use for setting the
                self href of the items. If not provided, defaults to
                the layout strategy of the parent or root and falls back to
                :class:`~pystac.layout.BestPracticesLayoutStrategy`.

        Returns:
            List[Link]: A list of links created for the item
        """
        return [self.add_item(item, strategy=strategy) for item in items]

    def get_child(
        self, id: str, recursive: bool = False, sort_links_by_id: bool = True
    ) -> Catalog | Collection | None:
        """Gets the child of this catalog with the given ID, if it exists.

        Args:
            id : The ID of the child to find.
            recursive : If True, search this catalog and all children for the
                item; otherwise, only search the children of this catalog. Defaults
                to False.
            sort_links_by_id : If True, links containing the ID will be checked
                first. If links do not contain the ID then setting this to False
                will improve performance. Defaults to True.

        Return:
            Catalog or Collection or None: The child with the given ID,
            or None if not found.
        """
        if not recursive:
            children: Iterable[pystac.Catalog | pystac.Collection]
            if not sort_links_by_id:
                children = self.get_children()
            else:

                def sort_function(links: list[Link]) -> list[Link]:
                    return sorted(
                        links,
                        key=lambda x: (href := x.get_href()) is None or id not in href,
                    )

                children = map(
                    lambda x: cast(pystac.Catalog | pystac.Collection, x),
                    self.get_stac_objects(
                        pystac.RelType.CHILD, modify_links=sort_function
                    ),
                )
            return next((c for c in children if c.id == id), None)
        else:
            for root, _, _ in self.walk():
                child = root.get_child(id, recursive=False)
                if child is not None:
                    return child
            return None

    def get_children(self) -> Iterable[Catalog | Collection]:
        """Return all children of this catalog.

        Return:
            Iterable[Catalog or Collection]: Iterable of children who's parent
            is this catalog.
        """
        return map(
            lambda x: cast(pystac.Catalog | pystac.Collection, x),
            self.get_stac_objects(pystac.RelType.CHILD),
        )

    def get_collections(self) -> Iterable[Collection]:
        """Return all children of this catalog that are :class:`~pystac.Collection`
        instances."""
        return map(
            lambda x: cast(pystac.Collection, x),
            self.get_stac_objects(pystac.RelType.CHILD, pystac.Collection),
        )

    def get_all_collections(self) -> Iterable[Collection]:
        """Get all collections from this catalog and all subcatalogs. Will traverse
        any subcatalogs recursively."""
        yield from self.get_collections()
        for child in self.get_children():
            yield from child.get_all_collections()

    def get_child_links(self) -> list[Link]:
        """Return all child links of this catalog.

        Return:
            List[Link]: List of links of this catalog with ``rel == 'child'``
        """
        return self.get_links(
            rel=pystac.RelType.CHILD,
            media_type=pystac.media_type.STAC_JSON,
        )

    def clear_children(self) -> None:
        """Removes all children from this catalog.

        Return:
            Catalog: Returns ``self``
        """
        child_ids = [child.id for child in self.get_children()]
        for child_id in child_ids:
            self.remove_child(child_id)

    def remove_child(self, child_id: str) -> None:
        """Removes an child from this catalog.

        Args:
            child_id : The ID of the child to remove.
        """
        new_links: list[pystac.Link] = []
        root = self.get_root()
        for link in self.links:
            if link.rel != pystac.RelType.CHILD:
                new_links.append(link)
            else:
                link.resolve_stac_object(root=root)
                child = cast("Catalog", link.target)
                if child.id != child_id:
                    new_links.append(link)
                else:
                    child.set_parent(None)
                    child.set_root(None)
        self.links = new_links

    def get_item(self, id: str, recursive: bool = False) -> Item | None:
        """
        DEPRECATED.

        .. deprecated:: 1.8
            Use ``next(pystac.Catalog.get_items(id), None)`` instead.

        Returns an item with a given ID.

        Args:
            id : The ID of the item to find.
            recursive : If True, search this catalog and all children for the
                item; otherwise, only search the items of this catalog. Defaults
                to False.

        Return:
            Item or None: The item with the given ID, or None if not found.
        """
        warnings.warn(
            "get_item is deprecated and will be removed in v2. "
            "Use next(self.get_items(id), None) instead",
            DeprecationWarning,
        )
        if not recursive:
            return next((i for i in self.get_items() if i.id == id), None)
        else:
            for root, _, _ in self.walk():
                item = root.get_item(id, recursive=False)
                if item is not None:
                    return item
            return None

    def get_items(self, *ids: str, recursive: bool = False) -> Iterator[Item]:
        """Return all items or specific items of this catalog.

        Args:
            *ids : The IDs of the items to include.
            recursive : If True, search this catalog and all children for the
                item; otherwise, only search the items of this catalog. Defaults
                to False.

        Return:
            Iterator[Item]: Generator of items whose parent is this catalog, and
                (if recursive) all catalogs or collections connected to this catalog
                through child links.
        """
        items: Iterator[Item]
        if not recursive:
            items = map(
                lambda x: cast(pystac.Item, x),
                self.get_stac_objects(pystac.RelType.ITEM),
            )
        else:
            items = chain(
                self.get_items(recursive=False),
                *(child.get_items(recursive=True) for child in self.get_children()),
            )
        if ids:
            yield from (i for i in items if i.id in ids)
        else:
            yield from items

    def clear_items(self) -> None:
        """Removes all items from this catalog.

        Return:
            Catalog: Returns ``self``
        """
        for link in self.get_item_links():
            if link.is_resolved():
                item = cast(pystac.Item, link.target)
                item.set_parent(None)
                item.set_root(None)

        self.links = [link for link in self.links if link.rel != pystac.RelType.ITEM]

    def remove_item(self, item_id: str) -> None:
        """Removes an item from this catalog.

        Args:
            item_id : The ID of the item to remove.
        """
        new_links: list[pystac.Link] = []
        root = self.get_root()
        for link in self.links:
            if link.rel != pystac.RelType.ITEM:
                new_links.append(link)
            else:
                link.resolve_stac_object(root=root)
                item = cast(pystac.Item, link.target)
                if item.id != item_id:
                    new_links.append(link)
                else:
                    item.set_parent(None)
                    item.set_root(None)
        self.links = new_links

    def get_all_items(self) -> Iterator[Item]:
        """
        DEPRECATED.

        .. deprecated:: 1.8
            Use ``pystac.Catalog.get_items(recursive=True)`` instead.

        Get all items from this catalog and all subcatalogs. Will traverse
        any subcatalogs recursively.

        Returns:
            Generator[Item]: All items that belong to this catalog, and all
                catalogs or collections connected to this catalog through
                child links.
        """
        warnings.warn(
            "get_all_items is deprecated and will be removed in v2",
            DeprecationWarning,
        )
        return chain(
            self.get_items(),
            *(child.get_items(recursive=True) for child in self.get_children()),
        )

    def get_item_links(self) -> list[Link]:
        """Return all item links of this catalog.

        Return:
            List[Link]: List of links of this catalog with ``rel == 'item'``
        """
        return self.get_links(
            rel=pystac.RelType.ITEM, media_type=pystac.media_type.STAC_JSON
        )

    def to_dict(
        self, include_self_link: bool = True, transform_hrefs: bool = True
    ) -> dict[str, Any]:
        links = [
            x
            for x in self.links
            if x.rel != pystac.RelType.ROOT or x.get_href(transform_hrefs) is not None
        ]
        if not include_self_link:
            links = [x for x in links if x.rel != pystac.RelType.SELF]

        d: dict[str, Any] = {
            "type": self.STAC_OBJECT_TYPE.value.title(),
            "id": self.id,
            "stac_version": pystac.get_stac_version(),
            "description": self.description,
            "links": [link.to_dict(transform_href=transform_hrefs) for link in links],
        }

        if self.stac_extensions:
            d["stac_extensions"] = self.stac_extensions

        for key in self.extra_fields:
            d[key] = self.extra_fields[key]

        if self.title is not None:
            d["title"] = self.title

        return d

    def clone(self) -> Catalog:
        cls = self.__class__
        clone = cls(
            id=self.id,
            description=self.description,
            title=self.title,
            stac_extensions=self.stac_extensions.copy(),
            extra_fields=deepcopy(self.extra_fields),
            catalog_type=self.catalog_type,
        )
        clone._resolved_objects.cache(clone)

        for link in self.links:
            if link.rel == pystac.RelType.ROOT:
                # Catalog __init__ sets correct root to clone; don't reset
                # if the root link points to self
                root_is_self = link.is_resolved() and link.target is self
                if not root_is_self:
                    clone.set_root(None)
                    clone.add_link(link.clone())
            else:
                clone.add_link(link.clone())

        return clone

    def make_all_asset_hrefs_relative(self) -> None:
        """Recursively makes all the HREFs of assets in this catalog relative"""
        for item in self.get_items(recursive=True):
            item.make_asset_hrefs_relative()
        for collection in self.get_all_collections():
            collection.make_asset_hrefs_relative()

    def make_all_asset_hrefs_absolute(self) -> None:
        """Recursively makes all the HREFs of assets in this catalog absolute"""
        for item in self.get_items(recursive=True):
            item.make_asset_hrefs_absolute()
        for collection in self.get_all_collections():
            collection.make_asset_hrefs_absolute()

    def normalize_and_save(
        self,
        root_href: str,
        catalog_type: CatalogType | None = None,
        strategy: HrefLayoutStrategy | None = None,
        stac_io: pystac.StacIO | None = None,
        skip_unresolved: bool = False,
    ) -> None:
        """Normalizes link HREFs to the given root_href, and saves the catalog.

        This is a convenience method that simply calls :func:`Catalog.normalize_hrefs
        <pystac.Catalog.normalize_hrefs>` and :func:`Catalog.save <pystac.Catalog.save>`
        in sequence.

        Args:
            root_href : The absolute HREF that all links will be normalized
                against.
            catalog_type : The catalog type that dictates the structure of
                the catalog to save. Use a member of :class:`~pystac.CatalogType`.
                Defaults to the root catalog.catalog_type or the current catalog
                catalog_type if there is no root catalog.
            strategy : The layout strategy to use in setting the
                HREFS for this catalog. If not provided, defaults to
                the layout strategy of the parent or root and falls back to
                :class:`~pystac.layout.BestPracticesLayoutStrategy`
            stac_io : Optional instance of :class:`~pystac.StacIO` to use. If not
                provided, will use the instance set while reading in the catalog,
                or the default instance if this is not available.
            skip_unresolved : Skip unresolved links when normalizing the tree.
                Defaults to False. Because unresolved links are not saved, this
                argument can be used to normalize and save only newly-added
                objects.
        """
        self.normalize_hrefs(
            root_href, strategy=strategy, skip_unresolved=skip_unresolved
        )
        self.save(catalog_type, stac_io=stac_io)

    def normalize_hrefs(
        self,
        root_href: str,
        strategy: HrefLayoutStrategy | None = None,
        skip_unresolved: bool = False,
    ) -> None:
        """Normalize HREFs will regenerate all link HREFs based on
        an absolute root_href and the canonical catalog layout as specified
        in the STAC specification's best practices.

        This method mutates the entire catalog tree, unless ``skip_unresolved``
        is True, in which case only resolved links are modified. This is useful
        in the case when you have loaded a large catalog and you've added a few
        items/children, and you only want to update those newly-added objects,
        not the whole tree.

        Args:
            root_href : The absolute HREF that all links will be normalized against.
            strategy : The layout strategy to use in setting the HREFS
                for this catalog. If not provided, defaults to
                the layout strategy of the parent or root and falls back to
                :class:`~pystac.layout.BestPracticesLayoutStrategy`
            skip_unresolved : Skip unresolved links when normalizing the tree.
                Defaults to False.

        See:
            :stac-spec:`STAC best practices document <best-practices.md#catalog-layout>`
            for the canonical layout of a STAC.
        """

        _strategy = self._get_strategy(strategy)

        # Normalizing requires an absolute path
        if not is_absolute_href(root_href):
            root_href = make_absolute_href(root_href, os.getcwd(), start_is_dir=True)

        if isinstance(_strategy, APILayoutStrategy) and not _is_url(root_href):
            raise STACError("When using APILayoutStrategy the root_href must be a URL")

        def process_item(
            item: Item, _root_href: str, is_root: bool, parent: Catalog | None
        ) -> Callable[[], None] | None:
            if not skip_unresolved:
                item.resolve_links()

            # Abort as the intended parent is not the actual parent
            # https://github.com/stac-utils/pystac/issues/1116
            if parent is not None and item.get_parent() != parent:
                return None

            new_self_href = _strategy.get_href(item, _root_href, is_root)

            def fn() -> None:
                item.set_self_href(new_self_href)

            return fn

        def process_catalog(
            cat: Catalog,
            _root_href: str,
            is_root: bool,
            parent: Catalog | None = None,
        ) -> list[Callable[[], None]]:
            setter_funcs: list[Callable[[], None]] = []

            if not skip_unresolved:
                cat.resolve_links()

            # Abort as the intended parent is not the actual parent
            # https://github.com/stac-utils/pystac/issues/1116
            if parent is not None and cat.get_parent() != parent:
                return setter_funcs

            new_self_href = _strategy.get_href(cat, _root_href, is_root)
            new_root = new_self_href

            for link in cat.get_links():
                if skip_unresolved and not link.is_resolved():
                    continue
                elif link.rel == pystac.RelType.ITEM:
                    link.resolve_stac_object(root=self.get_root())
                    item_fn = process_item(
                        cast(pystac.Item, link.target), new_root, is_root, cat
                    )
                    if item_fn is not None:
                        setter_funcs.append(item_fn)
                elif link.rel == pystac.RelType.CHILD:
                    link.resolve_stac_object(root=self.get_root())
                    setter_funcs.extend(
                        process_catalog(
                            cast(pystac.Catalog | pystac.Collection, link.target),
                            new_root,
                            is_root=False,
                            parent=cat,
                        )
                    )

            def fn() -> None:
                cat.set_self_href(new_self_href)

            setter_funcs.append(fn)

            return setter_funcs

        # Collect functions that will actually mutate the objects.
        # Delay mutation as setting hrefs while walking the catalog
        # can result in bad links.
        setter_funcs = process_catalog(self, root_href, is_root=True)

        for fn in setter_funcs:
            fn()

    def generate_subcatalogs(
        self,
        template: str,
        defaults: dict[str, Any] | None = None,
        parent_ids: list[str] | None = None,
    ) -> list[Catalog]:
        """Walks through the catalog and generates subcatalogs
        for items based on the template string.

        See :class:`~pystac.layout.LayoutTemplate`
        for details on the construction of template strings. This template string
        will be applied to the items, and subcatalogs will be created that separate
        and organize the items based on template values.

        Args:
            template :   A template string that
                can be consumed by a :class:`~pystac.layout.LayoutTemplate`
            defaults :  Default values for the template variables
                that will be used if the property cannot be found on
                the item.
            parent_ids : Optional list of the parent catalogs'
                identifiers. If the bottom-most subcatalogs already match the
                template, no subcatalog is added.

        Returns:
            list[Catalog]: List of new catalogs created
        """
        result: list[Catalog] = []
        parent_ids = parent_ids or list()
        parent_ids.append(self.id)
        for child in self.get_children():
            result.extend(
                child.generate_subcatalogs(
                    template, defaults=defaults, parent_ids=parent_ids.copy()
                )
            )

        layout_template = LayoutTemplate(template, defaults=defaults)

        keep_item_links: list[Link] = []
        item_links = [lk for lk in self.links if lk.rel == pystac.RelType.ITEM]
        for link in item_links:
            link.resolve_stac_object(root=self.get_root())
            item = cast(pystac.Item, link.target)
            subcat_ids = layout_template.substitute(item).split("/")
            id_iter = reversed(parent_ids)
            if all([f"{id}" == next(id_iter, None) for id in reversed(subcat_ids)]):
                # Skip items for which the sub-catalog structure already
                # matches the template. The list of parent IDs can include more
                # elements on the root side, so compare the reversed sequences.
                keep_item_links.append(link)
                continue
            curr_parent = self
            for subcat_id in subcat_ids:
                subcat = curr_parent.get_child(subcat_id)
                if subcat is None:
                    subcat_desc = "Catalog of items from {} with id {}".format(
                        curr_parent.id, subcat_id
                    )
                    subcat = pystac.Catalog(id=subcat_id, description=subcat_desc)
                    curr_parent.add_child(subcat)
                    result.append(subcat)
                curr_parent = subcat

            # resolve collection link so when added back points to correct location
            col_link = item.get_single_link(pystac.RelType.COLLECTION)
            if col_link is not None:
                col_link.resolve_stac_object()

            curr_parent.add_item(item)

        # keep only non-item links and item links that have not been moved elsewhere
        self.links = [
            lk for lk in self.links if lk.rel != pystac.RelType.ITEM
        ] + keep_item_links

        return result

    def save(
        self,
        catalog_type: CatalogType | None = None,
        dest_href: str | None = None,
        stac_io: pystac.StacIO | None = None,
    ) -> None:
        """Save this catalog and all it's children/item to files determined by the
        object's self link HREF or a specified path.

        Args:
            catalog_type : The catalog type that dictates the structure of
                the catalog to save. Use a member of :class:`~pystac.CatalogType`.
                If not supplied, the catalog_type of this catalog will be used.
                If that attribute is not set, an exception will be raised.
            dest_href : The location where the catalog is to be saved.
                If not supplied, the catalog's self link HREF is used to determine
                the location of the catalog file and children's files.
            stac_io : Optional instance of :class:`~pystac.StacIO` to use. If not
                provided, will use the instance set while reading in the catalog,
                or the default instance if this is not available.
        Note:
            If the catalog type is ``CatalogType.ABSOLUTE_PUBLISHED``,
            all self links will be included, and hierarchical links be absolute URLs.
            If the catalog type is ``CatalogType.RELATIVE_PUBLISHED``, this catalog's
            self link will be included, but no child catalog will have self links, and
            hierarchical links will be relative URLs
            If the catalog  type is ``CatalogType.SELF_CONTAINED``, no self links will
            be included and hierarchical links will be relative URLs.
        """

        root = self.get_root()
        if root is None:
            raise Exception("There is no root catalog")

        if catalog_type is not None:
            root.catalog_type = catalog_type

        items_include_self_link = root.catalog_type in [CatalogType.ABSOLUTE_PUBLISHED]

        for child_link in self.get_child_links():
            if child_link.is_resolved():
                child = cast(Catalog, child_link.target)
                if dest_href is not None:
                    rel_href = make_relative_href(child.self_href, self.self_href)
                    child_dest_href = make_absolute_href(
                        rel_href, dest_href, start_is_dir=True
                    )
                    child.save(
                        dest_href=os.path.dirname(child_dest_href),
                        stac_io=stac_io,
                    )
                else:
                    child.save(stac_io=stac_io)

        for item_link in self.get_item_links():
            if item_link.is_resolved():
                item = cast(pystac.Item, item_link.target)
                if dest_href is not None:
                    rel_href = make_relative_href(item.self_href, self.self_href)
                    item_dest_href = make_absolute_href(
                        rel_href, dest_href, start_is_dir=True
                    )
                    item.save_object(
                        include_self_link=items_include_self_link,
                        dest_href=item_dest_href,
                        stac_io=stac_io,
                    )
                else:
                    item.save_object(
                        include_self_link=items_include_self_link, stac_io=stac_io
                    )

        include_self_link = False
        # include a self link if this is the root catalog
        # or if ABSOLUTE_PUBLISHED catalog
        if root.catalog_type == CatalogType.ABSOLUTE_PUBLISHED:
            include_self_link = True
        elif root.catalog_type != CatalogType.SELF_CONTAINED:
            root_link = self.get_root_link()
            if root_link and root_link.get_absolute_href() == self.get_self_href():
                include_self_link = True

        catalog_dest_href = None
        if dest_href is not None:
            rel_href = make_relative_href(self.self_href, self.self_href)
            catalog_dest_href = make_absolute_href(
                rel_href, dest_href, start_is_dir=True
            )
        self.save_object(
            include_self_link=include_self_link,
            dest_href=catalog_dest_href,
            stac_io=stac_io,
        )
        if catalog_type is not None:
            self.catalog_type = catalog_type

    def walk(
        self,
    ) -> Iterable[tuple[Catalog, Iterable[Catalog], Iterable[Item]]]:
        """Walks through children and items of catalogs.

        For each catalog in the STAC's tree rooted at this catalog (including this
        catalog itself), it yields a 3-tuple (root, subcatalogs, items). The root in
        that 3-tuple refers to the current catalog being walked, the subcatalogs are any
        catalogs or collections for which the root is a parent, and items represents
        any items that have the root as a parent.

        This has similar functionality to Python's :func:`os.walk`.

        Returns:
           Generator[(Catalog, Generator[Catalog], Generator[Item])]: A generator that
           yields a 3-tuple (parent_catalog, children, items).
        """
        children = self.get_children()
        items = self.get_items()

        yield self, children, items
        for child in self.get_children():
            yield from child.walk()

    def fully_resolve(self) -> None:
        """Resolves every link in this catalog.

        Useful if, e.g., you'd like to read a catalog from a filesystem, upgrade
        every object in the catalog to the latest STAC version, and save it back
        to the filesystem. By default, :py:meth:`~pystac.Catalog.save` skips
        unresolved links.
        """
        for _, _, items in self.walk():
            # items is a generator, so we need to consume it to resolve the
            # items
            for item in items:
                pass

    def validate_all(self, max_items: int | None = None, recursive: bool = True) -> int:
        """Validates each catalog, collection, item contained within this catalog.

        Walks through the children and items of the catalog and validates each
        stac object.

        Args:
            max_items : The maximum number of STAC items to validate. Default
                is None which means, validate them all.
            recursive : Whether to validate catalog, collections, and items contained
                within child objects.

        Returns:
            int : Number of STAC items validated.

        Raises:
            STACValidationError: Raises this error on any item that is invalid.
                Will raise on the first invalid stac object encountered.
        """
        n = 0
        self.validate()
        for child in self.get_children():
            if recursive:
                inner_max_items = None if max_items is None else max_items - n
                n += child.validate_all(max_items=inner_max_items, recursive=True)
            else:
                child.validate()
        for item in self.get_items():
            if max_items is not None and n >= max_items:
                break
            item.validate()
            n += 1
        return n

    def _object_links(self) -> list[str | pystac.RelType]:
        return [
            pystac.RelType.CHILD,
            pystac.RelType.ITEM,
            *pystac.EXTENSION_HOOKS.get_extended_object_links(self),
        ]

    def map_items(
        self,
        item_mapper: Callable[[Item], Item | list[Item]],
    ) -> Catalog:
        """Creates a copy of a catalog, with each item passed through the
        item_mapper function.

        Args:
            item_mapper :   A function that takes in an item, and returns
                either an item or list of items. The item that is passed into the
                item_mapper is a copy, so the method can mutate it safely.

        Returns:
            Catalog: A full copy of this catalog, with items manipulated according
            to the item_mapper function.
        """

        new_cat = self.full_copy()

        def process_catalog(catalog: Catalog) -> None:
            for child in catalog.get_children():
                process_catalog(child)

            item_links: list[Link] = []
            for item_link in catalog.get_item_links():
                item_link.resolve_stac_object(root=self.get_root())
                mapped = item_mapper(cast(pystac.Item, item_link.target))
                if mapped is None:
                    raise Exception("item_mapper cannot return None.")
                if isinstance(mapped, pystac.Item):
                    item_link.target = mapped
                    item_links.append(item_link)
                else:
                    for i in mapped:
                        new_link = item_link.clone()
                        new_link.target = i
                        item_links.append(new_link)
            catalog.clear_items()
            catalog.add_links(item_links)

        process_catalog(new_cat)
        return new_cat

    def map_assets(
        self,
        asset_mapper: Callable[
            [str, Asset],
            Asset | tuple[str, Asset] | dict[str, Asset],
        ],
    ) -> Catalog:
        """Creates a copy of a catalog, with each Asset for each Item passed
        through the asset_mapper function.

        Args:
            asset_mapper : A function that takes in an key and an Asset, and
                returns either an Asset, a (key, Asset), or a dictionary of Assets with
                unique keys. The Asset that is passed into the item_mapper is a copy,
                so the method can mutate it safely.

        Returns:
            Catalog: A full copy of this catalog, with assets manipulated according
            to the asset_mapper function.
        """

        def apply_asset_mapper(
            tup: tuple[str, Asset],
        ) -> list[tuple[str, pystac.Asset]]:
            k, v = tup
            result = asset_mapper(k, v)
            if result is None:
                raise Exception("asset_mapper cannot return None.")
            if isinstance(result, pystac.Asset):
                return [(k, result)]
            elif isinstance(result, tuple):
                return [result]
            else:
                assets = list(result.items())
                if len(assets) < 1:
                    raise Exception("asset_mapper must return a non-empty list")
                return assets

        def item_mapper(item: pystac.Item) -> pystac.Item:
            new_assets = [
                x
                for result in map(apply_asset_mapper, item.assets.items())
                for x in result
            ]
            item.assets = dict(new_assets)
            return item

        return self.map_items(item_mapper)

    def describe(self, include_hrefs: bool = False, _indent: int = 0) -> None:
        """Prints out information about this Catalog and all contained
        STACObjects.

        Args:
            include_hrefs (bool) - If True, print out each object's self link
                HREF along with the object ID.
        """
        s = "{}* {}".format(" " * _indent, self)
        if include_hrefs:
            s += f" {self.get_self_href()}"
        print(s)
        for child in self.get_children():
            child.describe(include_hrefs=include_hrefs, _indent=_indent + 4)
        for item in self.get_items():
            s = "{}* {}".format(" " * (_indent + 2), item)
            if include_hrefs:
                s += f" {item.get_self_href()}"
            print(s)

    @classmethod
    def from_dict(
        cls: type[C],
        d: dict[str, Any],
        href: str | None = None,
        root: Catalog | None = None,
        migrate: bool = True,
        preserve_dict: bool = True,
    ) -> C:
        if migrate:
            info = identify_stac_object(d)
            d = migrate_to_latest(d, info)

        if not cls.matches_object_type(d):
            raise STACTypeError(d, cls)

        catalog_type = CatalogType.determine_type(d)

        if preserve_dict:
            d = deepcopy(d)

        id = d.pop("id")
        description = d.pop("description")
        title = d.pop("title", None)
        stac_extensions = d.pop("stac_extensions", None)
        links = d.pop("links")

        d.pop("stac_version")

        cat = cls(
            id=id,
            description=description,
            title=title,
            stac_extensions=stac_extensions,
            extra_fields=d,
            href=href,
            catalog_type=catalog_type or CatalogType.ABSOLUTE_PUBLISHED,
        )

        for link in links:
            if link["rel"] == pystac.RelType.ROOT:
                # Remove the link that's generated in Catalog's constructor.
                cat.remove_links(pystac.RelType.ROOT)

            if link["rel"] != pystac.RelType.SELF or href is None:
                cat.add_link(Link.from_dict(link))

        if root:
            cat.set_root(root)

        return cat

    def full_copy(
        self, root: Catalog | None = None, parent: Catalog | None = None
    ) -> Catalog:
        return cast(Catalog, super().full_copy(root, parent))

    @classmethod
    def from_file(cls: type[C], href: HREF, stac_io: pystac.StacIO | None = None) -> C:
        if stac_io is None:
            stac_io = pystac.StacIO.default()

        result = super().from_file(href, stac_io)
        result._stac_io = stac_io

        return result

    @classmethod
    def matches_object_type(cls, d: dict[str, Any]) -> bool:
        return identify_stac_object_type(d) == STACObjectType.CATALOG

    @property
    def ext(self) -> CatalogExt:
        """Accessor for extension classes on this catalog

        Example::

            print(collection.ext.version)
        """
        from pystac.extensions.ext import CatalogExt

        return CatalogExt(stac_object=self)
