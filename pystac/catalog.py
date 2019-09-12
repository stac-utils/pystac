import os
import json

from pystac import STAC_VERSION
from pystac.stac_object import STACObject
from pystac.io import STAC_IO
from pystac.link import Link
from pystac.item import Asset
from pystac.resolved_object_cache import ResolvedObjectCache

class Catalog(STACObject):
    DEFAULT_FILE_NAME = "catalog.json"

    def __init__(self, id, description, title=None, href=None):
        self.id = id
        self.description = description
        self.title = title
        self.links = [Link.root(self)]

        if href is not None:
            self.set_self_href(href)

        self._resolved_objects = ResolvedObjectCache()

    def __repr__(self):
        return '<Catalog id={}>'.format(self.id)

    def set_root(self, root, recursive=False):
        STACObject.set_root(self, root)
        root._resolved_objects = ResolvedObjectCache.merge(root._resolved_objects,
                                                           self._resolved_objects)

        if recursive:
            for child in self.get_children():
                child.set_root(root, recurive=True)
            for item in self.get_items():
                item.set_root(root)

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

    def get_item(self, id):
        return next((i for i in self.get_items() if i.id == id), None)

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

    def to_dict(self):
        d = {
            'id': self.id,
            'stac_version': STAC_VERSION,
            'description': self.description,
            'links': [l.to_dict() for l in self.links]
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

    def set_uris_from_root(self, root_uri):
        self.set_self_href(os.path.join(root_uri, self.DEFAULT_FILE_NAME))
        for child in self.get_children():
            child_root = os.path.join(root_uri, '{}/'.format(child.id))
            child.set_uris_from_root(child_root)
        for item in self.get_items():
            item.set_self_href(os.path.join(root_uri, '{}.json'.format(item.id)))

    def set_relative_paths(self, include_assets=True):
        """Converts all HREFs in links (and optionally assets) into relative paths.

        Any path that does not share a root with the self HREF (i.e. cannot be made relative)
        will be skipped.
        """
        self_href = self.get_self_href()
        if self_href is None:
            raise STACError('Self HREFs must be set in order to make relative paths.')

        os.path.basename(self_href)

    def save(self):
        for child_link in self.get_child_links():
            if child_link.is_resolved():
                child_link.target.save()

        for item_link in self.get_item_links():
            if item_link.is_resolved():
                item_link.target.save()

        STAC_IO.save_json(self.get_self_href(), self.to_dict())

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
            child.describe(indent=indent+4)
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

        return cat

    @staticmethod
    def from_file(uri):
        d = json.loads(STAC_IO.read_text(uri))
        c = Catalog.from_dict(d)
        c.set_self_href(uri)
        return c
