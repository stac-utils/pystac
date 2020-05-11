from copy import deepcopy

from pystac import STACError
from pystac.extension import Extension
from pystac.collection import Collection
from pystac.item import Item

class VersionedItem(Item):

    _EXTENSION_FIELDS = ['version', 'deprecated']

    def __init__(self,
                 id,
                 geometry,
                 bbox,
                 datetime,
                 properties,
                 version,
                 stac_extensions=None,
                 href=None,
                 collection=None,
                 deprecated=False):
        if stac_extensions is None:
            stac_extensions = []
        if Extension.VERSIONING not in stac_extensions:
            stac_extensions.append(Extension.VERSIONING)
        super().__init__(id, geometry, bbox, datetime, properties, stac_extensions, href,
                         collection)

        self.version = version
        self.deprecated = deprecated
    
    def __repr__(self):
        return '<VersionedItem id={}>'.format(self.id)
    
    @classmethod
    def from_dict(cls, d, href=None, root=None):
        item = Item.from_dict(d, href=href, root=root)
        return cls.from_item(item)
    
    @classmethod
    def from_item(cls, item):
        if isinstance(item, VersionedItem):
            return item.clone()
        
        v = cls(id=item.id,
                geometry=item.geometry,
                bbox=item.bbox,
                datetime=item.datetime,
                properties=item.properties,
                stac_extensions=item.stac_extensions,
                collection=item.collection,
                version=item.properties.get('version'),
                deprecated=item.properties.get('deprecated'))
        
        v.links = item.links
        v.assets = {}
        for k, asset in item.assets.items():
            v.assets[k] = asset
            asset.set_owner(v)
        
        return v

    def to_dict(self, include_self_links=True):
        d = super().to_dict(include_self_link=include_self_links)
        if 'properties' not in d.keys():
            d['properties'] = {}
        d['properties']['version'] = self.version
        d['properties']['deprecated'] = self.deprecated


class VersionedCollection(Collection):
    def __init__(self,
                 id,
                 description,
                 extent,
                 version,
                 title=None,
                 stac_extensions=None,
                 href=None,
                 license='proprietary',
                 keywords=None,
                 providers=None,
                 properties=None,
                 summaries=None,
                 deprecated=False):
        if stac_extensions is None:
            stac_extensions = []
        if Extension.VERSIONING not in stac_extensions:
            stac_extensions.append(Extension.VERSIONING)
        super().__init__(id=id,
                         description=description,
                         extent=extent,
                         title=title,
                         stac_extension=stac_extensions,
                         href=href,
                         license=license,
                         keywords=keywords,
                         providers=providers,
                         properties=properties,
                         summaries=summaries)
        self.version = version
        self.deprecated = deprecated
    
    def __repr__(self):
        return '<VersionedCollection id={}>'.format(self.id)
    
    @classmethod
    def from_dict(cls, d, href=None, root=None):
        collection = Collection.from_dict(d, href=href, root=root)
        return cls.from_collection(collection)

    @classmethod
    def from_collection(cls, collection):
        if isinstance(collection, VersionedCollection):
            return collection.clone()
        
        c = cls(id=id,
                description=collection.description,
                extent=collection.extent,
                version=collection.properties.get('version'),
                title=collection.title,
                stac_extensions=collection.stac_extensions,
                href=collection.href,
                license=collection.license,
                keywords=collection.keywords,
                providers=collection.providers,
                properties=collection.properties,
                summaries=collection.summaries,
                deprecated=collection.properties.get('deprecated'))
        
        c.links = collection.links
        c.assets = {}
        for k, asset in collection.assets.items():
            c.assets[k] = asset
            asset.set_owner(c)
        
        return c
