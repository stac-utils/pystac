import os
from copy import deepcopy

import pystac
from pystac import (STAC_VERSION, STACError)
from pystac.stac_object import STACObject
from pystac.link import (Link, LinkType)
from pystac.cache import ResolvedObjectCache
from pystac.utils import (is_absolute_href, make_absolute_href)


class CatalogType:
    SELF_CONTAINED = 'SELF_CONTAINED'
    """A 'self-contained catalog' is one that is designed for portability.
    Users may want to download a catalog from online and be able to use it on their
    local computer, so all links need to be relative.

    See:
        `The best practices documentation on self-contained catalogs <https://github.com/radiantearth/stac-spec/blob/v0.8.1/best-practices.md#self-contained-catalogs>`_
    """ # noqa E501

    ABSOLUTE_PUBLISHED = 'ABSOLUTE_PUBLISHED'
    """
    Absolute Published Catalog is a catalog that uses absolute links for everything,
    both in the links objects and in the asset hrefs.

    See:
        `The best practices documentation on published catalogs <https://github.com/radiantearth/stac-spec/blob/v0.8.1/best-practices.md#published-catalogs>`_
    """ # noqa E501

    RELATIVE_PUBLISHED = 'RELATIVE_PUBLISHED'
    """
    Relative Published Catalog is a catalog that uses relative links for everything,
    but includes an absolute self link at the root catalog, to identify its online location.

    See:
        `The best practices documentation on published catalogs <https://github.com/radiantearth/stac-spec/blob/v0.8.1/best-practices.md#published-catalogs>`_
    """ # noqa E501


