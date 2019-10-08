import os

from copy import (copy, deepcopy)
import dateutil.parser
import json

from pystac import STAC_VERSION
from pystac.stac_object import STACObject
from pystac.io import STAC_IO
from pystac.link import (Link, LinkType)
from pystac.utils import (make_relative_href, make_absolute_href, is_absolute_href)

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

    def add_asset(self, key, asset):
        self.assets[key] = asset
        return self

    def make_asset_hrefs_relative(self):
        for asset in self.assets.values():
            asset.href = make_relative_href(asset.href, self.get_self_href())
        return self

    def make_asset_hrefs_absolute(self):
        for asset in self.assets.values():
            asset.href = make_absolute_href(asset.href, self.get_self_href())

        return self

    def set_collection(self, collection, link_type=None):
        if not link_type:
            prev = self.get_single_link('collection')
            if prev is not None:
                link_type = prev.link_type
            else:
                link_type = LinkType.ABSOLUTE
        self.remove_links('collection')
        self.add_link(Link.collection(collection, link_type=link_type))
        return self

    def to_dict(self, include_self_link=True):
        links = self.links
        if not include_self_link:
            links = filter(lambda x: x.rel != 'self', links)

        assets = dict(map(lambda x: (x[0], x[1].to_dict()), self.assets.items()))

        self.properties['datetime'] = '{}Z'.format(self.datetime.replace(microsecond=0, tzinfo=None))

        d = {
            'type': 'Feature',
            'stac_version': STAC_VERSION,
            'id': self.id,
            'properties': self.properties,
            'geometry': self.geometry,
            'bbox': self.bbox,
            'links': [l.to_dict() for l in links],
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
        for link in self.links:
            clone.add_link(link.clone())

        clone.assets = dict([(k, a.clone()) for (k, a) in self.assets.items()])

        return clone

    def _object_links(self):
        return ['collection']

    def normalize_hrefs(self, root_href):
        old_self_href = self.get_self_href()
        new_self_href = os.path.join(root_href, '{}.json'.format(self.id))
        self.set_self_href(new_self_href)

        # Make sure relative asset links remain valid.
        # This will only work if there is a self href set.
        for asset in self.assets.values():
            asset_href = asset.href
            if not is_absolute_href(asset_href) and old_self_href is not None:
                abs_href = make_absolute_href(asset_href, old_self_href)
                new_relative_href = make_relative_href(abs_href, new_self_href)
                asset.href = new_relative_href

    def save(self, include_self_link=True):
        STAC_IO.save_json(self.get_self_href(), self.to_dict(include_self_link))

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
        if not is_absolute_href(uri):
            uri = make_absolute_href(uri)
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

        # The Item which owns this Asset.
        self.item = None

    def set_owner(self, item):
        self.item = item

    def get_absolute_href(self):
        """Gets the aboslute href for this asset, if possible.

        If this Asset has no associated Item, this will return whatever the
        href is (as it cannot determine the absolute path, if the asset
        href is relative)."""
        if not is_absolute_href(self.href):
            if self.item is not None:
                return make_absolute_href(href, self.owner.get_self_href())

        return self.href

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
