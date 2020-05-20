from copy import deepcopy

from pystac import STACError
from pystac.extension import Extension
from pystac.item import (Item, Asset)


class EOItem(Item):
    """EOItem represents a snapshot of the earth for a single date and time.

    Args:
        id (str): Provider identifier. Must be unique within the STAC.
        geometry (dict): Defines the full footprint of the asset represented by this item,
            formatted according to `RFC 7946, section 3.1 (GeoJSON)
            <https://tools.ietf.org/html/rfc7946>`_.
        bbox (List[float]):  Bounding Box of the asset represented by this item using
            either 2D or 3D geometries. The length of the array must be 2*n where n is the
            number of dimensions.
        datetime (Datetime): Datetime associated with this item.
        properties (dict): A dictionary of additional metadata for the item.
        gsd (float): Ground Sample Distance at the sensor.
        bands (List[Band]): This is a list of :class:`~pystac.Band` objects that represent
            the available bands.
        epsg (int): Optional `EPSG code <http://www.epsg-registry.org/>`_.
        cloud_cover (float): Optional estimate of cloud cover as a percentage (0-100) of the
            entire scene. If not available the field should not be provided.
        href (str or None): Optional HREF for this item, which be set as the item's
            self link's HREF.
        collection (Collection or str): The Collection or Collection ID that this item
            belongs to.

    Attributes:
        id (str): Provider identifier. Unique within the STAC.
        geometry (dict): Defines the full footprint of the asset represented by this item,
            formatted according to `RFC 7946, section 3.1 (GeoJSON)
            <https://tools.ietf.org/html/rfc7946>`_.
        bbox (List[float]):  Bounding Box of the asset represented by this item using
            either 2D or 3D geometries. The length of the array is 2*n where n is the
            number of dimensions.
        datetime (Datetime): Datetime associated with this item.
        properties (dict): A dictionary of additional metadata for the item.
        stac_extensions (List[str] or None): Optional list of extensions the Item implements.
        collection (Collection or None): Collection that this item is a part of.
        gsd (float): Ground Sample Distance at the sensor.
        bands (List[Band]): This is a list of :class:`~pystac.Band` objects that represent
            the available bands.
        epsg (int or None): `EPSG code <http://www.epsg-registry.org/>`_.
        cloud_cover (float or None): Estimate of cloud cover as a percentage (0-100) of the
            entire scene. If not available the field should not be provided.
        links (List[Link]): A list of :class:`~pystac.Link` objects representing
            all links associated with this STACObject.
        assets (Dict[str, Asset]): Dictionary of asset objects that can be downloaded,
            each with a unique key.
        collection_id (str or None): The Collection ID that this item belongs to, if any.

    """
    _EO_FIELDS = ['gsd', 'bands', 'epsg', 'cloud_cover']

    @staticmethod
    def _eo_key(key):
        return 'eo:{}'.format(key)

    def __init__(self,
                 id,
                 geometry,
                 bbox,
                 datetime,
                 properties,
                 gsd,
                 bands,
                 epsg=None,
                 cloud_cover=None,
                 stac_extensions=None,
                 href=None,
                 collection=None):
        if stac_extensions is None:
            stac_extensions = []
        if Extension.EO not in stac_extensions:
            stac_extensions.append(Extension.EO)
        super().__init__(id, geometry, bbox, datetime, properties, stac_extensions, href,
                         collection)
        self.gsd = gsd
        self.bands = bands
        self.epsg = epsg
        self.cloud_cover = cloud_cover

    def __repr__(self):
        return '<EOItem id={}>'.format(self.id)

    @classmethod
    def from_dict(cls, d, href=None, root=None):
        item = Item.from_dict(d, href=href, root=root)
        return cls.from_item(item)

    @classmethod
    def from_item(cls, item):
        """Creates an EOItem from an Item.

        Args:
            item (Item): The Item to create an EOItem from.

        Returns:
            EOItem: A new EOItem from item. If the item
                item is already an EOItem, simply returns a clone of item.
        """
        if isinstance(item, EOItem):
            return item.clone()

        eo_params = {}
        for eof in EOItem._EO_FIELDS:
            eo_key = EOItem._eo_key(eof)
            if eo_key in item.properties.keys():
                if eof == 'bands':
                    eo_params[eof] = [Band.from_dict(b) for b in item.properties.pop(eo_key)]
                else:
                    eo_params[eof] = item.properties.pop(eo_key)
            elif eof in ('gsd', 'bands'):
                raise STACError("Missing required field '{}' in properties".format(eo_key))

        if not any(item.properties):
            item.properties = None

        e = cls(id=item.id,
                geometry=item.geometry,
                bbox=item.bbox,
                datetime=item.datetime,
                properties=item.properties,
                stac_extensions=item.stac_extensions,
                collection=item.collection_id,
                **eo_params)

        e.links = item.links
        e.assets = item.assets

        for k, v in item.assets.items():
            if EOAsset.is_eo_asset(v):
                e.assets[k] = EOAsset.from_asset(v)
            e.assets[k].set_owner(e)

        return e

    def get_eo_assets(self):
        """Gets the assets of this item that are :class:`~pystac.EOAsset` s.

        Returns:
            Dict[EOAsset]: This item's assets, subestted to only include EOAssets.
        """
        return {k: v for k, v in self.assets.items() if isinstance(v, EOAsset)}

    def add_asset(self, key, asset):
        """Adds an Asset to this item. If this Asset contains band  information
        in it's properties, converts the Asset to an :class:`~pystac.EOAsset`.

        Args:
            key (str): The unique key of this asset.
            asset (Asset): The Asset to add.
        """
        if asset.properties is not None and 'eo:bands' in asset.properties:
            asset = EOAsset.from_asset(asset)
        return super().add_asset(key, asset)

    def clone(self):
        c = super(EOItem, self).clone()
        self._add_eo_fields_to_dict(c.properties)
        return EOItem.from_item(c)

    def to_dict(self, include_self_link=True):
        d = super().to_dict(include_self_link=include_self_link)
        if 'properties' not in d.keys():
            d['properties'] = {}
        self._add_eo_fields_to_dict(d['properties'])
        return deepcopy(d)

    def _add_eo_fields_to_dict(self, d):
        for eof in EOItem._EO_FIELDS:
            try:
                a = getattr(self, eof)
                if a is not None:
                    d[EOItem._eo_key(eof)] = a
                    if eof == 'bands':
                        d['eo:bands'] = [b.to_dict() for b in d['eo:bands']]
            except AttributeError:
                pass


