from copy import (copy, deepcopy)
import dateutil.parser

from pystac import STAC_VERSION
from pystac.stac_object import STACObject
from pystac.io import STAC_IO
from pystac.link import Link

class Item(STACObject):
    def __init__(self,
                 id,
                 geometry,
                 bbox,
                 datetime,
                 properties,
                 stac_extensions=None,
                 href=None):
        self.id = id
        self.geometry = geometry
        self.bbox = bbox
        self.datetime = datetime
        self.properties = properties
        self.stac_extensions = stac_extensions

        self.links = []
        self.assets = {}

        if href is not None:
            self.set_self_href(href)

    def __repr__(self):
        return '<Item id={}>'.format(self.id)

    def get_assets(self):
        return dict(self.assets.items())

    def add_asset(self, key, href, title=None, media_type=None, properties=None):
        self.assets[key] = Asset(href, title=title, media_type=media_type, properties=None)

    def set_collection(self, collection):
        self.links = [l for l in self.links if l.rel != 'collection']
        self.links.append(Link.collection(collection))

    def to_dict(self):
        links = list(map(lambda x: x.to_dict(), self.links))
        assets = dict(map(lambda x: (x[0], x[1].to_dict()), self.assets.items()))

        self.properties['datetime'] = '{}Z'.format(self.datetime.replace(microsecond=0))

        d = {
            'type': 'Feature',
            'stac_version': STAC_VERSION,
            'id': self.id,
            'properties': self.properties,
            'geometry': self.geometry,
            'bbox': self.bbox,
            'links': links,
            'assets': assets
        }

        if self.stac_extensions is not None:
            d['stac_extensions'] = self.stac_extensions

        return d

    def clone(self):
        clone = Item(id=self.id,
                     geometry=deepcopy(self.geometry),
                     bbox=copy(self.bbox),
                     datetime=copy(self.datetime),
                     properties=deepcopy(self.properties),
                     stac_extensions=deepcopy(self.stac_extensions))
        clone.links = [l.clone() for l in self.links]
        clone.assets = dict([(k, a.clone()) for (k, a) in self.assets.items()])
        return clone

    def full_copy(self, root=None, parent=None):
        clone = self.clone()
        if root:
            clone.set_root(root)
        if parent:
            clone.set_parent(parent)

        collection_link = clone.get_single_link('collection')
        if collection_link and root:
            collection_link.resolve_stac_object(root=root)
            target = root._resolved_objects.get_or_set(collection_link.target)
            collection_link.target = target

        return clone

    def save(self):
        STAC_IO.save_json(self.get_self_href(), self.to_dict())

    @staticmethod
    def from_dict(d):
        id = d['id']
        geometry = d['geometry']
        bbox = d['bbox']
        properties = d['properties']
        stac_extensions = d.get('stac_extensions')

        datetime = properties.get('datetime')
        if datetime is None:
            raise STACError('Item dict is missing a "datetime" property in the "properties" field')
        datetime = dateutil.parser.parse(datetime)

        item = Item(id=id,
                    geometry=geometry,
                    bbox=bbox,
                    datetime=datetime,
                    properties=properties,
                    stac_extensions=stac_extensions)

        for l in d['links']:
            item.add_link(Link.from_dict(l))

        for k, v in d['assets'].items():
            item.assets[k] = Asset.from_dict(v)

        return item

    @staticmethod
    def from_file(uri):
        d = json.loads(STAC_IO.read_text(uri))
        return Item.from_dict(d)

class Asset:
    class MEDIA_TYPE:
        TIFF = 'image/tiff'
        GEOTIFF = 'image/vnd.stac.geotiff'
        COG = 'image/vnd.stac.geotiff; cloud-optimized=true'
        JPEG2000 = 'image/jp2'
        PNG = 'image/png'
        JPEG = 'image/jpeg'
        XML = 'application/xml'
        JSON = 'application/json'
        TEXT = 'text/plain'
        GEOJSON = 'application/geo+json'
        GEOPACKAGE = 'application/geopackage+sqlite3'
        HDF5 = 'application/x-hdf5' # Hierarchical Data Format version 5
        HDF = 'application/x-hdf' # Hierarchical Data Format versions 4 and earlier.

    def __init__(self, href, title=None, media_type=None, properties=None):
        self.href = href
        self.title = title
        self.media_type = media_type
        self.properties = None

    def to_dict(self):
        d = {
            'href': self.href
        }

        if self.media_type is not None:
            d['type'] = self.media_type

        if self.title is not None:
            d['title'] = self.title

        if self.properties is not None:
            for k in properties:
                d[k] = properties[k]

        return d

    def clone(self):
        return Asset(href=self.href,
                     title=self.title,
                     media_type=self.media_type)

    def __repr__(self):
        return '<Asset href={}>'.format(self.href)

    @staticmethod
    def from_dict(d):
        d = copy(d)
        href = d.pop('href')
        media_type = d.pop('type', None)
        title = d.pop('title', None)

        properties = None
        if any(d):
            properties = d

        return Asset(href=href,
                     media_type=media_type,
                     title=title,
                     properties=properties)
