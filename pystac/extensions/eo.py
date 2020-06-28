from copy import deepcopy

from pystac import (STACError, Extensions)
from pystac.item import (Item, Asset)
from pystac.extensions.base import (ItemExtension, ExtensionDefinition, ExtendedObject)


class EOItemExt(ItemExtension):
    """EOItem represents a snapshot of the earth for a single date and time.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The Item that is being extended.
    """
    _EO_FIELDS = ['gsd', 'bands', 'epsg', 'cloud_cover']

    @staticmethod
    def _eo_key(key):
        return 'eo:{}'.format(key)

    def __init__(self, item):
        if item.stac_extensions is None:
            item.stac_extensions = [Extensions.EO]
        elif Extensions.LABEL not in item.stac_extensions:
            item.stac_extensions.append(Extensions.EO)

        self.item = item

    def apply(gsd,
              bands,
              cloud_cover=None):
        self.gsd = gsd
        self.bands = bands
        self.cloud_cover = cloud_cover

    @property
    def gsd(self):
        """Get or sets the Ground Sample Distance at the sensor.

        Returns:
            [float]
        """
        return self.item.properties.get('eo:gsd')

    @gsd.setter
    def gsd(self, v):
        self.item.properties['eo:gsd'] = v

    @property
    def bands(self):
        """Get or sets a list of :class:`~pystac.Band` objects that represent
            the available bands.

        Returns:
            [List[Band]]
        """
        bands = self.item.properties.get('eo:bands')
        if bands is None:
            raise STACError("Missing required field 'eo:bands' in item properties")
        return  [Band.from_dict(b) for b in bands]

    @bands.setter
    def bands(self, v):
        self.item.properties['eo:bands'] = [b.to_dict() for b in v]

    @property
    def cloud_cover(self):
        """Get or sets the estimate of cloud cover as a percentage (0-100) of the
            entire scene. If not available the field should not be provided.

        Returns:
            [float or None]
        """
        return self.item.properties.get('eo:cloud_cover')

    @cloud_cover.setter
    def cloud_cover(self, v):
        self.item.properties['eo:cloud_cover'] = v

    def __repr__(self):
        return '<EOItemExt Item id={}>'.format(self.id)

    def get_bands(self, asset_key):
        """Gets the bands for the item's asset if the exist.

        If the asset_key doesn't exist returns None.

        Returns:
            [List[Band] or None]: A list of Band objects associated with asset, or None
            if the asset doesn't exist or does not contain band information.
        """
        asset = self.item.assets.get(asset_key)
        if asset is None:
            return None
        if 'eo:bands' not in asset.properties:
            return None

        result = []
        band_length = len(self.item.bands)
        for band_idx in asset.properties['eo:bands']:
            if band_idx >= band_length:
                raise STACError("Item {} contains assets with band indexes out of range! "
                                "Band index {} is greater than the number of bands "
                                "for the item ({})".format(self.item.id, band_idx, band_length))
            result.append(self.item.bands[band_idx])

        return result

    def set_bands(self, asset_key, band_names):
        """Sets the band information for an asset of this item.

        Args:
            band_names (List[str]): List of band names to assign to the asset.
                These names must reference names in the item's bands property.
        """
        asset = self.item.assets.get(asset_key)
        if asset is None:
            raise KeyError("Asset with key {} does not exist in Item '{}'".format(
                asset_key, self.item.id))
        band_idxs = [
            i for i, b in enumerate(self.item.bands)
            if b.name in band_names
        ]

        if len(set(band_idxs)) != len(set(band_names)):
            missing_band_names = set(band_names) - set([
                self.item.bands[i] for i in band_idxs
            ])

            raise KeyError("Bands not found in item's bands: {}".format(
                ','.join(map(lambda x: "'{}'".format(x), missing_band_names))
            ))

        asset.properties['eo:bands'] = band_idxs

    @classmethod
    def _object_links(cls):
        return []

    @classmethod
    def from_item(cls, item):
        return cls(item)


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

EO_EXTENSION_DEFINITION = ExtensionDefinition("eo", [
    ExtendedObject(Item, EOItemExt)
])
