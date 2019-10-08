import json
import os

from pystac.collection import Collection
from pystac.io import STAC_IO
from pystac.item import Item
from pystac.item_collection import ItemCollection


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
            sd = d['search']
            search_obj = Search(sd['endpoint'], sd['parameters'])
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
