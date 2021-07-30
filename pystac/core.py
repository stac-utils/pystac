import os
from copy import copy, deepcopy
from datetime import datetime as Datetime
from dateutil import parser, tz
from enum import Enum
from pystac.errors import STACTypeError
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    TYPE_CHECKING,
    TypeVar,
    Tuple,
    Union,
    cast,
)

import pystac
from pystac.asset import Asset
from pystac.common_metadata import CommonMetadata
from pystac.errors import STACError
from pystac.stac_object import STACObject, STACObjectType
from pystac.layout import (
    BestPracticesLayoutStrategy,
    HrefLayoutStrategy,
    LayoutTemplate,
)
from pystac.link import Link
from pystac.provider import Provider
from pystac.rel_type import RelType
from pystac.cache import ResolvedObjectCache
from pystac.serialization import (
    identify_stac_object_type,
    identify_stac_object,
    migrate_to_latest,
)
from pystac.stac_io import StacIO
from pystac.summaries import Summaries
from pystac.utils import is_absolute_href, make_absolute_href, make_relative_href, datetime_to_str, str_to_datetime

if TYPE_CHECKING:
    from pystac.asset import Asset as Asset_Type
    from pystac.common_metadata import CommonMetadata as CommonMetadata_Type
    from pystac.link import Link as Link_Type
    from pystac.provider import Provider as Provider_Type


