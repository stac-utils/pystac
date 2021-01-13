from pystac import Extensions
from pystac.item import Item
from pystac.extensions.base import (ItemExtension, ExtensionDefinition, ExtendedObject)


class EOItemExt(ItemExtension):
    """EOItemExt is the extension of the Item in the eo extension which
    represents a snapshot of the earth for a single date and time.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The Item that is being extended.

    Note:
        Using EOItemExt to directly wrap an item will add the 'eo' extension ID to
        the item's stac_extensions.
    """
    def __init__(self, item):
        if item.stac_extensions is None:
            item.stac_extensions = [Extensions.EO]
        elif Extensions.EO not in item.stac_extensions:
            item.stac_extensions.append(Extensions.EO)

        self.item = item

    def apply(self, bands, cloud_cover=None):
        """Applies label extension properties to the extended Item.

        Args:
            bands (List[Band]): a list of :class:`~pystac.Band` objects that represent
                the available bands.
            cloud_cover (float or None): The estimate of cloud cover as a percentage (0-100) of the
                entire scene. If not available the field should not be provided.
        """
        self.bands = bands
        self.cloud_cover = cloud_cover

    @property
    def bands(self):
        """Get or sets a list of :class:`~pystac.Band` objects that represent
            the available bands.

        Returns:
            List[Band]
        """
        return self.get_bands()

    @bands.setter
    def bands(self, v):
        self.set_bands(v)

    def get_bands(self, asset=None):
        """Gets an Item or an Asset bands.

        If an Asset is supplied and the bands property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value or
        all the asset's eo bands

        Returns:
            List[Band]
        """
        if asset is not None and 'eo:bands' in asset.properties:
            bands = asset.properties.get('eo:bands')
        else:
            bands = self.item.properties.get('eo:bands')

        # get assets with eo:bands even if not in item
        if asset is None and bands is None:
            bands = []
            for (key, value) in self.item.get_assets().items():
                if 'eo:bands' in value.properties:
                    bands.extend(value.properties.get('eo:bands'))

        if bands is not None:
            bands = [Band(b) for b in bands]

        return bands

    def set_bands(self, bands, asset=None):
        """Set an Item or an Asset bands.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        band_dicts = [b.to_dict() for b in bands]
        if asset is not None:
            asset.properties['eo:bands'] = band_dicts
        else:
            self.item.properties['eo:bands'] = band_dicts

    @property
    def cloud_cover(self):
        """Get or sets the estimate of cloud cover as a percentage (0-100) of the
            entire scene. If not available the field should not be provided.

        Returns:
            float or None
        """
        return self.get_cloud_cover()

    @cloud_cover.setter
    def cloud_cover(self, v):
        self.set_cloud_cover(v)

    def get_cloud_cover(self, asset=None):
        """Gets an Item or an Asset cloud_cover.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            float
        """
        if asset is None or 'eo:cloud_cover' not in asset.properties:
            return self.item.properties.get('eo:cloud_cover')
        else:
            return asset.properties.get('eo:cloud_cover')

    def set_cloud_cover(self, cloud_cover, asset=None):
        """Set an Item or an Asset cloud_cover.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.item.properties['eo:cloud_cover'] = cloud_cover
        else:
            asset.properties['eo:cloud_cover'] = cloud_cover

    def __repr__(self):
        return '<EOItemExt Item id={}>'.format(self.item.id)

    @classmethod
    def _object_links(cls):
        return []

    @classmethod
    def from_item(cls, item):
        return cls(item)


class Band:
    """Represents Band information attached to an Item that implements the eo extension.

    Use Band.create to create a new Band.
    """
    def __init__(self, properties):
        self.properties = properties

    def apply(self,
              name,
              common_name=None,
              description=None,
              center_wavelength=None,
              full_width_half_max=None):
        """
        Sets the properties for this Band.

        Args:
            name (str): The name of the band (e.g., "B01", "B02", "B1", "B5", "QA").
            common_name (str): The name commonly used to refer to the band to make it easier
                to search for bands across instruments. See the `list of accepted common names
                <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/eo#common-band-names>`_.
            description (str): Description to fully explain the band.
            center_wavelength (float): The center wavelength of the band, in micrometers (μm).
            full_width_half_max (float): Full width at half maximum (FWHM). The width of the band,
                as measured at half the maximum transmission, in micrometers (μm).
        """
        self.name = name
        self.common_name = common_name
        self.description = description
        self.center_wavelength = center_wavelength
        self.full_width_half_max = full_width_half_max

    @classmethod
    def create(cls,
               name,
               common_name=None,
               description=None,
               center_wavelength=None,
               full_width_half_max=None):
        """
        Creates a new band.

        Args:
            name (str): The name of the band (e.g., "B01", "B02", "B1", "B5", "QA").
            common_name (str): The name commonly used to refer to the band to make it easier
                to search for bands across instruments. See the `list of accepted common names
                <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/eo#common-band-names>`_.
            description (str): Description to fully explain the band.
            center_wavelength (float): The center wavelength of the band, in micrometers (μm).
            full_width_half_max (float): Full width at half maximum (FWHM). The width of the band,
                as measured at half the maximum transmission, in micrometers (μm).
        """
        b = cls({})
        b.apply(name=name,
                common_name=common_name,
                description=description,
                center_wavelength=center_wavelength,
                full_width_half_max=full_width_half_max)
        return b

    @property
    def name(self):
        """Get or sets the name of the band (e.g., "B01", "B02", "B1", "B5", "QA").

        Returns:
            str
        """
        return self.properties.get('name')

    @name.setter
    def name(self, v):
        self.properties['name'] = v

    @property
    def common_name(self):
        """Get or sets the name commonly used to refer to the band to make it easier
            to search for bands across instruments. See the `list of accepted common names
            <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/eo#common-band-names>`_.

        Returns:
            str
        """
        return self.properties.get('common_name')

    @common_name.setter
    def common_name(self, v):
        if v is not None:
            self.properties['common_name'] = v
        else:
            self.properties.pop('common_name', None)

    @property
    def description(self):
        """Get or sets the description to fully explain the band. CommonMark 0.29 syntax MAY be
        used for rich text representation.

        Returns:
            str
        """
        return self.properties.get('description')

    @description.setter
    def description(self, v):
        if v is not None:
            self.properties['description'] = v
        else:
            self.properties.pop('description', None)

    @property
    def center_wavelength(self):
        """Get or sets the center wavelength of the band, in micrometers (μm).

        Returns:
            float
        """
        return self.properties.get('center_wavelength')

    @center_wavelength.setter
    def center_wavelength(self, v):
        if v is not None:
            self.properties['center_wavelength'] = v
        else:
            self.properties.pop('center_wavelength', None)

    @property
    def full_width_half_max(self):
        """Get or sets the full width at half maximum (FWHM). The width of the band,
            as measured at half the maximum transmission, in micrometers (μm).

        Returns:
            [float]
        """
        return self.properties.get('full_width_half_max')

    @full_width_half_max.setter
    def full_width_half_max(self, v):
        if v is not None:
            self.properties['full_width_half_max'] = v
        else:
            self.properties.pop('full_width_half_max', None)

    def __repr__(self):
        return '<Band name={}>'.format(self.name)

    def to_dict(self):
        """Returns the dictionary representing the JSON of this Band.

        Returns:
            dict: The wrapped dict of the Band that can be written out as JSON.
        """
        return self.properties

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


EO_EXTENSION_DEFINITION = ExtensionDefinition(Extensions.EO, [ExtendedObject(Item, EOItemExt)])