class Catalog(STACObject):
    """A PySTAC Catalog represents a STAC catalog in memory.

    A Catalog is a :class:`~pystac.STACObject` that may contain children,
    which are instances of :class:`~pystac.Catalog` or :class:`~pystac.Collection`,
    as well as :class:`~pystac.Item` s.

    Args:
        id (str): Identifier for the catalog. Must be unique within the STAC.
        description (str): Detailed multi-line description to fully explain the catalog.
            `CommonMark 0.28 syntax <http://commonmark.org/>`_ MAY be used for rich text
            representation.
        title (str or None): Optional short descriptive one-line title for the catalog.
        stac_extensions (List[str]): Optional list of extensions the Catalog implements.
        href (str or None): Optional HREF for this catalog, which be set as the catalog's
            self link's HREF.

    Attributes:
        id (str): Identifier for the catalog.
        description (str): Detailed multi-line description to fully explain the catalog.
        title (str or None): Optional short descriptive one-line title for the catalog.
        stac_extensions (List[str] or None): Optional list of extensions the Catalog implements.
        links (List[Link]): A list of :class:`~pystac.Link` objects representing
            all links associated with this Catalog.
    """

    DEFAULT_FILE_NAME = "catalog.json"
    """Default file name that will be given to this STAC object in a cononical format."""
    def __init__(self, id, description, title=None, stac_extensions=None, href=None):
        self.id = id
        self.description = description
        self.title = title
        self.stac_extensions = stac_extensions
        self.links = []
        self.add_link(Link.root(self))

        if href is not None:
            self.set_self_href(href)

        self._resolved_objects = ResolvedObjectCache()
        self._resolved_objects.cache(self)

    def __repr__(self):
        return '<Catalog id={}>'.format(self.id)

    def set_root(self, root, link_type=LinkType.ABSOLUTE):
        STACObject.set_root(self, root, link_type)
        if root is not None:
            root._resolved_objects = ResolvedObjectCache.merge(root._resolved_objects,
                                                               self._resolved_objects)

    def add_child(self, child, title=None):
        """Adds a link to a child :class:`~pystac.Catalog` or :class:`~pystac.Collection`.
        This method will set the child's parent to this object, and its root to
        this Catalog's root.

        Args:
            child (Catalog or Collection): The child to add.
            title (str): Optional title to give to the :class:`~pystac.Link`
        """

        # Prevent typo confusion
        if isinstance(child, pystac.Item):
            raise STACError('Cannot add item as child. Use add_item instead.')

        child.set_root(self.get_root())
        child.set_parent(self)
        self.add_link(Link.child(child, title=title))

    def add_item(self, item, title=None):
        """Adds a link to an :class:`~pystac.Item`.
        This method will set the item's parent to this object, and its root to
        this Catalog's root.

        Args:
            item (Item): The item to add.
            title (str): Optional title to give to the :class:`~pystac.Link`
        """

        # Prevent typo confusion
        if isinstance(item, pystac.Catalog):
            raise STACError('Cannot add catalog as item. Use add_child instead.')

        item.set_root(self.get_root())
        item.set_parent(self)
        self.add_link(Link.item(item, title=title))

    def add_items(self, items):
        """Adds links to multiple :class:`~pystac.Item` s.
        This method will set each item's parent to this object, and their root to
        this Catalog's root.

        Args:
            items (Iterable[Item]): The items to add.
        """
        for item in items:
            self.add_item(item)

    def get_child(self, id, recursive=False):
        """Gets the child of this catalog with the given ID, if it exists.

        Args:
            id (str): The ID of the child to find.
            recursive (bool): If True, search this catalog and all children for the item;
                otherwise, only search the children of this catalog. Defaults to False.

        Return:
            Item or None: The item with the given ID, or None if not found.
        """
        if not recursive:
            return next((c for c in self.get_children() if c.id == id), None)
        else:
            for root, _, _ in self.walk():
                child = root.get_child(id, recursive=False)
                if child is not None:
                    return child
            return None

    def get_children(self):
        """Return all children of this catalog.

        Return:
            Generator[Catalog or Collection]: Generator of children who's parent
            is this catalog.
        """
        return self.get_stac_objects('child')

    def get_child_links(self):
        """Return all child links of this catalog.

        Return:
            List[Link]: List of links of this catalog with ``rel == 'child'``
        """
        return self.get_links('child')

    def clear_children(self):
        """Removes all children from this catalog.

        Return:
            Catalog: Returns ``self``
        """
        self.links = [link for link in self.links if link.rel != 'child']
        return self

    def remove_child(self, child_id):
        """Removes an child from this catalog.

        Args:
            child_id (str): The ID of the child to remove.
        """
        new_links = []
        root = self.get_root()
        for link in self.links:
            if link.rel != 'child':
                new_links.append(link)
            else:
                link.resolve_stac_object(root=root)
                if link.target.id != child_id:
                    new_links.append(link)
                else:
                    child = link.target
                    child.set_parent(None)
                    child.set_root(None)
        self.links = new_links

    def get_item(self, id, recursive=False):
        """Returns an item with a given ID.

        Args:
            id (str): The ID of the item to find.
            recursive (bool): If True, search this catalog and all children for the item;
                otherwise, only search the items of this catalog. Defaults to False.

        Return:
            Item or None: The item with the given ID, or None if not found.
        """
        if not recursive:
            return next((i for i in self.get_items() if i.id == id), None)
        else:
            for root, children, items in self.walk():
                item = root.get_item(id, recursive=False)
                if item is not None:
                    return item
            return None

    def get_items(self):
        """Return all items of this catalog.

        Return:
            Generator[Item]: Generator of items who's parent is this catalog.
        """
        return self.get_stac_objects('item')

    def clear_items(self):
        """Removes all items from this catalog.

        Return:
            Catalog: Returns ``self``
        """
        for link in self.get_item_links():
            if link.is_resolved():
                item = link.target
                item.set_parent(None)
                item.set_root(None)

        self.links = [link for link in self.links if link.rel != 'item']
        return self

    def remove_item(self, item_id):
        """Removes an item from this catalog.

        Args:
            item_id (str): The ID of the item to remove.
        """
        new_links = []
        root = self.get_root()
        for link in self.links:
            if link.rel != 'item':
                new_links.append(link)
            else:
                link.resolve_stac_object(root=root)
                if link.target.id != item_id:
                    new_links.append(link)
                else:
                    item = link.target
                    item.set_parent(None)
                    item.set_root(None)
        self.links = new_links

    def get_all_items(self):
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

    def get_item_links(self):
        """Return all item links of this catalog.

        Return:
            List[Link]: List of links of this catalog with ``rel == 'item'``
        """
        return self.get_links('item')

    def to_dict(self, include_self_link=True):
        links = self.links
        if not include_self_link:
            links = filter(lambda l: l.rel != 'self', links)

        d = {
            'id': self.id,
            'stac_version': STAC_VERSION,
            'description': self.description,
            'links': [link.to_dict() for link in links]
        }

        if self.title is not None:
            d['title'] = self.title

        return deepcopy(d)

    def clone(self):
        clone = Catalog(id=self.id, description=self.description, title=self.title)
        clone._resolved_objects.cache(clone)

        for link in self.links:
            if link.rel == 'root':
                # Catalog __init__ sets correct root to clone; don't reset
                # if the root link points to self
                root_is_self = link.is_resolved() and link.target is self
                if not root_is_self:
                    clone.set_root(None)
                    clone.add_link(link.clone())
            else:
                clone.add_link(link.clone())

        return clone

    def make_all_links_relative(self):
        """Makes all the links of this catalog and all children and item
        to be relative, recursively
        """
        super().make_links_relative()

        for child in self.get_children():
            child.make_all_links_relative()
        for item in self.get_items():
            item.make_links_relative()

    def make_all_links_absolute(self):
        """Makes all the links of this catalog and all children and item
        to be absolute, recursively
        """
        super().make_links_absolute()

        for child in self.get_children():
            child.make_all_links_absolute()
        for item in self.get_items():
            item.make_links_absolute()

    def make_all_asset_hrefs_relative(self):
        """Makes all the HREFs of assets belonging to items in this catalog
        and all children to be relative, recursively.
        """
        for _, _, items in self.walk():
            for item in items:
                item.make_asset_hrefs_relative()

    def make_all_asset_hrefs_absolute(self):
        """Makes all the HREFs of assets belonging to items in this catalog
        and all children to be absoluet, recursively.
        """
        for _, _, items in self.walk():
            for item in items:
                item.make_asset_hrefs_absolute()

    def normalize_and_save(self, root_href, catalog_type):
        """Normalizes link HREFs to the given root_href, and saves
        the catalog with the given catalog_type.

        This is a convenience method that simply calls :func:`Catalog.normalize_hrefs
        <pystac.Catalog.normalize_hrefs>` and :func:`Catalog.save <pystac.Catalog.save>`
        in sequence.

        Args:
            root_href (str): The absolute HREF that all links will be normalized against.
            catalog_type (str): The catalog type that dictates the structure of
                the catalog to save. Use a member of :class:`~pystac.CatalogType`.
        """
        self.normalize_hrefs(root_href)
        self.save(catalog_type)

    def normalize_hrefs(self, root_href):
        # Normalizing requires an absolute path
        if not is_absolute_href(root_href):
            root_href = make_absolute_href(root_href, os.getcwd(), start_is_dir=True)

        # Fully resolve the STAC to avoid linking issues.
        # This particularly can happen with unresolved links that have
        # relative paths.
        self.fully_resolve()

        for child in self.get_children():
            child_root = os.path.join(root_href, '{}/'.format(child.id))
            child.normalize_hrefs(child_root)

        for item in self.get_items():
            item_root = os.path.join(root_href, '{}'.format(item.id))
            item.normalize_hrefs(item_root)

        self.set_self_href(os.path.join(root_href, self.DEFAULT_FILE_NAME))

        return self

    def fully_resolve(self):
        link_rels = set(self._object_links())
        for link in self.links:
            if link.rel == 'root':
                if not link.is_resolved():
                    if link.get_absolute_href() != self.get_self_href():
                        link.target = self
                    else:
                        link.resolve_stac_object()
                        link.target.fully_resolve()
            if link.rel in link_rels:
                if not link.is_resolved():
                    link.resolve_stac_object(root=self.get_root())
                link.target.fully_resolve()

    def save(self, catalog_type):
        """Save this catalog and all it's children/item to files determined by the object's
        self link HREF.

        Args:
            catalog_type (str): The catalog type that dictates the structure of
                the catalog to save. Use a member of :class:`~pystac.CatalogType`.

        Note:
            If the catalog type is ``CatalogType.ABSOLUTE_PUBLISHED``,
            all self links will be included, and link type will be set to ABSOLUTE.
            If the catalog type is ``CatalogType.RELATIVE_PUBLISHED``, this catalog's self
            link will be included, but no child catalog will have self links.
            Link types will be set to RELATIVE.
            If the catalog  type is ``CatalogType.SELF_CONTAINED``, no self links will be
            included. Link types will be set to RELATIVE.
        """

        # Ensure relative vs absolute
        if catalog_type == CatalogType.ABSOLUTE_PUBLISHED:
            self.make_all_links_absolute()
        else:
            self.make_all_links_relative()

        include_self_link = catalog_type in [
            CatalogType.ABSOLUTE_PUBLISHED, CatalogType.RELATIVE_PUBLISHED
        ]

        if catalog_type == CatalogType.RELATIVE_PUBLISHED:
            child_catalog_type = CatalogType.SELF_CONTAINED
        else:
            child_catalog_type = catalog_type

        items_include_self_link = catalog_type in [CatalogType.ABSOLUTE_PUBLISHED]

        for child_link in self.get_child_links():
            if child_link.is_resolved():
                child_link.target.save(catalog_type=child_catalog_type)

        for item_link in self.get_item_links():
            if item_link.is_resolved():
                item_link.target.save_object(include_self_link=items_include_self_link)

        self.save_object(include_self_link=include_self_link)

    def walk(self):
        """Walks through children and items of catalogs.

        For each catalog in the STAC's tree rooted at this catalog (including this catalog
        itself), it yields a 3-tuple (root, subcatalogs, items). The root in that
        3-tuple refers to the current catalog being walked, the subcatalogs are any
        catalogs or collections for which the root is a parent, and items represents
        any items that have the root as a parent.

        This has similar functionality to Python's :func:`os.walk`.

        Returns:
           Generator[(Catalog, Generator[Catalog], Generator[Item])]: A generator that
           yields a 3-tuple (parent_catalog, children, items).
        """
        children = self.get_children()
        items = self.get_items()

        yield (self, children, items)
        for child in self.get_children():
            yield from child.walk()

    def _object_links(self):
        return ['child', 'item'] + (pystac.STAC_EXTENSIONS.get_extended_object_links(self))

    def map_items(self, item_mapper):
        """Creates a copy of a catalog, with each item passed through the
        item_mapper function.

        Args:
            item_mapper (Callable):   A function that takes in an item, and returns either
                an item or list of items. The item that is passed into the item_mapper
                is a copy, so the method can mutate it safetly.

        Returns:
            Catalog: A full copy of this catalog, with items manipulated according
            to the item_mapper function.
        """

        new_cat = self.full_copy()

        def process_catalog(catalog):
            for child in catalog.get_children():
                process_catalog(child)

            item_links = []
            for item_link in catalog.get_item_links():
                item_link.resolve_stac_object(root=self.get_root())
                mapped = item_mapper(item_link.target)
                if mapped is None:
                    raise Exception('item_mapper cannot return None.')
                if type(mapped) is not list:
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

    def map_assets(self, asset_mapper):
        """Creates a copy of a catalog, with each Asset for each Item passed
        through the asset_mapper function.

        Args:
            asset_mapper (Callable): A function that takes in an key and an Asset, and returns
               either an Asset, a (key, Asset), or a dictionary of Assets with unique keys.
               The Asset that is passed into the item_mapper is a copy, so the method can
               mutate it safetly.

        Returns:
            Catalog: A full copy of this catalog, with assets manipulated according
            to the asset_mapper function.
        """
        def apply_asset_mapper(tup):
            k, v = tup
            result = asset_mapper(k, v)
            if result is None:
                raise Exception('asset_mapper cannot return None.')
            if isinstance(result, pystac.Asset):
                return [(k, result)]
            elif isinstance(result, tuple):
                return [result]
            else:
                assets = list(result.items())
                if len(assets) < 1:
                    raise Exception('asset_mapper must return a non-empy list')
                return assets

        def item_mapper(item):
            new_assets = [
                x for result in map(apply_asset_mapper, item.assets.items()) for x in result
            ]
            item.assets = dict(new_assets)
            return item

        return self.map_items(item_mapper)

    def describe(self, include_hrefs=False, _indent=0):
        """Prints out information about this Catalog and all contained
        STACObjects.

        Args:
            include_hrefs (bool) - If True, print out each object's self link
                HREF along with the object ID.
        """
        s = '{}* {}'.format(' ' * _indent, self)
        if include_hrefs:
            s += ' {}'.format(self.get_self_href())
        print(s)
        for child in self.get_children():
            child.describe(include_hrefs=include_hrefs, _indent=_indent + 4)
        for item in self.get_items():
            s = '{}* {}'.format(' ' * (_indent + 2), item)
            if include_hrefs:
                s += ' {}'.format(item.get_self_href())
            print(s)

    @classmethod
    def from_dict(cls, d, href=None, root=None):
        id = d['id']
        description = d['description']
        title = d.get('title')

        cat = Catalog(id=id, description=description, title=title)

        has_self_link = False
        for link in d['links']:
            has_self_link |= link['rel'] == 'self'
            if link['rel'] == 'root':
                # Remove the link that's generated in Catalog's constructor.
                cat.remove_links('root')

            cat.add_link(Link.from_dict(link))

        if not has_self_link and href is not None:
            cat.add_link(Link.self_href(href))

        return cat