class CatalogType(str, Enum):
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
    def determine_type(cls, stac_json: Dict[str, Any]) -> Optional["CatalogType"]:
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
            if link["rel"] == RelType.SELF:
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
            `CommonMark 0.28 syntax <https://commonmark.org/>`_ MAY be used for rich
            text representation.
        title : Optional short descriptive one-line title for the catalog.
        stac_extensions : Optional list of extensions the Catalog implements.
        href : Optional HREF for this catalog, which be set as the
            catalog's self link's HREF.
        catalog_type : Optional catalog type for this catalog. Must
            be one of the values in :class`~pystac.CatalogType`.

    Attributes:
        id : Identifier for the catalog.
        description : Detailed multi-line description to fully explain the catalog.
        title : Optional short descriptive one-line title for the catalog.
        stac_extensions : Optional list of extensions the Catalog
            implements.
        extra_fields : Extra fields that are part of the top-level JSON
            properties of the Catalog.
        links : A list of :class:`~pystac.Link` objects representing
            all links associated with this Catalog.
        catalog_type : The catalog type. Defaults to ABSOLUTE_PUBLISHED
    """

    STAC_OBJECT_TYPE = STACObjectType.CATALOG

    _stac_io: Optional["StacIO"] = None
    """Optional instance of StacIO that will be used by default
    for any IO operations on objects contained by this catalog.
    Set while reading in a catalog. This is set when a catalog
    is read by a StacIO instance."""

    DEFAULT_FILE_NAME = "catalog.json"
    """Default file name that will be given to this STAC object in
    a canonical format.
    """

    def __init__(
        self,
        id: str,
        description: str,
        title: Optional[str] = None,
        stac_extensions: Optional[List[str]] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
        href: Optional[str] = None,
        catalog_type: CatalogType = CatalogType.ABSOLUTE_PUBLISHED,
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

        self._resolved_objects.cache(self)

    def __repr__(self) -> str:
        return "<Catalog id={}>".format(self.id)

    def set_root(self, root: Optional["Catalog"]) -> None:
        STACObject.set_root(self, root)
        if root is not None:
            root._resolved_objects = ResolvedObjectCache.merge(
                root._resolved_objects, self._resolved_objects
            )

    def is_relative(self) -> bool:
        return self.catalog_type in [
            CatalogType.RELATIVE_PUBLISHED,
            CatalogType.SELF_CONTAINED,
        ]

    def add_child(
        self,
        child: Union["Catalog", "Collection"],
        title: Optional[str] = None,
        strategy: Optional[HrefLayoutStrategy] = None,
    ) -> None:
        """Adds a link to a child :class:`~pystac.Catalog` or :class:`~pystac.Collection`.
        This method will set the child's parent to this object, and its root to
        this Catalog's root.

        Args:
            child : The child to add.
            title : Optional title to give to the :class:`~pystac.Link`
            strategy : The layout strategy to use for setting the
                self href of the child.
        """

        # Prevent typo confusion
        if isinstance(child, Item):
            raise STACError("Cannot add item as child. Use add_item instead.")

        if strategy is None:
            strategy = BestPracticesLayoutStrategy()

        child.set_root(self.get_root())
        child.set_parent(self)

        # set self link
        self_href = self.get_self_href()
        if self_href:
            child_href = strategy.get_href(child, os.path.dirname(self_href))
            child.set_self_href(child_href)

        self.add_link(Link.child(child, title=title))

    def add_children(
        self, children: Iterable[Union["Catalog", "Collection"]]
    ) -> None:
        """Adds links to multiple :class:`~pystac.Catalog` or `~pystac.Collection` objects.
        This method will set each child's parent to this object, and their root to
        this Catalog's root.

        Args:
            children : The children to add.
        """
        for child in children:
            self.add_child(child)

    def add_item(
        self,
        item: "Item",
        title: Optional[str] = None,
        strategy: Optional[HrefLayoutStrategy] = None,
    ) -> None:
        """Adds a link to an :class:`~pystac.Item`.
        This method will set the item's parent to this object, and its root to
        this Catalog's root.

        Args:
            item : The item to add.
            title : Optional title to give to the :class:`~pystac.Link`
        """

        # Prevent typo confusion
        if isinstance(item, Catalog):
            raise STACError("Cannot add catalog as item. Use add_child instead.")

        if strategy is None:
            strategy = BestPracticesLayoutStrategy()

        item.set_root(self.get_root())
        item.set_parent(self)

        # set self link
        self_href = self.get_self_href()
        if self_href:
            item_href = strategy.get_href(item, os.path.dirname(self_href))
            item.set_self_href(item_href)

        self.add_link(Link.item(item, title=title))

    def add_items(self, items: Iterable["Item"]) -> None:
        """Adds links to multiple :class:`~pystac.Item` s.
        This method will set each item's parent to this object, and their root to
        this Catalog's root.

        Args:
            items : The items to add.
        """
        for item in items:
            self.add_item(item)

    def get_child(
        self, id: str, recursive: bool = False
    ) -> Optional[Union["Catalog", "Collection"]]:
        """Gets the child of this catalog with the given ID, if it exists.

        Args:
            id : The ID of the child to find.
            recursive : If True, search this catalog and all children for the
                item; otherwise, only search the children of this catalog. Defaults
                to False.

        Return:
            Optional Catalog or Collection: The child with the given ID,
            or None if not found.
        """
        if not recursive:
            return next((c for c in self.get_children() if c.id == id), None)
        else:
            for root, _, _ in self.walk():
                child = root.get_child(id, recursive=False)
                if child is not None:
                    return child
            return None

    def get_children(self) -> Iterable[Union["Catalog", "Collection"]]:
        """Return all children of this catalog.

        Return:
            Iterable[Catalog or Collection]: Iterable of children who's parent
            is this catalog.
        """
        return map(
            lambda x: cast(Union[Catalog, Collection], x),
            self.get_stac_objects(RelType.CHILD),
        )

    def get_collections(self) -> Iterable["Collection"]:
        """Return all children of this catalog that are :class:`~pystac.Collection`
        instances."""
        return map(
            lambda x: cast(Collection, x),
            self.get_stac_objects(RelType.CHILD, Collection),
        )

    def get_all_collections(self) -> Iterable["Collection"]:
        """Get all collections from this catalog and all subcatalogs. Will traverse
        any subcatalogs recursively."""
        yield from self.get_collections()
        for child in self.get_children():
            yield from child.get_collections()

    def get_child_links(self) -> List[Link]:
        """Return all child links of this catalog.

        Return:
            List[Link]: List of links of this catalog with ``rel == 'child'``
        """
        return self.get_links(RelType.CHILD)

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
        new_links: List["Link_Type"] = []
        root = self.get_root()
        for link in self.links:
            if link.rel != RelType.CHILD:
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

    def get_item(self, id: str, recursive: bool = False) -> Optional["Item"]:
        """Returns an item with a given ID.

        Args:
            id : The ID of the item to find.
            recursive : If True, search this catalog and all children for the
                item; otherwise, only search the items of this catalog. Defaults
                to False.

        Return:
            Item or None: The item with the given ID, or None if not found.
        """
        if not recursive:
            return next((i for i in self.get_items() if i.id == id), None)
        else:
            for root, _, _ in self.walk():
                item = root.get_item(id, recursive=False)
                if item is not None:
                    return item
            return None

    def get_items(self) -> Iterable["Item"]:
        """Return all items of this catalog.

        Return:
            Iterable[Item]: Generator of items whose parent is this catalog.
        """
        return map(
            lambda x: cast("Item", x), self.get_stac_objects(RelType.ITEM)
        )

    def clear_items(self) -> None:
        """Removes all items from this catalog.

        Return:
            Catalog: Returns ``self``
        """
        for link in self.get_item_links():
            if link.is_resolved():
                item = cast("Item", link.target)
                item.set_parent(None)
                item.set_root(None)

        self.links = [link for link in self.links if link.rel != RelType.ITEM]

    def remove_item(self, item_id: str) -> None:
        """Removes an item from this catalog.

        Args:
            item_id : The ID of the item to remove.
        """
        new_links: List["Link_Type"] = []
        root = self.get_root()
        for link in self.links:
            if link.rel != RelType.ITEM:
                new_links.append(link)
            else:
                link.resolve_stac_object(root=root)
                item = cast("Item", link.target)
                if item.id != item_id:
                    new_links.append(link)
                else:
                    item.set_parent(None)
                    item.set_root(None)
        self.links = new_links

    def get_all_items(self) -> Iterable["Item"]:
        """Get all items from this catalog and all subcatalogs. Will traverse
        any subcatalogs recursively.

        Returns:
            Generator[Item]: All items that belong to this catalog, and all
                catalogs or collections connected to this catalog through
                child links.
        """
        yield from self.get_items()
        for child in self.get_children():
            yield from child.get_all_items()

    def get_item_links(self) -> List[Link]:
        """Return all item links of this catalog.

        Return:
            List[Link]: List of links of this catalog with ``rel == 'item'``
        """
        return self.get_links(RelType.ITEM)

    def to_dict(self, include_self_link: bool = True) -> Dict[str, Any]:
        links = self.links
        if not include_self_link:
            links = [x for x in links if x.rel != RelType.SELF]

        d: Dict[str, Any] = {
            "type": self.STAC_OBJECT_TYPE.value.title(),
            "id": self.id,
            "stac_version": pystac.get_stac_version(),
            "description": self.description,
            "links": [link.to_dict() for link in links],
        }

        if self.stac_extensions is not None:
            d["stac_extensions"] = self.stac_extensions

        for key in self.extra_fields:
            d[key] = self.extra_fields[key]

        if self.title is not None:
            d["title"] = self.title

        return d

    def clone(self) -> "Catalog":
        cls = self.__class__
        clone = cls(
            id=self.id,
            description=self.description,
            title=self.title,
            stac_extensions=self.stac_extensions,
            extra_fields=deepcopy(self.extra_fields),
            catalog_type=self.catalog_type,
        )
        clone._resolved_objects.cache(clone)

        for link in self.links:
            if link.rel == RelType.ROOT:
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
        """Makes all the HREFs of assets belonging to items in this catalog
        and all children to be relative, recursively.
        """
        for _, _, items in self.walk():
            for item in items:
                item.make_asset_hrefs_relative()

    def make_all_asset_hrefs_absolute(self) -> None:
        """Makes all the HREFs of assets belonging to items in this catalog
        and all children to be absolute, recursively.
        """
        for _, _, items in self.walk():
            for item in items:
                item.make_asset_hrefs_absolute()

    def normalize_and_save(
        self,
        root_href: str,
        catalog_type: Optional[CatalogType] = None,
        strategy: Optional[HrefLayoutStrategy] = None,
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
                HREFS for this catalog. Defaults to
                :class:`~pystac.layout.BestPracticesLayoutStrategy`
        """
        self.normalize_hrefs(root_href, strategy=strategy)
        self.save(catalog_type)

    def normalize_hrefs(
        self, root_href: str, strategy: Optional[HrefLayoutStrategy] = None
    ) -> None:
        """Normalize HREFs will regenerate all link HREFs based on
        an absolute root_href and the canonical catalog layout as specified
        in the STAC specification's best practices.

        This method mutates the entire catalog tree.

        Args:
            root_href : The absolute HREF that all links will be normalized against.
            strategy : The layout strategy to use in setting the HREFS
                for this catalog. Defaults to
                :class:`~pystac.layout.BestPracticesLayoutStrategy`

        See:
            :stac-spec:`STAC best practices document <best-practices.md#catalog-layout>`
            for the canonical layout of a STAC.
        """
        if strategy is None:
            _strategy: HrefLayoutStrategy = BestPracticesLayoutStrategy()
        else:
            _strategy = strategy

        # Normalizing requires an absolute path
        if not is_absolute_href(root_href):
            root_href = make_absolute_href(root_href, os.getcwd(), start_is_dir=True)

        def process_item(item: "Item", _root_href: str) -> Callable[[], None]:
            item.resolve_links()

            new_self_href = _strategy.get_href(item, _root_href)

            def fn() -> None:
                item.set_self_href(new_self_href)

            return fn

        def process_catalog(
            cat: Catalog, _root_href: str, is_root: bool
        ) -> List[Callable[[], None]]:
            setter_funcs: List[Callable[[], None]] = []

            cat.resolve_links()

            new_self_href = _strategy.get_href(cat, _root_href, is_root)
            new_root = os.path.dirname(new_self_href)

            for item in cat.get_items():
                setter_funcs.append(process_item(item, new_root))

            for child in cat.get_children():
                setter_funcs.extend(process_catalog(child, new_root, is_root=False))

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
        defaults: Optional[Dict[str, Any]] = None,
        parent_ids: Optional[List[str]] = None,
    ) -> List["Catalog"]:
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
            [catalog]: List of new catalogs created
        """
        result: List[Catalog] = []
        parent_ids = parent_ids or list()
        parent_ids.append(self.id)
        for child in self.get_children():
            result.extend(
                child.generate_subcatalogs(
                    template, defaults=defaults, parent_ids=parent_ids.copy()
                )
            )

        layout_template = LayoutTemplate(template, defaults=defaults)

        keep_item_links: List[Link] = []
        item_links = [lk for lk in self.links if lk.rel == RelType.ITEM]
        for link in item_links:
            link.resolve_stac_object(root=self.get_root())
            item = cast("Item", link.target)
            item_parts = layout_template.get_template_values(item)
            id_iter = reversed(parent_ids)
            if all(
                [
                    "{}".format(id) == next(id_iter, None)
                    for id in reversed(list(item_parts.values()))
                ]
            ):
                # Skip items for which the sub-catalog structure already
                # matches the template. The list of parent IDs can include more
                # elements on the root side, so compare the reversed sequences.
                keep_item_links.append(link)
                continue
            curr_parent = self
            for k, v in item_parts.items():
                subcat_id = "{}".format(v)
                subcat = curr_parent.get_child(subcat_id)
                if subcat is None:
                    subcat_desc = "Catalog of items from {} with {} of {}".format(
                        curr_parent.id, k, v
                    )
                    subcat = Catalog(id=subcat_id, description=subcat_desc)
                    curr_parent.add_child(subcat)
                    result.append(subcat)
                curr_parent = subcat

            # resolve collection link so when added back points to correct location
            col_link = item.get_single_link(RelType.COLLECTION)
            if col_link is not None:
                col_link.resolve_stac_object()

            curr_parent.add_item(item)

        # keep only non-item links and item links that have not been moved elsewhere
        self.links = [
            lk for lk in self.links if lk.rel != RelType.ITEM
        ] + keep_item_links

        return result

    def save(
        self,
        catalog_type: Optional[CatalogType] = None,
        dest_href: Optional[str] = None,
    ) -> None:
        """Save this catalog and all it's children/item to files determined by the object's
        self link HREF or a specified path.

        Args:
            catalog_type : The catalog type that dictates the structure of
                the catalog to save. Use a member of :class:`~pystac.CatalogType`.
                If not supplied, the catalog_type of this catalog will be used.
                If that attribute is not set, an exception will be raised.
            dest_href : The location where the catalog is to be saved.
                If not supplied, the catalog's self link HREF is used to determine
                the location of the catalog file and children's files.
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
                    child.save(dest_href=child_dest_href)
                else:
                    child.save()

        for item_link in self.get_item_links():
            if item_link.is_resolved():
                item = cast("Item", item_link.target)
                if dest_href is not None:
                    rel_href = make_relative_href(item.self_href, self.self_href)
                    item_dest_href = make_absolute_href(
                        rel_href, dest_href, start_is_dir=True
                    )
                    item.save_object(include_self_link=True, dest_href=item_dest_href)
                else:
                    item.save_object(include_self_link=items_include_self_link)

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
            include_self_link=include_self_link, dest_href=catalog_dest_href
        )
        if catalog_type is not None:
            self.catalog_type = catalog_type

    def walk(
        self,
    ) -> Iterable[Tuple["Catalog", Iterable["Catalog"], Iterable["Item"]]]:
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

    def validate_all(self) -> None:
        """Validates each catalog, collection contained within this catalog.

        Walks through the children and items of the catalog and validates each
        stac object.

        Raises:
            STACValidationError: Raises this error on any item that is invalid.
                Will raise on the first invalid stac object encountered.
        """
        self.validate()
        for child in self.get_children():
            child.validate_all()
        for item in self.get_items():
            item.validate()

    def _object_links(self) -> List[Union[str, RelType]]:
        return [
            RelType.CHILD,
            RelType.ITEM,
            *pystac.EXTENSION_HOOKS.get_extended_object_links(self),
        ]

    def map_items(
        self,
        item_mapper: Callable[["Item"], Union["Item", List["Item"]]],
    ) -> "Catalog":
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

            item_links: List[Link] = []
            for item_link in catalog.get_item_links():
                item_link.resolve_stac_object(root=self.get_root())
                mapped = item_mapper(cast("Item", item_link.target))
                if mapped is None:
                    raise Exception("item_mapper cannot return None.")
                if isinstance(mapped, Item):
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
            [str, "Asset_Type"],
            Union["Asset_Type", Tuple[str, "Asset_Type"], Dict[str, "Asset_Type"]],
        ],
    ) -> "Catalog":
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
            tup: Tuple[str, "Asset_Type"]
        ) -> List[Tuple[str, Asset]]:
            k, v = tup
            result = asset_mapper(k, v)
            if result is None:
                raise Exception("asset_mapper cannot return None.")
            if isinstance(result, Asset):
                return [(k, result)]
            elif isinstance(result, tuple):
                return [result]
            else:
                assets = list(result.items())
                if len(assets) < 1:
                    raise Exception("asset_mapper must return a non-empty list")
                return assets

        def item_mapper(item: Item) -> Item:
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
            s += " {}".format(self.get_self_href())
        print(s)
        for child in self.get_children():
            child.describe(include_hrefs=include_hrefs, _indent=_indent + 4)
        for item in self.get_items():
            s = "{}* {}".format(" " * (_indent + 2), item)
            if include_hrefs:
                s += " {}".format(item.get_self_href())
            print(s)

    @classmethod
    def from_dict(
        cls,
        d: Dict[str, Any],
        href: Optional[str] = None,
        root: Optional["Catalog"] = None,
        migrate: bool = False,
        preserve_dict: bool = True,
    ) -> "Catalog":
        if migrate:
            info = identify_stac_object(d)
            d = migrate_to_latest(d, info)

        if not cls.matches_object_type(d):
            raise STACTypeError(f"{d} does not represent a {cls.__name__} instance")

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
            if link["rel"] == RelType.ROOT:
                # Remove the link that's generated in Catalog's constructor.
                cat.remove_links(RelType.ROOT)

            if link["rel"] != RelType.SELF or href is None:
                cat.add_link(Link.from_dict(link))

        if root:
            cat.set_root(root)

        return cat

    def full_copy(
        self, root: Optional["Catalog"] = None, parent: Optional["Catalog"] = None
    ) -> "Catalog":
        return cast(Catalog, super().full_copy(root, parent))

    @classmethod
    def from_file(cls, href: str, stac_io: Optional[StacIO] = None) -> "Catalog":
        if stac_io is None:
            stac_io = StacIO.default()

        result = super().from_file(href, stac_io)
        if not isinstance(result, Catalog):
            raise STACTypeError(f"{result} is not a {Catalog}.")
        result._stac_io = stac_io

        return result

    @classmethod
    def matches_object_type(cls, d: Dict[str, Any]) -> bool:
        return identify_stac_object_type(d) == STACObjectType.CATALOG


