import json
import os
from pystac.io import STAC_IO
from pystac.item import Item
from pystac.link import Link
from pystac.resolved_object_cache import ResolvedObjectCache
from pystac.catalog import Catalog
from pystac.collection import Collection

class ItemCollection:
    DEFAULT_FILE_NAME = "item_collection.json"

    def __init__(self, features, links, type='FeatureCollection'):
        self.type = type
        self.features = features
        self.links = links
    
    def __repr__(self):
        return '<ItemCollection item ids={}>'.format([f.id for f in self.features])
    
    @staticmethod
    def from_dict(d):
        features = [Item.from_dict(feature) for feature in d['features']]
        links = [Link.from_dict(link) for link in d['links']]
        return ItemCollection(features, links, d['type'])

    @staticmethod
    def from_file(uri):
        d = json.loads(STAC_IO.read_text(uri))
        c = ItemCollection.from_dict(d)
        return c
    
    def to_dict(self, include_self_link=False):
        links = self.links
        if not include_self_link:
            links = filter(lambda l: l.rel != 'self', links)

        d = {
            'type': self.type,
            'features': [f.to_dict() for f in self.features],
            'links': [l.to_dict() for l in links]
        }

        return d
    
    def get_self_href(self):
        self_link = next((l for l in self.links if l.rel == 'self'), None)
        if self_link:
            return self_link.target
        return self_link
    
    def set_self_href(self, href):
        links = list(filter(lambda l: l.rel != 'self', self.links))
        links.append(Link('self', href))
        self.links = links
    
    def get_items(self):
        return self.features
    
    def normalize_hrefs(self, root_uri):
        self.set_self_href(os.path.join(root_uri, self.DEFAULT_FILE_NAME))
        for item in self.get_items():
            item.set_self_href(os.path.join(root_uri,
                                            '{}'.format(item.id),
                                            '{}.json'.format(item.id)))
    
    def save(self, include_self_link=True):
        """Saves this STAC Object to it's 'self' HREF.

        Args:
          include_self_link: If this is true, include the 'self' link with this object. Otherwise,
              leave out the self link (required for relative links and self contained catalogs).
        """
        STAC_IO.save_json(self.get_self_href(),
                          self.to_dict(include_self_link = include_self_link))
        for item in self.get_items():
            STAC_IO.save_json(item.get_self_href(),
                              self.to_dict(include_self_link))

class SingleFile(ItemCollection):
    def __init__(self, type, features, collections, search=None):
        self.type = type
        self.features = features
        self.collections = collections
        self.search = search
    
    def __repr__(self):
        return '<SingleFile collection ids={}>'.format([c.id for c in self.collections])

    @staticmethod
    def from_file(uri):
        d = json.loads(STAC_IO.read_text(uri))
        c = SingleFile.from_dict(d)
        return c

    @staticmethod
    def from_dict(d):
        type = d['type']
        features = [Item.from_dict(feature) for feature in d['features']]
        collections = [Collection.from_dict(c) for c in d['collections']]
        search_obj = None
        if 'search' in d.keys():
            search_obj = Search(**d['search'])
        return SingleFile(type, features, collections, search_obj)

    def to_dict(self):
        d = {}
        
        d['type'] = self.type
        d['features'] = [f.to_dict() for f in self.features]
        d['collections'] = [c.to_dict() for c in self.collections]
        d['search'] = self.search.to_dict()

        return d
    
    def save(self, uri=None):
        if not uri:
            uri = self.get_self_href()
        
        STAC_IO.save_json(os.path.abspath(uri), self.to_dict())

class Search:
    def __init__(self, endpoint, parameters):
        self.endpoint = endpoint
        self.parameters = parameters
    
    @staticmethod
    def from_dict(d):
        return Search(d['endpoint'], d['parameters'])

    def to_dict(self):
        return {'endpoint': self.endpoint, 'parameters': self.parameters}