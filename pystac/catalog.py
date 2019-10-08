import os
import json

from pystac import STACError
from pystac import STAC_VERSION
from pystac.stac_object import STACObject
from pystac.io import STAC_IO
from pystac.link import (Link, LinkType)
from pystac.item import Asset
from pystac.resolved_object_cache import ResolvedObjectCache
from pystac.utils import (is_absolute_href, make_absolute_href)

class CatalogType:
    """A 'self-contained catalog' is one that is designed for portability.
    Users may want to download a catalog from online and be able to use it on their
    local computer, so all links need to be relative.

    See: https://github.com/radiantearth/stac-spec/blob/v0.8.0-rc1/best-practices.md#self-contained-catalogs
    """
    SELF_CONTAINED = 'SELF_CONTAINED'

    """
    Absolute Published Catalog is a catalog that uses absolute links for everything,
    both in the links objects and in the asset hrefs.

    See: https://github.com/radiantearth/stac-spec/blob/v0.8.0-rc1/best-practices.md#published-catalogs
    """
    ABSOLUTE_PUBLISHED = 'ABSOLUTE_PUBLISHED'

    """
    Relative Published Catalog is a catalog that uses relative links for everything,
    but includes an absolute self link at the root catalog, to identify its online location.

    See: https://github.com/radiantearth/stac-spec/blob/v0.8.0-rc1/best-practices.md#published-catalogs
    """
    RELATIVE_PUBLISHED = 'RELATIVE_PUBLISHED'


