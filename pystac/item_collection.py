import json
import os

from pystac.io import STAC_IO
from pystac.item import Item
from pystac.link import Link, LinkType


class ItemCollection:
    DEFAULT_FILE_NAME = "item_collection.json"

    def __init__(self, features, links=[], type='FeatureCollection'):
        self.type = type
        self.features = features
        self.links = links

        if [l for l in self.links if l.rel == 'self'] == []:
            self.links.append(Link('self', './{}'.format(self.DEFAULT_FILE_NAME), link_type=LinkType.RELATIVE))

    def __repr__(self):    
        return '<ItemCollection item ids={}>'.format([f.id for f in self.features])
    
    @staticmethod
    def from_dict(d):
        features = [Item.from_dict(feature) for feature in d['features']]
        links = []
        if 'links' in d.keys():
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
    
    def get_items(self):
        return self.features

    def save(self, include_self_link=True):
        STAC_IO.save_json(self.get_self_href(), self.to_dict(include_self_link = include_self_link))