T = TypeVar("T")


class SpatialExtent:
    """Describes the spatial extent of a Collection.

    Args:
        bboxes : A list of bboxes that represent the spatial
            extent of the collection. Each bbox can be 2D or 3D. The length of the bbox
            array must be 2*n where n is the number of dimensions. For example, a
            2D Collection with only one bbox would be [[xmin, ymin, xmax, ymax]]

        extra_fields : Dictionary containing additional top-level fields defined on the
            Spatial Extent object.
    """

    bboxes: List[List[float]]
    """A list of bboxes that represent the spatial
    extent of the collection. Each bbox can be 2D or 3D. The length of the bbox
    array must be 2*n where n is the number of dimensions. For example, a
    2D Collection with only one bbox would be [[xmin, ymin, xmax, ymax]]"""

    extra_fields: Dict[str, Any]
    """Dictionary containing additional top-level fields defined on the Spatial
    Extent object."""

    def __init__(
        self,
        bboxes: Union[List[List[float]], List[float]],
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> None:
        # A common mistake is to pass in a single bbox instead of a list of bboxes.
        # Account for this by transforming the input in that case.
        if isinstance(bboxes, list) and isinstance(bboxes[0], float):
            self.bboxes: List[List[float]] = [cast(List[float], bboxes)]
        else:
            self.bboxes = cast(List[List[float]], bboxes)

        self.extra_fields = extra_fields or {}

    def to_dict(self) -> Dict[str, Any]:
        """Generate a dictionary representing the JSON of this SpatialExtent.

        Returns:
            dict: A serialization of the SpatialExtent that can be written out as JSON.
        """
        d = {"bbox": self.bboxes, **self.extra_fields}
        return d

    def clone(self) -> "SpatialExtent":
        """Clones this object.

        Returns:
            SpatialExtent: The clone of this object.
        """
        return SpatialExtent(
            bboxes=deepcopy(self.bboxes), extra_fields=deepcopy(self.extra_fields)
        )

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "SpatialExtent":
        """Constructs a SpatialExtent from a dict.

        Returns:
            SpatialExtent: The SpatialExtent deserialized from the JSON dict.
        """
        return SpatialExtent(
            bboxes=d["bbox"], extra_fields={k: v for k, v in d.items() if k != "bbox"}
        )

    @staticmethod
    def from_coordinates(
        coordinates: List[Any], extra_fields: Optional[Dict[str, Any]] = None
    ) -> "SpatialExtent":
        """Constructs a SpatialExtent from a set of coordinates.

        This method will only produce a single bbox that covers all points
        in the coordinate set.

        Args:
            coordinates : Coordinates to derive the bbox from.
            extra_fields : Dictionary containing additional top-level fields defined on
                the SpatialExtent object.

        Returns:
            SpatialExtent: A SpatialExtent with a single bbox that covers the
            given coordinates.
        """

        def process_coords(
            coord_lists: List[Any],
            xmin: Optional[float] = None,
            ymin: Optional[float] = None,
            xmax: Optional[float] = None,
            ymax: Optional[float] = None,
        ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
            for coord in coord_lists:
                if isinstance(coord[0], list):
                    xmin, ymin, xmax, ymax = process_coords(
                        coord, xmin, ymin, xmax, ymax
                    )
                else:
                    x, y = coord
                    if xmin is None or x < xmin:
                        xmin = x
                    elif xmax is None or xmax < x:
                        xmax = x
                    if ymin is None or y < ymin:
                        ymin = y
                    elif ymax is None or ymax < y:
                        ymax = y
            return xmin, ymin, xmax, ymax

        xmin, ymin, xmax, ymax = process_coords(coordinates)

        if xmin is None or ymin is None or xmax is None or ymax is None:
            raise ValueError(
                f"Could not determine bounds from coordinate sequence {coordinates}"
            )

        return SpatialExtent(
            bboxes=[[xmin, ymin, xmax, ymax]], extra_fields=extra_fields
        )


class TemporalExtent:
    """Describes the temporal extent of a Collection.

    Args:
        intervals :  A list of two datetimes wrapped in a list,
            representing the temporal extent of a Collection. Open date ranges are
            supported by setting either the start (the first element of the interval)
            or the end (the second element of the interval) to None.

        extra_fields : Dictionary containing additional top-level fields defined on the
            Temporal Extent object.
    Note:
        Datetimes are required to be in UTC.
    """

    intervals: List[List[Optional[Datetime]]]
    """A list of two datetimes wrapped in a list,
    representing the temporal extent of a Collection. Open date ranges are
    represented by either the start (the first element of the interval) or the
    end (the second element of the interval) being None."""

    extra_fields: Dict[str, Any]
    """Dictionary containing additional top-level fields defined on the Temporal
    Extent object."""

    def __init__(
        self,
        intervals: Union[List[List[Optional[Datetime]]], List[Optional[Datetime]]],
        extra_fields: Optional[Dict[str, Any]] = None,
    ):
        # A common mistake is to pass in a single interval instead of a
        # list of intervals. Account for this by transforming the input
        # in that case.
        if isinstance(intervals, list) and isinstance(intervals[0], Datetime):
            self.intervals = [cast(List[Optional[Datetime]], intervals)]
        else:
            self.intervals = cast(List[List[Optional[Datetime]]], intervals)

        self.extra_fields = extra_fields or {}

    def to_dict(self) -> Dict[str, Any]:
        """Generate a dictionary representing the JSON of this TemporalExtent.

        Returns:
            dict: A serialization of the TemporalExtent that can be written out as JSON.
        """
        encoded_intervals: List[List[Optional[str]]] = []
        for i in self.intervals:
            start = None
            end = None

            if i[0] is not None:
                start = datetime_to_str(i[0])

            if i[1] is not None:
                end = datetime_to_str(i[1])

            encoded_intervals.append([start, end])

        d = {"interval": encoded_intervals, **self.extra_fields}
        return d

    def clone(self) -> "TemporalExtent":
        """Clones this object.

        Returns:
            TemporalExtent: The clone of this object.
        """
        return TemporalExtent(
            intervals=deepcopy(self.intervals), extra_fields=deepcopy(self.extra_fields)
        )

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "TemporalExtent":
        """Constructs an TemporalExtent from a dict.

        Returns:
            TemporalExtent: The TemporalExtent deserialized from the JSON dict.
        """
        parsed_intervals: List[List[Optional[Datetime]]] = []
        for i in d["interval"]:
            start = None
            end = None

            if i[0]:
                start = parser.parse(i[0])
            if i[1]:
                end = parser.parse(i[1])
            parsed_intervals.append([start, end])

        return TemporalExtent(
            intervals=parsed_intervals,
            extra_fields={k: v for k, v in d.items() if k != "interval"},
        )

    @staticmethod
    def from_now() -> "TemporalExtent":
        """Constructs an TemporalExtent with a single open interval that has
        the start time as the current time.

        Returns:
            TemporalExtent: The resulting TemporalExtent.
        """
        return TemporalExtent(
            intervals=[[Datetime.utcnow().replace(microsecond=0), None]]
        )


class Extent:
    """Describes the spatiotemporal extents of a Collection.

    Args:
        spatial : Potential spatial extent covered by the collection.
        temporal : Potential temporal extent covered by the collection.
        extra_fields : Dictionary containing additional top-level fields defined on the
            Extent object.
    """

    spatial: SpatialExtent
    """Potential spatial extent covered by the collection."""

    temporal: TemporalExtent
    """Potential temporal extent covered by the collection."""

    extra_fields: Dict[str, Any]
    """Dictionary containing additional top-level fields defined on the Extent
    object."""

    def __init__(
        self,
        spatial: SpatialExtent,
        temporal: TemporalExtent,
        extra_fields: Optional[Dict[str, Any]] = None,
    ):
        self.spatial = spatial
        self.temporal = temporal
        self.extra_fields = extra_fields or {}

    def to_dict(self) -> Dict[str, Any]:
        """Generate a dictionary representing the JSON of this Extent.

        Returns:
            dict: A serialization of the Extent that can be written out as JSON.
        """
        d = {
            "spatial": self.spatial.to_dict(),
            "temporal": self.temporal.to_dict(),
            **self.extra_fields,
        }

        return d

    def clone(self) -> "Extent":
        """Clones this object.

        Returns:
            Extent: The clone of this extent.
        """
        return Extent(
            spatial=self.spatial.clone(),
            temporal=self.temporal.clone(),
            extra_fields=deepcopy(self.extra_fields),
        )

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Extent":
        """Constructs an Extent from a dict.

        Returns:
            Extent: The Extent deserialized from the JSON dict.
        """
        return Extent(
            spatial=SpatialExtent.from_dict(d["spatial"]),
            temporal=TemporalExtent.from_dict(d["temporal"]),
            extra_fields={
                k: v for k, v in d.items() if k not in {"spatial", "temporal"}
            },
        )

    @staticmethod
    def from_items(
        items: Iterable["Item"], extra_fields: Optional[Dict[str, Any]] = None
    ) -> "Extent":
        """Create an Extent based on the datetimes and bboxes of a list of items.

        Args:
            items : A list of items to derive the extent from.
            extra_fields : Optional dictionary containing additional top-level fields
                defined on the Extent object.

        Returns:
            Extent: An Extent that spatially and temporally covers all of the
                given items.
        """
        bounds_values: List[List[float]] = [
            [float("inf")],
            [float("inf")],
            [float("-inf")],
            [float("-inf")],
        ]
        datetimes: List[Datetime] = []
        starts: List[Datetime] = []
        ends: List[Datetime] = []

        for item in items:
            if item.bbox is not None:
                for i in range(0, 4):
                    bounds_values[i].append(item.bbox[i])
            if item.datetime is not None:
                datetimes.append(item.datetime)
            if item.common_metadata.start_datetime is not None:
                starts.append(item.common_metadata.start_datetime)
            if item.common_metadata.end_datetime is not None:
                ends.append(item.common_metadata.end_datetime)

        if not any(datetimes + starts):
            start_timestamp = None
        else:
            start_timestamp = min(
                [
                    dt if dt.tzinfo else dt.replace(tzinfo=tz.UTC)
                    for dt in datetimes + starts
                ]
            )
        if not any(datetimes + ends):
            end_timestamp = None
        else:
            end_timestamp = max(
                [
                    dt if dt.tzinfo else dt.replace(tzinfo=tz.UTC)
                    for dt in datetimes + ends
                ]
            )

        spatial = SpatialExtent(
            [
                [
                    min(bounds_values[0]),
                    min(bounds_values[1]),
                    max(bounds_values[2]),
                    max(bounds_values[3]),
                ]
            ]
        )
        temporal = TemporalExtent([[start_timestamp, end_timestamp]])

        return Extent(spatial=spatial, temporal=temporal, extra_fields=extra_fields)


class Collection(Catalog):
    """A Collection extends the Catalog spec with additional metadata that helps
    enable discovery.

    Args:
        id : Identifier for the collection. Must be unique within the STAC.
        description : Detailed multi-line description to fully explain the
            collection. `CommonMark 0.28 syntax <https://commonmark.org/>`_ MAY
            be used for rich text representation.
        extent : Spatial and temporal extents that describe the bounds of
            all items contained within this Collection.
        title : Optional short descriptive one-line title for the
            collection.
        stac_extensions : Optional list of extensions the Collection
            implements.
        href : Optional HREF for this collection, which be set as the
            collection's self link's HREF.
        catalog_type : Optional catalog type for this catalog. Must
            be one of the values in :class`~pystac.CatalogType`.
        license :  Collection's license(s) as a
            `SPDX License identifier <https://spdx.org/licenses/>`_,
            `various`, or `proprietary`. If collection includes
            data with multiple different licenses, use `various` and add a link for
            each. Defaults to 'proprietary'.
        keywords : Optional list of keywords describing the collection.
        providers : Optional list of providers of this Collection.
        summaries : An optional map of property summaries,
            either a set of values or statistics such as a range.
        extra_fields : Extra fields that are part of the top-level
            JSON properties of the Collection.

    Attributes:
        id : Identifier for the collection.
        description : Detailed multi-line description to fully explain the
            collection.
        extent : Spatial and temporal extents that describe the bounds of
            all items contained within this Collection.
        title : Optional short descriptive one-line title for the
            collection.
        stac_extensions : Optional list of extensions the Collection
            implements.
        keywords : Optional list of keywords describing the
            collection.
        providers : Optional list of providers of this
            Collection.
        assets : Optional map of Assets
        summaries : An optional map of property summaries,
            either a set of values or statistics such as a range.
        links : A list of :class:`~pystac.Link` objects representing
            all links associated with this Collection.
        extra_fields : Extra fields that are part of the top-level
            JSON properties of the Catalog.
    """

    STAC_OBJECT_TYPE = STACObjectType.COLLECTION

    DEFAULT_FILE_NAME = "collection.json"
    """Default file name that will be given to this STAC object
    in a canonical format."""

    def __init__(
        self,
        id: str,
        description: str,
        extent: Extent,
        title: Optional[str] = None,
        stac_extensions: Optional[List[str]] = None,
        href: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
        catalog_type: Optional[CatalogType] = None,
        license: str = "proprietary",
        keywords: Optional[List[str]] = None,
        providers: Optional[List["Provider_Type"]] = None,
        summaries: Optional[Summaries] = None,
    ):
        super().__init__(
            id,
            description,
            title,
            stac_extensions,
            extra_fields,
            href,
            catalog_type or CatalogType.ABSOLUTE_PUBLISHED,
        )
        self.extent = extent
        self.license = license

        self.stac_extensions: List[str] = stac_extensions or []
        self.keywords = keywords
        self.providers = providers
        self.summaries = summaries or Summaries.empty()

        self.assets: Dict[str, Asset] = {}

    def __repr__(self) -> str:
        return "<Collection id={}>".format(self.id)

    def add_item(
        self,
        item: "Item",
        title: Optional[str] = None,
        strategy: Optional[HrefLayoutStrategy] = None,
    ) -> None:
        super().add_item(item, title, strategy)
        item.set_collection(self)

    def to_dict(self, include_self_link: bool = True) -> Dict[str, Any]:
        d = super().to_dict(include_self_link)
        d["extent"] = self.extent.to_dict()
        d["license"] = self.license
        if self.stac_extensions is not None:
            d["stac_extensions"] = self.stac_extensions
        if self.keywords is not None:
            d["keywords"] = self.keywords
        if self.providers is not None:
            d["providers"] = list(map(lambda x: x.to_dict(), self.providers))
        if not self.summaries.is_empty():
            d["summaries"] = self.summaries.to_dict()
        if any(self.assets):
            d["assets"] = {k: v.to_dict() for k, v in self.assets.items()}

        return d

    def clone(self) -> "Collection":
        cls = self.__class__
        clone = cls(
            id=self.id,
            description=self.description,
            extent=self.extent.clone(),
            title=self.title,
            stac_extensions=self.stac_extensions,
            extra_fields=self.extra_fields,
            catalog_type=self.catalog_type,
            license=self.license,
            keywords=self.keywords,
            providers=self.providers,
            summaries=self.summaries,
        )

        clone._resolved_objects.cache(clone)

        for link in self.links:
            if link.rel == RelType.ROOT:
                # Collection __init__ sets correct root to clone; don't reset
                # if the root link points to self
                root_is_self = link.is_resolved() and link.target is self
                if not root_is_self:
                    clone.set_root(None)
                    clone.add_link(link.clone())
            else:
                clone.add_link(link.clone())

        return clone

    @classmethod
    def from_dict(
        cls,
        d: Dict[str, Any],
        href: Optional[str] = None,
        root: Optional[Catalog] = None,
        migrate: bool = False,
        preserve_dict: bool = True,
    ) -> "Collection":
        if migrate:
            info = identify_stac_object(d)
            d = migrate_to_latest(d, info)

        if not cls.matches_object_type(d):
            raise STACTypeError(f"{d} does not represent a {cls.__name__} instance")

        catalog_type = CatalogType.determine_type(d)

        if preserve_dict:
            d = deepcopy(d)

        id = d.pop("id")
        description = d.pop("description")
        license = d.pop("license")
        extent = Extent.from_dict(d.pop("extent"))
        title = d.get("title")
        stac_extensions = d.get("stac_extensions")
        keywords = d.get("keywords")
        providers = d.get("providers")
        if providers is not None:
            providers = list(map(lambda x: Provider.from_dict(x), providers))
        summaries = d.get("summaries")
        if summaries is not None:
            summaries = Summaries(summaries)

        assets: Optional[Dict[str, Any]] = d.get("assets", None)
        links = d.pop("links")

        d.pop("stac_version")

        collection = cls(
            id=id,
            description=description,
            extent=extent,
            title=title,
            stac_extensions=stac_extensions,
            extra_fields=d,
            license=license,
            keywords=keywords,
            providers=providers,
            summaries=summaries,
            href=href,
            catalog_type=catalog_type,
        )

        for link in links:
            if link["rel"] == RelType.ROOT:
                # Remove the link that's generated in Catalog's constructor.
                collection.remove_links(RelType.ROOT)

            if link["rel"] != RelType.SELF or href is None:
                collection.add_link(Link.from_dict(link))

        if assets is not None:
            for asset_key, asset_dict in assets.items():
                collection.add_asset(asset_key, Asset.from_dict(asset_dict))

        if root:
            collection.set_root(root)

        return collection

    def get_assets(self) -> Dict[str, Asset]:
        """Get this item's assets.

        Returns:
            Dict[str, Asset]: A copy of the dictionary of this item's assets.
        """
        return dict(self.assets.items())

    def add_asset(self, key: str, asset: Asset) -> None:
        """Adds an Asset to this item.

        Args:
            key : The unique key of this asset.
            asset : The Asset to add.
        """
        asset.set_owner(self)
        self.assets[key] = asset

    def update_extent_from_items(self) -> None:
        """
        Update datetime and bbox based on all items to a single bbox and time window.
        """
        self.extent = Extent.from_items(self.get_all_items())

    def full_copy(
        self, root: Optional["Catalog"] = None, parent: Optional["Catalog"] = None
    ) -> "Collection":
        return cast(Collection, super().full_copy(root, parent))

    @classmethod
    def from_file(
        cls, href: str, stac_io: Optional[StacIO] = None
    ) -> "Collection":
        result = super().from_file(href, stac_io)
        if not isinstance(result, Collection):
            raise STACTypeError(f"{result} is not a {Collection}.")
        return result

    @classmethod
    def matches_object_type(cls, d: Dict[str, Any]) -> bool:
        return identify_stac_object_type(d) == STACObjectType.COLLECTION


class Item(STACObject):
    """An Item is the core granular entity in a STAC, containing the core metadata
    that enables any client to search or crawl online catalogs of spatial 'assets' -
    satellite imagery, derived data, DEM's, etc.

    Args:
        id : Provider identifier. Must be unique within the STAC.
        geometry : Defines the full footprint of the asset represented by this
            item, formatted according to
            `RFC 7946, section 3.1 (GeoJSON) <https://tools.ietf.org/html/rfc7946>`_.
        bbox :  Bounding Box of the asset represented by this item
            using either 2D or 3D geometries. The length of the array must be 2*n
            where n is the number of dimensions. Could also be None in the case of a
            null geometry.
        datetime : Datetime associated with this item. If None,
            a start_datetime and end_datetime must be supplied in the properties.
        properties : A dictionary of additional metadata for the item.
        stac_extensions : Optional list of extensions the Item implements.
        href : Optional HREF for this item, which be set as the item's
            self link's HREF.
        collection : The Collection or Collection ID that this item
            belongs to.
        extra_fields : Extra fields that are part of the top-level JSON
            properties of the Item.

    Attributes:
        id : Provider identifier. Unique within the STAC.
        geometry : Defines the full footprint of the asset represented by this
            item, formatted according to
            `RFC 7946, section 3.1 (GeoJSON) <https://tools.ietf.org/html/rfc7946>`_.
        bbox :  Bounding Box of the asset represented by this item
            using either 2D or 3D geometries. The length of the array is 2*n where n
            is the number of dimensions. Could also be None in the case of a null
            geometry.
        datetime : Datetime associated with this item. If None,
            the start_datetime and end_datetime in the common_metadata
            will supply the datetime range of the Item.
        properties : A dictionary of additional metadata for the item.
        stac_extensions : Optional list of extensions the Item
            implements.
        collection : Collection that this item is a part of.
        links : A list of :class:`~pystac.Link` objects representing
            all links associated with this STACObject.
        assets : Dictionary of asset objects that can be downloaded,
            each with a unique key.
        collection_id : The Collection ID that this item belongs to, if
            any.
        extra_fields : Extra fields that are part of the top-level JSON
            properties of the Item.
    """

    STAC_OBJECT_TYPE = STACObjectType.ITEM

    def __init__(
        self,
        id: str,
        geometry: Optional[Dict[str, Any]],
        bbox: Optional[List[float]],
        datetime: Optional[Datetime],
        properties: Dict[str, Any],
        stac_extensions: Optional[List[str]] = None,
        href: Optional[str] = None,
        collection: Optional[Union[str, Collection]] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(stac_extensions or [])

        self.id = id
        self.geometry = geometry
        self.bbox = bbox
        self.properties = properties
        if extra_fields is None:
            self.extra_fields = {}
        else:
            self.extra_fields = extra_fields

        self.assets: Dict[str, Asset] = {}

        self.datetime: Optional[Datetime] = None
        if datetime is None:
            if "start_datetime" not in properties or "end_datetime" not in properties:
                raise STACError(
                    "Invalid Item: If datetime is None, "
                    "a start_datetime and end_datetime "
                    "must be supplied in "
                    "the properties."
                )
            self.datetime = None
        else:
            self.datetime = datetime

        if href is not None:
            self.set_self_href(href)

        self.collection_id: Optional[str] = None
        if collection is not None:
            if isinstance(collection, Collection):
                self.set_collection(collection)
            else:
                self.collection_id = collection

    def __repr__(self) -> str:
        return "<Item id={}>".format(self.id)

    def set_self_href(self, href: Optional[str]) -> None:
        """Sets the absolute HREF that is represented by the ``rel == 'self'``
        :class:`~pystac.Link`.

        Changing the self HREF of the item will ensure that all asset HREFs
        remain valid. If asset HREFs are relative, the HREFs will change
        to point to the same location based on the new item self HREF,
        either by making them relative to the new location or making them
        absolute links if the new location does not share the same protocol
        as the old location.

        Args:
            href : The absolute HREF of this object. If the given HREF
                is not absolute, it will be transformed to an absolute
                HREF based on the current working directory. If this is None
                the call will clear the self HREF link.
        """
        prev_href = self.get_self_href()
        super().set_self_href(href)
        new_href = self.get_self_href()  # May have been made absolute.

        if prev_href is not None and new_href is not None:
            # Make sure relative asset links remain valid.
            for asset in self.assets.values():
                asset_href = asset.href
                if not is_absolute_href(asset_href):
                    abs_href = make_absolute_href(asset_href, prev_href)
                    new_relative_href = make_relative_href(abs_href, new_href)
                    asset.href = new_relative_href

    def get_datetime(self, asset: Optional[Asset] = None) -> Optional[Datetime]:
        """Gets an Item or an Asset datetime.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value.

        Returns:
            datetime or None
        """
        if asset is None or "datetime" not in asset.extra_fields:
            return self.datetime
        else:
            asset_dt = asset.extra_fields.get("datetime")
            if asset_dt is None:
                return None
            else:
                return str_to_datetime(asset_dt)

    def set_datetime(self, datetime: Datetime, asset: Optional[Asset] = None) -> None:
        """Set an Item or an Asset datetime.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.datetime = datetime
        else:
            asset.extra_fields["datetime"] = datetime_to_str(datetime)

    def get_assets(self) -> Dict[str, Asset]:
        """Get this item's assets.

        Returns:
            Dict[str, Asset]: A copy of the dictionary of this item's assets.
        """
        return dict(self.assets.items())

    def add_asset(self, key: str, asset: Asset) -> None:
        """Adds an Asset to this item.

        Args:
            key : The unique key of this asset.
            asset : The Asset to add.
        """
        asset.set_owner(self)
        self.assets[key] = asset

    def make_asset_hrefs_relative(self) -> "Item":
        """Modify each asset's HREF to be relative to this item's self HREF.

        Returns:
            Item: self
        """

        self_href = None
        for asset in self.assets.values():
            href = asset.href
            if is_absolute_href(href):
                if self_href is None:
                    self_href = self.get_self_href()
                    if self_href is None:
                        raise STACError(
                            "Cannot make asset HREFs relative "
                            "if no self_href is set."
                        )
                asset.href = make_relative_href(asset.href, self_href)
        return self

    def make_asset_hrefs_absolute(self) -> "Item":
        """Modify each asset's HREF to be absolute.

        Any asset HREFs that are relative will be modified to absolute based on this
        item's self HREF.

        Returns:
            Item: self
        """
        self_href = None
        for asset in self.assets.values():
            href = asset.href
            if not is_absolute_href(href):
                if self_href is None:
                    self_href = self.get_self_href()
                    if self_href is None:
                        raise STACError(
                            "Cannot make relative asset HREFs absolute "
                            "if no self_href is set."
                        )
                asset.href = make_absolute_href(asset.href, self_href)

        return self

    def set_collection(self, collection: Optional[Collection]) -> "Item":
        """Set the collection of this item.

        This method will replace any existing Collection link and attribute for
        this item.

        Args:
            collection : The collection to set as this
                item's collection. If None, will clear the collection.

        Returns:
            Item: self
        """
        self.remove_links(RelType.COLLECTION)
        self.collection_id = None
        if collection is not None:
            self.add_link(Link.collection(collection))
            self.collection_id = collection.id

        return self

    def get_collection(self) -> Optional[Collection]:
        """Gets the collection of this item, if one exists.

        Returns:
            Collection or None: If this item belongs to a collection, returns
            a reference to the collection. Otherwise returns None.
        """
        collection_link = self.get_single_link(RelType.COLLECTION)
        if collection_link is None:
            return None
        else:
            return cast(Collection, collection_link.resolve_stac_object().target)

    def to_dict(self, include_self_link: bool = True) -> Dict[str, Any]:
        links = self.links
        if not include_self_link:
            links = [x for x in links if x.rel != RelType.SELF]

        assets = {k: v.to_dict() for k, v in self.assets.items()}

        if self.datetime is not None:
            self.properties["datetime"] = datetime_to_str(self.datetime)
        else:
            self.properties["datetime"] = None

        d: Dict[str, Any] = {
            "type": "Feature",
            "stac_version": pystac.get_stac_version(),
            "id": self.id,
            "properties": self.properties,
            "geometry": self.geometry,
            "links": [link.to_dict() for link in links],
            "assets": assets,
        }

        if self.bbox is not None:
            d["bbox"] = self.bbox

        if self.stac_extensions is not None:
            d["stac_extensions"] = self.stac_extensions

        if self.collection_id:
            d["collection"] = self.collection_id

        for key in self.extra_fields:
            d[key] = self.extra_fields[key]

        return d

    def clone(self) -> "Item":
        cls = self.__class__
        clone = cls(
            id=self.id,
            geometry=deepcopy(self.geometry),
            bbox=copy(self.bbox),
            datetime=copy(self.datetime),
            properties=deepcopy(self.properties),
            stac_extensions=deepcopy(self.stac_extensions),
            collection=self.collection_id,
        )
        for link in self.links:
            clone.add_link(link.clone())

        for k, asset in self.assets.items():
            clone.add_asset(k, asset.clone())

        return clone

    def _object_links(self) -> List[Union[str, RelType]]:
        return [
            RelType.COLLECTION,
            *pystac.EXTENSION_HOOKS.get_extended_object_links(self),
        ]

    @classmethod
    def from_dict(
        cls,
        d: Dict[str, Any],
        href: Optional[str] = None,
        root: Optional[Catalog] = None,
        migrate: bool = False,
        preserve_dict: bool = True,
    ) -> "Item":
        if migrate:
            info = identify_stac_object(d)
            d = migrate_to_latest(d, info)

        if not cls.matches_object_type(d):
            raise STACTypeError(
                f"{d} does not represent a {cls.__name__} instance"
            )

        if preserve_dict:
            d = deepcopy(d)

        id = d.pop("id")
        geometry = d.pop("geometry")
        properties = d.pop("properties")
        bbox = d.pop("bbox", None)
        stac_extensions = d.get("stac_extensions")
        collection_id = d.pop("collection", None)

        datetime = properties.get("datetime")
        if datetime is not None:
            datetime = parser.parse(datetime)
        links = d.pop("links")
        assets = d.pop("assets")

        d.pop("type")
        d.pop("stac_version")

        item = cls(
            id=id,
            geometry=geometry,
            bbox=bbox,
            datetime=datetime,
            properties=properties,
            stac_extensions=stac_extensions,
            collection=collection_id,
            extra_fields=d,
        )

        has_self_link = False
        for link in links:
            has_self_link |= link["rel"] == RelType.SELF
            item.add_link(Link.from_dict(link))

        if not has_self_link and href is not None:
            item.add_link(Link.self_href(href))

        for k, v in assets.items():
            asset = Asset.from_dict(v)
            asset.set_owner(item)
            item.assets[k] = asset

        if root:
            item.set_root(root)

        return item

    @property
    def common_metadata(self) -> "CommonMetadata_Type":
        """Access the item's common metadata fields as a
        :class:`~pystac.CommonMetadata` object."""
        return CommonMetadata(self)

    def full_copy(
        self, root: Optional["Catalog"] = None, parent: Optional["Catalog"] = None
    ) -> "Item":
        return cast(Item, super().full_copy(root, parent))

    @classmethod
    def from_file(cls, href: str, stac_io: Optional[StacIO] = None) -> "Item":
        result = super().from_file(href, stac_io)
        if not isinstance(result, Item):
            raise STACTypeError(f"{result} is not a {Item}.")
        return result

    @classmethod
    def matches_object_type(cls, d: Dict[str, Any]) -> bool:
        return identify_stac_object_type(d) == STACObjectType.ITEM