class Catalog(STACObject):
    DEFAULT_FILE_NAME = "catalog.json"

    def __init__(self, id, description, title=None, href=None):
        self.id = id
        self.description = description
        self.title = title
        self.links = []
        self.add_link(Link.root(self))

        if href is not None:
            self.set_self_href(href)

        self._resolved_objects = ResolvedObjectCache()

    def __repr__(self):
        return '<Catalog id={}>'.format(self.id)

    def set_root(self, root, link_type=LinkType.ABSOLUTE):
        STACObject.set_root(self, root, link_type)
        root._resolved_objects = ResolvedObjectCache.merge(root._resolved_objects,
                                                           self._resolved_objects)

    def add_child(self, child, title=None):
        child.set_root(self.get_root())
        child.set_parent(self)
        self.add_link(Link.child(child, title=title))

    def add_item(self, item, title=None):
        item.set_root(self.get_root())
        item.set_parent(self)
        self.add_link(Link.item(item, title=title))

    def add_items(self, items):
        for item in items:
            self.add_item(item)

    def get_child(self, id):
        return next((c for c in self.get_children() if c.id == id), None)

    def get_children(self):
        return self.get_stac_objects('child', parent=self)

    def get_child_links(self):
        return self.get_links('child')

    def clear_children(self):
        self.links = [l for l in self.links if l.rel != 'child']
        return self

    def get_item(self, id, recursive=False):
        """Returns an item with a given ID.

        Args:
            id: The ID of the item to find.
            recursive: If True, search this catalog and all children for the item;
                otherwise, only search the items of this catalog. Defaults to False.
        """
        if not recursive:
            return next((i for i in self.get_items() if i.id == id), None)
        else:
            for root, children, items in self.walk():
                item = root.get_item(id, recursive=False)
                if item is not None:
                    return item

    def get_items(self):
        return self.get_stac_objects('item', parent=self)

    def clear_items(self):
        self.links = [l for l in self.links if l.rel != 'item']
        return self

    def get_all_items(self):
        """Get all items from this catalog and all subcatalogs."""
        items = self.get_items()
        for child in self.get_children():
            items += child.get_all_items()

        return items

    def get_item_links(self):
        return self.get_links('item')

    def to_dict(self, include_self_link=True):
        links = self.links
        if not include_self_link:
            links = filter(lambda l: l.rel != 'self', links)

        d = {
            'id': self.id,
            'stac_version': STAC_VERSION,
            'description': self.description,
            'links': [l.to_dict() for l in links]
        }

        if self.title is not None:
            d['title'] = self.title

        return d

    def clone(self):
        clone = Catalog(id=self.id,
                        description=self.description,
                        title=self.title)
        clone._resolved_objects.set(clone)

        clone.add_links([l.clone() for l in self.links])

        return clone

    def make_all_links_relative(self):
        super().make_links_relative()

        for child in self.get_children():
            child.make_all_links_relative()
        for item in self.get_items():
            item.make_links_relative()

    def make_all_links_absolute(self):
        super().make_links_absolute()

        for child in self.get_children():
            child.make_all_links_absolute()
        for item in self.get_items():
            item.make_links_absolute()

    def make_all_asset_hrefs_relative(self):
        for _, _, items in self.walk():
            for item in items:
                item.make_asset_hrefs_relative()

    def make_all_asset_hrefs_absolute(self):
        for _, _, items in self.walk():
            for item in items:
                item.make_asset_hrefs_absolute()

    def normalize_and_save(self,
                           root_href,
                           catalog_type):
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

    def save(self, catalog_type):
        """Save this catalog and all it's children/item to files determined by the object's
        self link HREF.

        Args:

            catalog_type: The catalog type that dictates the structure of the catalog to save.
                If the catalog type is CatalogType.ABSOLUTE_PUBLISHED, all self links will be included,
                and link type will be set to ABSOLUTE.
                If the catalog type is CatalogType.RELATIVE_PUBLISHED, this catalog's self link will be
                included, but no child catalog will have self links. Link types will be set to RELATIVE.
                If the catalog  type is CatalogType.SELF_CONTAINED, no self links will be included.
                Link types will be set to RELATIVE.
        """

        # Ensure relative vs absolute
        if catalog_type == CatalogType.ABSOLUTE_PUBLISHED:
            self.make_all_links_absolute()
        else:
            self.make_all_links_relative()

        include_self_link = catalog_type in [CatalogType.ABSOLUTE_PUBLISHED,
                                             CatalogType.RELATIVE_PUBLISHED]

        if catalog_type ==  CatalogType.RELATIVE_PUBLISHED:
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

        Returns:
           An iterator that yields a 3-tuple (parent_catalog, children, items).
        """
        children = self.get_children()
        items = self.get_items()

        yield (self, children, items)
        for child in children:
            yield from child.walk()

    def _object_links(self):
        return ['child', 'item']

    def map_items(self, item_mapper):
        """Creates a copy of a catalog, with each item passed through the item_mapper function.

        Args:
           item_mapper:   A function that takes in an item, and returns either an item or list of items.
              The item that is passed into the item_mapper is a copy, so the method can mutate it safetly.
        """

        new_cat = self.full_copy()

        def process_catalog(catalog):
            for child in catalog.get_children():
                process_catalog(child)

            item_links = []
            for item_link in catalog.get_item_links():
                mapped = item_mapper(item_link.target)
                if mapped is None:
                    raise Exception('item_mapper cannot return None.')
                if type(mapped) is not list:
                    item_link.target = mapped
                    item_links.append(item_link)
                else:
                    for i in mapped:
                        l = item_link.clone()
                        l.target = i
                        item_links.append(l)
            catalog.clear_items()
            catalog.add_links(item_links)

        process_catalog(new_cat)
        return new_cat

    def map_assets(self, asset_mapper):
        """Creates a copy of a catalog, with each Asset for each Item passed
        through the asset_mapper function.

        Args:
           asset_mapper:   A function that takes in an key and an Asset, and returns
             either an Asset, a (key, Asset), or a dictionary of Assets with unique keys.
             The Asset that is passed into the item_mapper is a copy, so the method can mutate it safetly.
        """
        def apply_asset_mapper(tup):
            k, v = tup
            result = asset_mapper(k, v)
            if result is None:
                raise Exception('asset_mapper cannot return None.')
            if issubclass(type(result), Asset):
                return [(k, result)]
            elif isinstance(result, tuple):
                return [result]
            else:
                assets = list(result.items())
                if len(assets) < 1:
                    raise Exception('asset_mapper must return a non-empy list')
                return assets

        def item_mapper(item):
            new_assets = [x for result in map(apply_asset_mapper, item.assets.items())
                            for x in result]
            item.assets = dict(new_assets)
            return item

        return self.map_items(item_mapper)

    def describe(self, indent=0, include_hrefs=False):
        s = '{}* {}'.format(' ' * indent, self)
        if include_hrefs:
            s += ' {}'.format(self.get_self_href())
        print(s)
        for child in self.get_children():
            child.describe(indent=indent+4, include_hrefs=include_hrefs)
        for item in self.get_items():
            s = '{}* {}'.format(' ' * (indent+2), item)
            if include_hrefs:
                s += ' {}'.format(item.get_self_href())
            print(s)

    @staticmethod
    def from_dict(d):
        id = d['id']
        description = d['description']
        title = d.get('title')

        cat = Catalog(id=id,
                      description=description,
                      title=title)

        for l in d['links']:
            if not l['rel'] == 'root':
                cat.add_link(Link.from_dict(l))
            else:
                # If a root link was included, we want to inheret
                # whether it was relative or not.
                if not is_absolute_href(l['href']):
                    cat.get_single_link('root').link_type = LinkType.RELATIVE

        return cat

    @staticmethod
    def from_file(uri):
        if not is_absolute_href(uri):
            uri = make_absolute_href(uri)
        d = json.loads(STAC_IO.read_text(uri))
        c = Catalog.from_dict(d)
        c.set_self_href(uri)
        return c
