from copy import deepcopy

from pystac.item import (Item, Asset)
from pystac import STACError


class EOItem(Item):
    EO_FIELDS = ['gsd', 'platform', 'instrument', 'bands', 'constellation', 'epsg',
                 'cloud_cover', 'off_nadir', 'azimuth', 'sun_azimuth', 'sun_elevation']

    def __init__(self,
                 id,
                 geometry,
                 bbox,
                 datetime,
                 properties,
                 gsd,
                 platform,
                 instrument,
                 bands,
                 constellation=None,
                 epsg=None,
                 cloud_cover=None,
                 off_nadir=None,
                 azimuth=None,
                 sun_azimuth=None,
                 sun_elevation=None,
                 stac_extensions=None,
                 href=None,
                 collection=None,
                 assets={}):
        if stac_extensions is None:
            stac_extensions = []
        if 'eo' not in stac_extensions:
            stac_extensions.append('eo')
        super().__init__(id, geometry, bbox, datetime,
                         properties, stac_extensions, href,
                         collection)
        self.gsd = gsd
        self.platform = platform
        self.instrument = instrument
        self.bands = [Band.from_dict(b) for b in bands]
        self.constellation = constellation
        self.epsg = epsg
        self.cloud_cover = cloud_cover
        self.off_nadir = off_nadir
        self.azimuth = azimuth
        self.sun_azimuth = sun_azimuth
        self.sun_elevation = sun_elevation
         

    def __repr__(self):
        return '<EOItem id={}>'.format(self.id)

    @staticmethod
    def from_dict(d):
        item = Item.from_dict(d)
        return EOItem.from_item(item)

    @classmethod
    def from_item(cls, item):
        eo_params = {}
        for eof in EOItem.EO_FIELDS:
            if eo_key(eof) in item.properties.keys():
                eo_params[eof] = item.properties.pop(eo_key(eof))
            elif eof in ('gsd', 'platform', 'instrument', 'bands'):
                raise STACError(
                    "Missing required field '{}' in properties".format(eo_key(eof)))

        if not any(item.properties):
            item.properties = None

        e = cls(item.id, item.geometry, item.bbox, item.datetime,
                item.properties, stac_extensions=item.stac_extensions,
                collection=item.collection, **eo_params)

        e.links = item.links
        e.assets = item.assets

        for k, v in item.assets.items():
            if is_eo(v):
                e.assets[k] = EOAsset.from_asset(v)
            e.assets[k].set_owner(e)

        return e

    def get_eo_assets(self):
        return {k: v for k, v in self.assets.items() if isinstance(v, EOAsset)}

    def add_asset(self, key, asset):
        if is_eo(asset) and not isinstance(asset, EOAsset):
            asset = EOAsset.from_asset(asset)
        asset.set_owner(self)
        self.assets[key] = asset
        return self

    @staticmethod
    def from_file(uri):
        return EOItem.from_item(Item.from_file(uri))

    def clone(self):
        c = super(EOItem, self).clone()
        self.add_eo_fields_to_dict(c.properties)
        return EOItem.from_item(c)

    def to_dict(self, include_self_link=True):
        d = super().to_dict(include_self_link=include_self_link)
        if 'properties' not in d.keys():
            d['properties'] = {}
        self.add_eo_fields_to_dict(d['properties'])
        return deepcopy(d)

    def add_eo_fields_to_dict(self, d):
        for eof in EOItem.EO_FIELDS:
            try:
                a = getattr(self, eof)
                if a is not None:
                    d[eo_key(eof)] = a
                    if eof == 'bands':
                        d['eo:bands'] = [b.to_dict() for b in d['eo:bands']]
            except AttributeError:
                pass


class EOAsset(Asset):
    def __init__(self, href, bands, title=None, media_type=None, properties=None):
        super().__init__(href, title, media_type, properties)
        self.bands = bands

    @staticmethod
    def from_dict(d):
        asset = Asset.from_dict(d)
        return EOAsset.from_asset(asset)

    @classmethod
    def from_asset(cls, asset):
        a = asset.clone()
        if not a.properties or 'eo:bands' not in a.properties.keys():
            raise STACError('Missing eo:bands property in asset')
        bands = a.properties.pop('eo:bands')
        properties = None
        if any(a.properties):
            properties = a.properties
        return cls(a.href, bands, a.title, a.media_type, properties)

    def to_dict(self):
        d = super().to_dict()
        d['eo:bands'] = self.bands

        return d

    def clone(self):
        return EOAsset(href=self.href,
                       title=self.title,
                       media_type=self.media_type,
                       bands=self.bands,
                       properties=self.properties)

    def __repr__(self):
        return '<EOAsset href={}>'.format(self.href)

    def get_band_objs(self):
        # Not sure exactly how this method fits in but
        # it seems like there should be a way to get the
        # Band objects associated with the indices
        if not self.item:
            raise STACError('Asset is currently not associated with an item')
        return [self.item.bands[i] for i in self.bands]


class Band:
    def __init__(self,
                 name=None,
                 common_name=None,
                 gsd=None,
                 center_wavelength=None,
                 full_width_half_max=None,
                 description=None,
                 accuracy=None):
        self.name = name
        self.common_name = common_name
        self.gsd = gsd
        self.center_wavelength = center_wavelength
        self.full_width_half_max = full_width_half_max
        self.description = description
        self.accuracy = accuracy

    def __repr__(self):
        return '<Band name={}>'.format(self.name)

    @staticmethod
    def from_dict(d):
        name = d.get('name', None)
        common_name = d.get('common_name', None)
        gsd = d.get('gsd', None)
        center_wavelength = d.get('center_wavelength', None)
        full_width_half_max = d.get('full_width_half_max', None)
        description = d.get('description', None)
        accuracy = d.get('accuracy', None)

        return Band(name, common_name, gsd, center_wavelength,
                    full_width_half_max, description, accuracy)

    def to_dict(self):
        d = {}
        if self.name:
            d['name'] = self.name
        if self.common_name:
            d['common_name'] = self.common_name
        if self.gsd:
            d['gsd'] = self.gsd
        if self.center_wavelength:
            d['center_wavelength'] = self.center_wavelength
        if self.full_width_half_max:
            d['full_width_half_max'] = self.full_width_half_max
        if self.description:
            d['description'] = self.description
        if self.accuracy:
            d['accuracy'] = self.accuracy
        return deepcopy(d)


def eo_key(key):
    return 'eo:{}'.format(key)


def band_range(common_name):
    name_to_range = {
        'coastal': (0.40, 0.45),
        'blue': (0.45, 0.50),
        'green': (0.50, 0.60),
        'red': (0.60, 0.70),
        'yellow': (0.58, 0.62),
        'pan': (0.50, 0.70),
        'rededge': (0.70, 0.75),
        'nir': (0.75, 1.00),
        'nir08': (0.75, 0.90),
        'nir09': (0.85, 1.05),
        'cirrus': (1.35, 1.40),
        'swir16': (1.55, 1.75),
        'swir22': (2.10, 2.30),
        'lwir': (10.5, 12.5),
        'lwir11': (10.5, 11.5),
        'lwir12': (11.5, 12.5)
    }
    return name_to_range.get(common_name, common_name)


def band_desc(common_name):
    r = band_range(common_name)
    if isinstance(r, str):
        return "Common name: {}".format(common_name)
    return "Common name: {}, Range: {} to {}".format(common_name, r[0], r[1])


def is_eo(obj):
    if obj.properties:
        if obj.properties.get('eo:bands', None):
            return True
    return False