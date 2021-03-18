from copy import copy, deepcopy

import dateutil.parser

import pystac
from pystac import (STACError, STACObjectType, STACObject)
from pystac.link import Link, LinkType

from pystac.utils import (datetime_to_str, str_to_datetime)
from pystac.collection import Collection, Provider
from pystac.asset import Asset, AssetsMixin


class Item(AssetsMixin, STACObject):
    """An Item is the core granular entity in a STAC, containing the core metadata
    that enables any client to search or crawl online catalogs of spatial 'assets' -
    satellite imagery, derived data, DEM's, etc.

    Args:
        id (str): Provider identifier. Must be unique within the STAC.
        geometry (dict): Defines the full footprint of the asset represented by this item,
            formatted according to `RFC 7946, section 3.1 (GeoJSON)
            <https://tools.ietf.org/html/rfc7946>`_.
        bbox (List[float] or None):  Bounding Box of the asset represented by this item using
            either 2D or 3D geometries. The length of the array must be 2*n where n is the
            number of dimensions. Could also be None in the case of a null geometry.
        datetime (datetime or None): Datetime associated with this item. If None,
            a start_datetime and end_datetime must be supplied in the properties.
        properties (dict): A dictionary of additional metadata for the item.
        stac_extensions (List[str]): Optional list of extensions the Item implements.
        href (str or None): Optional HREF for this item, which be set as the item's
            self link's HREF.
        collection (Collection or str): The Collection or Collection ID that this item
            belongs to.
        extra_fields (dict or None): Extra fields that are part of the top-level JSON properties
            of the Item.

    Attributes:
        id (str): Provider identifier. Unique within the STAC.
        geometry (dict): Defines the full footprint of the asset represented by this item,
            formatted according to `RFC 7946, section 3.1 (GeoJSON)
            <https://tools.ietf.org/html/rfc7946>`_.
        bbox (List[float] or None):  Bounding Box of the asset represented by this item using
            either 2D or 3D geometries. The length of the array is 2*n where n is the
            number of dimensions. Could also be None in the case of a null geometry.
        datetime (datetime or None): Datetime associated with this item. If None,
            the start_datetime and end_datetime in the common_metadata
            will supply the datetime range of the Item.
        properties (dict): A dictionary of additional metadata for the item.
        stac_extensions (List[str] or None): Optional list of extensions the Item implements.
        collection (Collection or None): Collection that this item is a part of.
        links (List[Link]): A list of :class:`~pystac.Link` objects representing
            all links associated with this STACObject.
        assets (Dict[str, Asset]): Dictionary of asset objects that can be downloaded,
            each with a unique key.
        collection_id (str or None): The Collection ID that this item belongs to, if any.
        extra_fields (dict or None): Extra fields that are part of the top-level JSON properties
            of the Item.
    """

    STAC_OBJECT_TYPE = STACObjectType.ITEM

    def __init__(self,
                 id,
                 geometry,
                 bbox,
                 datetime,
                 properties,
                 stac_extensions=None,
                 href=None,
                 collection=None,
                 extra_fields=None):
        super().__init__(stac_extensions)

        self.id = id
        self.geometry = geometry
        self.bbox = bbox
        self.datetime = datetime
        self.properties = properties
        if extra_fields is None:
            self.extra_fields = {}
        else:
            self.extra_fields = extra_fields

        self.assets = {}

        if datetime is None:
            if 'start_datetime' not in properties or \
               'end_datetime' not in properties:
                raise STACError('Invalid Item: If datetime is None, '
                                'a start_datetime and end_datetime '
                                'must be supplied in '
                                'the properties.')

        if href is not None:
            self.set_self_href(href)

        if collection is not None:
            if isinstance(collection, Collection):
                self.set_collection(collection)
            else:
                self.collection_id = collection
        else:
            self.collection_id = None

    def __repr__(self):
        return '<Item id={}>'.format(self.id)

    def get_datetime(self, asset=None):
        """Gets an Item or an Asset datetime.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value.

        Returns:
            datetime or None
        """
        if asset is None or 'datetime' not in asset.properties:
            return self.datetime
        else:
            return str_to_datetime(asset.properties.get('datetime'))

    def set_datetime(self, datetime, asset=None):
        """Set an Item or an Asset datetime.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.datetime = datetime
        else:
            asset.properties['datetime'] = datetime_to_str(datetime)

    def set_collection(self, collection, link_type=None):
        """Set the collection of this item.

        This method will replace any existing Collection link and attribute for
        this item.

        Args:
            collection (Collection or None): The collection to set as this
                item's collection. If None, will clear the collection.
            link_type (str): the link type to use for the collection link.
                One of :class:`~pystac.LinkType`.

        Returns:
            Item: self
        """
        if not link_type:
            prev = self.get_single_link('collection')
            if prev is not None:
                link_type = prev.link_type
            else:
                link_type = LinkType.ABSOLUTE
        self.remove_links('collection')
        self.collection_id = None
        if collection is not None:
            self.add_link(Link.collection(collection, link_type=link_type))
            self.collection_id = collection.id

        return self

    def get_collection(self):
        """Gets the collection of this item, if one exists.

        Returns:
            Collection or None: If this item belongs to a collection, returns
            a reference to the collection. Otherwise returns None.
        """
        collection_link = self.get_single_link('collection')
        if collection_link is None:
            return None
        else:
            return collection_link.resolve_stac_object().target

    def to_dict(self, include_self_link=True):
        links = self.links
        if not include_self_link:
            links = filter(lambda x: x.rel != 'self', links)

        assets = dict(map(lambda x: (x[0], x[1].to_dict()), self.assets.items()))

        if self.datetime is not None:
            self.properties['datetime'] = datetime_to_str(self.datetime)
        else:
            self.properties['datetime'] = None

        d = {
            'type': 'Feature',
            'stac_version': pystac.get_stac_version(),
            'id': self.id,
            'properties': self.properties,
            'geometry': self.geometry,
            'links': [link.to_dict() for link in links],
            'assets': assets
        }

        if self.bbox is not None:
            d['bbox'] = self.bbox

        if self.stac_extensions is not None:
            d['stac_extensions'] = self.stac_extensions

        if self.collection_id:
            d['collection'] = self.collection_id

        for key in self.extra_fields:
            d[key] = self.extra_fields[key]

        return d

    def clone(self):
        clone = Item(id=self.id,
                     geometry=deepcopy(self.geometry),
                     bbox=copy(self.bbox),
                     datetime=copy(self.datetime),
                     properties=deepcopy(self.properties),
                     stac_extensions=deepcopy(self.stac_extensions),
                     collection=self.collection_id)
        for link in self.links:
            clone.add_link(link.clone())

        for k, asset in self.assets.items():
            clone.add_asset(k, asset.clone())

        return clone

    def _object_links(self):
        return ['collection'] + (pystac.STAC_EXTENSIONS.get_extended_object_links(self))

    @classmethod
    def from_dict(cls, d, href=None, root=None):
        d = deepcopy(d)
        id = d.pop('id')
        geometry = d.pop('geometry')
        properties = d.pop('properties')
        bbox = d.pop('bbox', None)
        stac_extensions = d.get('stac_extensions')
        collection_id = d.pop('collection', None)

        datetime = properties.get('datetime')
        if datetime is not None:
            datetime = dateutil.parser.parse(datetime)
        links = d.pop('links')
        assets = d.pop('assets')

        d.pop('type')
        d.pop('stac_version')

        item = Item(id=id,
                    geometry=geometry,
                    bbox=bbox,
                    datetime=datetime,
                    properties=properties,
                    stac_extensions=stac_extensions,
                    collection=collection_id,
                    extra_fields=d)

        has_self_link = False
        for link in links:
            has_self_link |= link['rel'] == 'self'
            item.add_link(Link.from_dict(link))

        if not has_self_link and href is not None:
            item.add_link(Link.self_href(href))

        for k, v in assets.items():
            asset = Asset.from_dict(v)
            asset.set_owner(item)
            item.assets[k] = asset

        return item

    @property
    def common_metadata(self):
        """Access the item's common metadat fields as a CommonMetadata object

        Returns:
            CommonMetada: contains all common metadata fields in the items properties
        """
        return CommonMetadata(self.properties)


class CommonMetadata:
    """Object containing fields that are not included in core item schema but
    are still commonly used. All attributes are defined within the properties of
    this item and are optional

    Args:
        properties (dict): Dictionary of attributes that is the Item's properties
    """
    def __init__(self, properties):
        self.properties = properties

    # Basics
    @property
    def title(self):
        """Get or set the item's title

        Returns:
            str: Human readable title describing the item
        """
        return self.properties.get('title')

    @title.setter
    def title(self, v):
        self.properties['title'] = v

    @property
    def description(self):
        """Get or set the item's description

        Returns:
            str: Detailed description of the item
        """
        return self.properties.get('description')

    @description.setter
    def description(self, v):
        self.properties['description'] = v

    # Date and Time Range
    @property
    def start_datetime(self):
        """Get or set the item's start_datetime. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Returns:
            datetime: Start date and time for the item
        """
        return self.get_start_datetime()

    @start_datetime.setter
    def start_datetime(self, v):
        self.set_start_datetime(v)

    def get_start_datetime(self, asset=None):
        """Gets an Item or an Asset start_datetime.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            datetime
        """
        if asset is None or 'start_datetime' not in asset.properties:
            start_datetime = self.properties.get('start_datetime')
        else:
            start_datetime = asset.properties.get('start_datetime')

        if start_datetime:
            start_datetime = str_to_datetime(start_datetime)

        return start_datetime

    def set_start_datetime(self, start_datetime, asset=None):
        """Set an Item or an Asset start_datetime.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties['start_datetime'] = datetime_to_str(start_datetime)
        else:
            asset.properties['start_datetime'] = datetime_to_str(start_datetime)

    @property
    def end_datetime(self):
        """Get or set the item's end_datetime. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Returns:
            datetime: End date and time for the item
        """
        return self.get_end_datetime()

    @end_datetime.setter
    def end_datetime(self, v):
        self.set_end_datetime(v)

    def get_end_datetime(self, asset=None):
        """Gets an Item or an Asset end_datetime.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            datetime
        """
        if asset is None or 'end_datetime' not in asset.properties:
            end_datetime = self.properties.get('end_datetime')
        else:
            end_datetime = asset.properties.get('end_datetime')

        if end_datetime:
            end_datetime = str_to_datetime(end_datetime)

        return end_datetime

    def set_end_datetime(self, end_datetime, asset=None):
        """Set an Item or an Asset end_datetime.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties['end_datetime'] = datetime_to_str(end_datetime)
        else:
            asset.properties['end_datetime'] = datetime_to_str(end_datetime)

    # License
    @property
    def license(self):
        """Get or set the current license

        Returns:
            str: Item's license(s), either SPDX identifier of 'various'
        """
        return self.get_license()

    @license.setter
    def license(self, v):
        self.set_license(v)

    def get_license(self, asset=None):
        """Gets an Item or an Asset license.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or 'license' not in asset.properties:
            return self.properties.get('license')
        else:
            return asset.properties.get('license')

    def set_license(self, license, asset=None):
        """Set an Item or an Asset license.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties['license'] = license
        else:
            asset.properties['license'] = license

    # Providers
    @property
    def providers(self):
        """Get or set a list of the item's providers. The setter can take either
        a Provider object or a dict but always stores each provider as a dict

        Returns:
            List[Provider]: List of organizations that captured or processed the data,
            encoded as Provider objects
        """
        return self.get_providers()

    @providers.setter
    def providers(self, v):
        self.set_providers(v)

    def get_providers(self, asset=None):
        """Gets an Item or an Asset providers.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            List[Provider]
        """
        if asset is None or 'providers' not in asset.properties:
            providers = self.properties.get('providers')
        else:
            providers = asset.properties.get('providers')

        if providers is not None:
            providers = [Provider.from_dict(d) for d in providers]

        return providers

    def set_providers(self, providers, asset=None):
        """Set an Item or an Asset providers.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        providers_dicts = [d.to_dict() for d in providers]
        if asset is None:
            self.properties['providers'] = providers_dicts
        else:
            asset.properties['providers'] = providers_dicts

    # Instrument
    @property
    def platform(self):
        """Get or set the item's platform attribute

        Returns:
            str: Unique name of the specific platform to which the instrument
            is attached
        """
        return self.get_platform()

    @platform.setter
    def platform(self, v):
        self.set_platform(v)

    def get_platform(self, asset=None):
        """Gets an Item or an Asset platform.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or 'platform' not in asset.properties:
            return self.properties.get('platform')
        else:
            return asset.properties.get('platform')

    def set_platform(self, platform, asset=None):
        """Set an Item or an Asset platform.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties['platform'] = platform
        else:
            asset.properties['platform'] = platform

    @property
    def instruments(self):
        """Get or set the names of the instruments used

        Returns:
            List[str]: Name(s) of instrument(s) used
        """
        return self.get_instruments()

    @instruments.setter
    def instruments(self, v):
        self.set_instruments(v)

    def get_instruments(self, asset=None):
        """Gets an Item or an Asset instruments.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            List[str]
        """
        if asset is None or 'instruments' not in asset.properties:
            return self.properties.get('instruments')
        else:
            return asset.properties.get('instruments')

    def set_instruments(self, instruments, asset=None):
        """Set an Item or an Asset instruments.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties['instruments'] = instruments
        else:
            asset.properties['instruments'] = instruments

    @property
    def constellation(self):
        """Get or set the name of the constellation associate with an item

        Returns:
            str: Name of the constellation to which the platform belongs
        """
        return self.get_constellation()

    @constellation.setter
    def constellation(self, v):
        self.set_constellation(v)

    def get_constellation(self, asset=None):
        """Gets an Item or an Asset constellation.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or 'constellation' not in asset.properties:
            return self.properties.get('constellation')
        else:
            return asset.properties.get('constellation')

    def set_constellation(self, constellation, asset=None):
        """Set an Item or an Asset constellation.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties['constellation'] = constellation
        else:
            asset.properties['constellation'] = constellation

    @property
    def mission(self):
        """Get or set the name of the mission associated with an item

        Returns:
            str: Name of the mission in which data are collected
        """
        return self.get_mission()

    @mission.setter
    def mission(self, v):
        self.set_mission(v)

    def get_mission(self, asset=None):
        """Gets an Item or an Asset mission.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or 'mission' not in asset.properties:
            return self.properties.get('mission')
        else:
            return asset.properties.get('mission')

    def set_mission(self, mission, asset=None):
        """Set an Item or an Asset mission.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties['mission'] = mission
        else:
            asset.properties['mission'] = mission

    @property
    def gsd(self):
        """Get or sets the Ground Sample Distance at the sensor.

        Returns:
            [float]: Ground Sample Distance at the senso
        """
        return self.get_gsd()

    @gsd.setter
    def gsd(self, v):
        self.set_gsd(v)

    def get_gsd(self, asset=None):
        """Gets an Item or an Asset gsd.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            float
        """
        if asset is None or 'gsd' not in asset.properties:
            return self.properties.get('gsd')
        else:
            return asset.properties.get('gsd')

    def set_gsd(self, gsd, asset=None):
        """Set an Item or an Asset gsd.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties['gsd'] = gsd
        else:
            asset.properties['gsd'] = gsd

    # Metadata
    @property
    def created(self):
        """Get or set the metadata file's creation date. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Returns:
            datetime: Creation date and time of the metadata file
        """
        return self.get_created()

    @created.setter
    def created(self, v):
        self.set_created(v)

    def get_created(self, asset=None):
        """Gets an Item or an Asset created time.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value.

        Note:
            ``created`` and ``updated`` have different meaning depending on where they are used.
            If those fields are available in the Item `properties`, it's referencing to the
            creation and update times of the metadata. Having those fields in the Item `assets`
            refers to the creation and update times of the actual data linked to
            in the Asset Object.

        Returns:
            datetime
        """
        if asset is None or 'created' not in asset.properties:
            created = self.properties.get('created')
        else:
            created = asset.properties.get('created')

        if created:
            created = str_to_datetime(created)

        return created

    def set_created(self, created, asset=None):
        """Set an Item or an Asset created time.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties['created'] = datetime_to_str(created)
        else:
            asset.properties['created'] = datetime_to_str(created)

    @property
    def updated(self):
        """Get or set the metadata file's update date. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Note:
            ``created`` and ``updated`` have different meaning depending on where they are used.
            If those fields are available in the Item `properties`, it's referencing to the
            creation and update times of the metadata. Having those fields in the Item `assets`
            refers to the creation and update times of the actual data linked to
            in the Asset Object.


        Returns:
            datetime: Date and time that the metadata file was most recently
                updated
        """
        return self.get_updated()

    @updated.setter
    def updated(self, v):
        self.set_updated(v)

    def get_updated(self, asset=None):
        """Gets an Item or an Asset updated time.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value.

        Note:
            ``created`` and ``updated`` have different meaning depending on where they are used.
            If those fields are available in the Item `properties`, it's referencing to the
            creation and update times of the metadata. Having those fields in the Item `assets`
            refers to the creation and update times of the actual data linked to
            in the Asset Object.

        Returns:
            datetime
        """
        if asset is None or 'updated' not in asset.properties:
            updated = self.properties.get('updated')
        else:
            updated = asset.properties.get('updated')

        if updated:
            updated = str_to_datetime(updated)

        return updated

    def set_updated(self, updated, asset=None):
        """Set an Item or an Asset updated time.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties['updated'] = datetime_to_str(updated)
        else:
            asset.properties['updated'] = datetime_to_str(updated)
