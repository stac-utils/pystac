import os
from html import escape
from copy import deepcopy
from pystac.errors import STACTypeError
from pystac.html.jinja_env import get_jinja_env
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    TYPE_CHECKING,
    Tuple,
    Union,
    cast,
)

import pystac
from pystac.stac_object import STACObject, STACObjectType
from pystac.layout import (
    BestPracticesLayoutStrategy,
    HrefLayoutStrategy,
    LayoutTemplate,
)
from pystac.link import Link
from pystac.cache import ResolvedObjectCache
from pystac.serialization import (
    identify_stac_object_type,
    identify_stac_object,
    migrate_to_latest,
)
from pystac.utils import (
    StringEnum,
    is_absolute_href,
    make_absolute_href,
    make_relative_href,
)

if TYPE_CHECKING:
    from pystac.asset import Asset as Asset_Type
    from pystac.item import Item as Item_Type
    from pystac.collection import Collection as Collection_Type


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
    """

    catalog_type: CatalogType
    """The catalog type. Defaults to :attr:`CatalogType.ABSOLUTE_PUBLISHED`."""

    description: str
    """Detailed multi-line description to fully explain the catalog."""

    extra_fields: Dict[str, Any]
    """Extra fields that are part of the top-level JSON properties of the Catalog."""

    id: str
    """Identifier for the catalog."""

    links: List[Link]
    """A list of :class:`~pystac.Link` objects representing all links associated with
    this Catalog."""

    title: Optional[str]
    """Optional short descriptive one-line title for the catalog."""

    stac_extensions: List[str]
    """List of extensions the Catalog implements."""

    _resolved_objects: ResolvedObjectCache

    STAC_OBJECT_TYPE = pystac.STACObjectType.CATALOG

    _stac_io: Optional[pystac.StacIO] = None
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

    def _repr_html_(self) -> str:
        jinja_env = get_jinja_env()
        if jinja_env:
            template = jinja_env.get_template("Catalog.jinja2")
            return str(template.render(catalog=self))
        else:
            return escape(repr(self))

    def set_root(self, root: Optional["Catalog"]) -> None:
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

    def add_child(
        self,
        child: Union["Catalog", "Collection_Type"],
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
        if isinstance(child, pystac.Item):
            raise pystac.STACError("Cannot add item as child. Use add_item instead.")

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
        self, children: Iterable[Union["Catalog", "Collection_Type"]]
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
        item: "Item_Type",
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
        if isinstance(item, pystac.Catalog):
            raise pystac.STACError("Cannot add catalog as item. Use add_child instead.")

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

    def add_items(self, items: Iterable["Item_Type"]) -> None:
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
    ) -> Optional[Union["Catalog", "Collection_Type"]]:
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

    def get_children(self) -> Iterable[Union["Catalog", "Collection_Type"]]:
        """Return all children of this catalog.

        Return:
            Iterable[Catalog or Collection]: Iterable of children who's parent
            is this catalog.
        """
        return map(
            lambda x: cast(Union[pystac.Catalog, pystac.Collection], x),
            self.get_stac_objects(pystac.RelType.CHILD),
        )

    def get_collections(self) -> Iterable["Collection_Type"]:
        """Return all children of this catalog that are :class:`~pystac.Collection`
        instances."""
        return map(
            lambda x: cast(pystac.Collection, x),
            self.get_stac_objects(pystac.RelType.CHILD, pystac.Collection),
        )

    def get_all_collections(self) -> Iterable["Collection_Type"]:
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
        return self.get_links(pystac.RelType.CHILD)

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
        new_links: List[pystac.Link] = []
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

    def get_item(self, id: str, recursive: bool = False) -> Optional["Item_Type"]:
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

    def get_items(self) -> Iterable["Item_Type"]:
        """Return all items of this catalog.

        Return:
            Iterable[Item]: Generator of items whose parent is this catalog.
        """
        return map(
            lambda x: cast(pystac.Item, x), self.get_stac_objects(pystac.RelType.ITEM)
        )

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
        new_links: List[pystac.Link] = []
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

    def get_all_items(self) -> Iterable["Item_Type"]:
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
        return self.get_links(pystac.RelType.ITEM)

    def to_dict(
        self, include_self_link: bool = True, transform_hrefs: bool = True
    ) -> Dict[str, Any]:
        links = self.links
        if not include_self_link:
            links = [x for x in links if x.rel != pystac.RelType.SELF]

        d: Dict[str, Any] = {
            "type": self.STAC_OBJECT_TYPE.value.title(),
            "id": self.id,
            "stac_version": pystac.get_stac_version(),
            "description": self.description,
            "links": [link.to_dict(transform_href=transform_hrefs) for link in links],
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
        stac_io: Optional[pystac.StacIO] = None,
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
            stac_io : Optional instance of :class:`~pystac.StacIO` to use. If not
                provided, will use the instance set while reading in the catalog,
                or the default instance if this is not available.
        """
        self.normalize_hrefs(root_href, strategy=strategy)
        self.save(catalog_type, stac_io=stac_io)

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

        def process_item(item: "Item_Type", _root_href: str) -> Callable[[], None]:
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
        item_links = [lk for lk in self.links if lk.rel == pystac.RelType.ITEM]
        for link in item_links:
            link.resolve_stac_object(root=self.get_root())
            item = cast(pystac.Item, link.target)
            subcat_ids = layout_template.substitute(item).split("/")
            id_iter = reversed(parent_ids)
            if all(
                ["{}".format(id) == next(id_iter, None) for id in reversed(subcat_ids)]
            ):
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
        catalog_type: Optional[CatalogType] = None,
        dest_href: Optional[str] = None,
        stac_io: Optional[pystac.StacIO] = None,
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
    ) -> Iterable[Tuple["Catalog", Iterable["Catalog"], Iterable["Item_Type"]]]:
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

    def _object_links(self) -> List[Union[str, pystac.RelType]]:
        return [
            pystac.RelType.CHILD,
            pystac.RelType.ITEM,
            *pystac.EXTENSION_HOOKS.get_extended_object_links(self),
        ]

    def map_items(
        self,
        item_mapper: Callable[["Item_Type"], Union["Item_Type", List["Item_Type"]]],
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
        ) -> List[Tuple[str, pystac.Asset]]:
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
            if link["rel"] == pystac.RelType.ROOT:
                # Remove the link that's generated in Catalog's constructor.
                cat.remove_links(pystac.RelType.ROOT)

            if link["rel"] != pystac.RelType.SELF or href is None:
                cat.add_link(Link.from_dict(link))

        if root:
            cat.set_root(root)

        return cat

    def full_copy(
        self, root: Optional["Catalog"] = None, parent: Optional["Catalog"] = None
    ) -> "Catalog":
        return cast(Catalog, super().full_copy(root, parent))

    @classmethod
    def from_file(cls, href: str, stac_io: Optional[pystac.StacIO] = None) -> "Catalog":
        if stac_io is None:
            stac_io = pystac.StacIO.default()

        result = super().from_file(href, stac_io)
        if not isinstance(result, Catalog):
            raise pystac.STACTypeError(f"{result} is not a {Catalog}.")
        result._stac_io = stac_io

        return result

    @classmethod
    def matches_object_type(cls, d: Dict[str, Any]) -> bool:
        return identify_stac_object_type(d) == STACObjectType.CATALOG