class EOAsset(Asset):
    """An Asset that contains band information via a bands property that is an array of 0
    based indexes to the correct band object on the owning EOItem.

    Args:
        href (str): Link to the asset object. Relative and absolute links are both allowed.
        bands (List[int]): Lists the band names available in the asset.
        title (str): Optional displayed title for clients and users.
        description (str): A description of the Asset providing additional details, such as
            how it was processed or created. CommonMark 0.29 syntax MAY be used for rich
            text representation.
        media_type (str): Optional description of the media type. Registered Media Types
            are preferred. See :class:`~pystac.MediaType` for common media types.
        roles ([str]): Optional, Semantic roles (i.e. thumbnail, overview, data, metadata)
            of the asset.
        properties (dict): Optional, additional properties for this asset.

    Attributes:
        href (str): Link to the asset object. Relative and absolute links are both allowed.
        bands (List[int]): Lists the band names available in the asset.
        title (str): Optional displayed title for clients and users.
        description (str): A description of the Asset providing additional details, such as
            how it was processed or created. CommonMark 0.29 syntax MAY be used for rich
            text representation.
        media_type (str): Optional description of the media type. Registered Media Types
            are preferred. See :class:`~pystac.MediaType` for common media types.
        roles ([str]): Optional, Semantic roles (i.e. thumbnail, overview, data, metadata)
            of the asset.
        properties (dict): Optional, additional properties for this asset. This is used by
            extensions as a way to serialize and deserialize properties on asset
            object JSON.
        owner (Item or None): The Item this asset belongs to.
    """
    def __init__(self,
                 href,
                 bands,
                 title=None,
                 description=None,
                 media_type=None,
                 roles=None,
                 properties=None):
        super().__init__(href, title, description, media_type, roles, properties)
        self.bands = bands

    @staticmethod
    def is_eo_asset(asset):
        """Method for checking if an Asset represents an EOAsset.

        Args:
            asset (Asset): The asset to check.

        Returns:
            bool: True if the asset is an instance of EOAsset, or if
            the asset contains eo:band information in it's properties.
        """
        if isinstance(asset, EOAsset):
            return True
        return asset.properties is not None and \
            'eo:bands' in asset.properties

    @staticmethod
    def from_dict(d):
        """Constructs an EOAsset from a dict.

        Returns:
            EOAsset: The EOAsset deserialized from the JSON dict.
        """
        asset = Asset.from_dict(d)
        return EOAsset.from_asset(asset)

    @classmethod
    def from_asset(cls, asset):
        """Constructs an EOAsset from an Asset.

        Returns:
            EOAsset: The EOAsset created from this asset. If the asset is
            already an EOAsset, will return a clone.

        Raises:
            :class:`~pystac.STACError`: Raised if no band information is in the properties
            of asset.
        """
        a = asset.clone()
        if isinstance(a, EOAsset):
            return a
        if not a.properties or 'eo:bands' not in a.properties.keys():
            raise STACError('Missing eo:bands property in asset.')
        bands = a.properties.pop('eo:bands')
        properties = None
        if any(a.properties):
            properties = a.properties

        return cls(href=a.href,
                   bands=bands,
                   title=a.title,
                   description=a.description,
                   media_type=a.media_type,
                   roles=a.roles,
                   properties=properties)

    def to_dict(self):
        """Generate a dictionary representing the JSON of this EOAsset.

        Returns:
            dict: A serializion of the EOAsset that can be written out as JSON.
        """
        d = super().to_dict()
        d['eo:bands'] = self.bands

        return d

    def clone(self):
        return EOAsset(href=self.href,
                       title=self.title,
                       description=self.description,
                       media_type=self.media_type,
                       bands=self.bands,
                       roles=self.roles,
                       properties=self.properties)

    def __repr__(self):
        return '<EOAsset href={}>'.format(self.href)

    def get_bands(self):
        """Returns the band information from the owning item for the bands referenced
        by this EOAsset.

        Returns:
            List[Band]: The band information from the owning item for each band that
            is represented by this EOAsset's :attr:`~pystac.EOAsset.bands`.

        Raises:
            :class:`~pystac.STACError`: Raised if no band information is in the properties
            of asset.
        """

        if not self.owner:
            raise STACError('Asset is currently not associated with an item.')
        return [self.owner.bands[i] for i in self.bands]


