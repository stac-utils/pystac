import os
from copy import copy, deepcopy

import dateutil.parser

import pystac
from pystac import (STAC_VERSION, STACError)
from pystac.link import Link, LinkType
from pystac.stac_object import STACObject
from pystac.utils import (is_absolute_href, make_absolute_href, make_relative_href, datetime_to_str,
                          str_to_datetime)
from pystac.collection import Collection, Provider


class Item(STACObject):
    """An Item is the core granular entity in a STAC, containing the core metadata
    that enables any client to search or crawl online catalogs of spatial 'assets' -
    satellite imagery, derived data, DEM's, etc.

    Args:
        id (str): Provider identifier. Must be unique within the STAC.
        geometry (dict): Defines the full footprint of the asset represented by this item,
            formatted according to `RFC 7946, section 3.1 (GeoJSON)
            <https://tools.ietf.org/html/rfc7946>`_.
        bbox (List[float]):  Bounding Box of the asset represented by this item using
            either 2D or 3D geometries. The length of the array must be 2*n where n is the
            number of dimensions.
        datetime (datetime): Datetime associated with this item.
        properties (dict): A dictionary of additional metadata for the item.
        stac_extensions (List[str]): Optional list of extensions the Item implements.
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
        datetime (datetime): Datetime associated with this item.
        properties (dict): A dictionary of additional metadata for the item.
        stac_extensions (List[str] or None): Optional list of extensions the Item implements.
        collection (Collection or None): Collection that this item is a part of.
        links (List[Link]): A list of :class:`~pystac.Link` objects representing
            all links associated with this STACObject.
        assets (Dict[str, Asset]): Dictionary of asset objects that can be downloaded,
            each with a unique key.
        collection_id (str or None): The Collection ID that this item belongs to, if any.
    """
    def __init__(self,
                 id,
                 geometry,
                 bbox,
                 datetime,
                 properties,
                 stac_extensions=None,
                 href=None,
                 collection=None):
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

        if collection is not None:
            if isinstance(collection, Collection):
                self.set_collection(collection)
            else:
                self.collection_id = collection
        else:
            self.collection_id = None

    def __repr__(self):
        return '<Item id={}>'.format(self.id)

    def get_assets(self):
        """Get this item's assets.

        Returns:
            Dict[str, Asset]: A copy of the dictonary of this item's assets.
        """
        return dict(self.assets.items())

    def add_asset(self, key, asset):
        """Adds an Asset to this item.

        Args:
            key (str): The unique key of this asset.
            asset (Asset): The Asset to add.
        """
        asset.set_owner(self)
        self.assets[key] = asset
        return self

    def make_asset_hrefs_relative(self):
        """Modify each asset's HREF to be relative to this item's self HREF.

        Returns:
            Item: self
        """
        self_href = self.get_self_href()
        if self_href is None:
            raise STACError('Cannot make asset HREFs relative if no self_href is set.')
        for asset in self.assets.values():
            asset.href = make_relative_href(asset.href, self_href)
        return self

    def make_asset_hrefs_absolute(self):
        """Modify each asset's HREF to be absolute.

        Any asset HREFs that are relative will be modified to absolute based on this
        item's self HREF.

        Returns:
            Item: self
        """
        self_href = None
        for asset in self.assets.values():
            href = asset.href
            if not is_absolute_href(href):
                if self_href is None:
                    self_href = self.get_self_href()
                    if self_href is None:
                        raise STACError('Cannot make relative asset HREFs absolute '
                                        'if no self_href is set.')
                asset.href = make_absolute_href(asset.href, self_href)

        return self

    def set_collection(self, collection, link_type=None):
        """Set the collection of this item.

        This method will replace any existing Collection link and attribute for
        this item.

        Args:
            collection (Collection): The collection to set as this item's collection.
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
        self.add_link(Link.collection(collection, link_type=link_type))
        self.collection_id = collection.id
        return self

    def to_dict(self, include_self_link=True):
        links = self.links
        if not include_self_link:
            links = filter(lambda x: x.rel != 'self', links)

        assets = dict(map(lambda x: (x[0], x[1].to_dict()), self.assets.items()))

        self.properties['datetime'] = datetime_to_str(self.datetime)

        d = {
            'type': 'Feature',
            'stac_version': STAC_VERSION,
            'id': self.id,
            'properties': self.properties,
            'geometry': self.geometry,
            'bbox': self.bbox,
            'links': [link.to_dict() for link in links],
            'assets': assets
        }

        if self.stac_extensions is not None:
            d['stac_extensions'] = self.stac_extensions

        if self.collection_id:
            d['collection'] = self.collection_id

        return deepcopy(d)

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
        return ['collection'] + (pystac.STAC_EXTENSIONS.get_extended_object_links(self))

    def normalize_hrefs(self, root_href):
        if not is_absolute_href(root_href):
            root_href = make_absolute_href(root_href, os.getcwd(), start_is_dir=True)

        old_self_href = self.get_self_href()
        new_self_href = os.path.join(root_href, '{}.json'.format(self.id))
        self.set_self_href(new_self_href)

        # Make sure relative asset links remain valid.
        # This will only work if there is a self href set.
        for asset in self.assets.values():
            asset_href = asset.href
            if not is_absolute_href(asset_href):
                if old_self_href is not None:
                    abs_href = make_absolute_href(asset_href, old_self_href)
                    new_relative_href = make_relative_href(abs_href, new_self_href)
                    asset.href = new_relative_href

    def fully_resolve(self):
        link_rels = set(self._object_links())
        for link in self.links:
            if link.rel in link_rels:
                if not link.is_resolved():
                    link.resolve_stac_object(root=self.get_root())

    @classmethod
    def from_dict(cls, d, href=None, root=None):
        id = d['id']
        geometry = d['geometry']
        bbox = d['bbox']
        properties = d['properties']
        stac_extensions = d.get('stac_extensions')
        collection_id = None
        if 'collection' in d.keys():
            collection_id = d['collection']

        datetime = properties.get('datetime')
        if datetime is None:
            raise STACError('Item dict is missing a "datetime" property in the "properties" field')
        datetime = dateutil.parser.parse(datetime)

        item = Item(id=id,
                    geometry=geometry,
                    bbox=bbox,
                    datetime=datetime,
                    properties=properties,
                    stac_extensions=stac_extensions,
                    collection=collection_id)

        has_self_link = False
        for link in d['links']:
            has_self_link |= link['rel'] == 'self'
            item.add_link(Link.from_dict(link))

        if not has_self_link and href is not None:
            item.add_link(Link.self_href(href))

        for k, v in d['assets'].items():
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


class Asset:
    """An object that contains a link to data associated with the Item that can be
    downloaded or streamed.

    Args:
        href (str): Link to the asset object. Relative and absolute links are both allowed.
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

    Attributes:
        href (str): Link to the asset object. Relative and absolute links are both allowed.
        title (str): Optional displayed title for clients and users.
        description (str): A description of the Asset providing additional details, such as
            how it was processed or created. CommonMark 0.29 syntax MAY be used for rich
            text representation.
        media_type (str): Optional description of the media type. Registered Media Types
            are preferred. See :class:`~pystac.MediaType` for common media types.
        properties (dict): Optional, additional properties for this asset. This is used by
            extensions as a way to serialize and deserialize properties on asset
            object JSON.
        owner (Item or None): The Item this asset belongs to.
    """
    def __init__(self,
                 href,
                 title=None,
                 description=None,
                 media_type=None,
                 roles=None,
                 properties=None):
        self.href = href
        self.title = title
        self.description = description
        self.media_type = media_type
        self.roles = roles

        if properties is not None:
            self.properties = properties
        else:
            self.properties = {}

        # The Item which owns this Asset.
        self.owner = None

    def set_owner(self, item):
        """Sets the owning item of this Asset.

        The owning item will be used to resolve relative HREFs of this asset.

        Args:
            item (Item): The Item that owns this asset.
        """
        self.owner = item

    def get_absolute_href(self):
        """Gets the absolute href for this asset, if possible.

        If this Asset has no associated Item, this will return whatever the
        href is (as it cannot determine the absolute path, if the asset
        href is relative).

        Returns:
            str: The absolute HREF of this asset, or a relative HREF is an abslolute HREF
            cannot be determined.
        """
        if not is_absolute_href(self.href):
            if self.owner is not None:
                return make_absolute_href(self.href, self.owner.get_self_href())

        return self.href

    def to_dict(self):
        """Generate a dictionary representing the JSON of this Asset.

        Returns:
            dict: A serializion of the Asset that can be written out as JSON.
        """

        d = {'href': self.href}

        if self.media_type is not None:
            d['type'] = self.media_type

        if self.title is not None:
            d['title'] = self.title

        if self.description is not None:
            d['description'] = self.description

        if self.properties is not None and len(self.properties) > 0:
            for k, v in self.properties.items():
                d[k] = v

        if self.roles is not None:
            d['roles'] = self.roles

        return deepcopy(d)

    def clone(self):
        """Clones this asset.

        Returns:
            Asset: The clone of this asset.
        """
        return Asset(href=self.href,
                     title=self.title,
                     description=self.description,
                     media_type=self.media_type,
                     roles=self.roles,
                     properties=self.properties)

    def __repr__(self):
        return '<Asset href={}>'.format(self.href)

    @staticmethod
    def from_dict(d):
        """Constructs an Asset from a dict.

        Returns:
            Asset: The Asset deserialized from the JSON dict.
        """
        d = copy(d)
        href = d.pop('href')
        media_type = d.pop('type', None)
        title = d.pop('title', None)
        description = d.pop('description', None)
        roles = d.pop('roles', None)
        properties = None
        if any(d):
            properties = d

        return Asset(href=href,
                     media_type=media_type,
                     title=title,
                     description=description,
                     roles=roles,
                     properties=properties)


class CommonMetadata:
    """Object containing fields that are not included in core item schema but
    are still commonly used. All attributes are defined within the properties of
    this item and are optional

    Args:
        properties (dict): Dictionary of attributes to search for common
            common metadata fields in
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
        start_datetime = self.properties.get('start_datetime')
        if start_datetime:
            start_datetime = str_to_datetime(start_datetime)

        return start_datetime

    @start_datetime.setter
    def start_datetime(self, v):
        self.properties['start_datetime'] = v

    @property
    def end_datetime(self):
        """Get or set the item's end_datetime. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Returns:
            datetime: End date and time for the item
        """
        end_datetime = self.properties.get('end_datetime')
        if end_datetime:
            end_datetime = str_to_datetime(end_datetime)

        return end_datetime

    @end_datetime.setter
    def end_datetime(self, v):
        self.properties['end_datetime'] = v

    # License
    @property
    def license(self):
        """Get or set the current license

        Returns:
            str: Item's license(s), either SPDX identifier of 'various'
        """
        return self.properties.get('license')

    @license.setter
    def license(self, v):
        self.properties['license'] = v

    # Providers
    @property
    def providers(self):
        """Get or set a list of the item's providers. The setter can take either
        a Provider object or a dict but always stores each provider as a dict

        Returns:
            [Provider]: List of organizations that captured or processed the data,
            encoded as Provider objects
        """
        providers = self.properties.get('providers')
        if providers is not None:
            providers = [Provider.from_dict(d) for d in providers]

        return providers

    @providers.setter
    def providers(self, v):
        self.properties['providers'] = v

    # Instrument
    @property
    def platform(self):
        """Get or set the item's platform attribute

        Returns:
            str: Unique name of the specific platform to which the instrument
            is attached
        """
        return self.properties.get('platform')

    @platform.setter
    def platform(self, v):
        self.properties['platform'] = v

    @property
    def instruments(self):
        """Get or set the names of the instruments used

        Returns:
            [str]: Name(s) of instrument(s) used
        """
        return self.properties.get('instruments')

    @instruments.setter
    def instruments(self, v):
        self.properties['instruments'] = v

    @property
    def constellation(self):
        """Get or set the name of the constellation associate with an item

        Returns:
            str: Name of the constellation to which the platform belongs
        """
        return self.properties.get('constellation')

    @constellation.setter
    def constellation(self, v):
        self.properties['constellation'] = v

    @property
    def mission(self):
        """Get or set the name of the mission associated with an item

        Returns:
            str: Name of the mission in which data are collected
        """
        return self.properties.get('mission')

    @mission.setter
    def mission(self, v):
        self.properties['mission'] = v

    # Metadata
    @property
    def created(self):
        """Get or set the metadata file's creation date. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Returns:
            datetime: Creation date and time of the metadata file
        """
        created = self.properties.get('created')
        if created:
            created = str_to_datetime(created)

        return created

    @created.setter
    def created(self, v):
        self.properties['created'] = v

    @property
    def updated(self):
        """Get or set the metadata file's creation date. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Returns:
            datetime: Date and time that the metadata file was most recently
                updated
        """
        updated = self.properties.get('updated')
        if updated:
            updated = str_to_datetime(updated)

        return updated

    @updated.setter
    def updated(self, v):
        self.properties['updated'] = v