class Band:
    """Represents Band information attached to an EOItem.

    Args:
        name (str): The name of the band (e.g., "B01", "B02", "B1", "B5", "QA").
        common_name (str): The name commonly used to refer to the band to make it easier
            to search for bands across instruments. See the `list of accepted common names
            <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/eo#common-band-names>`_.
        description (str): Description to fully explain the band.
        center_wavelength (float): The center wavelength of the band, in micrometers (μm).
        full_width_half_max (float): Full width at half maximum (FWHM). The width of the band,
            as measured at half the maximum transmission, in micrometers (μm).

    Attributes:
        name (str): The name of the band (e.g., "B01", "B02", "B1", "B5", "QA").
        common_name (str): The name commonly used to refer to the band to make it easier
            to search for bands across instruments. See the `list of accepted common names
            <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/eo#common-band-names>`_.
        description (str): Description to fully explain the band.
        center_wavelength (float): The center wavelength of the band, in micrometers (μm).
        full_width_half_max (float): Full width at half maximum (FWHM). The width of the band,
            as measured at half the maximum transmission, in micrometers (μm).
    """
    def __init__(self,
                 name=None,
                 common_name=None,
                 description=None,
                 center_wavelength=None,
                 full_width_half_max=None):
        self.name = name
        self.common_name = common_name
        self.description = description
        self.center_wavelength = center_wavelength
        self.full_width_half_max = full_width_half_max

    def __repr__(self):
        return '<Band name={}>'.format(self.name)

    @staticmethod
    def band_range(common_name):
        """Gets the band range for a common band name.

        Args:
            common_name (str): The common band name. Must be one of the `list of accepted common names <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/eo#common-band-names>`_.

        Returns:
            Tuple[float, float] or None: The band range for this name as (min, max), or
            None if this is not a recognized common name.
        """ # noqa E501
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

        return name_to_range.get(common_name)

    @staticmethod
    def band_description(common_name):
        """Returns a description of the band for one with a common name.

        Args:
            common_name (str): The common band name. Must be one of the `list of accepted common names <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/eo#common-band-names>`_.

        Returns:
            str or None: If a recognized common name, returns a description including the
            band range. Otherwise returns None.
        """ # noqa E501
        r = Band.band_range(common_name)
        if r is not None:
            r = "Common name: {}, Range: {} to {}".format(common_name, r[0], r[1])
        return r

    @staticmethod
    def from_dict(d):
        """Constructs a Band from a dict.

        Returns:
            Band: The Band deserialized from the JSON dict.
        """
        name = d.get('name')
        common_name = d.get('common_name')
        center_wavelength = d.get('center_wavelength')
        full_width_half_max = d.get('full_width_half_max')
        description = d.get('description')

        return Band(name=name,
                    common_name=common_name,
                    description=description,
                    center_wavelength=center_wavelength,
                    full_width_half_max=full_width_half_max)

    def to_dict(self):
        """Generate a dictionary representing the JSON of this Band.

        Returns:
            dict: A serializion of the Band that can be written out as JSON.
        """
        d = {}
        if self.name:
            d['name'] = self.name
        if self.common_name:
            d['common_name'] = self.common_name
        if self.center_wavelength:
            d['center_wavelength'] = self.center_wavelength
        if self.full_width_half_max:
            d['full_width_half_max'] = self.full_width_half_max
        if self.description:
            d['description'] = self.description
        return deepcopy(d)
